from embedder import search, get_stats

print('Stats:', get_stats())
print()

# Test search for BBRI
results = search('Siapa pemegang saham terbesar BBRI?', n_results=3)
print('Search results for BBRI:')
for r in results:
    print(f"  - {r['metadata']['ticker']} ({r['metadata'].get('chunk_type', 'unknown')})")
    print(f"    Distance: {r['distance']:.4f}")
    print(f"    Text preview: {r['text'][:200]}...")
    print()

# Test search for foreign ownership
print("\n" + "="*50)
results = search('kepemilikan asing tertinggi foreign ownership', n_results=3)
print('Search results for foreign ownership:')
for r in results:
    print(f"  - {r['metadata']['ticker']} ({r['metadata'].get('chunk_type', 'unknown')})")
    print(f"    Distance: {r['distance']:.4f}")
    print(f"    Text preview: {r['text'][:200]}...")
    print()
