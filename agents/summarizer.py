# agents/summarizer.py

import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from mcp_server.server import save_meeting, save_action_items, save_embeddings

load_dotenv()

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.3,
    api_key=os.getenv("OPENAI_API_KEY")
)

SUMMARY_PROMPT = """
You are an expert meeting summarizer.

Given the meeting transcript and extracted data, generate:

1. summary: a concise 3-line summary of what the meeting was about

2. email_draft: a professional follow-up email in this exact structure:

Subject: Meeting Follow-Up — [Meeting Topic]

Dear Team,

[2 sentence meeting summary]

Action Items:
- [Task] — Owner: [Name] | Deadline: [Date] | Priority: [High/Medium/Low]

Decisions Made:
- [Decision 1]
- [Decision 2]

Risks to Monitor:
- [Risk 1]

Please ensure all action items are completed by their respective deadlines.

Best regards,
[Your Name]

Return ONLY valid JSON. No explanation. No markdown. Format:
{
  "summary": "3 line summary here",
  "email_draft": "Full structured email text here"
}
"""


def strip_json(content: str) -> str:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return content.strip()


def generate_summary(transcript: str, extracted_data: dict) -> dict:
    messages = [
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=f"""
Extracted Structured Data:
{json.dumps(extracted_data, indent=2)}
""")
    ]

    response = llm.invoke(messages)

    try:
        result = json.loads(strip_json(response.content))
    except json.JSONDecodeError:
        result = {
            "summary": "Meeting summary unavailable.",
            "email_draft": "Follow-up email unavailable."
        }

    return result


def save_to_database(title: str, transcript: str, extracted_data: dict, summary: str) -> int:
    # --------------------------------------------------
    # pass summary, decisions and risks to save_meeting
    # so they are stored in DB and retrievable later
    # --------------------------------------------------
    meeting_result = save_meeting(
        title=title,
        transcript=transcript,
        summary=summary,
        decisions=extracted_data.get("decisions", []),
        risks=extracted_data.get("risks", [])
    )
    meeting_id = meeting_result["meeting_id"]

    save_action_items(
        meeting_id=meeting_id,
        action_items=extracted_data.get("action_items", [])
    )

    save_embeddings(
        meeting_id=meeting_id,
        transcript=transcript
    )

    return meeting_id