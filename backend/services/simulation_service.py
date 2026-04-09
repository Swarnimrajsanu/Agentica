from loguru import logger
from typing import List, Dict, Optional, Callable, Any
import asyncio
from services.llm_services import llm_service
from services.memory_service import memory_service
from services.graph_service import graph_service
from config.settings import settings
from services.consensus_heatmap_service import consensus_heatmap_service
from services.aggregation_engine import aggregation_engine


class SimulationService:
    """Multi-Agent Simulation Service for orchestrating agent discussions."""
    
    def __init__(self):
        self.active_simulations = {}
        self._human_inbox: Dict[str, asyncio.Queue] = {}
        logger.info("Simulation Service initialized")

    def inject_human_message(
        self,
        simulation_id: str,
        message: str,
        influence_level: float = 0.6,
        display_name: str = "Human",
    ) -> bool:
        """
        Inject a human participant post into a running simulation.
        The message will be appended at the start of the next round.
        """
        sim = self.active_simulations.get(simulation_id)
        if not sim or sim.get("status") != "running":
            return False
        if simulation_id not in self._human_inbox:
            self._human_inbox[simulation_id] = asyncio.Queue()
        payload = {
            "message": message,
            "influence_level": max(0.1, min(1.0, float(influence_level))),
            "display_name": (display_name or "Human").strip()[:40],
        }
        try:
            self._human_inbox[simulation_id].put_nowait(payload)
            return True
        except Exception:
            return False
    
    async def run_simulation(
        self,
        agents: List[Dict],
        topic: str,
        rounds: int = None,
        callback: Optional[Callable] = None
    ) -> Dict:
        """
        Run a multi-agent simulation discussion.
        
        Args:
            agents: List of agent dictionaries with role, personality, etc.
            topic: Discussion topic
            rounds: Number of discussion rounds (defaults to settings.MAX_SIMULATION_ROUNDS)
            callback: Optional callback function for real-time updates
            
        Returns:
            Simulation results including all messages and consensus
        """
        max_rounds = rounds or settings.MAX_SIMULATION_ROUNDS
        simulation_id = f"sim_{topic.replace(' ', '_')[:50]}"
        all_messages = []
        
        logger.info(f"Starting simulation '{simulation_id}' with {len(agents)} agents, {max_rounds} rounds")
        
        # Initialize simulation
        self.active_simulations[simulation_id] = {
            "simulation_id": simulation_id,
            "status": "running",
            "agents": agents,
            "topic": topic,
            "messages": []
        }
        self._human_inbox[simulation_id] = asyncio.Queue()
        
        # PERSIST START
        await memory_service.save_simulation(simulation_id, self.active_simulations[simulation_id])
        
        try:
            # Send initial message to callback
            if callback:
                await callback({
                    "type": "simulation_start",
                    "simulation_id": simulation_id,
                    "topic": topic,
                    "agents": agents
                })
            
            # Run simulation rounds
            for round_num in range(1, max_rounds + 1):
                logger.info(f"Round {round_num}/{max_rounds}")
                
                if callback:
                    await callback({
                        "type": "round_start",
                        "round": round_num,
                        "total_rounds": max_rounds
                    })

                # Drain any pending human posts and inject at start of the round
                try:
                    inbox = self._human_inbox.get(simulation_id)
                    while inbox and not inbox.empty():
                        item = inbox.get_nowait()
                        human_message = {
                            "simulation_id": simulation_id,
                            "round": round_num,
                            "agent_role": item.get("display_name", "Human"),
                            "agent_personality": f"Human participant (reach={item.get('influence_level', 0.6):.2f})",
                            "content": item.get("message", ""),
                            "timestamp": str(__import__("datetime").datetime.utcnow()),
                            "meta": {
                                "type": "human",
                                "influence_level": item.get("influence_level", 0.6),
                            },
                        }
                        all_messages.append(human_message)
                        await memory_service.save_message(human_message)
                        if callback:
                            await callback({"type": "human_injected", "message": human_message})
                except Exception as e:
                    logger.warning(f"Human injection drain failed: {e}")
                
                # Each agent speaks in this round
                for agent in agents:
                    agent_response = await self._generate_agent_response(
                        agent=agent,
                        topic=topic,
                        conversation_history=all_messages,
                        round_num=round_num
                    )
                    
                    if agent_response:
                        message = {
                            "simulation_id": simulation_id,
                            "round": round_num,
                            "agent_role": agent["role"],
                            "agent_personality": agent.get("personality", ""),
                            "content": agent_response,
                            "timestamp": str(__import__('datetime').datetime.utcnow())
                        }
                        
                        all_messages.append(message)
                        
                        # Save to memory
                        await memory_service.save_message(message)
                        
                        # Send to callback
                        if callback:
                            # 1. Send text response
                            await callback({
                                "type": "agent_response",
                                "message": message
                            })
                            
                            # 2. Extract and send graph update
                            try:
                                graph_data = await graph_service.extract_nodes_and_edges(agent_response)
                                if graph_data and graph_data.get("nodes"):
                                    await callback({
                                        "type": "graph_update",
                                        "nodes": graph_data["nodes"],
                                        "links": graph_data["links"],
                                        "agent": agent["role"]
                                    })
                            except Exception as ge:
                                logger.warning(f"Live graph extraction failed: {ge}")
                
                if callback:
                    await callback({
                        "type": "round_end",
                        "round": round_num
                    })

                    # Emit per-round consensus heatmap (pairwise agreement)
                    try:
                        heatmap = consensus_heatmap_service.compute_round_heatmap(
                            messages=all_messages,
                            round_num=round_num
                        )
                        await callback({
                            "type": "consensus_heatmap",
                            "round": round_num,
                            "agents": heatmap.agents,
                            "matrix": heatmap.matrix
                        })
                    except Exception as e:
                        logger.warning(f"Consensus heatmap generation failed: {e}")

                    # Dynamic prediction update after each round
                    try:
                        interim_consensus = await self._generate_consensus(topic=topic, conversation=all_messages)
                        interim_prediction = await aggregation_engine.generate_final_prediction(
                            topic=topic,
                            messages=all_messages,
                            consensus=interim_consensus
                        )
                        if callback:
                            await callback({
                                "type": "prediction_update",
                                "round": round_num,
                                "consensus": interim_consensus,
                                "prediction": interim_prediction
                            })
                    except Exception as e:
                        logger.warning(f"Dynamic prediction update failed: {e}")

                    # Red Team Analysis update after each round
                    try:
                        red_team_analysis = await self._generate_red_team_analysis(
                            topic=topic, 
                            conversation=all_messages,
                            consensus=interim_consensus,
                            prediction=interim_prediction
                        )
                        if callback:
                            await callback({
                                "type": "red_team_update",
                                "round": round_num,
                                "analysis": red_team_analysis
                            })
                    except Exception as e:
                        logger.warning(f"Live Red Team analysis failed: {e}")
             
            # Generate consensus
            consensus = await self._generate_consensus(
                topic=topic,
                conversation=all_messages
            )
            
            # Generate final red team report
            final_red_team = await self._generate_red_team_analysis(
                topic=topic, 
                conversation=all_messages,
                consensus=consensus,
                prediction=final_prediction
            )
            
            # Run LLM Aggregation Engine for final prediction
            from services.aggregation_engine import aggregation_engine
            final_prediction = await aggregation_engine.generate_final_prediction(
                topic=topic,
                messages=all_messages,
                consensus=consensus
            )
            
            # Complete simulation
            self.active_simulations[simulation_id]["status"] = "completed"
            self.active_simulations[simulation_id]["messages"] = all_messages
            self.active_simulations[simulation_id]["consensus"] = consensus
            self.active_simulations[simulation_id]["final_prediction"] = final_prediction
            self.active_simulations[simulation_id]["red_team_report"] = final_red_team
            
            # PERSIST COMPLETION
            await memory_service.save_simulation(simulation_id, self.active_simulations[simulation_id])
            
            result = {
                "simulation_id": simulation_id,
                "status": "completed",
                "topic": topic,
                "agents": agents,
                "rounds_completed": max_rounds,
                "messages": all_messages,
                "consensus": consensus,
                "final_prediction": final_prediction,
                "red_team_report": final_red_team
            }
            
            if callback:
                await callback({
                    "type": "simulation_end",
                    "result": result
                })
            
            logger.info(f"Simulation '{simulation_id}' completed successfully")
            try:
                self._human_inbox.pop(simulation_id, None)
            except Exception:
                pass
            return result
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            self.active_simulations[simulation_id]["status"] = "failed"
            try:
                self._human_inbox.pop(simulation_id, None)
            except Exception:
                pass
            
            if callback:
                await callback({
                    "type": "simulation_error",
                    "error": str(e)
                })
            
            return {
                "simulation_id": simulation_id,
                "status": "failed",
                "error": str(e),
                "messages": all_messages
            }
    
    async def _generate_agent_response(
        self,
        agent: Dict,
        topic: str,
        conversation_history: List[Dict],
        round_num: int
    ) -> Optional[str]:
        """
        Generate response for a specific agent.
        
        Args:
            agent: Agent configuration
            topic: Discussion topic
            conversation_history: Previous messages in the conversation
            round_num: Current round number
            
        Returns:
            Agent's response text
        """
        role = agent["role"]
        personality = agent.get("personality", "")
        
        # Build context from conversation history
        context = ""
        if conversation_history:
            context = "\n\n".join([
                f"{msg['agent_role']}: {msg['content']}"
                for msg in conversation_history[-10:]  # Last 10 messages
            ])
        
        # Get graph context if available
        graph_context = ""
        try:
            graph_results = graph_service.get_graph_context(topic, limit=5)
            if graph_results:
                graph_context = "\n\nRelevant knowledge graph context:\n" + str(graph_results)
        except Exception as e:
            logger.warning(f"Could not retrieve graph context: {e}")
        
        # Create system prompt
        system_prompt = f"""You are simulating a {role} with the following personality: {personality}.

You are participating in a multi-agent discussion about: {topic}

{graph_context}

Rules:
1. Stay in character as a {role}
2. Consider the conversation history
3. Provide thoughtful, perspective responses
4. Keep your response concise (2-3 sentences)
5. Use your personality traits to inform your viewpoint"""
        
        # Create user prompt
        if round_num == 1:
            user_prompt = f"Share your initial perspective on: {topic}"
        else:
            user_prompt = f"""Round {round_num} of the discussion.

Previous conversation:
{context}

What is your response?"""
        
        # Call LLM
        response = await llm_service.call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=300
        )
        
        return response
    
    async def _generate_consensus(self, topic: str, conversation: List[Dict]) -> Dict:
        """
        Generate consensus from the conversation.
        
        Args:
            topic: Discussion topic
            conversation: All conversation messages
            
        Returns:
            Consensus analysis
        """
        if not conversation:
            return {"consensus": "No discussion occurred", "agreement_level": 0}
        
        # Build conversation summary
        conversation_text = "\n\n".join([
            f"{msg['agent_role']}: {msg['content']}"
            for msg in conversation
        ])
        
        system_prompt = """You are an expert analyst evaluating multi-agent discussions.
Your task is to:
1. Identify key points of agreement
2. Identify key points of disagreement
3. Determine overall consensus level (0-100%)
4. Summarize the main conclusions

CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no explanation, just the JSON object."""
        
        user_prompt = f"""Analyze this discussion about: {topic}

Conversation:
{conversation_text}

Respond with ONLY this JSON format (no other text):
{{"consensus": "Brief summary of the consensus reached", "agreement_level": 75, "key_agreements": ["point1", "point2"], "key_disagreements": ["point1", "point2"], "conclusions": ["conclusion1", "conclusion2"]}}"""
        
        response = await llm_service.call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse JSON response with robust extraction
        if response:
            try:
                import json
                import re
                
                # Try direct parsing first
                try:
                    consensus_data = json.loads(response)
                    logger.info("Consensus JSON parsed successfully")
                    return consensus_data
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code blocks
                    json_match = re.search(r'```json\s*\n(.*?)\n\s*```', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        consensus_data = json.loads(json_str)
                        logger.info("Consensus JSON extracted from markdown block")
                        return consensus_data
                    
                    # Try to find JSON object in response
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        consensus_data = json.loads(json_str)
                        logger.info("Consensus JSON extracted using regex")
                        return consensus_data
                    
                    raise ValueError("No valid JSON found in response")
                    
            except Exception as e:
                logger.error(f"Error parsing consensus JSON: {e}")
                logger.debug(f"Raw response: {response[:200]}")
        
        # Fallback - create consensus from conversation
        logger.warning("Using fallback consensus generation")
        return {
            "consensus": f"Discussion completed with {len(conversation)} messages from {len(set(msg.get('agent_role', '') for msg in conversation))} agents",
            "agreement_level": 50,
            "key_agreements": [],
            "key_disagreements": [],
            "conclusions": [msg.get('content', '')[:100] for msg in conversation[-3:]]
        }

    async def _generate_red_team_analysis(self, topic: str, conversation: List[Dict], consensus: Dict = None, prediction: Dict = None) -> Dict:
        """Adversarial analysis of simulation and its current consensus."""
        if not conversation:
            return {"vulnerabilities": [], "revised_confidence": 0, "blind_spots": []}
            
        conv_text = "\n".join([f"{m['agent_role']}: {m['content']}" for m in conversation[-15:]])
        consensus_text = consensus.get("consensus", "") if consensus else "No consensus reached yet."
        decision_text = prediction.get("final_decision", "") if prediction else "No final decision yet."

        prompt = f"""Perform a Red Team adversarial analysis of this AI agent simulation.
        Topic: {topic}
        
        Current Consensus: {consensus_text}
        Proposed Final Decision: {decision_text}
        
        Conversation Context:
        {conv_text}
        
        MISSION: Play Devil's Advocate. Your job is to find why the agents are WRONG. 
        Attack the groupthink. Find the critical vulnerabilities, systemic blind spots, and a worst-case scenario that would derail this plan.
        
        Respond with ONLY JSON:
        {{
          "revised_confidence": 65,
          "vulnerabilities": [
            {{
              "level": "CRITICAL|HIGH|MEDIUM|LOW",
              "name": "Title",
              "description": "Short desc",
              "missedBy": ["AgentName"],
              "mitigation": "Fix",
              "details": "Nitty gritty"
            }}
          ],
          "blind_spots": ["point 1", "point 2"],
          "worst_case": "description"
        }}
        """
        
        try:
            res = await llm_service.call_llm(prompt, temperature=0.7)
            import json, re
            match = re.search(r'\{.*\}', res, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            logger.warning(f"Red Team generation failed: {e}")
            
        return {"vulnerabilities": [], "revised_confidence": 50, "blind_spots": ["No blind spots identified by automated scan"]}
    
    def get_simulation_status(self, simulation_id: str) -> Optional[Dict]:
        """Get status of a specific simulation."""
        return self.active_simulations.get(simulation_id)
    
    def list_active_simulations(self) -> List[Dict]:
        """List all active simulations."""
        return [
            {"id": sid, **data}
            for sid, data in self.active_simulations.items()
            if data.get("status") == "running"
        ]


# Global simulation service instance
simulation_service = SimulationService()