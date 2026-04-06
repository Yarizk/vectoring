"""
Ingest KSEI JSON ownership data into ChromaDB.
Flattens ownership records into readable text chunks.
"""

import json
import os
from typing import List, Dict, Any
from collections import defaultdict
from embedder import embed_and_store, get_stats, delete_collection
from tqdm import tqdm


def load_ksei_json(filepath: str) -> Dict[str, Any]:
    """Load KSEI JSON data file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def group_by_ticker(records: List[Dict]) -> Dict[str, List[Dict]]:
    """Group ownership records by stock ticker."""
    tickers = defaultdict(list)
    for record in records:
        tickers[record['share_code']].append(record)
    return tickers


def format_ticker_summary(ticker: str, records: List[Dict], report_date: str) -> str:
    """
    Create a natural language summary of a stock's ownership structure.
    
    Returns a readable text describing the ownership profile.
    """
    if not records:
        return ""
    
    # Get issuer name from first record
    issuer_name = records[0]['issuer_name']
    
    # Calculate totals by ownership type
    local_total = sum(r['percentage'] for r in records if r['local_foreign'] == 'L')
    foreign_total = sum(r['percentage'] for r in records if r['local_foreign'] == 'A')
    
    # Get top holders
    sorted_records = sorted(records, key=lambda x: x['percentage'], reverse=True)
    top_holders = sorted_records[:10]  # Top 10 holders
    
    # Build summary text
    lines = [
        f"SAHAM: {ticker} - {issuer_name}",
        f"Tanggal Laporan: {report_date}",
        f"",
        f"KEPEMILIKAN KESELURUHAN:",
        f"- Kepemilikan Lokal: {local_total:.2f}%",
        f"- Kepemilikan Asing: {foreign_total:.2f}%",
        f"",
        f"PEMEGANG SAHAM TERBESAR (Top {len(top_holders)}):",
    ]
    
    for i, r in enumerate(top_holders, 1):
        holder_type = "Asing" if r['local_foreign'] == 'A' else "Lokal"
        investor_type = r.get('investor_type', 'Unknown')
        domicile = r.get('domicile', 'Unknown')
        
        line = f"{i}. {r['investor_name']} - {r['percentage']:.2f}% ({holder_type}"
        if domicile and domicile != 'Unknown':
            line += f", {domicile}"
        line += f", {investor_type})"
        lines.append(line)
    
    # Group by investor type for additional context
    lines.append("")
    lines.append("KEPEMILIKAN BERDASARKAN TIPE INVESTOR:")
    
    type_groups = defaultdict(list)
    for r in records:
        inv_type = r.get('investor_type', 'Other') or 'Other'
        type_groups[inv_type].append(r)
    
    for inv_type, type_records in sorted(type_groups.items()):
        total_pct = sum(r['percentage'] for r in type_records)
        lines.append(f"- {inv_type}: {total_pct:.2f}%")
    
    return "\n".join(lines)


def format_holder_focused_chunks(records: List[Dict], report_date: str) -> List[Dict[str, Any]]:
    """
    Create chunks focused on individual significant holders (>1%).
    This helps answer questions about specific investors.
    """
    chunks = []
    
    for r in records:
        if r['percentage'] < 1.0:  # Skip small holders
            continue
            
        ticker = r['share_code']
        issuer = r['issuer_name']
        holder = r['investor_name']
        holder_type = "Asing" if r['local_foreign'] == 'A' else "Lokal"
        investor_type = r.get('investor_type', 'Unknown')
        domicile = r.get('domicile', '')
        
        text = f"""
