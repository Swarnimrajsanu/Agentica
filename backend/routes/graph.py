from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from loguru import logger

from services.graph_service import graph_service


router = APIRouter()


# ─────────────────────────────────────────────
# REQUEST/RESPONSE MODELS
# ─────────────────────────────────────────────

class GraphQueryRequest(BaseModel):
    """Request model for graph query."""
    query: str = Field(..., description="Search query or topic", min_length=1, max_length=500)
    limit: Optional[int] = Field(10, description="Maximum results to return", ge=1, le=100)


class GraphNodeRequest(BaseModel):
    """Request model for adding a node."""
    label: str = Field(..., description="Node label/type", min_length=1, max_length=100)
    properties: Dict[str, Any] = Field(..., description="Node properties")


class GraphRelationshipRequest(BaseModel):
    """Request model for adding a relationship."""
    from_node_id: str = Field(..., description="Source node ID")
    to_node_id: str = Field(..., description="Target node ID")
    relationship_type: str = Field(..., description="Relationship type", min_length=1, max_length=100)
    properties: Optional[Dict[str, Any]] = Field(None, description="Relationship properties")


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/query")
async def query_graph(request: GraphQueryRequest):
    """
    Query the knowledge graph for context.
    
    - **query**: Search query or topic
    - **limit**: Maximum number of results (1-100)
    """
    try:
        logger.info(f"Graph query: {request.query}")
        
        results = graph_service.get_graph_context(
            query=request.query,
            limit=request.limit
        )
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Graph query error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error querying graph: {str(e)}"
        )


@router.post("/node")
async def add_node(request: GraphNodeRequest):
    """
    Add a node to the knowledge graph.
    
    - **label**: Node type/label
    - **properties**: Node properties as key-value pairs
    """
    try:
        logger.info(f"Adding node with label: {request.label}")
        
        node = graph_service.add_node(
            label=request.label,
            properties=request.properties
        )
        
        if not node:
            raise HTTPException(status_code=500, detail="Failed to add node")
        
        return {
            "message": "Node added successfully",
            "node": node
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add node error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding node: {str(e)}"
        )


@router.post("/relationship")
async def add_relationship(request: GraphRelationshipRequest):
    """
    Add a relationship between two nodes.
    
    - **from_node_id**: Source node ID
    - **to_node_id**: Target node ID
    - **relationship_type**: Type of relationship
    - **properties**: Optional relationship properties
    """
    try:
        logger.info(f"Adding relationship: {request.relationship_type}")
        
        relationship = graph_service.add_relationship(
            from_node_id=request.from_node_id,
            to_node_id=request.to_node_id,
            relationship_type=request.relationship_type,
            properties=request.properties
        )
        
        if not relationship:
            raise HTTPException(status_code=500, detail="Failed to add relationship")
        
        return {
            "message": "Relationship added successfully",
            "relationship": relationship
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add relationship error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding relationship: {str(e)}"
        )


@router.get("/stats")
async def get_graph_stats():
    """Get basic graph statistics."""
    try:
        # Query for node and relationship counts
        stats = {
            "status": "connected",
            "uri": graph_service.driver.get_server_info().address if graph_service.driver else "unknown"
        }
        return stats
    except Exception as e:
        logger.error(f"Graph stats error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }