# 🧠 AI Meeting Brain

An intelligent meeting analysis system that transforms raw meeting transcripts into structured action items, decisions, risks, and follow-up emails using LangGraph multi-agent orchestration and MCP protocol.

---

## 🎯 What It Does

Paste any meeting transcript → AI agents extract and organize:
- ✅ Action items with owner, deadline, priority, and confidence score
- 🎯 Key decisions made
- ⚠️ Risks and blockers identified
- 📧 Auto-generated follow-up email draft
- 🔍 Semantic search across all past meetings

---

## 🏗️ System Architecture
Transcript Input
↓
[Extractor Agent] → extracts action items, decisions, risks
↓
[Classifier Agent] → assigns priority, flags low-confidence items
↓        ↓
(if needs   (if confident)
review)         ↓
[Human Review] → [Summarizer Agent] → generates summary + email
↓
[MCP Server] → saves to PostgreSQL + pgVector

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph |
| LLM | OpenAI GPT-3.5-turbo |
| MCP Server | FastMCP (Python) |
| Backend API | FastAPI |
| Database | PostgreSQL + pgVector |
| Embeddings | OpenAI text-embedding-ada-002 |
| Observability | LangSmith |
| Containerization | Docker + Docker Compose |
| Frontend | HTML + CSS + JavaScript |

---

## 🔑 Key Features

**Multi-Agent LangGraph Pipeline**
Three specialized agents (Extractor → Classifier → Summarizer) with conditional routing — low confidence items are flagged for human review before proceeding.

**MCP Protocol Integration**
All database operations are exposed as MCP tools. Agents never touch the database directly — they call MCP tools, making the system fully modular and swappable.

**Confidence Scoring**
Every extracted action item includes a confidence score (0.0–1.0). Items below 0.7 are flagged with a review badge in the UI.

**Semantic Search**
Transcripts are chunked, embedded via OpenAI, and stored in pgVector. Search across months of meetings using natural language queries.

---

## 🚀 Running Locally

### Prerequisites
- Docker Desktop
- OpenAI API key
- UV package manager (`pip install uv`)

### Setup

```bash
git clone https://github.com/ajitaiml/ai-meeting-brain.git
cd ai-meeting-brain

# create .env file
cp .env.example .env
# add your OPENAI_API_KEY to .env

# start all services
docker-compose up --build -d

# open in browser
http://localhost:8000
```

---

## 📁 Project Structure
ai-meeting-brain/
├── agents/
│   ├── extractor.py      # extracts action items from transcript
│   ├── classifier.py     # assigns priority and confidence flags
│   ├── summarizer.py     # generates summary and email draft
│   └── graph.py          # LangGraph pipeline orchestration
├── mcp_server/
│   └── server.py         # MCP tools: save, search, embed
├── api/
│   └── main.py           # FastAPI endpoints
├── db/
│   └── models.py         # SQLAlchemy models + pgVector
├── ui/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docker-compose.yml
└── Dockerfile
---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/analyze` | Run full pipeline on transcript |
| GET | `/meetings` | List all past meetings |
| GET | `/meetings/{id}` | Get meeting with action items |
| POST | `/search` | Semantic search across meetings |
| GET | `/health` | Health check |

---

## 💡 Why MCP?

Most AI projects hardcode integrations. This project uses the **Model Context Protocol (MCP)** to expose database operations as tools. This means:
- Agents are fully decoupled from the database
- Swapping PostgreSQL for another DB requires zero agent code changes
- The same MCP server can be connected to Claude Desktop or any MCP-compatible client

---

## 📸 Screenshots

> Add screenshots here after deployment

---

## 👤 Author

**Ajit** — AI Engineer  
[LinkedIn](https://linkedin.com/in/ajitaiml) · [GitHub](https://github.com/ajitaiml)
