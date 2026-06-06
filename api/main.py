# api/main.py

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.models import init_db, get_db, Meeting, ActionItem
from agents.graph import meeting_graph
from mcp_server.server import search_past_meetings

# --------------------------------------------------
# 1. Load env and initialize FastAPI app
# --------------------------------------------------
load_dotenv()

app = FastAPI(
    title="AI Meeting Brain",
    description="Analyze meeting transcripts with AI",
    version="1.0.0"
)

# --------------------------------------------------
# 2. CORS middleware
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# 3. Create DB tables on startup
# --------------------------------------------------
@app.on_event("startup")
def startup():
    init_db()


# --------------------------------------------------
# 4. Pydantic request models
# --------------------------------------------------
class AnalyzeRequest(BaseModel):
    title: str
    transcript: str

class SearchRequest(BaseModel):
    query: str


# --------------------------------------------------
# 5. POST /analyze
# --------------------------------------------------
@app.post("/analyze")
def analyze_meeting(request: AnalyzeRequest):
    try:
        initial_state = {
            "title": request.title,
            "transcript": request.transcript,
            "extracted_data": None,
            "classified_data": None,
            "summary": None,
            "email_draft": None,
            "meeting_id": None,
            "needs_human_review": False,
            "review_items": []
        }

        result = meeting_graph.invoke(initial_state)

        return {
            "meeting_id": result["meeting_id"],
            "summary": result["summary"],
            "email_draft": result["email_draft"],
            "action_items": result["classified_data"].get("action_items", []),
            "decisions": result["classified_data"].get("decisions", []),
            "risks": result["classified_data"].get("risks", []),
            "needs_human_review": result["needs_human_review"],
            "review_items": result["review_items"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# 6. GET /meetings
# --------------------------------------------------
@app.get("/meetings")
def get_meetings(db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "created_at": m.created_at.isoformat()
        }
        for m in meetings
    ]


# --------------------------------------------------
# 7. GET /meetings/{id}
# --------------------------------------------------
@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    action_items = db.query(ActionItem).filter(
        ActionItem.meeting_id == meeting_id
    ).all()

    return {
        "id": meeting.id,
        "title": meeting.title,
        "transcript": meeting.raw_transcript,
        "created_at": meeting.created_at.isoformat(),
        "action_items": [
            {
                "task": i.task,
                "owner": i.owner,
                "deadline": i.deadline,
                "priority": i.priority,
                "confidence_score": i.confidence_score,
                "needs_review": i.needs_review
            }
            for i in action_items
        ]
    }


# --------------------------------------------------
# 8. POST /search
# --------------------------------------------------
@app.post("/search")
def search_meetings(request: SearchRequest):
    try:
        results = search_past_meetings(query=request.query)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# 9. GET /health
# --------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------
# 10. Serve frontend — MUST be last
#     mounts ui/ folder at root
#     html=True serves index.html for unknown routes
# --------------------------------------------------
app.mount("/", StaticFiles(directory="ui", html=True), name="ui")