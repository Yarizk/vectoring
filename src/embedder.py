"""
Shared embedding and chunking logic for KSEI RAG.
Uses sentence-transformers (all-MiniLM-L6-v2) for local embeddings.
"""

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import hashlib
import os

# Get the project root directory (parent of src)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "chroma_db")

# Also ensure chroma_db directory exists
os.makedirs(CHROMA_DB_PATH, exist_ok=True)

# Initialize embedding model (local, free)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
# Get the project root directory (parent of src)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "chroma_db")

# Ensure chroma_db directory exists
os.makedirs(CHROMA_DB_PATH, exist_ok=True)

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Initialize embedding model
model = SentenceTransformer(EMBEDDING_MODEL)


def get_or_create_collection(collection_name: str = "ksei_data"):
    """Get or create a ChromaDB collection."""
    return chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "KSEI ownership and PDF data"}
    )


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence or word boundary
        if end < len(text):
            # Look for sentence ending
            last_period = chunk.rfind('.')
            last_space = chunk.rfind(' ')
            
            if last_period > chunk_size * 0.7:
                end = start + last_period + 1
            elif last_space > chunk_size * 0.7:
                end = start + last_space
        
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    return chunks


def generate_id(text: str, metadata: Dict[str, Any], index: int = 0) -> str:
    """Generate a unique ID for a chunk based on content and metadata."""
    # Include more metadata fields for uniqueness + index to avoid collisions
    content = f"{text}_{metadata.get('ticker', '')}_{metadata.get('source', '')}_{metadata.get('date', '')}_{metadata.get('filename', '')}_{metadata.get('page_number', '')}_{index}"
    return hashlib.md5(content.encode()).hexdigest()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts using the sentence-transformers model."""
    return model.encode(texts, show_progress_bar=False).tolist()


def embed_and_store(
    chunks: List[str],
    metadata_list: List[Dict[str, Any]],
    collection_name: str = "ksei_data",
    batch_size: int = 5000
) -> int:
    """
    Embed chunks and store them in ChromaDB.
    
    Args:
        chunks: List of text chunks
        metadata_list: List of metadata dicts (one per chunk)
        collection_name: ChromaDB collection name
        batch_size: Maximum batch size for ChromaDB
    
    Returns:
        Number of chunks stored
    """
    if not chunks:
        return 0
    
    collection = get_or_create_collection(collection_name)
    total_stored = 0
    
    # Process in batches
    id_counter = 0
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_metadata = metadata_list[i:i + batch_size]
        
        # Generate unique IDs with counter to avoid collisions
        ids = []
        for chunk, meta in zip(batch_chunks, batch_metadata):
            ids.append(generate_id(chunk, meta, id_counter))
            id_counter += 1
        
        # Embed texts
        embeddings = embed_texts(batch_chunks)
        
        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=batch_chunks,
            metadatas=batch_metadata
        )
        
        total_stored += len(batch_chunks)
    
    return total_stored


def search(
    query: str,
    n_results: int = 5,
    collection_name: str = "ksei_data",
    where: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search for relevant chunks in ChromaDB.
    
    Args:
        query: Search query
        n_results: Number of results to return
        collection_name: ChromaDB collection name
        where: Optional filter conditions
    
    Returns:
        List of result dictionaries with text, metadata, and distance
    """
    collection = get_or_create_collection(collection_name)
    
    # Embed query
    query_embedding = model.encode([query]).tolist()
    
    # Search
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"]
    )
    
    # Format results
    formatted_results = []
    if results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            formatted_results.append({
                "id": doc_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
    
    return formatted_results


def get_stats(collection_name: str = "ksei_data") -> Dict[str, Any]:
    """Get collection statistics."""
    collection = get_or_create_collection(collection_name)
    count = collection.count()
    
    return {
        "collection_name": collection_name,
        "document_count": count,
        "embedding_model": EMBEDDING_MODEL,
        "chroma_db_path": os.path.abspath(CHROMA_DB_PATH)
    }


def delete_collection(collection_name: str = "ksei_data"):
    """Delete a collection."""
    try:
        chroma_client.delete_collection(name=collection_name)
        return True
    except Exception:
        return False
