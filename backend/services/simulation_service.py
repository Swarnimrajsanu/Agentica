from loguru import logger
from typing import List, Dict, Optional, Callable
from services.llm_services import llm_service
from services.memory_service import memory_service
from services.graph_service import graph_service
from config.settings import settings


class SimulationService:
    """Multi-Agent Simulation Service for orchestrating agent discussions."""
    
    def __init__(self):
        self.active_simulations = {}
        logger.info("Simulation Service initialized")
    
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
            "status": "running",
            "agents": agents,
            "topic": topic,
            "messages": []
        }
        
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
                            await callback({
                                "type": "agent_response",
                                "message": message
                            })
                
                if callback:
                    await callback({
                        "type": "round_end",
                        "round": round_num
                    })
            
            # Generate consensus
            consensus = await self._generate_consensus(
                topic=topic,
                conversation=all_messages
            )
            
            # Complete simulation
            self.active_simulations[simulation_id]["status"] = "completed"
            self.active_simulations[simulation_id]["messages"] = all_messages
            self.active_simulations[simulation_id]["consensus"] = consensus
            
            result = {
                "simulation_id": simulation_id,
                "status": "completed",
                "topic": topic,
                "agents": agents,
                "rounds_completed": max_rounds,
                "messages": all_messages,
                "consensus": consensus
            }
            
            if callback:
                await callback({
                    "type": "simulation_end",
                    "result": result
                })
            
            logger.info(f"Simulation '{simulation_id}' completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            self.active_simulations[simulation_id]["status"] = "failed"
            
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
4. Summarize the main conclusions"""
        
        user_prompt = f"""Analyze this discussion about: {topic}

Conversation:
{conversation_text}

Provide your analysis in JSON format:
{{
  "consensus": "Brief summary of the consensus reached",
  "agreement_level": 75,  // 0-100 percentage
  "key_agreements": ["point1", "point2"],
  "key_disagreements": ["point1", "point2"],
  "conclusions": ["conclusion1", "conclusion2"]
}}"""
        
        response = await llm_service.call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse JSON response
        if response:
            try:
                import json
                consensus_data = json.loads(response)
                return consensus_data
            except Exception as e:
                logger.error(f"Error parsing consensus JSON: {e}")
        
        # Fallback
        return {
            "consensus": response or "Unable to determine consensus",
            "agreement_level": 50,
            "key_agreements": [],
            "key_disagreements": [],
            "conclusions": []
        }
    
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