import json
from loguru import logger
from typing import Optional, Dict, List
from services.llm_services import llm_service


class PredictionService:
    """Service for generating predictions from agent simulations."""
    
    def __init__(self):
        logger.info("Prediction Service initialized")
    
    async def generate_prediction(
        self,
        topic: str,
        messages: List[Dict],
        include_sentiment: bool = True
    ) -> Optional[Dict]:
        """
        Generate prediction from simulation results.
        
        Args:
            topic: Discussion topic
            messages: List of simulation messages
            include_sentiment: Whether to include sentiment analysis
            
        Returns:
            Prediction results as dictionary
        """
        if not messages:
            logger.warning("No messages provided for prediction")
            return {
                "final_decision": "No discussion occurred",
                "confidence": 0,
                "key_reasoning": [],
                "sentiment": {}
            }
        
        # Combine messages for analysis
        combined = "\n".join([
            f"{msg.get('agent_role', 'Unknown')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        prompt = f"""Analyze this multi-agent discussion about: {topic}

Conversation:
{combined}

Provide a comprehensive analysis in JSON format:
{{
  "final_decision": "Summary of the consensus or final decision reached",
  "confidence": 75,  // 0-100 integer
  "key_reasoning": ["reason1", "reason2", "reason3"],
  "risks": ["risk1", "risk2"],
  "recommendations": ["recommendation1", "recommendation2"]
}}"""
        
        try:
            result = await llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are an expert analyst. Always respond with ONLY valid JSON. No markdown, no explanation.",
                temperature=0.3,
                max_tokens=800
            )
            
            if result:
                # Parse JSON response with robust extraction
                try:
                    import json
                    import re
                    
                    # Try direct parsing first
                    try:
                        prediction_data = json.loads(result)
                        logger.info("Prediction JSON parsed successfully")
                        return prediction_data
                    except json.JSONDecodeError:
                        # Try to extract JSON from markdown code blocks
                        json_match = re.search(r'```json\s*\n(.*?)\n\s*```', result, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                            prediction_data = json.loads(json_str)
                            logger.info("Prediction JSON extracted from markdown block")
                            return prediction_data
                        
                        # Try to find JSON object in response
                        json_match = re.search(r'\{.*\}', result, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            prediction_data = json.loads(json_str)
                            logger.info("Prediction JSON extracted using regex")
                            return prediction_data
                        
                        raise ValueError("No valid JSON found in response")
                        
                except Exception as e:
                    logger.error(f"Error parsing prediction JSON: {e}")
                    logger.debug(f"Raw response: {result[:200]}")
                    # Return structured result if JSON parsing fails
                    return {
                        "final_decision": result[:200] if result else "Unable to generate prediction",
                        "confidence": 50,
                        "key_reasoning": [result[:300] if result else "No response"],
                        "risks": [],
                        "recommendations": []
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            return None
    
    async def analyze_sentiment(self, messages: List[Dict]) -> Dict:
        """
        Analyze sentiment of simulation messages.
        
        Args:
            messages: List of simulation messages
            
        Returns:
            Sentiment analysis results
        """
        if not messages:
            return {"overall": "neutral", "scores": {}}
        
        combined = "\n".join([
            f"{msg.get('agent_role', 'Unknown')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        prompt = f"""Analyze the sentiment of this discussion.

Text:
{combined}

Return JSON:
{{
  "overall": "positive|negative|neutral|mixed",
  "scores": {{
    "positive": 0.6,
    "negative": 0.2,
    "neutral": 0.2
  }},
  "key_emotions": ["emotion1", "emotion2"]
}}"""
        
        try:
            result = await llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are a sentiment analysis expert. Always respond with ONLY valid JSON. No markdown.",
                temperature=0.2,
                max_tokens=400
            )
            
            if result:
                try:
                    import json
                    import re
                    
                    # Try to extract JSON
                    try:
                        sentiment_data = json.loads(result)
                        return sentiment_data
                    except json.JSONDecodeError:
                        json_match = re.search(r'\{.*\}', result, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group(0))
                        raise
                    
                except Exception:
                    return {"overall": "unknown", "scores": {}}
            
            return {"overall": "unknown", "scores": {}}
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"overall": "error", "scores": {}}
    
    async def generate_butterfly_effect(
        self,
        topic: str,
        original_messages: List[Dict],
        alternative_scenario: str
    ) -> Optional[Dict]:
        """
        Analyze butterfly effect - how small changes impact outcomes.
        
        Args:
            topic: Discussion topic
            original_messages: Original simulation messages
            alternative_scenario: Alternative scenario to analyze
            
        Returns:
            Butterfly effect analysis
        """
        original_summary = "\n".join([
            f"{msg.get('agent_role', 'Unknown')}: {msg.get('content', '')}"
            for msg in original_messages[:5]  # First 5 messages
        ])
        
        prompt = f"""Original discussion about: {topic}

{original_summary}

Alternative scenario: {alternative_scenario}

Analyze how this small change could create a butterfly effect. Return JSON:
{{
  "original_outcome": "Summary of original outcome",
  "alternative_outcome": "Predicted alternative outcome",
  "divergence_level": 75,  // 0-100 how different the outcomes are
  "key_inflection_points": ["point1", "point2"],
  "long_term_implications": ["implication1", "implication2"]
}}"""
        
        try:
            result = await llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are a chaos theory and systems thinking expert. Always respond with ONLY valid JSON. No markdown.",
                temperature=0.5,
                max_tokens=600
            )
            
            if result:
                try:
                    import json
                    import re
                    
                    # Try to extract JSON
                    try:
                        return json.loads(result)
                    except json.JSONDecodeError:
                        json_match = re.search(r'\{.*\}', result, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group(0))
                        return None
                except Exception:
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating butterfly effect analysis: {e}")
            return None


# Global prediction service instance
prediction_service = PredictionService()