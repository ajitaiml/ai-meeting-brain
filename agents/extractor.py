# agents/extractor.py

import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

EXTRACTION_PROMPT = """
You are an expert meeting analyst. Extract ALL of the following from the meeting transcript. Be thorough and do not miss any items.

1. action_items: EVERY task, deliverable, or commitment mentioned, each with:
   - task: what needs to be done (string)
   - owner: who is responsible (string or null if unclear)
   - deadline: when it's due (string or null if not mentioned)
   - confidence_score: how confident you are this is a real action item (float 0.0 to 1.0)

2. decisions: EVERY decision made in the meeting (list of strings)

3. risks: EVERY risk, blocker, concern or dependency mentioned (list of strings)

4. people: list of all people mentioned by name (list of strings)

Be exhaustive. If someone says "I will do X by Y" that is an action item.
If someone says "we decided" or "we agreed" that is a decision.
If someone says "risk", "concern", "dependency", "blocker", "might not", "could be an issue" that is a risk.

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
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return content.strip()


def _extract_chunk(transcript: str) -> dict:
    """Extract from a single chunk of transcript"""
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


def extract_from_transcript(transcript: str) -> dict:
    # --------------------------------------------------
    # for long transcripts split into overlapping chunks
    # each chunk is 4000 chars with 500 char overlap
    # overlap ensures action items at boundaries
    # are not missed
    # --------------------------------------------------
    chunk_size = 4000
    overlap = 500

    if len(transcript) <= chunk_size:
        return _extract_chunk(transcript)

    # split into chunks
    chunks = []
    start = 0
    while start < len(transcript):
        end = start + chunk_size
        chunks.append(transcript[start:end])
        start = end - overlap

    # extract from each chunk
    all_action_items = []
    all_decisions = []
    all_risks = []
    all_people = []

    for chunk in chunks:
        result = _extract_chunk(chunk)
        all_action_items.extend(result.get("action_items", []))
        all_decisions.extend(result.get("decisions", []))
        all_risks.extend(result.get("risks", []))
        all_people.extend(result.get("people", []))

    # deduplicate people
    all_people = list(set(all_people))

    # deduplicate decisions and risks by text similarity
    seen_decisions = set()
    unique_decisions = []
    for d in all_decisions:
        if d.lower() not in seen_decisions:
            seen_decisions.add(d.lower())
            unique_decisions.append(d)

    seen_risks = set()
    unique_risks = []
    for r in all_risks:
        if r.lower() not in seen_risks:
            seen_risks.add(r.lower())
            unique_risks.append(r)

    # deduplicate action items by task text
    seen_tasks = set()
    unique_action_items = []
    for item in all_action_items:
        task_key = item["task"].lower()[:50]
        if task_key not in seen_tasks:
            seen_tasks.add(task_key)
            unique_action_items.append(item)

    return {
        "action_items": unique_action_items,
        "decisions": unique_decisions,
        "risks": unique_risks,
        "people": all_people
    }