INVESTOR: {holder}
Saham: {ticker} ({issuer})
Kepemilikan: {r['percentage']:.2f}%
Tipe: {investor_type} ({holder_type})
Domicile: {domicile or 'Unknown'}
Report Date: {report_date}
        """.strip()
        
        metadata = {
            "source": "ksei_json",
            "ticker": ticker,
            "issuer": issuer,
            "holder_name": holder,
            "holder_type": holder_type,
            "investor_type": investor_type,
            "percentage": r['percentage'],
            "domicile": domicile,
            "date": report_date,
            "chunk_type": "holder_focus"
        }
        
        chunks.append({"text": text, "metadata": metadata})
    
    return chunks


def ingest_ksei_json(filepath: str, clear_existing: bool = False) -> Dict[str, int]:
    """
    Ingest a KSEI JSON file into ChromaDB.
    
    Args:
        filepath: Path to KSEI JSON file
        clear_existing: Whether to clear existing collection first
    
    Returns:
        Stats about ingestion
    """
    print(f"Loading {filepath}...")
    data = load_ksei_json(filepath)
    
    metadata = data.get('metadata', {})
    records = data.get('records', [])
    report_date = metadata.get('report_date', 'unknown')
    
    print(f"Report: {report_date}")
    print(f"Records: {len(records)}")
    print(f"Unique stocks: {metadata.get('unique_stocks', 'unknown')}")
    
    if clear_existing:
        print("Clearing existing collection...")
        delete_collection("ksei_data")
    
    # Group by ticker
    print("Grouping records by ticker...")
    ticker_groups = group_by_ticker(records)
    
    all_chunks = []
    all_metadata = []
    
    # Create ticker summary chunks
    print("Creating ticker summaries...")
    for ticker, ticker_records in tqdm(ticker_groups.items(), desc="Processing tickers"):
        summary_text = format_ticker_summary(ticker, ticker_records, report_date)
        
        metadata_dict = {
            "source": "ksei_json",
            "ticker": ticker,
            "issuer": ticker_records[0]['issuer_name'],
            "date": report_date,
            "chunk_type": "ticker_summary",
            "num_holders": len(ticker_records)
        }
        
        all_chunks.append(summary_text)
        all_metadata.append(metadata_dict)
    
    # Create holder-focused chunks for significant holders
    print("Creating holder-focused chunks...")
    holder_chunks = format_holder_focused_chunks(records, report_date)
    for chunk in holder_chunks:
        all_chunks.append(chunk['text'])
        all_metadata.append(chunk['metadata'])
    
    # Store in ChromaDB
    print(f"Storing {len(all_chunks)} chunks in ChromaDB...")
    stored_count = embed_and_store(all_chunks, all_metadata, collection_name="ksei_data")
    
    return {
        "records_processed": len(records),
        "tickers_processed": len(ticker_groups),
        "chunks_created": len(all_chunks),
        "chunks_stored": stored_count,
        "report_date": report_date
    }


def ingest_all_json_files(json_dir: str = None, clear_existing: bool = False) -> Dict[str, Any]:
    """
    Ingest all KSEI JSON files in a directory.
    
    Args:
        json_dir: Directory containing KSEI JSON files (defaults to ../archive)
        clear_existing: Whether to clear existing collection first
    
    Returns:
        Combined stats
    """
    if json_dir is None:
        # Get the directory of this script and go up one level
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_dir = os.path.join(os.path.dirname(script_dir), "archive")
    
    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
    json_files.sort()
    
    if not json_files:
        print(f"No JSON files found in {json_dir}")
        return {"error": "No JSON files found"}
    
    print(f"Found {len(json_files)} JSON files: {json_files}")
    
    all_stats = []
    
    for i, json_file in enumerate(json_files):
        filepath = os.path.join(json_dir, json_file)
        
        # Only clear on first file
        should_clear = clear_existing and (i == 0)
        
        stats = ingest_ksei_json(filepath, clear_existing=should_clear)
        all_stats.append({"file": json_file, **stats})
    
    # Print summary
    print("\n" + "="*50)
    print("INGESTION SUMMARY")
    print("="*50)
    for s in all_stats:
        print(f"{s['file']}: {s['chunks_created']} chunks from {s['tickers_processed']} tickers")
    
    total_chunks = sum(s['chunks_created'] for s in all_stats)
    print(f"\nTotal chunks in database: {get_stats()['document_count']}")
    
    return {
        "files_processed": len(json_files),
        "total_chunks": total_chunks,
        "file_stats": all_stats
    }


if __name__ == "__main__":
    import sys
    
    # Check if chromadb and sentence-transformers are installed
    try:
        import chromadb
        import sentence_transformers
    except ImportError:
        print("Error: Required packages not installed.")
        print("Run: pip install chromadb sentence-transformers")
        sys.exit(1)
    
    # Ingest all JSON files
    result = ingest_all_json_files(clear_existing=True)
    print("\nDone!")
