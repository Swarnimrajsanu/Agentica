from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
from loguru import logger
import uuid
import asyncio

from websocket.manager import websocket_manager


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time simulation streaming.
    
    Client sends:
    - {"type": "subscribe", "simulation_id": "sim_..."}
    
    Server sends:
    - {"type": "connected", "message": "...", "client_id": "..."}
    - {"type": "simulation_update", "simulation_id": "...", "data": {...}}
    """
    # Generate unique client ID
    client_id = str(uuid.uuid4())
    
    # Connect
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "subscribe":
                simulation_id = data.get("simulation_id")
                if simulation_id:
                    await websocket_manager.subscribe_to_simulation(client_id, simulation_id)
                    await websocket_manager.send_personal_message({
                        "type": "subscribed",
                        "simulation_id": simulation_id,
                        "message": f"Subscribed to simulation updates"
                    }, client_id)
                else:
                    await websocket_manager.send_personal_message({
                        "type": "error",
                        "message": "simulation_id is required for subscribe"
                    }, client_id)
            
            elif message_type == "ping":
                await websocket_manager.send_personal_message({
                    "type": "pong",
                    "timestamp": str(__import__('datetime').datetime.utcnow())
                }, client_id)
            
            else:
                await websocket_manager.send_personal_message({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }, client_id)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
        websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        websocket_manager.disconnect(client_id)


@router.websocket("/ws/simulate/{topic}")
async def websocket_simulate(websocket: WebSocket, topic: str):
    """
    WebSocket endpoint that automatically runs a simulation and streams results.
    
    This is the MOST IMPRESSIVE endpoint for demos!
    Just connect and watch the simulation happen in real-time.
    """
    from services.agent_service import agent_service
    from services.simulation_service import simulation_service
    
    client_id = str(uuid.uuid4())
    await websocket_manager.connect(websocket, client_id)
    
    try:
        # Decode topic from URL
        topic_decoded = topic.replace("_", " ")
        
        logger.info(f"Starting live simulation via WebSocket: {topic_decoded}")
        
        # Notify client simulation is starting
        await websocket_manager.send_personal_message({
            "type": "simulation_starting",
            "topic": topic_decoded,
            "message": "🚀 Starting multi-agent simulation..."
        }, client_id)
        
        # Spawn agents
        agents = agent_service.spawn_agents(context=topic_decoded)
        
        await websocket_manager.send_personal_message({
            "type": "agents_spawned",
            "agents_count": len(agents),
            "agents": [{"role": a["role"], "personality": a["personality"][:50]} for a in agents],
            "message": f"✨ {len(agents)} AI agents spawned and ready"
        }, client_id)
        
        # Create callback for real-time updates
        async def simulation_callback(update: dict):
            await websocket_manager.send_personal_message(update, client_id)

        # Run simulation in background so we can receive human posts live
        sim_task: Optional[asyncio.Task] = None
        sim_result: dict = {}

        async def _run():
            nonlocal sim_result
            sim_result = await simulation_service.run_simulation(
                agents=agents,
                topic=topic_decoded,
                rounds=3,
                callback=simulation_callback,
            )

        sim_task = asyncio.create_task(_run())

        # Wait for simulation_start to learn simulation_id by polling active_simulations key
        # (run_simulation uses deterministic sim_id from topic)
        simulation_id = f"sim_{topic_decoded.replace(' ', '_')[:50]}"

        # Listen for client messages while simulation runs
        while True:
            if sim_task.done():
                break
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            mtype = data.get("type")
            if mtype == "human_message":
                msg = (data.get("message") or "").strip()
                influence = float(data.get("influence_level", 0.6))
                name = (data.get("display_name") or "Human").strip()
                if msg:
                    ok = simulation_service.inject_human_message(
                        simulation_id=simulation_id,
                        message=msg,
                        influence_level=influence,
                        display_name=name,
                    )
                    await websocket_manager.send_personal_message(
                        {"type": "human_ack", "accepted": bool(ok)},
                        client_id,
                    )
            elif mtype == "close":
                break
        
        # Send final result
        await websocket_manager.send_personal_message({
            "type": "simulation_complete",
            "message": "✅ Simulation completed successfully!",
            "result": {
                "simulation_id": sim_result.get("simulation_id"),
                "status": sim_result.get("status"),
                "messages_count": len(sim_result.get("messages", [])),
                "consensus": sim_result.get("consensus"),
                "final_prediction": sim_result.get("final_prediction"),
            }
        }, client_id)
        
        # Keep connection open for a bit in case client wants to query more
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "close":
                    break
        except:
            pass
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket simulation disconnected: {client_id}")
        websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket simulation error: {e}")
        try:
            await websocket_manager.send_personal_message({
                "type": "error",
                "message": f"Simulation failed: {str(e)}"
            }, client_id)
        except:
            pass
        websocket_manager.disconnect(client_id)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "active_connections": websocket_manager.get_active_connections_count(),
        "message": "WebSocket server is running"
    }
