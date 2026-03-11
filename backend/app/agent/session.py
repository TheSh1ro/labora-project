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


def _build_openai_messages(
    messages: List[Message], system_prompt: str
) -> List[Dict[str, Any]]:
    """Constrói a lista de mensagens no formato OpenAI.

    Mensagens com role='tool' requerem obrigatoriamente 'tool_call_id' no formato
    OpenAI. Se o campo estiver ausente no histórico (bug latente em conversas multi-
    turno), a API devolve 400. Esta função filtra pares inválidos para garantir que
    o histórico enviado é sempre aceite pela API.
    """
    openai_messages = [{"role": "system", "content": system_prompt}]

    # Pré-passo: identificar tool_call_ids válidos presentes no histórico.
    # Uma tool message só é válida se existir uma assistant message anterior
    # com um tool_call que tenha o mesmo id.
    valid_tool_call_ids: set = set()
    for msg in messages:
        if msg.role == "assistant" and msg.tool_calls:
            for tc in msg.tool_calls:
                tc_id = (
                    tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                )
                if tc_id:
                    valid_tool_call_ids.add(tc_id)

    for msg in messages:
        if msg.role == "tool":
            # Descarta tool messages sem tool_call_id ou cujo id não tem
            # assistant message correspondente — evita erro 400 da API.
            if not msg.tool_call_id or msg.tool_call_id not in valid_tool_call_ids:
                logging.warning(
                    f"[session] tool message descartada — tool_call_id ausente ou órfão: "
                    f"{msg.tool_call_id!r}"
                )
                continue

        msg_dict: Dict[str, Any] = {"role": msg.role, "content": msg.content}
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
        prompt_tokens * PRICING["prompt"] + completion_tokens * PRICING["completion"],
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
