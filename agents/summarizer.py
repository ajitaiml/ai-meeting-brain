# agents/summarizer.py

import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from mcp_server.server import save_meeting, save_action_items, save_embeddings

# --------------------------------------------------
# 1. Load env and initialize LLM
#    temperature=0.3 → slight creativity for
#    natural sounding summary and email
# --------------------------------------------------
load_dotenv()

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.3,
    api_key=os.getenv("OPENAI_API_KEY")
)


# --------------------------------------------------
# 2. System prompt for summary + email generation
# --------------------------------------------------
SUMMARY_PROMPT = """
You are an expert meeting summarizer.

Given the meeting transcript and extracted data, generate:

1. summary: a concise 3-line summary of what the meeting was about
2. email_draft: a professional follow-up email that includes:
   - Brief summary of meeting
   - List of action items with owners and deadlines
   - Next steps

Return ONLY valid JSON. No explanation. No markdown. Format:
{
  "summary": "3 line summary here",
  "email_draft": "Full email text here"
}
"""


# --------------------------------------------------
# 3. generate_summary()
#    Input  → transcript + classified extracted data
#    Output → summary string + email draft string
# --------------------------------------------------
def generate_summary(transcript: str, extracted_data: dict) -> dict:
    messages = [
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=f"""
Transcript:
{transcript}

Extracted Data:
{json.dumps(extracted_data, indent=2)}
""")
    ]

    response = llm.invoke(messages)

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {
            "summary": "Meeting summary unavailable.",
            "email_draft": "Follow-up email unavailable."
        }

    return result


# --------------------------------------------------
# 4. save_to_database()
#    Calls MCP tools directly to persist everything
#    This is where MCP protocol is used —
#    summarizer doesn't touch DB directly,
#    it delegates to MCP tools
# --------------------------------------------------
def save_to_database(title: str, transcript: str, extracted_data: dict) -> int:
    # save meeting transcript → get meeting_id
    meeting_result = save_meeting(title=title, transcript=transcript)
    meeting_id = meeting_result["meeting_id"]

    # save all classified action items
    save_action_items(
        meeting_id=meeting_id,
        action_items=extracted_data.get("action_items", [])
    )

    # chunk transcript and save embeddings for semantic search
    save_embeddings(
        meeting_id=meeting_id,
        transcript=transcript
    )

    return meeting_id