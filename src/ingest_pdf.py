"""
Ingest KSEI PDF files into ChromaDB.
Extracts text per page and stores with metadata.
"""

import os
from typing import List, Dict, Any
from embedder import embed_and_store, chunk_text, get_stats, delete_collection

# Try to import pdfplumber
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not available. PDF ingestion will be skipped.")


def extract_pdf_text(filepath: str) -> List[Dict[str, Any]]:
    """
    Extract text from a PDF file page by page.
    
    Args:
        filepath: Path to PDF file
    
    Returns:
        List of dicts with 'page_number', 'text', and 'metadata'
    """
    if not PDFPLUMBER_AVAILABLE:
        print(f"Cannot extract {filepath}: pdfplumber not installed")
        return []
    
    pages = []
    
    try:
        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({
                        'page_number': i,
                        'text': text.strip(),
                        'char_count': len(text)
                    })
    except Exception as e:
        print(f"Error extracting {filepath}: {e}")
        return []
    
    return pages


def parse_month_year(filename: str) -> str:
    """Parse month/year from filename like 'mar26.pdf' or 'feb26.pdf'."""
    # Remove extension
    name = os.path.splitext(filename)[0].lower()
    
    # Month mapping
    months = {
        'jan': 'January', 'feb': 'February', 'mar': 'March',
        'apr': 'April', 'may': 'May', 'jun': 'June',
        'jul': 'July', 'aug': 'August', 'sep': 'September',
        'oct': 'October', 'nov': 'November', 'dec': 'December'
    }
    
    # Extract month abbreviation (first 3 chars if alphabetic)
    month_abbr = ''
    year = ''
    
    for char in name:
        if char.isalpha():
            month_abbr += char
        elif char.isdigit():
            year += char
    
    month_name = months.get(month_abbr[:3], month_abbr)
    full_year = f"20{year}" if len(year) == 2 else year
    
    return f"{month_name} {full_year}"


def ingest_pdf(filepath: str, collection_name: str = "ksei_data") -> Dict[str, int]:
    """
    Ingest a single PDF file into ChromaDB.
    
    Args:
        filepath: Path to PDF file
        collection_name: ChromaDB collection name
    
    Returns:
        Stats about ingestion
    """
    filename = os.path.basename(filepath)
    print(f"Extracting {filename}...")
    
    # Extract text from PDF
    pages = extract_pdf_text(filepath)
    
    if not pages:
        print(f"  No text extracted from {filename}")
        return {"pages_extracted": 0, "chunks_created": 0}
    
    print(f"  Extracted {len(pages)} pages")
    
    # Parse month/year from filename
    month_year = parse_month_year(filename)
    
    # Process each page into chunks
    all_chunks = []
    all_metadata = []
    
    for page in pages:
        # Chunk the page text
        page_chunks = chunk_text(page['text'], chunk_size=800, overlap=100)
        
        for chunk in page_chunks:
            metadata = {
                "source": "ksei_pdf",
                "filename": filename,
                "page_number": page['page_number'],
                "month_year": month_year,
                "chunk_type": "pdf_page"
            }
            
            all_chunks.append(chunk)
            all_metadata.append(metadata)
    
    # Store in ChromaDB
    print(f"  Storing {len(all_chunks)} chunks...")
    stored_count = embed_and_store(all_chunks, all_metadata, collection_name)
    
    return {
        "pages_extracted": len(pages),
        "chunks_created": len(all_chunks),
        "chunks_stored": stored_count
    }


def ingest_all_pdfs(pdf_dir: str = None, collection_name: str = "ksei_data") -> Dict[str, Any]:
    """
    Ingest all PDF files in a directory.
    
    Args:
        pdf_dir: Directory containing PDF files (defaults to ../raw_data)
        collection_name: ChromaDB collection name
    
    Returns:
        Combined stats
    """
    if pdf_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_dir = os.path.join(os.path.dirname(script_dir), "raw_data")
    
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    pdf_files.sort()
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        return {"error": "No PDF files found"}
    
    print(f"Found {len(pdf_files)} PDF files: {pdf_files}")
    
    all_stats = []
    
    for pdf_file in pdf_files:
        filepath = os.path.join(pdf_dir, pdf_file)
        stats = ingest_pdf(filepath, collection_name)
        all_stats.append({"file": pdf_file, **stats})
    
    # Print summary
    print("\n" + "="*50)
    print("PDF INGESTION SUMMARY")
    print("="*50)
    total_chunks = 0
    for s in all_stats:
        chunks = s.get('chunks_created', 0)
        total_chunks += chunks
        print(f"{s['file']}: {s.get('pages_extracted', 0)} pages -> {chunks} chunks")
    
    print(f"\nTotal PDF chunks added: {total_chunks}")
    print(f"Total documents in database: {get_stats()['document_count']}")
    
    return {
        "files_processed": len(pdf_files),
        "total_chunks": total_chunks,
        "file_stats": all_stats
    }


if __name__ == "__main__":
    import sys
    
    # Check dependencies
    if not PDFPLUMBER_AVAILABLE:
        print("Error: pdfplumber is required for PDF ingestion.")
        print("Run: pip install pdfplumber")
        sys.exit(1)
    
    # Ingest all PDFs
    result = ingest_all_pdfs()
    print("\nDone!")
