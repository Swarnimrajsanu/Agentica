from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger

from services.decision_tree_service import decision_tree_builder
from services.simulation_service import simulation_service


router = APIRouter()


# ─────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ─────────────────────────────────────────────

class DecisionTreeRequest(BaseModel):
    """Request model for decision tree generation."""
    simulation_id: str = Field(..., description="Simulation ID to visualize")


class CustomTreeRequest(BaseModel):
    """Request model for custom tree from messages."""
    topic: str = Field(..., description="Discussion topic", min_length=3)
    messages: List[Dict[str, Any]] = Field(..., description="All agent messages", min_items=1)
    consensus: Optional[Dict] = Field(None, description="Consensus data")


class TreeResponse(BaseModel):
    """Response model for decision tree."""
    simulation_id: Optional[str] = None
    topic: str
    tree: Dict[str, Any]
    d3_format: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/generate", response_model=TreeResponse)
async def generate_decision_tree(request: DecisionTreeRequest):
    """
    Generate decision tree visualization from simulation.
    
    Converts all 30+ debate messages into an interactive tree:
    - Every argument is a node
    - Every logical connection is an edge
    - Supports pro/con/neutral categorization
    - Includes strength and sentiment data
    """
    try:
        logger.info(f"🌳 Generating decision tree for simulation: {request.simulation_id}")
        
        # Get simulation data
        sim_status = simulation_service.get_simulation_status(request.simulation_id)
        
        if not sim_status:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        if sim_status.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Simulation not completed. Status: {sim_status.get('status')}"
            )
        
        # Check if tree already exists
        if "decision_tree" in sim_status:
            logger.info("Returning cached decision tree")
            tree = sim_status["decision_tree"]
        else:
            # Generate tree
            tree = await decision_tree_builder.build_decision_tree(
                topic=sim_status.get("topic", ""),
                messages=sim_status.get("messages", []),
                consensus=sim_status.get("consensus", {})
            )
            
            # Cache it
            sim_status["decision_tree"] = tree
        
        # Generate D3.js format
        d3_format = decision_tree_builder.generate_d3_format(tree)
        
        response = {
            "simulation_id": request.simulation_id,
            "topic": tree.get("metadata", {}).get("topic", ""),
            "tree": tree,
            "d3_format": d3_format,
            "metadata": tree.get("metadata", {})
        }
        
        logger.info(f"✅ Decision tree generated: {tree['metadata']['total_nodes']} nodes, {tree['metadata']['total_edges']} edges")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Decision tree generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Decision tree generation failed: {str(e)}"
        )


@router.get("/tree/{simulation_id}", response_model=TreeResponse)
async def get_decision_tree(simulation_id: str):
    """
    Get decision tree for a simulation (GET endpoint for convenience).
    """
    return await generate_decision_tree(DecisionTreeRequest(simulation_id=simulation_id))


@router.post("/custom-tree", response_model=TreeResponse)
async def custom_decision_tree(request: CustomTreeRequest):
    """
    Generate decision tree from custom messages (not tied to a simulation).
    """
    try:
        logger.info(f"🌳 Generating custom decision tree for: {request.topic}")
        
        # Generate tree
        tree = await decision_tree_builder.build_decision_tree(
            topic=request.topic,
            messages=request.messages,
            consensus=request.consensus or {}
        )
        
        # Generate D3.js format
        d3_format = decision_tree_builder.generate_d3_format(tree)
        
        response = {
            "topic": tree.get("metadata", {}).get("topic", ""),
            "tree": tree,
            "d3_format": d3_format,
            "metadata": tree.get("metadata", {})
        }
        
        logger.info(f"✅ Custom tree generated: {tree['metadata']['total_nodes']} nodes, {tree['metadata']['total_edges']} edges")
        return response
        
    except Exception as e:
        logger.error(f"Custom decision tree error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Custom decision tree failed: {str(e)}"
        )


@router.get("/stats/{simulation_id}")
async def get_tree_stats(simulation_id: str):
    """
    Get decision tree statistics without full tree.
    """
    try:
        sim_status = simulation_service.get_simulation_status(simulation_id)
        
        if not sim_status:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        tree = sim_status.get("decision_tree")
        
        if not tree:
            return {
                "simulation_id": simulation_id,
                "status": "not_generated",
                "message": "Decision tree not yet generated. Call /generate first."
            }
        
        metadata = tree.get("metadata", {})
        
        return {
            "simulation_id": simulation_id,
            "status": "generated",
            "total_nodes": metadata.get("total_nodes", 0),
            "total_edges": metadata.get("total_edges", 0),
            "tree_depth": metadata.get("tree_depth", 0),
            "agents_involved": metadata.get("agents_involved", []),
            "consensus_level": metadata.get("consensus_level", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tree stats error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Tree stats failed: {str(e)}"
        )


@router.get("/compare-trees/{sim_id_1}/{sim_id_2}")
async def compare_trees(sim_id_1: str, sim_id_2: str):
    """
    Compare decision trees from two simulations.
    """
    try:
        sim1 = simulation_service.get_simulation_status(sim_id_1)
        sim2 = simulation_service.get_simulation_status(sim_id_2)
        
        if not sim1:
            raise HTTPException(status_code=404, detail=f"Simulation {sim_id_1} not found")
        if not sim2:
            raise HTTPException(status_code=404, detail=f"Simulation {sim_id_2} not found")
        
        tree1 = sim1.get("decision_tree", {})
        tree2 = sim2.get("decision_tree", {})
        
        metadata1 = tree1.get("metadata", {})
        metadata2 = tree2.get("metadata", {})
        
        comparison = {
            "simulation_1": {
                "id": sim_id_1,
                "topic": metadata1.get("topic"),
                "nodes": metadata1.get("total_nodes", 0),
                "edges": metadata1.get("total_edges", 0),
                "depth": metadata1.get("tree_depth", 0),
                "consensus": metadata1.get("consensus_level", 0)
            },
            "simulation_2": {
                "id": sim_id_2,
                "topic": metadata2.get("topic"),
                "nodes": metadata2.get("total_nodes", 0),
                "edges": metadata2.get("total_edges", 0),
                "depth": metadata2.get("tree_depth", 0),
                "consensus": metadata2.get("consensus_level", 0)
            },
            "analysis": {
                "complexity_difference": abs(
                    metadata1.get("total_nodes", 0) - metadata2.get("total_nodes", 0)
                ),
                "more_complex": sim_id_1 if metadata1.get("total_nodes", 0) > metadata2.get("total_nodes", 0) else sim_id_2
            }
        }
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tree comparison error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Tree comparison failed: {str(e)}"
        )
