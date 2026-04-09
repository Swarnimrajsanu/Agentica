from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from config.settings import settings
from typing import Optional
from datetime import datetime
import copy


class MemoryService:
    """MongoDB Memory Service for conversation and agent memory."""
    
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB_NAME]
        self.messages_collection = self.db.messages
        self.agent_memory_collection = self.db.agent_memory
        self.simulations_collection = self.db.simulations
        logger.info(f"MongoDB connection established (DB: {settings.MONGO_DB_NAME})")
    
    async def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
            
    async def save_simulation(self, simulation_id: str, data: dict) -> bool:
        """
        Save or update simulation metadata.
        """
        try:
            doc = copy.deepcopy(data)
            doc["updated_at"] = datetime.utcnow()
            if "created_at" not in doc:
                doc["created_at"] = datetime.utcnow()
            
            await self.simulations_collection.update_one(
                {"simulation_id": simulation_id},
                {"$set": doc},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving simulation {simulation_id}: {e}")
            return False

    async def list_simulations(self, limit: int = 20) -> list:
        """
        Retrieve list of simulations from database.
        """
        try:
            cursor = self.simulations_collection.find().sort("updated_at", -1).limit(limit)
            sims = await cursor.to_list(length=limit)
            return [self._sanitize_document(s) for s in sims]
        except Exception as e:
            logger.error(f"Error listing simulations: {e}")
            return []

    async def get_simulation(self, simulation_id: str) -> Optional[dict]:
        """
        Retrieve a single simulation by ID.
        """
        try:
            doc = await self.simulations_collection.find_one({"simulation_id": simulation_id})
            return self._sanitize_document(doc)
        except Exception as e:
            logger.error(f"Error getting simulation {simulation_id}: {e}")
            return None

    async def delete_simulation(self, simulation_id: str) -> bool:
        """
        Delete simulation and all its messages.
        """
        try:
            # Delete simulation metadata
            await self.simulations_collection.delete_one({"simulation_id": simulation_id})
            # Delete all messages for this simulation
            await self.messages_collection.delete_many({"simulation_id": simulation_id})
            logger.info(f"Deleted simulation {simulation_id} and its messages")
            return True
        except Exception as e:
            logger.error(f"Error deleting simulation {simulation_id}: {e}")
            return False

    async def clear_all_simulations(self) -> bool:
        """
        Clear all simulation history.
        """
        try:
            await self.simulations_collection.delete_many({})
            await self.messages_collection.delete_many({})
            logger.info("Cleared all simulation history")
            return True
        except Exception as e:
            logger.error(f"Error clearing all simulations: {e}")
            return False
    
    def _sanitize_document(self, doc: dict) -> dict:
        """
        Convert MongoDB-specific types to JSON-serializable types.
        
        Args:
            doc: Document with potential MongoDB types
            
        Returns:
            Sanitized document
        """
        if not doc:
            return doc
        
        sanitized = copy.deepcopy(doc)
        
        # Convert ObjectId to string
        if "_id" in sanitized:
            from bson import ObjectId
            if isinstance(sanitized["_id"], ObjectId):
                sanitized["_id"] = str(sanitized["_id"])
        
        # Convert datetime to string
        if "timestamp" in sanitized:
            if isinstance(sanitized["timestamp"], datetime):
                sanitized["timestamp"] = sanitized["timestamp"].isoformat()
        
        return sanitized
    
    async def save_message(self, data: dict) -> Optional[str]:
        """
        Save a message to the database.
        
        Args:
            data: Message data dictionary
            
        Returns:
            Inserted document ID or None if error
        """
        try:
            # Create a copy to avoid modifying the original
            doc_to_save = copy.deepcopy(data)
            
            # Add timestamp if not present
            if "timestamp" not in doc_to_save:
                doc_to_save["timestamp"] = datetime.utcnow()
            
            result = await self.messages_collection.insert_one(doc_to_save)
            logger.info(f"Message saved with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    async def get_messages(self, limit: int = 50, skip: int = 0) -> list:
        """
        Retrieve messages from the database.
        
        Args:
            limit: Maximum number of messages to return
            skip: Number of messages to skip (for pagination)
            
        Returns:
            List of messages
        """
        try:
            cursor = self.messages_collection.find().sort("timestamp", -1).skip(skip).limit(limit)
            messages = await cursor.to_list(length=limit)
            
            # Sanitize all messages
            sanitized_messages = [self._sanitize_document(msg) for msg in messages]
            
            logger.info(f"Retrieved {len(sanitized_messages)} messages")
            return sanitized_messages
        except Exception as e:
            logger.error(f"Error retrieving messages: {e}")
            return []
    
    async def save_agent_memory(self, agent_id: str, memory_data: dict) -> Optional[str]:
        """
        Save agent-specific memory.
        
        Args:
            agent_id: Unique identifier for the agent
            memory_data: Memory data to store
            
        Returns:
            Inserted document ID or None if error
        """
        try:
            memory_doc = {
                "agent_id": agent_id,
                "data": memory_data,
                "timestamp": datetime.utcnow()
            }
            
            result = await self.agent_memory_collection.insert_one(memory_doc)
            logger.info(f"Agent memory saved for agent {agent_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving agent memory: {e}")
            return None
    
    async def get_agent_memory(self, agent_id: str, limit: int = 20) -> list:
        """
        Retrieve agent-specific memory.
        
        Args:
            agent_id: Unique identifier for the agent
            limit: Maximum number of memory entries to return
            
        Returns:
            List of agent memory entries
        """
        try:
            cursor = (
                self.agent_memory_collection
                .find({"agent_id": agent_id})
                .sort("timestamp", -1)
                .limit(limit)
            )
            memories = await cursor.to_list(length=limit)
            
            # Sanitize memories
            sanitized_memories = [self._sanitize_document(mem) for mem in memories]
            
            logger.info(f"Retrieved {len(sanitized_memories)} memories for agent {agent_id}")
            return sanitized_memories
        except Exception as e:
            logger.error(f"Error retrieving agent memory: {e}")
            return []
    
    async def clear_agent_memory(self, agent_id: str) -> bool:
        """
        Clear all memory for a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.agent_memory_collection.delete_many({"agent_id": agent_id})
            logger.info(f"Cleared {result.deleted_count} memories for agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing agent memory: {e}")
            return False
    
    async def get_conversation_history(self, session_id: str, limit: int = 50) -> list:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of messages in the session
        """
        try:
            cursor = (
                self.messages_collection
                .find({"session_id": session_id})
                .sort("timestamp", 1)
                .limit(limit)
            )
            messages = await cursor.to_list(length=limit)
            
            # Sanitize messages
            sanitized_messages = [self._sanitize_document(msg) for msg in messages]
            
            logger.info(f"Retrieved {len(sanitized_messages)} messages for session {session_id}")
            return sanitized_messages
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []


# Global memory service instance
memory_service = MemoryService()