import os 
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from sqlalchemy.orm import Session
from openai import OpenAI

from db.models import(
    SessionLocal, Meeting, ActionItem, MeetingEmbedding
)

# 1. load env variables
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. Initialize MCP Server
mcp = FastMCP("meeting-intelligence")

# 3. Helper - get DB session
def get_session() -> Session:
    return SessionLocal()

# 4. TOOL: save_meeting
@mcp.tool()
def save_action_items(meeting_id: int, action_items: list[dict]) -> dict:
    """Save extracted action items to the database"""
    db = get_session()
    try:
        for item in action_items:
            action = ActionItem(
                task = item["task"],
                owner = item.get("owner"),
                deadline = item.get("deadline"),
                priority = item["priority"],
                confidence_score = item["confidence_score"],
                needs_review = item["confidence_score"] < 0.7
            )
            db.add(action)
        db.commit()
        return {"saved":len(action_items),"meeting_id":meeting_id}
    finally:
        db.close()
        
# 6. TOOL: save embeddings
@mcp.tool()
def save_embeddings(meeting_id: int, transcript: str) -> dict:
    db = get_session()
    try:
        # split transcript into 500 char chunks with 50 char overlap
        chunk_size = 500
        overlap = 50
        chunks = []
        start = 0
        while start < len(transcript):
            end = start + chunk_size
            chunks.append(transcript[start:end])
            start = end
            
        # embed each document using OpenAI
        for chunk in chunks:
            response = openai_client.embeddings.create(
                input = chunk,
                model = "text-embedding-ada-002"
            )
            embedding_vector = response.data[0].embedding
            
            record = MeetingEmbedding(
                meeting_id = meeting_id,
                chunk_text = chunk,
                embedding = embedding_vector
            )
            
        db.commit()
        return {"chunks_saved": len(chunks), "meeting_id": meeting_id}
    finally:
        db.close()
        
# 7. TOOL: search_past_meetings
@mcp.tool()
def search_past_meetings(query: str) -> list[dict]:
    """Search past meetings semantically using pgvector"""
    db = get_session()
    try:
        # embed the search query
        response = openai_client.embeddings.create(
            input=query,
            model="text-embedding-ada-002"
        )
        query_embedding = response.data[0].embedding

        # pgvector cosine distance search — <=> operator
        # orders by similarity, returns top 3 chunks
        results = db.query(MeetingEmbedding).order_by(
            MeetingEmbedding.embedding.cosine_distance(query_embedding)
        ).limit(3).all()

        return [
            {
                "meeting_id": r.meeting_id,
                "chunk_text": r.chunk_text
            }
            for r in results
        ]
    finally:
        db.close()
        

# 8. TOOL: get_meeting_action_items
@mcp.tool()
def get_meeting_action_items(meeting_id: int) -> list[dict]:
    """Get all action items for a specific meeting"""
    db = get_session()
    try:
        items = db.query(ActionItem).filter(
            ActionItem.meeting_id == meeting_id
        ).all()

        return [
            {
                "task": i.task,
                "owner": i.owner,
                "deadline": i.deadline,
                "priority": i.priority,
                "confidence_score": i.confidence_score,
                "needs_review": i.needs_review
            }
            for i in items
        ]
    finally:
        db.close()


# 9. Run MCP server
if __name__ == "__main__":
    mcp.run(transport="stdio")