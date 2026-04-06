from embedder import get_or_create_collection

coll = get_or_create_collection('ksei_data')

# Check BBRI data
results = coll.get(where={'ticker': 'BBRI'}, limit=5)
print(f'Found {len(results["ids"])} BBRI chunks')
for i, doc in enumerate(results['documents']):
    print(f'\n--- BBRI chunk {i+1} ---')
    print(doc[:400])

# List all tickers with metadata summary
print("\n\n=== Sample tickers in DB ===")
all_results = coll.get(limit=100)
seen_tickers = set()
for meta in all_results['metadatas']:
    ticker = meta.get('ticker', 'unknown')
    if ticker not in seen_tickers:
        seen_tickers.add(ticker)
        print(f"  {ticker}: {meta.get('chunk_type', 'unknown')}")
