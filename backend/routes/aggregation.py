from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger

from services.aggregation_engine import aggregation_engine
from services.simulation_service import simulation_service


router = APIRouter()


# ─────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ─────────────────────────────────────────────

class AggregationRequest(BaseModel):
    """Request model for manual aggregation."""
    simulation_id: str = Field(..., description="Simulation ID to aggregate")


class CustomAggregationRequest(BaseModel):
    """Request model for custom aggregation with provided messages."""
    topic: str = Field(..., description="Discussion topic", min_length=3)
    messages: List[Dict[str, Any]] = Field(..., description="All agent messages", min_items=1)
    consensus: Optional[Dict] = Field(None, description="Consensus data")


class PredictionResponse(BaseModel):
    """Response model for prediction."""
    simulation_id: Optional[str] = None
    topic: str
    confidence_level: int
    prediction: str
    recommendation: str
    reasoning_chain: List[str]
    critical_success_factors: List[str]
    risk_factors: List[Any]
    success_factors: List[Any]
    executive_summary: str
    key_metrics_to_track: List[str]
    timeline: Dict[str, str]


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/aggregate", response_model=PredictionResponse)
async def aggregate_simulation(request: AggregationRequest):
    """
    Run LLM aggregation engine on completed simulation.
    
    This endpoint:
    1. Retrieves all simulation messages
    2. Analyzes sentiment and conviction
    3. Extracts key insights
    4. Calculates weighted consensus
    5. Generates final prediction with reasoning
    """
    try:
        logger.info(f"🧠 Running aggregation for simulation: {request.simulation_id}")
        
        # Get simulation data
        sim_status = simulation_service.get_simulation_status(request.simulation_id)
        
        if not sim_status:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        if sim_status.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Simulation not completed. Status: {sim_status.get('status')}"
            )
        
        # Check if prediction already exists
        if "final_prediction" in sim_status:
            logger.info("Returning cached prediction")
            prediction = sim_status["final_prediction"]
        else:
            # Generate prediction
            prediction = await aggregation_engine.generate_final_prediction(
                topic=sim_status.get("topic", ""),
                messages=sim_status.get("messages", []),
                consensus=sim_status.get("consensus", {})
            )
        
        # Format response
        final_pred = prediction.get("final_prediction", {})
        
        response = {
            "simulation_id": request.simulation_id,
            "topic": prediction.get("topic", ""),
            "confidence_level": prediction.get("confidence_level", 0),
            "prediction": final_pred.get("prediction", "inconclusive"),
            "recommendation": prediction.get("recommendation", ""),
            "reasoning_chain": final_pred.get("reasoning_chain", []),
            "critical_success_factors": final_pred.get("critical_success_factors", []),
            "risk_factors": prediction.get("risk_factors", []),
            "success_factors": prediction.get("success_factors", []),
            "executive_summary": final_pred.get("executive_summary", ""),
            "key_metrics_to_track": final_pred.get("key_metrics_to_track", []),
            "timeline": final_pred.get("timeline", {})
        }
        
        logger.info(f"✅ Aggregation complete. Confidence: {response['confidence_level']}%")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Aggregation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Aggregation failed: {str(e)}"
        )


@router.post("/custom-prediction", response_model=PredictionResponse)
async def custom_prediction(request: CustomAggregationRequest):
    """
    Generate prediction from custom messages (not tied to a simulation).
    
    Useful for analyzing external conversations or importing data.
    """
    try:
        logger.info(f"🧠 Running custom prediction for: {request.topic}")
        
        # Generate prediction
        prediction = await aggregation_engine.generate_final_prediction(
            topic=request.topic,
            messages=request.messages,
            consensus=request.consensus or {}
        )
        
        # Format response
        final_pred = prediction.get("final_prediction", {})
        
        response = {
            "topic": prediction.get("topic", ""),
            "confidence_level": prediction.get("confidence_level", 0),
            "prediction": final_pred.get("prediction", "inconclusive"),
            "recommendation": prediction.get("recommendation", ""),
            "reasoning_chain": final_pred.get("reasoning_chain", []),
            "critical_success_factors": final_pred.get("critical_success_factors", []),
            "risk_factors": prediction.get("risk_factors", []),
            "success_factors": prediction.get("success_factors", []),
            "executive_summary": final_pred.get("executive_summary", ""),
            "key_metrics_to_track": final_pred.get("key_metrics_to_track", []),
            "timeline": final_pred.get("timeline", {})
        }
        
        logger.info(f"✅ Custom prediction complete. Confidence: {response['confidence_level']}%")
        return response
        
    except Exception as e:
        logger.error(f"Custom prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Custom prediction failed: {str(e)}"
        )


@router.get("/prediction/{simulation_id}", response_model=PredictionResponse)
async def get_prediction(simulation_id: str):
    """
    Get prediction for a simulation (GET endpoint for convenience).
    """
    return await aggregate_simulation(AggregationRequest(simulation_id=simulation_id))


@router.get("/compare/{sim_id_1}/{sim_id_2}")
async def compare_predictions(sim_id_1: str, sim_id_2: str):
    """
    Compare predictions from two different simulations.
    
    Useful for A/B testing different scenarios.
    """
    try:
        # Get both simulations
        sim1 = simulation_service.get_simulation_status(sim_id_1)
        sim2 = simulation_service.get_simulation_status(sim_id_2)
        
        if not sim1:
            raise HTTPException(status_code=404, detail=f"Simulation {sim_id_1} not found")
        if not sim2:
            raise HTTPException(status_code=404, detail=f"Simulation {sim_id_2} not found")
        
        pred1 = sim1.get("final_prediction", {})
        pred2 = sim2.get("final_prediction", {})
        
        comparison = {
            "simulation_1": {
                "id": sim_id_1,
                "topic": sim1.get("topic"),
                "prediction": pred1.get("final_prediction", {}).get("prediction"),
                "confidence": pred1.get("confidence_level")
            },
            "simulation_2": {
                "id": sim_id_2,
                "topic": sim2.get("topic"),
                "prediction": pred2.get("final_prediction", {}).get("prediction"),
                "confidence": pred2.get("confidence_level")
            },
            "analysis": {
                "confidence_difference": abs(
                    pred1.get("confidence_level", 0) - pred2.get("confidence_level", 0)
                ),
                "same_prediction": pred1.get("final_prediction", {}).get("prediction") == pred2.get("final_prediction", {}).get("prediction"),
                "recommendation": ""
            }
        }
        
        # Generate comparison recommendation
        conf1 = pred1.get("confidence_level", 0)
        conf2 = pred2.get("confidence_level", 0)
        
        if conf1 > conf2 + 20:
            comparison["analysis"]["recommendation"] = f"Simulation 1 ({sim_id_1}) shows significantly higher confidence"
        elif conf2 > conf1 + 20:
            comparison["analysis"]["recommendation"] = f"Simulation 2 ({sim_id_2}) shows significantly higher confidence"
        else:
            comparison["analysis"]["recommendation"] = "Both simulations show similar confidence levels"
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )
