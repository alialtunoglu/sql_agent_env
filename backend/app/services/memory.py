"""
Abstract Memory Layer for Chat History Management
Follows SOLID principles with Abstract Base Class and concrete implementations
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import json
import redis
from langchain.schema import HumanMessage, AIMessage, BaseMessage
from app.models import ChatMessage


class AbstractChatMemory(ABC):
    """
    Abstract base class for chat memory storage.
    Enables easy switching between different storage backends (Redis, PostgreSQL, etc.)
    """

    @abstractmethod
    def add_messages(self, session_id: str, messages: List[BaseMessage]) -> None:
        """Add messages to the session history"""
        pass

    @abstractmethod
    def get_messages(self, session_id: str) -> List[BaseMessage]:
        """Retrieve all messages for a session"""
        pass

    @abstractmethod
    def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session"""
        pass

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        pass


class RedisChatMemory(AbstractChatMemory):
    """
    Redis-based chat memory implementation.
    Provides persistent, distributed storage for production use.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl: int = 86400,  # 24 hours default TTL
    ):
        self.ttl = ttl
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
        )
        # Test connection
        try:
            self.redis_client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def _serialize_message(self, message: BaseMessage) -> Dict[str, Any]:
        """Convert LangChain message to JSON-serializable dict"""
        return {
            "type": message.__class__.__name__,
            "content": message.content,
        }

    def _deserialize_message(self, data: Dict[str, Any]) -> BaseMessage:
        """Convert dict back to LangChain message"""
        message_type = data.get("type")
        content = data.get("content", "")

        if message_type == "HumanMessage":
            return HumanMessage(content=content)
        elif message_type == "AIMessage":
            return AIMessage(content=content)
        else:
            raise ValueError(f"Unknown message type: {message_type}")

    def add_messages(self, session_id: str, messages: List[BaseMessage]) -> None:
        """Add messages to Redis list with TTL"""
        key = f"chat_history:{session_id}"
        serialized = [json.dumps(self._serialize_message(msg)) for msg in messages]
        
        # Use pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        for msg in serialized:
            pipe.rpush(key, msg)
        pipe.expire(key, self.ttl)
        pipe.execute()

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        """Retrieve all messages from Redis"""
        key = f"chat_history:{session_id}"
        raw_messages = self.redis_client.lrange(key, 0, -1)
        
        messages = []
        for raw in raw_messages:
            try:
                data = json.loads(raw)
                messages.append(self._deserialize_message(data))
            except (json.JSONDecodeError, ValueError) as e:
                # Log error but continue processing other messages
                print(f"Warning: Failed to deserialize message: {e}")
                continue
        
        return messages

    def clear_session(self, session_id: str) -> None:
        """Delete session from Redis"""
        key = f"chat_history:{session_id}"
        self.redis_client.delete(key)

    def session_exists(self, session_id: str) -> bool:
        """Check if session key exists in Redis"""
        key = f"chat_history:{session_id}"
        return self.redis_client.exists(key) > 0


class InMemoryChatMemory(AbstractChatMemory):
    """
    In-memory chat memory implementation.
    Suitable for development/testing or single-instance deployments.
    Data is lost on application restart.
    """

    def __init__(self):
        self._storage: Dict[str, List[BaseMessage]] = {}

    def add_messages(self, session_id: str, messages: List[BaseMessage]) -> None:
        """Add messages to in-memory storage"""
        if session_id not in self._storage:
            self._storage[session_id] = []
        self._storage[session_id].extend(messages)

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        """Retrieve messages from memory"""
        return self._storage.get(session_id, [])

    def clear_session(self, session_id: str) -> None:
        """Clear session from memory"""
        if session_id in self._storage:
            del self._storage[session_id]

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists in memory"""
        return session_id in self._storage


def create_memory_backend(backend_type: str = "redis", **kwargs) -> AbstractChatMemory:
    """
    Factory function to create appropriate memory backend.
    Follows Factory Pattern for easy extensibility.
    
    Args:
        backend_type: Type of backend ('redis', 'in-memory')
        **kwargs: Backend-specific configuration
    
    Returns:
        AbstractChatMemory implementation
    
    Raises:
        ValueError: If backend_type is not supported
    """
    if backend_type.lower() == "redis":
        return RedisChatMemory(**kwargs)
    elif backend_type.lower() == "in-memory":
        return InMemoryChatMemory()
    else:
        raise ValueError(
            f"Unsupported memory backend: {backend_type}. "
            f"Supported backends: 'redis', 'in-memory'"
        )
