from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger

from services.agent_service import agent_service
from services.simulation_service import simulation_service


router = APIRouter()


# ─────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ─────────────────────────────────────────────

class SimulationRequest(BaseModel):
    """Request model for simulation endpoint."""
    topic: str = Field(..., description="Discussion topic", min_length=3, max_length=500)
    rounds: Optional[int] = Field(3, description="Number of simulation rounds", ge=1, le=10)
    custom_roles: Optional[List[str]] = Field(
        None,
        description="Custom agent roles (optional)"
    )
    temperature: Optional[float] = Field(0.7, description="LLM temperature", ge=0.0, le=1.0)


class SimulationResponse(BaseModel):
    """Response model for simulation endpoint."""
    simulation_id: str
    status: str
    topic: str
    rounds_completed: int
    messages: List[Dict[str, Any]]
    consensus: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────
# HUMAN-IN-THE-LOOP MODELS
# ─────────────────────────────────────────────

class HumanInjectRequest(BaseModel):
    message: str = Field(..., description="Human participant post", min_length=1, max_length=4000)
    influence_level: Optional[float] = Field(0.6, description="0.1-1.0 reach multiplier", ge=0.1, le=1.0)
    display_name: Optional[str] = Field("Human", description="Display name for the user", min_length=1, max_length=40)


class HumanInjectResponse(BaseModel):
    simulation_id: str
    accepted: bool


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/", response_model=SimulationResponse)
async def simulate(request: SimulationRequest):
    """
    Run a multi-agent simulation on a given topic.
    
    - **topic**: The discussion topic
    - **rounds**: Number of discussion rounds (1-10)
    - **custom_roles**: Optional custom agent roles
    - **temperature**: LLM temperature for response generation
    """
    try:
        logger.info(f"Starting simulation for topic: {request.topic}")
        
        # Spawn agents
        agents = agent_service.spawn_agents(
            context=request.topic,
            custom_roles=request.custom_roles
        )
        
        if not agents:
            raise HTTPException(status_code=400, detail="Failed to spawn agents")
        
        # Run simulation
        result = await simulation_service.run_simulation(
            agents=agents,
            topic=request.topic,
            rounds=request.rounds
        )
        
        if result.get("status") == "failed":
            raise HTTPException(
                status_code=500,
                detail=f"Simulation failed: {result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"Simulation completed: {result.get('simulation_id')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/status/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """Get status of a specific simulation."""
    status = simulation_service.get_simulation_status(simulation_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return status


@router.get("/active")
async def list_active_simulations():
    """List all currently active simulations."""
    active = simulation_service.list_active_simulations()
    return {"active_simulations": active, "count": len(active)}


@router.post("/{simulation_id}/inject-human", response_model=HumanInjectResponse)
async def inject_human(simulation_id: str, request: HumanInjectRequest):
    """
    Inject a human participant message into a running simulation.
    The message will appear at the start of the next round and affect subsequent predictions.
    """
    accepted = simulation_service.inject_human_message(
        simulation_id=simulation_id,
        message=request.message,
        influence_level=request.influence_level or 0.6,
        display_name=request.display_name or "Human",
    )
    if not accepted:
        raise HTTPException(status_code=400, detail="Simulation not running or not found")
    return {"simulation_id": simulation_id, "accepted": True}