"""
RAG (Retrieval-Augmented Generation) System for Dynamic Schema Management
Uses ChromaDB to store table/column embeddings and retrieve only relevant schema information
"""

import os
import json
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain.embeddings import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
from app.core.config import CHROMA_PERSIST_DIRECTORY, GOOGLE_API_KEY, BASE_DIR


class SchemaRAG:
    """
    Manages vector storage and retrieval of database schema information.
    Reduces token usage by fetching only relevant tables based on user query.
    """

    def __init__(
        self,
        persist_directory: str = CHROMA_PERSIST_DIRECTORY,
        collection_name: str = "schema_metadata",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY
        )
        
        # Ensure persist directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize Chroma vector store
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
        )

    def initialize_from_metadata(self, metadata_path: Optional[str] = None) -> None:
        """
        Load schema metadata from JSON and create embeddings.
        Should be called once during application startup or when schema changes.
        
        Args:
            metadata_path: Path to schema_metadata.json file
        """
        if metadata_path is None:
            metadata_path = os.path.join(BASE_DIR, "data", "schema_metadata.json")
        
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Schema metadata not found at {metadata_path}")
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        # Check if collection already has documents
        existing_count = self.vector_store._collection.count()
        if existing_count > 0:
            print(f"Schema RAG already initialized with {existing_count} documents")
            return
        
        documents = []
        
        # Create documents for each table
        for table_name, table_info in metadata.get("tables", {}).items():
            # Main table document with comprehensive information
            table_content = self._format_table_document(
                table_name,
                table_info,
                metadata.get("database_description", "")
            )
            
            doc = Document(
                page_content=table_content,
                metadata={
                    "table_name": table_name,
                    "type": "table",
                    "description": table_info.get("description", ""),
                }
            )
            documents.append(doc)
            
            # Create additional documents for relationships (for better JOIN discovery)
            if table_info.get("relationships"):
                rel_content = f"Table: {table_name}\n"
                rel_content += f"Relationships:\n"
                for rel in table_info["relationships"]:
                    rel_content += f"- {rel}\n"
                
                rel_doc = Document(
                    page_content=rel_content,
                    metadata={
                        "table_name": table_name,
                        "type": "relationships",
                    }
                )
                documents.append(rel_doc)
        
        # Add common join patterns as separate documents
        for idx, join_pattern in enumerate(metadata.get("common_join_patterns", [])):
            join_doc = Document(
                page_content=f"Common Join Pattern: {join_pattern.get('description', '')}\n"
                            f"Example Query: {join_pattern.get('query', '')}",
                metadata={
                    "type": "join_pattern",
                    "pattern_id": idx,
                }
            )
            documents.append(join_doc)
        
        # Add all documents to vector store
        self.vector_store.add_documents(documents)
        print(f"✓ Initialized Schema RAG with {len(documents)} documents")

    def _format_table_document(
        self, table_name: str, table_info: Dict[str, Any], db_description: str
    ) -> str:
        """Format table information into a searchable text document"""
        content = f"Database: {db_description}\n\n"
        content += f"Table Name: {table_name}\n"
        content += f"Description: {table_info.get('description', 'No description')}\n\n"
        
        # Add columns
        content += "Columns:\n"
        for col_name, col_desc in table_info.get("columns", {}).items():
            content += f"  - {col_name}: {col_desc}\n"
        
        # Add relationships
        if table_info.get("relationships"):
            content += "\nRelationships:\n"
            for rel in table_info["relationships"]:
                content += f"  - {rel}\n"
        
        # Add business rules
        if table_info.get("business_rules"):
            content += "\nBusiness Rules:\n"
            for rule in table_info["business_rules"]:
                content += f"  - {rule}\n"
        
        # Add example queries
        if table_info.get("example_queries"):
            content += "\nExample Use Cases:\n"
            for query in table_info["example_queries"]:
                content += f"  - {query}\n"
        
        return content

    def get_relevant_schema(
        self, user_query: str, top_k: int = 5
    ) -> str:
        """
        Retrieve relevant table schemas based on user query using similarity search.
        
        Args:
            user_query: User's natural language question
            top_k: Number of most relevant documents to retrieve
        
        Returns:
            Formatted schema description containing only relevant tables
        """
        # Perform similarity search
        relevant_docs = self.vector_store.similarity_search(
            user_query, k=top_k
        )
        
        # Extract unique table names
        relevant_tables = set()
        join_patterns = []
        
        for doc in relevant_docs:
            if doc.metadata.get("type") == "table":
                relevant_tables.add(doc.metadata["table_name"])
            elif doc.metadata.get("type") == "join_pattern":
                join_patterns.append(doc.page_content)
        
        # Build schema description from relevant documents
        schema_parts = []
        
        # Add database context
        schema_parts.append("## RELEVANT DATABASE SCHEMA:")
        
        # Add table information
        for doc in relevant_docs:
            if doc.metadata.get("type") == "table":
                schema_parts.append(f"\n### {doc.metadata['table_name']}")
                schema_parts.append(doc.page_content)
        
        # Add relevant join patterns
        if join_patterns:
            schema_parts.append("\n## RELEVANT JOIN PATTERNS:")
            for pattern in join_patterns:
                schema_parts.append(pattern)
        
        result = "\n".join(schema_parts)
        
        # Debug info
        print(f"RAG: Retrieved {len(relevant_tables)} relevant tables for query: '{user_query[:50]}...'")
        print(f"Tables: {', '.join(relevant_tables)}")
        
        return result

    def clear_collection(self) -> None:
        """Clear all documents from the vector store"""
        self.vector_store.delete_collection()
        print("✓ Cleared schema RAG collection")


# Singleton instance
_schema_rag_instance: Optional[SchemaRAG] = None


def get_schema_rag() -> SchemaRAG:
    """
    Get or create singleton SchemaRAG instance.
    
    Returns:
        SchemaRAG instance
    """
    global _schema_rag_instance
    
    if _schema_rag_instance is None:
        _schema_rag_instance = SchemaRAG()
    
    return _schema_rag_instance


def initialize_schema_rag() -> None:
    """
    Initialize Schema RAG system on application startup.
    Safe to call multiple times (checks if already initialized).
    """
    try:
        rag = get_schema_rag()
        rag.initialize_from_metadata()
        print("✓ Schema RAG system ready")
    except Exception as e:
        print(f"⚠ Failed to initialize Schema RAG: {e}")
        print("⚠ Will fall back to full schema description")
