from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger

from services.red_team_service import red_team_service
from services.simulation_service import simulation_service


router = APIRouter()


# ─────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ─────────────────────────────────────────────

class RedTeamAnalysisRequest(BaseModel):
    """Request model for Red Team analysis."""
    topic: str = Field(..., description="Discussion topic", min_length=3, max_length=500)
    plan: str = Field(..., description="The plan to analyze", min_length=10)
    simulation_id: Optional[str] = Field(None, description="Optional simulation ID for context")
    assumptions: Optional[List[str]] = Field(None, description="Assumptions to attack")


class AssumptionsAttackRequest(BaseModel):
    """Request model for attacking assumptions."""
    topic: str = Field(..., description="Discussion topic", min_length=3)
    plan: str = Field(..., description="The plan", min_length=10)
    assumptions: List[str] = Field(..., description="Assumptions to attack", min_items=1)


class FailureModesRequest(BaseModel):
    """Request model for failure mode analysis."""
    topic: str = Field(..., description="Discussion topic", min_length=3)
    plan: str = Field(..., description="The plan to analyze", min_length=10)


class ConsensusBreakRequest(BaseModel):
    """Request model for breaking consensus."""
    topic: str = Field(..., description="Discussion topic", min_length=3)
    consensus: str = Field(..., description="The consensus to break", min_length=10)
    simulation_id: str = Field(..., description="Simulation ID with agent opinions")


class RedTeamResponse(BaseModel):
    """Response model for Red Team analysis."""
    topic: str
    verdict: str
    critical_risks_count: int
    critical_risks: List[Dict[str, Any]]
    failure_modes: Dict[str, Any]
    assumptions_attacked: Optional[Dict[str, Any]] = None
    consensus_broken: Optional[Dict[str, Any]] = None
    recommendations: List[str]


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/analyze", response_model=RedTeamResponse)
async def red_team_analysis(request: RedTeamAnalysisRequest):
    """
    Run comprehensive Red Team analysis on a plan.
    
    This endpoint:
    - Attacks all assumptions
    - Finds failure modes
    - Breaks consensus
    - Provides go/no-go recommendation
    """
    try:
        logger.info(f"🔴 Starting Red Team analysis: {request.topic}")
        
        # Get simulation context if provided
        agent_opinions = []
        consensus = {}
        
        if request.simulation_id:
            sim_status = simulation_service.get_simulation_status(request.simulation_id)
            if sim_status:
                agent_opinions = sim_status.get("messages", [])
                consensus = sim_status.get("consensus", {})
        
        # Run full Red Team analysis
        result = await red_team_service.full_red_team_analysis(
            topic=request.topic,
            plan=request.plan,
            consensus=consensus,
            agent_opinions=agent_opinions,
            assumptions=request.assumptions
        )
        
        response = {
            "topic": request.topic,
            "verdict": result.get("red_team_verdict", "RECONSIDER"),
            "critical_risks_count": len(result.get("critical_risks", [])),
            "critical_risks": result.get("critical_risks", []),
            "failure_modes": result.get("failure_modes", {}),
            "assumptions_attacked": result.get("assumptions_attacked"),
            "consensus_broken": result.get("consensus_broken"),
            "recommendations": result.get("recommendations", [])
        }
        
        logger.info(f"🔴 Red Team verdict: {response['verdict']}")
        return response
        
    except Exception as e:
        logger.error(f"Red Team analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Red Team analysis failed: {str(e)}"
        )


@router.post("/assumptions")
async def attack_assumptions(request: AssumptionsAttackRequest):
    """
    Specifically attack assumptions in a plan.
    """
    try:
        result = await red_team_service.attack_assumptions(
            topic=request.topic,
            plan=request.plan,
            assumptions=request.assumptions
        )
        
        return {
            "topic": request.topic,
            "assumptions_count": len(request.assumptions),
            "analysis": result
        }
        
    except Exception as e:
        logger.error(f"Assumption attack error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Assumption attack failed: {str(e)}"
        )


@router.post("/failure-modes")
async def find_failure_modes(request: FailureModesRequest):
    """
    Find all possible failure modes for a plan.
    """
    try:
        result = await red_team_service.find_failure_modes(
            topic=request.topic,
            plan=request.plan
        )
        
        return {
            "topic": request.topic,
            "failure_modes_count": len(result.get("failure_modes", [])),
            "analysis": result
        }
        
    except Exception as e:
        logger.error(f"Failure mode analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failure mode analysis failed: {str(e)}"
        )


@router.post("/break-consensus")
async def break_consensus(request: ConsensusBreakRequest):
    """
    Break consensus by finding blind spots and groupthink.
    """
    try:
        # Get simulation data
        sim_status = simulation_service.get_simulation_status(request.simulation_id)
        
        if not sim_status:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        agent_opinions = sim_status.get("messages", [])
        
        result = await red_team_service.break_consensus(
            topic=request.topic,
            consensus=request.consensus,
            agent_opinions=agent_opinions
        )
        
        return {
            "topic": request.topic,
            "consensus_broken": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Consensus breaking error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Consensus breaking failed: {str(e)}"
        )


@router.get("/verdict/{simulation_id}")
async def get_red_team_verdict(simulation_id: str):
    """
    Get Red Team verdict for an existing simulation.
    Automatically extracts plan and consensus from simulation.
    """
    try:
        sim_status = simulation_service.get_simulation_status(simulation_id)
        
        if not sim_status:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        if sim_status.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Simulation not completed")
        
        topic = sim_status.get("topic", "")
        consensus = sim_status.get("consensus", {})
        messages = sim_status.get("messages", [])
        
        # Extract plan from consensus
        plan = consensus.get("consensus", "No consensus reached")
        
        # Run Red Team analysis
        result = await red_team_service.full_red_team_analysis(
            topic=topic,
            plan=plan,
            consensus=consensus,
            agent_opinions=messages
        )
        
        return {
            "simulation_id": simulation_id,
            "topic": topic,
            "red_team_verdict": result.get("red_team_verdict"),
            "critical_risks": result.get("critical_risks", []),
            "recommendations": result.get("recommendations", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Red Team verdict error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Red Team verdict failed: {str(e)}"
        )
