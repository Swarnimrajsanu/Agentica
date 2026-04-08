from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger

from services.agent_service import agent_service
from services.simulation_service import simulation_service
from services.prediction_service import prediction_service


router = APIRouter()


# ─────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ─────────────────────────────────────────────

class PredictionRequest(BaseModel):
    """Request model for prediction endpoint."""
    topic: str = Field(..., description="Discussion topic", min_length=3, max_length=500)
    rounds: Optional[int] = Field(3, description="Number of simulation rounds", ge=1, le=10)
    include_sentiment: Optional[bool] = Field(True, description="Include sentiment analysis")


class PredictionResponse(BaseModel):
    """Response model for prediction endpoint."""
    simulation_id: str
    topic: str
    prediction: Dict[str, Any]
    messages_count: int
    sentiment: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Run simulation and generate prediction with analysis.
    
    - **topic**: The discussion topic
    - **rounds**: Number of discussion rounds (1-10)
    - **include_sentiment**: Whether to include sentiment analysis
    """
    try:
        logger.info(f"Starting prediction for topic: {request.topic}")
        
        # Step 1: Spawn agents
        agents = agent_service.spawn_agents(context=request.topic)
        
        if not agents:
            raise HTTPException(status_code=400, detail="Failed to spawn agents")
        
        # Step 2: Run simulation
        simulation_result = await simulation_service.run_simulation(
            agents=agents,
            topic=request.topic,
            rounds=request.rounds
        )
        
        if simulation_result.get("status") == "failed":
            raise HTTPException(
                status_code=500,
                detail=f"Simulation failed: {simulation_result.get('error', 'Unknown error')}"
            )
        
        messages = simulation_result.get("messages", [])
        
        # Step 3: Generate prediction
        prediction = await prediction_service.generate_prediction(
            topic=request.topic,
            messages=messages
        )
        
        if not prediction:
            raise HTTPException(status_code=500, detail="Failed to generate prediction")
        
        # Step 4: Optional sentiment analysis
        sentiment = None
        if request.include_sentiment:
            sentiment = await prediction_service.analyze_sentiment(messages=messages)
        
        response = {
            "simulation_id": simulation_result.get("simulation_id"),
            "topic": request.topic,
            "prediction": prediction,
            "messages_count": len(messages),
            "sentiment": sentiment
        }
        
        logger.info(f"Prediction completed for: {request.topic}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


class ButterflyEffectRequest(BaseModel):
    """Request model for butterfly effect analysis."""
    topic: str = Field(..., description="Discussion topic", min_length=3, max_length=500)
    simulation_id: str = Field(..., description="Original simulation ID")
    alternative_scenario: str = Field(..., description="Alternative scenario to analyze", min_length=10)


@router.post("/butterfly-effect")
async def butterfly_effect(request: ButterflyEffectRequest):
    """
    Analyze butterfly effect - how small changes impact outcomes.
    
    Requires an existing simulation to compare against.
    """
    try:
        logger.info(f"Analyzing butterfly effect for: {request.topic}")
        
        # Get original simulation
        sim_status = simulation_service.get_simulation_status(request.simulation_id)
        
        if not sim_status:
            raise HTTPException(status_code=404, detail="Original simulation not found")
        
        if sim_status.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Original simulation not completed")
        
        original_messages = sim_status.get("messages", [])
        
        # Generate butterfly effect analysis
        analysis = await prediction_service.generate_butterfly_effect(
            topic=request.topic,
            original_messages=original_messages,
            alternative_scenario=request.alternative_scenario
        )
        
        if not analysis:
            raise HTTPException(status_code=500, detail="Failed to generate butterfly effect analysis")
        
        return {
            "original_simulation_id": request.simulation_id,
            "topic": request.topic,
            "alternative_scenario": request.alternative_scenario,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Butterfly effect analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )