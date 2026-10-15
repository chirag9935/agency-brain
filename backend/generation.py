import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3.8-flash"

class Proposal(BaseModel):
    scope: str
    deliverables: list[str]
    timeline: str
    price_range: str
    assumptions: list[str]
    source_chunk_ids: list[int]

def generate_proposal(brief: str, chunks: list[dict]) -> Proposal:
    context = "\n\n".join(f"[{c['id']}]\n{c['content']}" for c in chunks)
    prompt = f"""You write agency proposals using ONLY the context below.
    If pricing or timeline is not in the context, write "Not found in sources".
    List the ids of chunks you used in source_chunk_ids.

    CONTEXT:
    {context}

    CLIENT BRIEF:
    {brief}"""
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Proposal,
        ),
    )
    return resp.parsed