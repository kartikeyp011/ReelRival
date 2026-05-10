from backend.retrieval.retriever import format_chunks_for_prompt


SYSTEM_PROMPT = """You are ReelRival — an expert YouTube content analyst helping creators understand why videos perform the way they do.

You have access to transcript excerpts and engagement statistics for two videos. Use ONLY the provided evidence to support your answers. Be specific, reference timestamps when available, and cite sources as [Source N].

Your tone is direct, analytical, and creator-friendly. Always end comparison answers with one actionable improvement suggestion.

Rules:
- Only make factual claims supported by the provided evidence.
- When evidence is insufficient, say so clearly.
- Use [Source N] inline citations tied to the evidence block below.
- Keep answers focused — under 300 words unless a detailed breakdown is requested.
- Never invent statistics or metrics not present in the evidence."""


def build_prompt(
    user_message: str,
    retrieved_chunks: list[dict],
    session_id: str,
    conversation_history: str,
) -> str:
    """
    Assemble the full prompt sent to DeepSeek-R1:8b.

    Structure:
    1. System instruction
    2. Evidence block (retrieved chunks)
    3. Conversation history (last N turns)
    4. Current user question
    """
    evidence_block = format_chunks_for_prompt(retrieved_chunks)

    parts = [SYSTEM_PROMPT]

    parts.append("\n=== VIDEO EVIDENCE ===")
    parts.append(evidence_block)

    if conversation_history:
        parts.append(f"\n{conversation_history}")

    parts.append(f"\n=== CURRENT QUESTION ===\nCreator: {user_message}")
    parts.append("\nAssistant:")

    return "\n".join(parts)