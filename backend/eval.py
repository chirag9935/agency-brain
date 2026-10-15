import json, os, sys
from dotenv import load_dotenv
from supabase import create_client
from embeddings import embed_texts

load_dotenv()
K = int(sys.argv[1]) if len(sys.argv) > 1 else 5

def login():
    c = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    c.auth.sign_in_with_password({"email": "alice@test.com", "password": "alice123"})
    return c

client = login()
items = json.load(open("eval_set.json"))
hits_at_k, reciprocal_ranks, misses = 0, [], []

for it in items:
    qvec = embed_texts([it["question"]], task="RETRIEVAL_QUERY")[0]
    res = client.rpc("match_chunks", {"query_embedding": qvec, "match_count": K}).execute().data
    rank = next((i + 1 for i, r in enumerate(res)
                 if it["expected_keyword"].lower() in r["content"].lower()), None)
    if rank:
        hits_at_k += 1
        reciprocal_ranks.append(1 / rank)
    else:
        reciprocal_ranks.append(0)
        misses.append(it["question"])

n = len(items)
print(f"recall@{K}: {hits_at_k / n:.0%}  ({hits_at_k}/{n})")
print(f"MRR: {sum(reciprocal_ranks) / n:.2f}")
print("Missed:", misses)