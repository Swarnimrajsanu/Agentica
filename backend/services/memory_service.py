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
        logger.info(f"MongoDB connection established (DB: {settings.MONGO_DB_NAME})")
    
    async def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
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