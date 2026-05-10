# ⚔️ ReelRival

> AI-powered YouTube video comparison for content creators.  
> Paste two video URLs. Get deep insights on hooks, engagement, structure, and improvements — powered by RAG + DeepSeek-R1.

<!-- ![ReelRival Demo](docs/demo_screenshot.png) -->

---

## What It Does

ReelRival takes two YouTube video URLs and lets creators have an intelligent conversation about them:

- **Engagement analytics** — views, likes, comments, engagement rate computed automatically
- **Transcript indexing** — full transcripts chunked and stored in a local FAISS vector index
- **RAG chat** — questions answered using retrieved transcript evidence, not hallucination
- **Streaming responses** — tokens stream live as DeepSeek-R1 reasons through the evidence
- **Source citations** — every answer cites the exact transcript segment it used
- **Conversation memory** — follow-up questions retain context from earlier in the session

---

## Architecture

```
┌─────────────────────────────────────────┐
│           LOCAL MACHINE                 │
│  FastAPI backend  +  React frontend     │
│  - URL ingestion (yt-dlp + YT API v3)   │
│  - FAISS vector store (CPU)             │
│  - Session memory                       │
│  - Prompt assembly + SSE proxy          │
└──────────────┬──────────────────────────┘
               │ httpx calls via ngrok
               ▼
┌─────────────────────────────────────────┐
│         KAGGLE (T4 × 2 GPU)             │
│  /embed  → BGE-Large-en-v1.5 (cuda:0)   │
│  /chat/stream → DeepSeek-R1:8b (cuda:1) │
│  Exposed via ngrok free tier            │
└─────────────────────────────────────────┘
```

**Why this split?**  
Heavy inference (embedding + LLM) runs free on Kaggle GPUs. The local backend stays lightweight — pure orchestration, no GPU needed.

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Backend | FastAPI + uvicorn | Async, SSE streaming, clean API |
| Embeddings | BAAI/bge-large-en-v1.5 | Top MTEB retrieval benchmark, 1024-dim |
| LLM | DeepSeek-R1:8b via Ollama | Strong reasoning model, fits in 1× T4 |
| Vector DB | FAISS (IndexFlatIP) | In-process, GPU-ready, cosine similarity |
| Transcript | youtube-transcript-api | Free, timestamped, no API key |
| Metadata | YouTube Data API v3 + yt-dlp fallback | Reliable with zero-quota fallback |
| Frontend | React + Vite | Fast dev, streaming SSE support |
| Tunneling | ngrok | Exposes Kaggle endpoints to local backend |

**No LangChain. No LangGraph.** Raw pipeline — easier to debug, shows deeper understanding of RAG.

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Kaggle account with GPU quota
- A free ngrok account
- YouTube Data API v3 key ([get one here](https://console.cloud.google.com))

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/reelrival.git
cd reelrival

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:
```env
YOUTUBE_API_KEY=your_key_here
EMBED_SERVICE_URL=https://xxxx.ngrok-free.app   # from Kaggle step
LLM_SERVICE_URL=https://xxxx.ngrok-free.app     # same URL
KAGGLE_SERVICE_TOKEN=your_secret_token
```

### 3. Start Kaggle GPU services

- Open `notebooks/reelrival_gpu_services.ipynb` in Kaggle
- Enable **T4 × 2 GPU** and **Internet**
- Run all cells in order
- Copy the ngrok URL printed by Cell 13 into your `.env`

### 4. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

---

## How It Works

### Ingestion Pipeline

```
URL → extract video ID → fetch metadata (YT API v3 → yt-dlp fallback)
    → fetch transcript (youtube-transcript-api)
    → compute engagement rate = (likes + comments) / views × 100
    → chunk transcript (60s windows, 15s overlap, ~200 tokens/chunk)
    → embed chunks (BGE-Large on Kaggle GPU)
    → store vectors in FAISS + metadata in JSON
```

### Chat Pipeline

```
User query → embed query (Kaggle)
           → FAISS search (top-5 chunks, cosine similarity)
           → build prompt (system + evidence + memory + question)
           → stream from DeepSeek-R1:8b (Kaggle)
           → proxy SSE tokens to frontend
           → save turn to session memory
```

---

## Chunking Strategy

Transcripts are chunked by **60-second time windows** with **15-second overlap**, preserving timestamps for citations. Each video also gets one **metadata summary chunk** containing title, channel, views, likes, comments, and engagement rate — this is always retrieved first for high-level comparison questions.

---

## Scalability Notes

| Concern | Current (MVP) | At Scale (1k creators/day) |
|---|---|---|
| Embeddings | Kaggle free T4 | Persistent GPU VM (Lambda/RunPod) |
| LLM | Kaggle free T4 | Same GPU VM, multiple workers |
| Vector DB | FAISS local | Qdrant Cloud for dynamic updates |
| Transcript cache | Re-fetches each time | PostgreSQL cache by video ID |
| Session memory | In-memory dict | Redis with TTL |
| Ingestion | Synchronous | Background job queue (Celery/ARQ) |

**Cost at 1k creators/day (scaled):**  
~$2–5/day using GPU VM + Qdrant serverless + cached transcript fetches.

---

## Project Structure

```
reelrival/
├── backend/
│   ├── main.py              # FastAPI routes
│   ├── config.py            # Settings from .env
│   ├── models.py            # Pydantic schemas
│   ├── ingestion/           # YouTube fetch + chunker
│   ├── retrieval/           # FAISS + metadata store + retriever
│   ├── services/            # Kaggle HTTP clients
│   └── chat/                # Prompt builder + memory + pipeline
├── frontend/                # React + Vite chat UI
├── notebooks/               # Kaggle GPU services notebook
├── tests/                   # E2E test suite
├── docs/                    # Architecture + demo plan
├── data/                    # FAISS index + metadata (gitignored)
└── .env.example
```

---

## Demo Questions to Try

- *"Which video has a stronger hook and why?"*
- *"Compare the engagement rates — what explains the difference?"*
- *"What should the lower-performing video change to improve retention?"*
- *"Which video has a better call to action?"*
- *"Summarize the structural differences between both videos."*

---

## Known Limitations

- YouTube only (TikTok/Instagram support is a one-file extension)
- Kaggle session expires after ~40 minutes of inactivity — requires manual activity
- Videos without auto-generated captions return no transcript
- ngrok free tier URL changes every Kaggle session

---

## License

MIT