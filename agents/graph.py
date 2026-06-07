# agents/graph.py

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from agents.extractor import extract_from_transcript
from agents.classifier import classify_action_items
from agents.summarizer import generate_summary, save_to_database

# --------------------------------------------------
# 1. State — shared data that flows through all nodes
#    every node reads from and writes to this state
#    TypedDict enforces what keys are allowed
# --------------------------------------------------
class MeetingState(TypedDict):
    title: str                          # meeting title
    transcript: str                     # raw transcript input
    extracted_data: Optional[dict]      # output of extractor node
    classified_data: Optional[dict]     # output of classifier node
    summary: Optional[str]              # output of summarizer node
    email_draft: Optional[str]          # follow-up email
    meeting_id: Optional[int]           # DB id after saving
    needs_human_review: bool            # flag for conditional edge
    review_items: Optional[list]        # items flagged for review


# --------------------------------------------------
# 2. Node: extractor_node
#    Reads transcript from state
#    Writes extracted_data to state
# --------------------------------------------------
def extractor_node(state: MeetingState) -> MeetingState:
    extracted = extract_from_transcript(state["transcript"])
    return {**state, "extracted_data": extracted}


# --------------------------------------------------
# 3. Node: classifier_node
#    Reads extracted_data from state
#    Writes classified_data + needs_human_review to state
# --------------------------------------------------
def classifier_node(state: MeetingState) -> MeetingState:
    classified = classify_action_items(state["extracted_data"])

    # check if any action items need human review
    review_items = [
        item for item in classified.get("action_items", [])
        if item.get("needs_review", False)
    ]

    return {
        **state,
        "classified_data": classified,
        "needs_human_review": len(review_items) > 0,
        "review_items": review_items
    }


# --------------------------------------------------
# 4. Node: summarizer_node
#    Reads transcript + classified_data from state
#    Generates summary + email, saves to DB via MCP
# --------------------------------------------------
def summarizer_node(state: MeetingState) -> MeetingState:
    result = generate_summary(
        transcript=state["transcript"],
        extracted_data=state["classified_data"]
    )

    meeting_id = save_to_database(
        title=state["title"],
        transcript=state["transcript"],
        extracted_data=state["classified_data"],
        summary=result["summary"]  
    )

    return {
        **state,
        "summary": result["summary"],
        "email_draft": result["email_draft"],
        "meeting_id": meeting_id
    }


# --------------------------------------------------
# 5. Node: human_review_node
#    Reached only when needs_human_review is True
#    Doesn't block — just flags and continues
#    In production this could pause and wait for input
# --------------------------------------------------
def human_review_node(state: MeetingState) -> MeetingState:
    print(f"\n⚠️  {len(state['review_items'])} action items need human review:")
    for item in state["review_items"]:
        print(f"  - {item['task']} (confidence: {item['confidence_score']})")
    # continues to summarizer after flagging
    return state


# --------------------------------------------------
# 6. Conditional edge function
#    Called after classifier_node
#    Returns which node to go to next
# --------------------------------------------------
def route_after_classifier(state: MeetingState) -> str:
    if state["needs_human_review"]:
        return "human_review"   # → human_review_node → summarizer_node
    return "summarizer"         # → summarizer_node directly


# --------------------------------------------------
# 7. Build and compile the graph
# --------------------------------------------------
def build_graph():
    graph = StateGraph(MeetingState)

    # add all nodes
    graph.add_node("extractor", extractor_node)
    graph.add_node("classifier", classifier_node)
    graph.add_node("summarizer", summarizer_node)
    graph.add_node("human_review", human_review_node)

    # add edges
    graph.add_edge(START, "extractor")
    graph.add_edge("extractor", "classifier")

    # conditional edge after classifier
    graph.add_conditional_edges(
        "classifier",
        route_after_classifier,
        {
            "human_review": "human_review",
            "summarizer": "summarizer"
        }
    )

    # human_review always goes to summarizer
    graph.add_edge("human_review", "summarizer")
    graph.add_edge("summarizer", END)

    return graph.compile()


# --------------------------------------------------
# 8. Single compiled graph instance
#    imported by FastAPI and used per request
# --------------------------------------------------
meeting_graph = build_graph()