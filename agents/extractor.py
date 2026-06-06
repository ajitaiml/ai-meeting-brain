import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.getenv('OPENAI_API_KEY'),
)

EXTRACTION_PROMPT = """
You are an expert meeting analyst. Extract the following from the meeting transcript:

1. action_items: list of tasks mentioned, each with:
   - task: what needs to be done (string)
   - owner: who is responsible (string or null if unclear)
   - deadline: when it's due (string or null if not mentioned)
   - confidence_score: how confident you are this is a real action item (float 0.0 to 1.0)

2. decisions: list of decisions made in the meeting (list of strings)

3. risks: list of risks or blockers mentioned (list of strings)

4. people: list of all people mentioned by name (list of strings)

Return ONLY valid JSON. No explanation. No markdown. Example format:
{
  "action_items": [
    {
      "task": "Send project proposal to client",
      "owner": "John",
      "deadline": "Friday",
      "confidence_score": 0.95
    }
  ],
  "decisions": ["Approved Q3 budget"],
  "risks": ["Vendor delivery delay"],
  "people": ["John", "Sarah"]
}
"""

def strip_json(content: str) -> str:
    # --------------------------------------------------
    # strips markdown code fences if LLM adds them
    # e.g. ```json ... ``` → just the JSON string
    # --------------------------------------------------
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return content.strip()

def extract_from_transcript(transcript: str) -> dict:
    messages = [
        SystemMessage(content=EXTRACTION_PROMPT),
        HumanMessage(content=f"Meeting transcript:\n\n{transcript}")
    ]

    response = llm.invoke(messages)

    try:
        extracted = json.loads(strip_json(response.content))
    except json.JSONDecodeError:
        extracted = {
            "action_items": [],
            "decisions": [],
            "risks": [],
            "people": []
        }

    return extracted