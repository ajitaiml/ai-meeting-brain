# AI Meeting Brain

## Introduction

Every organization loses productivity to poorly documented meetings. Action items get forgotten, decisions go unrecorded, and follow-ups never happen. AI Meeting Brain solves this by turning any raw meeting transcript into a fully structured intelligence report in seconds.

This project is built for teams that want to stop manually writing meeting notes and start focusing on execution. Paste a transcript, and the system automatically identifies who is responsible for what, by when, and how urgent it is. It flags risks before they become blockers, summarizes decisions made, and drafts a professional follow-up email ready to send.

Beyond single meetings, the system builds a searchable memory of every meeting your team has ever had. Ask a natural language question like "what did we decide about the payment gateway?" and the system returns the most relevant context from past meetings using semantic vector search.

On the technical side, this project is built around two modern AI infrastructure patterns that most production AI systems are moving toward. The first is multi-agent orchestration using LangGraph, where three specialized agents (Extractor, Classifier, Summarizer) handle different responsibilities in a directed pipeline with conditional routing. The second is the Model Context Protocol (MCP), which decouples the AI agents from the underlying infrastructure by exposing all database operations as callable tools. This means agents never touch the database directly, the system is fully modular, and the MCP server can be connected to Claude Desktop or any other MCP-compatible client with zero changes to agent code.

The entire system runs in Docker with a single command, uses pgVector for production-grade semantic search, and is served through a FastAPI backend with a clean frontend interface.

---

## Live Demo

[https://ai-meeting-brain.onrender.com](https://ai-meeting-brain.onrender.com)

> Note: Hosted on Render free tier — first load may take 30-50 seconds if the service has been inactive.

---

## What It Does

Paste any meeting transcript and the system automatically extracts:

- Action items with owner, deadline, priority, and confidence score
- Key decisions made during the meeting
- Risks and blockers identified
- Auto-generated professional follow-up email draft
- Semantic search across all past meetings using natural language

---

## System Architecture

```
Transcript Input
      |
[Extractor Agent]     extracts action items, decisions, risks, people
      |
[Classifier Agent]    assigns priority, flags low-confidence items
      |                         |
 needs review               confident
      |                         |
[Human Review]       [Summarizer Agent]    generates summary + email
                               |
                         [MCP Server]      saves to PostgreSQL + pgVector
```

---

## Tech Stack

| Layer                | Technology                      |
|----------------------|---------------------------------|
| Agent Orchestration  | LangGraph                       |
| LLM                  | OpenAI GPT-3.5-turbo            |
| MCP Server           | FastMCP (Python)                |
| Backend API          | FastAPI                         |
| Database             | PostgreSQL + pgVector           |
| Embeddings           | OpenAI text-embedding-ada-002   |
| Containerization     | Docker + Docker Compose         |
| Frontend             | HTML + CSS + JavaScript         |
| Package Manager      | UV                              |

---

## Key Features

**Multi-Agent LangGraph Pipeline**
Three specialized agents (Extractor, Classifier, Summarizer) connected via LangGraph with conditional routing. Low confidence items are automatically flagged for human review before the pipeline continues.

**MCP Protocol Integration**
All database operations are exposed as MCP tools. Agents never interact with the database directly — they call MCP tools, making the system fully modular. Swapping PostgreSQL for another database requires zero changes to agent code.

**Confidence Scoring**
Every extracted action item includes a confidence score from 0.0 to 1.0. Items scoring below 0.7 are flagged for human review and highlighted in the UI.

**Semantic Search**
Meeting transcripts are chunked, embedded via OpenAI, and stored in pgVector. Search across all past meetings using natural language queries with cosine similarity ranking.

---

## Project Structure

```
ai-meeting-brain/
├── agents/
│   ├── extractor.py       extracts action items from transcript
│   ├── classifier.py      assigns priority and confidence flags
│   ├── summarizer.py      generates summary and email draft
│   └── graph.py           LangGraph pipeline orchestration
├── mcp_server/
│   └── server.py          MCP tools: save, search, embed
├── api/
│   └── main.py            FastAPI endpoints
├── db/
│   └── models.py          SQLAlchemy models + pgVector
├── ui/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docker-compose.yml
└── Dockerfile
```

---

## API Endpoints

| Method | Endpoint           | Description                          |
|--------|--------------------|--------------------------------------|
| POST   | /analyze           | Run full pipeline on transcript      |
| GET    | /meetings          | List all past meetings               |
| GET    | /meetings/{id}     | Get single meeting with action items |
| POST   | /search            | Semantic search across meetings      |
| GET    | /health            | Health check                         |

---

## Running Locally

**Prerequisites**
- Docker Desktop
- OpenAI API key
- UV package manager

**Setup**

```bash
git clone https://github.com/ajitaiml/ai-meeting-brain.git
cd ai-meeting-brain

cp .env.example .env
# add your OPENAI_API_KEY to .env

docker-compose up --build -d
```

Open browser at http://localhost:8000

---

## Why MCP

Most AI projects hardcode their integrations. This project uses the Model Context Protocol to expose all database operations as tools. This decouples agents from infrastructure — the same MCP server can be connected to Claude Desktop or any MCP-compatible client without modifying agent code.

---

## Author

Ajit — AI Engineer
LinkedIn: https://linkedin.com/in/ajitaiml
GitHub: https://github.com/ajitaiml
