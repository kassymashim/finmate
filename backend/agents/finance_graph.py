"""
FinMate LangGraph Workflow - Multi-step financial assistant agent.

Architecture:
1. Classify user intent (budget analysis, savings advice, spending insights, general Q&A)
2. Route to appropriate specialist node
3. Retrieve relevant context via RAG
4. Generate personalized response
5. Optional: human-in-the-loop for financial actions (budget changes, goal setting)

Conditional logic: branching based on intent, loop for clarification,
human confirmation for actionable recommendations.
"""

from typing import TypedDict, Literal, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from backend.utils.config import OPENAI_API_KEY, DEFAULT_MODEL, FALLBACK_MODEL, TEMPERATURE, MAX_TOKENS
from backend.rag.knowledge_rag import retrieve_context, format_context
import json
import pandas as pd


class FinanceState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str
    context: str
    transaction_data: str
    user_profile: str
    needs_confirmation: bool
    confirmed: bool
    response: str
    metadata: dict


def get_llm(model: str = None, temperature: float = None):
    """Get LLM instance with fallback support."""
    try:
        return ChatOpenAI(
            model=model or DEFAULT_MODEL,
            openai_api_key=OPENAI_API_KEY,
            temperature=temperature or TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
    except Exception:
        return ChatOpenAI(
            model=FALLBACK_MODEL,
            openai_api_key=OPENAI_API_KEY,
            temperature=temperature or TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )


def classify_intent(state: FinanceState) -> FinanceState:
    """Classify user's financial query intent."""
    llm = get_llm(temperature=0.0)

    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    classification_prompt = f"""Classify the following user message into exactly one category.
Categories:
- budget_analysis: Questions about budgeting, spending breakdown, category analysis
- savings_advice: Questions about saving money, emergency funds, investment tips
- spending_insights: Requests for spending patterns, trends, anomalies, comparisons
- goal_setting: Setting or tracking financial goals, milestones
- receipt_analysis: User uploaded an image/receipt for analysis
- general_qa: General financial questions or chitchat

User message: {last_message}

Respond with ONLY the category name, nothing else."""

    response = llm.invoke([HumanMessage(content=classification_prompt)])
    intent = response.content.strip().lower()

    valid_intents = ["budget_analysis", "savings_advice", "spending_insights", "goal_setting", "receipt_analysis", "general_qa"]
    if intent not in valid_intents:
        intent = "general_qa"

    return {**state, "intent": intent, "metadata": {**state.get("metadata", {}), "intent": intent}}


def retrieve_knowledge(state: FinanceState) -> FinanceState:
    """Retrieve relevant financial knowledge from RAG."""
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""

    intent_queries = {
        "budget_analysis": f"budgeting strategies spending allocation {last_message}",
        "savings_advice": f"savings tips emergency fund investing {last_message}",
        "spending_insights": f"spending analysis patterns benchmarks {last_message}",
        "goal_setting": f"financial goals SMART planning milestones {last_message}",
        "general_qa": last_message,
    }

    query = intent_queries.get(state["intent"], last_message)
    documents = retrieve_context(query, k=3)
    context = format_context(documents)

    return {**state, "context": context}


def analyze_budget(state: FinanceState) -> FinanceState:
    """Analyze user's budget based on transaction data."""
    llm = get_llm()

    system_prompt = """You are FinMate, a friendly and knowledgeable personal finance assistant.
You're analyzing the user's budget. Be specific, use numbers, and reference the 50/30/20 rule
or other frameworks when relevant. Give actionable advice.

Financial Knowledge Context:
{context}

User's Transaction Data:
{transaction_data}

User Profile:
{user_profile}"""

    prompt = system_prompt.format(
        context=state.get("context", ""),
        transaction_data=state.get("transaction_data", "No transaction data loaded"),
        user_profile=state.get("user_profile", "No profile loaded"),
    )

    messages = [SystemMessage(content=prompt)] + state["messages"]
    response = llm.invoke(messages)

    return {**state, "response": response.content, "messages": state["messages"] + [AIMessage(content=response.content)]}


def provide_savings_advice(state: FinanceState) -> FinanceState:
    """Provide personalized savings recommendations."""
    llm = get_llm()

    system_prompt = """You are FinMate, a personal finance assistant specializing in savings optimization.
Provide specific, actionable savings advice based on the user's spending patterns and goals.
Reference concrete numbers from their data. Suggest specific amounts and timelines.

Financial Knowledge Context:
{context}

User's Transaction Data:
{transaction_data}

User Profile:
{user_profile}"""

    prompt = system_prompt.format(
        context=state.get("context", ""),
        transaction_data=state.get("transaction_data", "No transaction data loaded"),
        user_profile=state.get("user_profile", "No profile loaded"),
    )

    messages = [SystemMessage(content=prompt)] + state["messages"]
    response = llm.invoke(messages)

    return {**state, "response": response.content, "messages": state["messages"] + [AIMessage(content=response.content)]}


def analyze_spending(state: FinanceState) -> FinanceState:
    """Provide spending pattern insights and anomaly detection."""
    llm = get_llm()

    system_prompt = """You are FinMate, a personal finance assistant focused on spending analysis.
Identify patterns, trends, and anomalies in the user's spending. Compare to benchmarks.
Highlight areas of concern and areas where they're doing well. Use specific numbers.

Financial Knowledge Context:
{context}

User's Transaction Data:
{transaction_data}

User Profile:
{user_profile}"""

    prompt = system_prompt.format(
        context=state.get("context", ""),
        transaction_data=state.get("transaction_data", "No transaction data loaded"),
        user_profile=state.get("user_profile", "No profile loaded"),
    )

    messages = [SystemMessage(content=prompt)] + state["messages"]
    response = llm.invoke(messages)

    return {**state, "response": response.content, "messages": state["messages"] + [AIMessage(content=response.content)]}


def handle_goal_setting(state: FinanceState) -> FinanceState:
    """Help user set or track financial goals - requires confirmation."""
    llm = get_llm()

    system_prompt = """You are FinMate, helping the user set or review financial goals.
Use the SMART framework. Based on their income and spending, suggest realistic timelines.
If they want to set a new goal or modify existing ones, ask for confirmation before finalizing.

Financial Knowledge Context:
{context}

User's Transaction Data:
{transaction_data}

User Profile:
{user_profile}

IMPORTANT: End your response by asking the user to confirm if they'd like to proceed
with the suggested goal/changes. Format your suggestion clearly."""

    prompt = system_prompt.format(
        context=state.get("context", ""),
        transaction_data=state.get("transaction_data", "No transaction data loaded"),
        user_profile=state.get("user_profile", "No profile loaded"),
    )

    messages = [SystemMessage(content=prompt)] + state["messages"]
    response = llm.invoke(messages)

    return {
        **state,
        "response": response.content,
        "needs_confirmation": True,
        "messages": state["messages"] + [AIMessage(content=response.content)],
    }


def handle_general_qa(state: FinanceState) -> FinanceState:
    """Handle general financial questions."""
    llm = get_llm()

    system_prompt = """You are FinMate, a friendly personal finance assistant.
Answer the user's question using the provided financial knowledge. Be helpful,
accurate, and concise. If you don't know something, say so rather than guessing.

Financial Knowledge Context:
{context}

User Profile:
{user_profile}"""

    prompt = system_prompt.format(
        context=state.get("context", ""),
        user_profile=state.get("user_profile", "No profile loaded"),
    )

    messages = [SystemMessage(content=prompt)] + state["messages"]
    response = llm.invoke(messages)

    return {**state, "response": response.content, "messages": state["messages"] + [AIMessage(content=response.content)]}


def route_by_intent(state: FinanceState) -> str:
    """Route to the appropriate handler based on classified intent."""
    intent = state.get("intent", "general_qa")
    routes = {
        "budget_analysis": "analyze_budget",
        "savings_advice": "provide_savings_advice",
        "spending_insights": "analyze_spending",
        "goal_setting": "handle_goal_setting",
        "general_qa": "handle_general_qa",
        "receipt_analysis": "handle_general_qa",
    }
    return routes.get(intent, "handle_general_qa")


def check_confirmation(state: FinanceState) -> str:
    """Check if response needs user confirmation (human-in-the-loop)."""
    if state.get("needs_confirmation", False):
        return "await_confirmation"
    return "end"


def build_finance_graph() -> StateGraph:
    """Build and compile the FinMate LangGraph workflow."""
    workflow = StateGraph(FinanceState)

    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("retrieve_knowledge", retrieve_knowledge)
    workflow.add_node("analyze_budget", analyze_budget)
    workflow.add_node("provide_savings_advice", provide_savings_advice)
    workflow.add_node("analyze_spending", analyze_spending)
    workflow.add_node("handle_goal_setting", handle_goal_setting)
    workflow.add_node("handle_general_qa", handle_general_qa)

    workflow.set_entry_point("classify_intent")
    workflow.add_edge("classify_intent", "retrieve_knowledge")

    workflow.add_conditional_edges(
        "retrieve_knowledge",
        route_by_intent,
        {
            "analyze_budget": "analyze_budget",
            "provide_savings_advice": "provide_savings_advice",
            "analyze_spending": "analyze_spending",
            "handle_goal_setting": "handle_goal_setting",
            "handle_general_qa": "handle_general_qa",
        },
    )

    workflow.add_edge("analyze_budget", END)
    workflow.add_edge("provide_savings_advice", END)
    workflow.add_edge("analyze_spending", END)
    workflow.add_edge("handle_goal_setting", END)
    workflow.add_edge("handle_general_qa", END)

    return workflow.compile()


# Global graph instance
finance_graph = None


def get_finance_graph():
    """Get or create the finance graph singleton."""
    global finance_graph
    if finance_graph is None:
        finance_graph = build_finance_graph()
    return finance_graph


def run_finance_agent(
    user_message: str,
    transaction_data: str = "",
    user_profile: str = "",
    chat_history: list = None,
) -> dict:
    """
    Run the finance agent with a user message.
    Returns the response and metadata.
    """
    graph = get_finance_graph()

    messages = []
    if chat_history:
        messages.extend(chat_history)
    messages.append(HumanMessage(content=user_message))

    initial_state: FinanceState = {
        "messages": messages,
        "intent": "",
        "context": "",
        "transaction_data": transaction_data,
        "user_profile": user_profile,
        "needs_confirmation": False,
        "confirmed": False,
        "response": "",
        "metadata": {},
    }

    result = graph.invoke(initial_state)

    return {
        "response": result["response"],
        "intent": result["intent"],
        "needs_confirmation": result.get("needs_confirmation", False),
        "messages": result["messages"],
        "metadata": result.get("metadata", {}),
    }
