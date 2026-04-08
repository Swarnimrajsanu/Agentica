from typing import List, Dict, Optional, Any
from loguru import logger
import json
import re
from services.llm_services import llm_service


class LLMAggregationEngine:
    """
    LLM Reasoning & Aggregation Engine.
    
    After simulation completes, this engine:
    1. Reviews ALL messages (30+ agent responses)
    2. Identifies patterns, contradictions, and consensus
    3. Produces final intelligent prediction
    4. Provides confidence scores with reasoning
    5. Generates actionable recommendations
    """
    
    def __init__(self):
        logger.info("🧠 LLM Aggregation Engine initialized")
    
    async def generate_final_prediction(
        self,
        topic: str,
        messages: List[Dict],
        consensus: Dict
    ) -> Dict:
        """
        Generate comprehensive final prediction from all simulation messages.
        
        Args:
            topic: Discussion topic
            messages: All agent messages from simulation
            consensus: Consensus data from simulation
            
        Returns:
            Comprehensive prediction with reasoning
        """
        logger.info(f"🧠 Generating final prediction for: {topic}")
        logger.info(f"   Analyzing {len(messages)} messages...")
        
        # Prepare conversation summary
        conversation_text = self._format_conversation(messages)
        
        # Run multi-stage analysis
        import asyncio
        
        tasks = [
            self._analyze_sentiment_and_conviction(topic, messages),
            self._extract_key_insights(topic, conversation_text),
            self._calculate_weighted_consensus(topic, messages, consensus),
            self._generate_prediction_with_reasoning(topic, conversation_text, consensus)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile final prediction
        prediction = {
            "topic": topic,
            "simulation_summary": {
                "total_messages": len(messages),
                "unique_agents": len(set(msg.get("agent_role", "") for msg in messages)),
                "discussion_depth": "Deep" if len(messages) > 20 else "Medium" if len(messages) > 10 else "Light"
            },
            "sentiment_analysis": results[0] if not isinstance(results[0], Exception) else {},
            "key_insights": results[1] if not isinstance(results[1], Exception) else {},
            "weighted_consensus": results[2] if not isinstance(results[2], Exception) else {},
            "final_prediction": results[3] if not isinstance(results[3], Exception) else {},
            "confidence_level": 0,
            "recommendation": "",
            "risk_factors": [],
            "success_factors": []
        }
        
        # Calculate overall confidence
        confidence_scores = []
        if "weighted_agreement_level" in prediction["weighted_consensus"]:
            confidence_scores.append(prediction["weighted_consensus"]["weighted_agreement_level"])
        elif "agreement_level" in prediction["weighted_consensus"]:
            confidence_scores.append(prediction["weighted_consensus"]["agreement_level"])
        if "confidence_score" in prediction["final_prediction"]:
            confidence_scores.append(prediction["final_prediction"]["confidence_score"])
        
        prediction["confidence_level"] = int(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 50
        
        # Extract risk and success factors
        if "key_insights" in prediction["key_insights"]:
            prediction["risk_factors"] = prediction["key_insights"].get("risks", [])
            prediction["success_factors"] = prediction["key_insights"].get("opportunities", [])
        
        # Generate overall recommendation
        prediction["recommendation"] = self._generate_recommendation(prediction)
        
        logger.info(f"✅ Final prediction generated. Confidence: {prediction['confidence_level']}%")
        return prediction
    
    async def _analyze_sentiment_and_conviction(
        self,
        topic: str,
        messages: List[Dict]
    ) -> Dict:
        """Analyze sentiment and conviction levels across all agents."""
        
        # Group messages by agent
        agent_messages = {}
        for msg in messages:
            role = msg.get("agent_role", "Unknown")
            if role not in agent_messages:
                agent_messages[role] = []
            agent_messages[role].append(msg.get("content", ""))
        
        # Analyze each agent's stance
        agent_stances = []
        for role, contents in agent_messages.items():
            combined = " ".join(contents)
            
            prompt = f"""Analyze this agent's stance on the topic.

Topic: {topic}
Agent Role: {role}
Agent's Messages: {combined[:500]}

Provide:
1. Overall sentiment (positive/negative/neutral)
2. Conviction level (how strongly they believe their position) 0-100
3. Key arguments they made
4. Any shifts in position during discussion

Respond in JSON:
{{
  "sentiment": "positive|negative|neutral",
  "conviction_level": 0-100,
  "key_arguments": ["arg1", "arg2"],
  "position_shifts": "description of any changes",
  "influence_score": 0-100 (how much they influenced others)
}}"""
            
            try:
                result = await llm_service.call_llm(
                    prompt=prompt,
                    system_prompt="You are an expert analyst. Be precise and objective.",
                    temperature=0.3,
                    max_tokens=300
                )
                
                if result:
                    stance = self._extract_json(result)
                    stance["agent_role"] = role
                    agent_stances.append(stance)
            except Exception as e:
                logger.error(f"Error analyzing {role}: {e}")
        
        # Calculate overall sentiment distribution
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        total_conviction = 0
        
        for stance in agent_stances:
            sentiment = stance.get("sentiment", "neutral")
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            total_conviction += stance.get("conviction_level", 50)
        
        avg_conviction = total_conviction / len(agent_stances) if agent_stances else 50
        
        return {
            "agent_stances": agent_stances,
            "sentiment_distribution": sentiment_counts,
            "average_conviction": int(avg_conviction),
            "dominant_sentiment": max(sentiment_counts, key=sentiment_counts.get)
        }
    
    async def _extract_key_insights(
        self,
        topic: str,
        conversation_text: str
    ) -> Dict:
        """Extract key insights, risks, and opportunities from conversation."""
        
        prompt = f"""Extract the MOST IMPORTANT insights from this multi-agent discussion.

Topic: {topic}

Full Conversation:
{conversation_text[:3000]}

Identify:
1. Top 3-5 risks mentioned
2. Top 3-5 opportunities/success factors
3. Critical decision points
4. Contradictions or disagreements
5. Unresolved questions
6. Action items

Respond in JSON:
{{
  "risks": [
    {{
      "risk": "description",
      "severity": "low|medium|high|critical",
      "mentioned_by": ["role1", "role2"]
    }}
  ],
  "opportunities": [
    {{
      "opportunity": "description",
      "potential_impact": "low|medium|high",
      "feasibility": "low|medium|high"
    }}
  ],
  "critical_decisions": ["decision1", "decision2"],
  "contradictions": ["contradiction1", "contradiction2"],
  "unresolved_questions": ["question1", "question2"],
  "action_items": ["action1", "action2"]
}}"""
        
        try:
            result = await llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are a strategic analyst. Extract only the most critical insights.",
                temperature=0.4,
                max_tokens=800
            )
            
            if result:
                return self._extract_json(result)
            
            return {}
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            return {}
    
    async def _calculate_weighted_consensus(
        self,
        topic: str,
        messages: List[Dict],
        consensus: Dict
    ) -> Dict:
        """Calculate weighted consensus based on agent expertise and conviction."""
        
        # Get unique roles
        roles = list(set(msg.get("agent_role", "") for msg in messages))
        
        prompt = f"""Calculate a WEIGHTED CONSENSUS considering different agent expertise levels.

Topic: {topic}
Agents: {', '.join(roles)}

Original Consensus: {consensus.get('consensus', 'None')}
Key Agreements: {', '.join(consensus.get('key_agreements', []))}
Key Disagreements: {', '.join(consensus.get('key_disagreements', []))}

Weight agents by expertise relevance:
- Expert/Analyst: Higher weight on technical aspects
- Investor: Higher weight on financial viability
- Customer: Higher weight on market fit
- Critic/Red Team: Higher weight on risk assessment

Provide:
1. Adjusted agreement level (0-100)
2. Which perspectives should be weighted more heavily
3. Final weighted position
4. Remaining disagreements that matter

Respond in JSON:
{{
  "weighted_agreement_level": 0-100,
  "perspective_weights": {{
    "Expert": 0.0-1.0,
    "Investor": 0.0-1.0,
    "Customer": 0.0-1.0,
    "Critic": 0.0-1.0
  }},
  "weighted_position": "summary",
  "critical_disagreements": ["disagreement1"],
  "consensus_strength": "weak|moderate|strong"
}}"""
        
        try:
            result = await llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are a consensus analyst. Weight opinions by expertise.",
                temperature=0.3,
                max_tokens=500
            )
            
            if result:
                return self._extract_json(result)
            
            return {"weighted_agreement_level": consensus.get("agreement_level", 50)}
        except Exception as e:
            logger.error(f"Error calculating weighted consensus: {e}")
            return {}
    
    async def _generate_prediction_with_reasoning(
        self,
        topic: str,
        conversation_text: str,
        consensus: Dict
    ) -> Dict:
        """Generate final prediction with detailed reasoning chain."""
        
        prompt = f"""You are a PREDICTION ENGINE. Based on this multi-agent simulation, produce a FINAL PREDICTION.

Topic: {topic}

Simulation Discussion:
{conversation_text[:3000]}

Consensus Reached: {consensus.get('consensus', 'None')}
Key Agreements: {', '.join(consensus.get('key_agreements', []))}

Your task:
1. Make a CLEAR prediction (will this succeed/fail? yes/no/maybe)
2. Provide confidence score with justification
3. Explain your reasoning chain step-by-step
4. Identify critical success factors
5. Identify fatal flaws (if any)
6. Provide timeline expectations
7. Suggest metrics to track

Respond in JSON:
{{
  "prediction": "succeed|fail|succeed_with_challenges|fail_unless_conditions_met",
  "confidence_score": 0-100,
  "reasoning_chain": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "critical_success_factors": ["factor1", "factor2"],
  "fatal_flaws": ["flaw1"] or [],
  "timeline": {{
    "short_term_outlook": "0-6 months",
    "medium_term_outlook": "6-18 months",
    "long_term_outlook": "18+ months"
  }},
  "key_metrics_to_track": ["metric1", "metric2"],
  "decision_recommendation": "go|no-go|go-with-conditions|needs-more-research",
  "executive_summary": "2-3 sentence summary for decision makers"
}}"""
        
        try:
            result = await llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are an expert prediction engine. Be decisive, evidence-based, and clear.",
                temperature=0.4,
                max_tokens=1000
            )
            
            if result:
                return self._extract_json(result)
            
            return {"prediction": "inconclusive", "confidence_score": 50}
        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            return {}
    
    def _format_conversation(self, messages: List[Dict]) -> str:
        """Format conversation for analysis."""
        formatted = []
        for i, msg in enumerate(messages, 1):
            role = msg.get("agent_role", "Unknown")
            content = msg.get("content", "")
            round_num = msg.get("round", 0)
            formatted.append(f"[Round {round_num}] {role}: {content}")
        
        return "\n\n".join(formatted)
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            json_match = re.search(r'```(?:json)?\s*\n(.*?)\n\s*```', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass
            
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
        return {}
    
    def _generate_recommendation(self, prediction: Dict) -> str:
        """Generate overall recommendation based on all analyses."""
        confidence = prediction.get("confidence_level", 50)
        prediction_outcome = prediction.get("final_prediction", {}).get("prediction", "")
        fatal_flaws = prediction.get("final_prediction", {}).get("fatal_flaws", [])
        
        if fatal_flaws:
            return "❌ DO NOT PROCEED - Fatal flaws identified. Address these before reconsidering."
        
        if confidence >= 80 and "succeed" in prediction_outcome:
            return "✅ STRONG GO - High confidence in success. Proceed with execution."
        
        if confidence >= 60 and "succeed" in prediction_outcome:
            return "✅ GO WITH CONDITIONS - Proceed but monitor key metrics closely."
        
        if confidence >= 40:
            return "⚠️ PROCEED WITH EXTREME CAUTION - Significant risks identified. Mitigate before proceeding."
        
        return "❌ NO-GO - Too many risks and low confidence. Reconsider strategy."


# Global aggregation engine instance
aggregation_engine = LLMAggregationEngine()
