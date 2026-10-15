import os
import math
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

DIM = 1536
BATCH = 100

def _normalize(vec):
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]

def embed_texts(texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    out = []
    for i in range(0, len(texts), BATCH):
        resp = client.models.embed_content(
            model = "gemini-embedding-001",
            contents = texts[i:i + BATCH],
            config=types.EmbedContentConfig(
                task_type = task,
                output_dimensionality = DIM,
            ),
        )
        out.extend(_normalize(e.values) for e in resp.embeddings)
    return out