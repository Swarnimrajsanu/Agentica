from fastapi import WebSocket
from typing import Dict, Set
from loguru import logger
import json


class WebSocketManager:
    """Manages WebSocket connections for real-time simulation streaming."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.simulation_subscriptions: Dict[str, Set[str]] = {}
        logger.info("WebSocket Manager initialized")
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Accept and store WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            client_id: Unique identifier for the client
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connected",
            "message": "Connected to Agentica WebSocket",
            "client_id": client_id
        }, client_id)
    
    def disconnect(self, client_id: str):
        """
        Remove WebSocket connection.
        
        Args:
            client_id: Client identifier to remove
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")
        
        # Clean up subscriptions
        for sim_id in list(self.simulation_subscriptions.keys()):
            if client_id in self.simulation_subscriptions[sim_id]:
                self.simulation_subscriptions[sim_id].discard(client_id)
            if not self.simulation_subscriptions[sim_id]:
                del self.simulation_subscriptions[sim_id]
    
    async def send_personal_message(self, message: dict, client_id: str):
        """
        Send message to specific client.
        
        Args:
            message: Message dictionary
            client_id: Target client ID
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def subscribe_to_simulation(self, client_id: str, simulation_id: str):
        """
        Subscribe client to simulation updates.
        
        Args:
            client_id: Client identifier
            simulation_id: Simulation ID to subscribe to
        """
        if simulation_id not in self.simulation_subscriptions:
            self.simulation_subscriptions[simulation_id] = set()
        
        self.simulation_subscriptions[simulation_id].add(client_id)
        logger.info(f"Client {client_id} subscribed to simulation {simulation_id}")
    
    async def broadcast_to_simulation(self, message: dict, simulation_id: str):
        """
        Broadcast message to all clients subscribed to a simulation.
        
        Args:
            message: Message to broadcast
            simulation_id: Simulation ID
        """
        if simulation_id in self.simulation_subscriptions:
            disconnected_clients = []
            
            for client_id in self.simulation_subscriptions[simulation_id]:
                if client_id in self.active_connections:
                    try:
                        await self.active_connections[client_id].send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to {client_id}: {e}")
                        disconnected_clients.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected_clients:
                self.disconnect(client_id)
    
    async def send_simulation_update(self, simulation_id: str, update: dict):
        """
        Send simulation update to all subscribers.
        
        Args:
            simulation_id: Simulation ID
            update: Update data
        """
        message = {
            "type": "simulation_update",
            "simulation_id": simulation_id,
            "data": update
        }
        
        await self.broadcast_to_simulation(message, simulation_id)
    
    def get_active_connections_count(self) -> int:
        """Get number of active WebSocket connections."""
        return len(self.active_connections)
    
    def get_simulation_subscribers_count(self, simulation_id: str) -> int:
        """Get number of subscribers for a simulation."""
        if simulation_id in self.simulation_subscriptions:
            return len(self.simulation_subscriptions[simulation_id])
        return 0


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
