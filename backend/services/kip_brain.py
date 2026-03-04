"""
KIP Brain — RAG Pipeline
Connects ChromaDB knowledge base with Claude API.
Handles retrieval, context injection, and response generation.
"""

import os
import json
import time
import logging
from typing import AsyncGenerator, Optional
import anthropic

from services.intent_classifier import classify_intent, get_system_prompt_for_type, ResponseType
from config import settings

logger = logging.getLogger("kip.brain")

# ── Anthropic client ──────────────────────────────────────────────────────────
_client: Optional[anthropic.Anthropic] = None

def get_claude_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


# ── ChromaDB (optional — graceful fallback if not installed) ──────────────────
_chroma_collection = None

def get_chroma_collection():
    global _chroma_collection
    if _chroma_collection is not None:
        return _chroma_collection
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        _chroma_collection = client.get_collection(
            name=settings.CHROMA_COLLECTION,
            embedding_function=ef,
        )
        logger.info(f"✅ ChromaDB loaded: {_chroma_collection.count()} chunks")
        return _chroma_collection
    except Exception as e:
        logger.warning(f"ChromaDB not available: {e}. Running without RAG.")
        return None


def retrieve_context(query: str, n_results: int = 5) -> str:
    """Retrieve relevant context chunks from the KIP knowledge base."""
    collection = get_chroma_collection()
    if collection is None:
        return ""
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "distances"],
        )
        docs = results.get("documents", [[]])[0]
        dists = results.get("distances", [[]])[0]

        # Only use chunks with reasonable relevance (distance < 1.2)
        relevant = [
            doc for doc, dist in zip(docs, dists)
            if dist < 1.2
        ]
        if not relevant:
            return ""
        context = "\n\n---\n\n".join(relevant[:4])
        return f"KNOWLEDGE BASE CONTEXT:\n{context}\n\nUse the above context to inform your response."
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        return ""


def build_conversation_history(messages: list[dict]) -> list[dict]:
    """Convert stored messages to Anthropic message format."""
    history = []
    for msg in messages[-10:]:  # Keep last 10 messages for context window
        history.append({
            "role": msg["role"],
            "content": msg["content"],
        })
    return history


def build_business_context(business_profile: Optional[dict]) -> str:
    """Inject user's business profile into every message if active."""
    if not business_profile:
        return ""
    return f"""
USER'S ACTIVE BUSINESS PROFILE:
Business: {business_profile.get('name', 'Unknown')}
Sector: {business_profile.get('sector', 'Unknown')}
Location: {business_profile.get('location', 'Unknown')}
Stage: {business_profile.get('stage', 'Unknown')}
Monthly Revenue: K{business_profile.get('monthly_revenue', 'Unknown')}
Employees: {business_profile.get('employees', 0)}

When answering, consider this specific business context.
"""


async def generate_response(
    user_message: str,
    conversation_history: list[dict],
    business_profile: Optional[dict] = None,
    stream: bool = False,
) -> dict:
    """
    Main KIP response generation pipeline:
    1. Classify intent → determines response layout
    2. Retrieve RAG context
    3. Build system prompt
    4. Call Claude API
    5. Parse and return structured response
    """
    start = time.time()
    client = get_claude_client()

    # Step 1: Classify intent
    response_type = classify_intent(user_message)
    logger.info(f"Intent classified as: {response_type.value}")

    # Step 2: Retrieve context
    rag_context = retrieve_context(user_message)

    # Step 3: Build system prompt
    # system_prompt = get_system_prompt_for_type(response_type)
    # if rag_context:
    #     system_prompt += f"\n\n{rag_context}"
    # if business_profile:
    #     system_prompt += f"\n\n{build_business_context(business_profile)}"
    # Step 3: Build system prompt with live economic + news context
    from services.learning_service import get_learning_context
    system_prompt = get_system_prompt_for_type(response_type)
    try:
        live_context = await get_learning_context()
        if live_context:
            system_prompt += f"\n\n{live_context}"
    except Exception as e:
        logger.warning(f"Live context injection failed: {e}")
    if rag_context:
        system_prompt += f"\n\n{rag_context}"
    if business_profile:
        system_prompt += f"\n\n{build_business_context(business_profile)}"


    # Step 4: Build message history
    history = build_conversation_history(conversation_history)

    # Step 5: Call Claude
    try:
        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=2000,
            system=system_prompt,
            messages=history + [{"role": "user", "content": user_message}],
        )
        raw_content = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        latency_ms  = int((time.time() - start) * 1000)

        # Step 6: Parse structured response if JSON layout
        structured = None
        if response_type != ResponseType.GENERAL:
            try:
                # Strip any markdown fences
                clean = raw_content.strip()
                if clean.startswith("```"):
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                structured = json.loads(clean)
            except Exception:
                # Fall back to general if JSON parse fails
                logger.warning(f"JSON parse failed for {response_type}, falling back to general")
                response_type = ResponseType.GENERAL
                structured = None

        return {
            "response_type": response_type.value,
            "content":       raw_content,
            "structured":    structured,
            "tokens_used":   tokens_used,
            "latency_ms":    latency_ms,
        }

    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
        raise


async def generate_business_log_analysis(
    log_title: str,
    log_description: str,
    log_type: str,
    amount_zmw: Optional[float],
    business_profile: dict,
    recent_logs: list[dict],
) -> dict:
    """
    Analyse a business log entry and generate KIP's next-step suggestions.
    Used when a user submits a business update through the journey tracker.
    """
    client = get_claude_client()

    recent_context = ""
    if recent_logs:
        entries = []
        for log in recent_logs[-5:]:
            entries.append(f"- [{log['log_type']}] {log['title']}: {log.get('description','')[:100]}")
        recent_context = "\nRECENT BUSINESS LOGS:\n" + "\n".join(entries)

    prompt = f"""You are KIP analysing a business update from a Zambian entrepreneur.

BUSINESS: {business_profile.get('name')} ({business_profile.get('sector')}, {business_profile.get('location')})
STAGE: {business_profile.get('stage')}
MONTHLY REVENUE: K{business_profile.get('monthly_revenue', 'Unknown')}
{recent_context}

NEW LOG ENTRY:
Type: {log_type}
Title: {log_title}
Description: {log_description}
Amount: {f'K{amount_zmw:,.0f}' if amount_zmw else 'Not specified'}

Provide a JSON response:
{{
  "analysis": "2-3 sentence honest assessment of this update",
  "what_this_means": "1 sentence translating the log into business impact",
  "suggestions": [
    {{"priority": "high|medium|low", "action": "Specific next step", "timeframe": "When to do it"}},
    {{"priority": "...", "action": "...", "timeframe": "..."}}
  ],
  "warning": null or "A concern KIP noticed if any",
  "encouragement": "A brief genuine encouragement based on this update"
}}
Return ONLY the JSON."""

    response = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        return json.loads(response.content[0].text.strip())
    except Exception:
        return {
            "analysis": response.content[0].text,
            "suggestions": [],
            "warning": None,
            "encouragement": "Keep going — every log helps KIP understand your business better.",
        }
