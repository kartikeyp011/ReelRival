from backend.config import settings


# In-memory session store
# { session_id: [{"role": "user"|"assistant", "content": str}, ...] }
_sessions: dict[str, list[dict]] = {}


def get_history(session_id: str) -> list[dict]:
    """Return conversation history for a session."""
    return _sessions.get(session_id, [])


def add_turn(session_id: str, user_message: str, assistant_message: str):
    """Append a completed turn to session memory."""
    if session_id not in _sessions:
        _sessions[session_id] = []

    _sessions[session_id].append({"role": "user", "content": user_message})
    _sessions[session_id].append({"role": "assistant", "content": assistant_message})

    # Keep only last N turns (each turn = 2 entries)
    max_entries = settings.max_memory_turns * 2
    if len(_sessions[session_id]) > max_entries:
        _sessions[session_id] = _sessions[session_id][-max_entries:]


def clear_session(session_id: str):
    """Clear memory for a session (on reset or new comparison)."""
    _sessions.pop(session_id, None)


def session_exists(session_id: str) -> bool:
    return session_id in _sessions


def format_history_for_prompt(session_id: str) -> str:
    """
    Format conversation history as a readable block for the LLM prompt.
    Returns empty string if no history.
    """
    history = get_history(session_id)
    if not history:
        return ""

    lines = ["=== CONVERSATION HISTORY ==="]
    for turn in history:
        role = "Creator" if turn["role"] == "user" else "Assistant"
        lines.append(f"{role}: {turn['content']}")

    return "\n".join(lines)