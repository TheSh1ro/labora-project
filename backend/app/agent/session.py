# backend\app\agent\session.py

"""
Gestão de sessão, histórico e contadores de tokens.
"""

import logging
from typing import List, Dict, Any

from ..models import Message, TokenUsage

MAX_HISTORY_TURNS = (
    5  # 5 pares user/assistant = 10 mensagens; o trim controla o contexto
)

PRICING = {
    "prompt": 0.15 / 1_000_000,
    "completion": 0.60 / 1_000_000,
}


def _trim_history(messages: List[Message]) -> List[Message]:
    """Mantém as últimas N trocas + mensagem actual."""
    max_messages = MAX_HISTORY_TURNS * 2  # cada turno = user + assistant
    if len(messages) <= max_messages:
        return messages
    # Preserva as mais recentes
    return messages[-max_messages:]


def _build_openai_messages(messages: List[Message], system_prompt: str) -> List[Dict[str, Any]]:
    """Constrói a lista de mensagens no formato OpenAI."""
    openai_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        msg_dict = {"role": msg.role, "content": msg.content}
        if msg.tool_calls:
            msg_dict["tool_calls"] = msg.tool_calls
        if msg.tool_call_id:
            msg_dict["tool_call_id"] = msg.tool_call_id
        if msg.name:
            msg_dict["name"] = msg.name
        openai_messages.append(msg_dict)
    return openai_messages


def _calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return round(
        prompt_tokens * PRICING["prompt"]
        + completion_tokens * PRICING["completion"],
        6,
    )


def get_session_usage(
    session_prompt_tokens: int, session_completion_tokens: int
) -> TokenUsage:
    total = session_prompt_tokens + session_completion_tokens
    return TokenUsage(
        prompt_tokens=session_prompt_tokens,
        completion_tokens=session_completion_tokens,
        total_tokens=total,
        estimated_cost_usd=_calculate_cost(
            session_prompt_tokens, session_completion_tokens
        ),
    )


def reset_session(session_messages: List[Message]) -> List[Message]:
    """Limpa o histórico da conversa activa. Os contadores de tokens NÃO são reiniciados."""
    cleared = len(session_messages)
    logging.info(
        f"[session] reset — {cleared} mensagens removidas; tokens acumulados mantidos"
    )
    return []
