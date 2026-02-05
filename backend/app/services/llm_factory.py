"""
LLM Factory - Configurable LLM Backend
Supports multiple LLM providers (Gemini, Ollama) following Factory Pattern
"""

from typing import Protocol
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings


class LLMProvider(Protocol):
    """Abstract LLM Provider Interface"""
    def create_chat_model(self) -> BaseChatModel:
        ...
    
    def create_embedding_model(self) -> Embeddings:
        ...


class GeminiProvider:
    """Google Gemini LLM Provider"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key
        self.model = model
    
    def create_chat_model(self) -> BaseChatModel:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=self.api_key,
            temperature=0
        )
    
    def create_embedding_model(self) -> Embeddings:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.api_key
        )


class OllamaProvider:
    """Ollama LLM Provider (Local, Free)"""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        embedding_model: str = "nomic-embed-text"
    ):
        self.base_url = base_url
        self.model = model
        self.embedding_model = embedding_model
    
    def create_chat_model(self) -> BaseChatModel:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0
        )
    
    def create_embedding_model(self) -> Embeddings:
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(
            base_url=self.base_url,
            model=self.embedding_model
        )


class LLMFactory:
    """
    Factory for creating LLM instances based on configuration.
    Follows Factory Pattern and Dependency Inversion Principle.
    """
    
    @staticmethod
    def create_chat_model(
        backend: str = "ollama",
        **kwargs
    ) -> BaseChatModel:
        """
        Create chat model based on backend type.
        
        Args:
            backend: "gemini" or "ollama"
            **kwargs: Provider-specific configuration
        
        Returns:
            BaseChatModel instance
        """
        backend = backend.lower()
        
        if backend == "gemini":
            provider = GeminiProvider(
                api_key=kwargs.get("api_key", ""),
                model=kwargs.get("model", "gemini-2.0-flash-exp")
            )
        elif backend == "ollama":
            provider = OllamaProvider(
                base_url=kwargs.get("base_url", "http://localhost:11434"),
                model=kwargs.get("model", "llama3.1:8b"),
                embedding_model=kwargs.get("embedding_model", "nomic-embed-text")
            )
        else:
            raise ValueError(
                f"Unknown LLM backend: {backend}. "
                f"Supported backends: 'gemini', 'ollama'"
            )
        
        return provider.create_chat_model()
    
    @staticmethod
    def create_embedding_model(
        backend: str = "ollama",
        **kwargs
    ) -> Embeddings:
        """
        Create embedding model based on backend type.
        
        Args:
            backend: "gemini" or "ollama"
            **kwargs: Provider-specific configuration
        
        Returns:
            Embeddings instance
        """
        backend = backend.lower()
        
        if backend == "gemini":
            provider = GeminiProvider(
                api_key=kwargs.get("api_key", ""),
                model=kwargs.get("model", "gemini-2.0-flash-exp")
            )
        elif backend == "ollama":
            provider = OllamaProvider(
                base_url=kwargs.get("base_url", "http://localhost:11434"),
                model=kwargs.get("model", "llama3.1:8b"),
                embedding_model=kwargs.get("embedding_model", "nomic-embed-text")
            )
        else:
            raise ValueError(
                f"Unknown LLM backend: {backend}. "
                f"Supported backends: 'gemini', 'ollama'"
            )
        
        return provider.create_embedding_model()
