from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json
import os
from dotenv import load_dotenv

# 1. Load env and initialize LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)


# 2. System prompt — takes extracted data and
CLASSIFICATION_PROMPT = """
You are an expert project manager. You will receive a list of action items extracted from a meeting.

For each action item, assign a priority level:
- High: urgent, has a near deadline, or is blocking others
- Medium: important but not immediately urgent
- Low: nice to have, no clear deadline, or minor task

Return ONLY valid JSON. No explanation. No markdown. Format:
{
  "action_items": [
    {
      "task": "original task text",
      "owner": "person name or null",
      "deadline": "deadline or null",
      "confidence_score": 0.95,
      "priority": "High"
    }
  ]
}
"""



# 3. classify_action_items()
#    Input  → extracted dict from extractor.py
#    Output → same dict with priority added to each item
#             and needs_review flag set
def classify_action_items(extracted_data: dict) -> dict:
    action_items = extracted_data.get("action_items", [])

    # if no action items found, return as is
    if not action_items:
        return extracted_data

    messages = [
        SystemMessage(content=CLASSIFICATION_PROMPT),
        HumanMessage(content=f"Action items to classify:\n\n{json.dumps(action_items, indent=2)}")
    ]

    response = llm.invoke(messages)

    try:
        classified = json.loads(response.content)
        action_items = classified.get("action_items", action_items)
    except json.JSONDecodeError:
        # if LLM fails, keep original items but assign Medium priority
        for item in action_items:
            item["priority"] = item.get("priority", "Medium")

    # flag items that need human review
    # confidence < 0.7 means LLM wasn't sure this
    # was a real action item → human should verify
    for item in action_items:
        item["needs_review"] = item.get("confidence_score", 1.0) < 0.7

    # merge back into full extracted data
    extracted_data["action_items"] = action_items
    return extracted_data