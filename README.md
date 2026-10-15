# AgencyBrain

AgencyBrain turns an agency's past work into a searchable knowledge base and uses it to draft new client proposals. Upload previous proposals and case studies (PDF/DOCX), then paste a new client brief and get a structured proposal (scope, deliverables, timeline, price range) grounded in your own material.

## Architecture

```
agencybrain/
├── backend/    FastAPI service: ingestion, embeddings, retrieval, generation
└── frontend/   Next.js 16 (React 19, Tailwind 4) web app
```

- **Auth & storage:** Supabase (Postgres + pgvector, Row Level Security so each user only sees their own documents)
- **Embeddings & generation:** Google Gemini
- **Pipeline:** upload -> text extraction -> chunking -> embeddings -> vector search (`match_chunks` RPC) -> proposal generation

## API

| Method | Path         | Description                                         |
| ------ | ------------ | --------------------------------------------------- |
| GET    | `/health`    | Health check                                        |
| POST   | `/documents` | Upload a PDF/DOCX; extracts, chunks and embeds it   |
| POST   | `/search`    | Semantic search over the user's chunks              |
| POST   | `/proposal`  | Generate a proposal from a brief using retrieved context |

All endpoints except `/health` require a Supabase JWT in the `Authorization: Bearer <token>` header.

## Getting started

### Prerequisites
- Python 3.10+
- Node.js 20+
- A Supabase project (with `documents` / `chunks` tables and a `match_chunks` function)
- A Gemini API key

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your values
uvicorn main:app --reload
```

Runs on http://localhost:8000.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local      # then fill in your values
npm run dev
```

Runs on http://localhost:3000.

## Environment variables

Real values live in `.env` / `.env.local`, which are git-ignored. Copy the `.env.example` files and fill them in. **Never commit secrets.**

| File                  | Variable                        | Purpose                          |
| --------------------- | ------------------------------- | -------------------------------- |
| `backend/.env`        | `SUPABASE_URL`                  | Supabase project URL             |
|                       | `SUPABASE_ANON_KEY`             | Supabase anon key                |
|                       | `SUPABASE_KEY`                  | Service key (`test_db.py` only)  |
|                       | `GEMINI_API_KEY`                | Gemini API key                   |
| `frontend/.env.local` | `NEXT_PUBLIC_SUPABASE_URL`      | Supabase project URL             |
|                       | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key                |
|                       | `NEXT_PUBLIC_API_URL`           | Backend URL                      |

## Evaluation

`backend/eval.py` runs retrieval against `eval_set.json` and reports hit rate at top-k:

```bash
python eval.py 5
```
