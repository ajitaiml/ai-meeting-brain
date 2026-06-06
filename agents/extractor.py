import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage,SystemMessage

# 1. Load env and initialize OpenAI model
load_dotenv()

llm = ChatOpenAI(
    model = "gpt-40-mini",
    temperature=0,
    api_key=os.get_env('OPENAI_API_KEY'),
)


# 2. System prompt — tells LLM exactly what to extract
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

# 3. extract_from_transcript()
#    Main function called by LangGraph extractor node
#    Input  → raw transcript string
#    Output → parsed dict with action_items, decisions, risks, people
def extract_from_transcript(transcript: str) -> dict:
    messages = [
        SystemMessage(content=EXTRACTION_PROMPT),
        HumanMessage(content=f"Meeting transcript:\n\n{transcript}")
    ]
    
    response = llm.invoke(messages)
    
    try:
        extracted = json.loads(response.content)
    except json.JSONDecodeError:
        # if LLM returns invalid JSON, return safe empty structure
        extracted = {
            "action_items": [],
            "decisions": [],
            "risks": [],
            "people": []
        }

    return extracted