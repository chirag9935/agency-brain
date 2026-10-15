from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from extract import extract_text
from chunking import chunk_text
from embeddings import embed_texts
import os
from dotenv import load_dotenv
from supabase import create_client
from supabase_auth.errors import AuthError
from postgrest.exceptions import APIError
from pydantic import BaseModel
from generation import generate_proposal
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
url = os.getenv("SUPABASE_URL")
anon_key = os.getenv("SUPABASE_ANON_KEY")

app = FastAPI(title="AgencyBrain")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)

class Brief(BaseModel):
    client_name: str
    text: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/brief")
def create_brief(brief: Brief):
    return {"received": brief.client_name, "chars": len(brief.text)}


def get_client_for_user(authorization: str = Header(...)):

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )

    token = authorization.split(" ", 1)[1].strip()

    # Create client
    client = create_client(url, anon_key)

    # Verify token (get_user raises AuthError on a malformed/expired token)
    try:
        user_response = client.auth.get_user(token)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    if not user_response or not user_response.user:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    # Pass user's JWT to PostgREST.
    # Must be .postgrest.auth() -- PostgrestClient.from_() sends its own
    # self.headers per request, which override session.headers, so mutating
    # session.headers leaves requests on the anon role and RLS rejects them.
    client.postgrest.auth(token)

    return client, user_response.user.id

@app.post("/documents")
async def upload_document(file: UploadFile = File(...), authorization: str = Header(...)):
    client, user_id = get_client_for_user(authorization)
    content = await file.read()

    try:
        text = extract_text(file.filename, content)
    except ValueError as e:
        raise HTTPException(400, str(e))

    doc_result = client.table("documents").insert({
        "user_id": user_id,
        "filename": file.filename,
        "doc_type": file.filename.split(".")[-1]
    }).execute()
    doc_id = doc_result.data[0]["id"]

    pieces = chunk_text(text)
    vectors = embed_texts(pieces)

    rows = [
        {
            "document_id": doc_id,
            "user_id": user_id,
            "content": piece,
            "embedding": vector
        }
        for piece, vector in zip(pieces, vectors)
    ]
    client.table("chunks").insert(rows).execute()

    return {"document_id": doc_id, "chunks_created": len(rows)}


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/search")
def search(req: SearchRequest, authorization: str = Header(...)):
    client, user_id = get_client_for_user(authorization)
    qvec = embed_texts([req.query], task="RETRIEVAL_QUERY")[0]
    res = client.rpc("match_chunks", {
        "query_embedding": qvec,
        "match_count": req.top_k
    }).execute()
    return res.data

MIN_SIMILARITY = 0.55

class ProposalRequest(BaseModel):
    brief: str

@app.post("/proposal")
def proposal(req: ProposalRequest, authorization: str = Header(...)):
    client, user_id = get_client_for_user(authorization)
    qvec = embed_texts([req.brief], task = "RETRIEVAL_QUERY")[0]
    hits = client.rpc("match_chunks", {"query_embedding": qvec, "match_count": 5}).execute().data
    hits = [h for h in hits if h["similarity"] >= MIN_SIMILARITY]
    if not hits:
        raise HTTPException(404, "No relevant source material found")
    return generate_proposal(req.brief, hits)