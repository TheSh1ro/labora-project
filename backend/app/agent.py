# backend\app\agent.py

"""
Agente Conversacional de Direito Laboral Português.
Implementa tool calling com Groq (moonshotai/kimi-k2-instruct).
"""

import asyncio
import os
import json
import time
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from groq import AsyncGroq

from .tools import TOOLS_SCHEMA, TOOL_FUNCTIONS
from .models import Message, Source, ToolCallInfo, ChatResponse, TokenUsage

from dotenv import load_dotenv

load_dotenv()

# Diretório de logs (backend/logs/)
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
openai_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

MODEL = "moonshotai/kimi-k2-instruct"

MAX_HISTORY_TURNS = (
    5  # 5 pares user/assistant = 10 mensagens; o trim controla o contexto
)

PRICING = {
    "prompt": 0.59 / 1_000_000,
    "completion": 0.79 / 1_000_000,
}

AGENT_CONFIG = {
    "model": MODEL,
    "provider": "Groq",
    "provider_url": "https://groq.com",
    "display_name": "Kimi K2 Instruct",
    "tool_calling": True,
    "max_iterations": 5,
    "temperature": 0,
    "features": ["tool_calling", "web_search", "citations", "calculations"],
    "pricing_usd_per_1m": {
        "prompt": 0.59,
        "completion": 0.79,
    },
}

# System prompt (versão otimizada - tokens reduzidos)
SYSTEM_PROMPT = """És um especialista em Direito Laboral Português. Respondes apenas sobre direito laboral e processamento salarial em Portugal.

REGRAS:
- Usa SEMPRE as tools disponíveis antes de responder — nunca respondas de memória
- Mostra fórmulas e passo a passo em cálculos
- Termina com secção "Fontes" com URLs das fontes consultadas
- Responde em português europeu
- Se não tiveres certeza, recusa graciosamente e recomenda consultar advogado
- Recusa questões fora do âmbito laboral português

FORMATO:
- Usa headers (##) para separar secções com mais de 2 tópicos
- Usa sempre Markdown — nunca respondas em texto plano puro
- Separa valor principal, cálculos e fontes com linha em branco entre cada bloco
- Valores monetários em negrito: **870 €**
- Listas apenas quando há 3+ itens enumeráveis
- Máximo 2 níveis de lista — nunca listas dentro de listas
- Fórmulas em linha de código: `870 € ÷ 22 dias = 39,55 €/dia`
- Respostas directas: o valor principal na primeira linha, detalhes a seguir
- Evita parágrafos introdutórios redundantes ("Com base no artigo X, o valor é...")
"""

# Keywords para classificação automática do contexto de negócio
_TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "salario": [
        "salário",
        "salario",
        "vencimento",
        "remuneração",
        "remuneracao",
        "smn",
    ],
    "ferias": ["férias", "ferias", "subsídio de férias", "subsidio de ferias"],
    "natal": ["natal", "subsídio de natal", "subsidio de natal", "13º", "13o"],
    "irs": ["irs", "retenção", "retencao", "imposto", "taxa marginal", "escalão"],
    "tsu": [
        "tsu",
        "segurança social",
        "seguranca social",
        "contribuição",
        "contribuicao",
    ],
    "despedimento": [
        "despedimento",
        "demissão",
        "demissao",
        "aviso prévio",
        "aviso previo",
        "justa causa",
    ],
    "layoff": ["lay-off", "layoff", "suspensão", "suspensao"],
    "teletrabalho": ["teletrabalho", "remoto", "trabalho à distância"],
    "nao_concorrencia": ["não concorrência", "nao concorrencia", "concorrência"],
    "contrato": ["contrato", "termo certo", "sem termo", "permanente", "temporário"],
}

_REFUSAL_KEYWORDS = [
    "não posso",
    "nao posso",
    "fora do meu âmbito",
    "fora do meu ambito",
    "recomendo consultar",
    "aconselho a consultar",
    "não tenho certeza",
    "nao tenho certeza",
    "advogado",
]

_CALCULATION_KEYWORDS = [
    "calcula",
    "cálculo",
    "formula",
    "fórmula",
    "passo a passo",
    "resultado",
    "€",
    "eur",
    "%",
    "dividid",
    "multiplicad",
]

# Tools de pesquisa (Tavily) vs. cálculo local
_SEARCH_TOOLS = {"search_labor_law", "search_irs_tables", "search_social_security"}
_CALCULATION_TOOLS = {
    "calculate_vacation_subsidy",
    "calculate_christmas_subsidy",
    "get_minimum_wage",
    "calculate_tsu",
}


def _classify_question(text: str) -> Dict[str, Any]:
    """Classifica a pergunta em tópicos e detecta intenção de cálculo."""
    text_lower = text.lower()
    detected_topics = [
        topic
        for topic, kws in _TOPIC_KEYWORDS.items()
        if any(kw in text_lower for kw in kws)
    ]
    has_calculation_intent = any(
        kw in text_lower
        for kw in [
            "calcula",
            "quanto",
            "valor",
            "percentagem",
            "taxa",
            "líquido",
            "liquido",
        ]
    )
    return {
        "detected_topics": detected_topics,
        "has_calculation_intent": has_calculation_intent,
        "char_count": len(text),
        "word_count": len(text.split()),
    }


def _classify_response(content: str) -> Dict[str, Any]:
    """Classifica a resposta: recusou? tem cálculo? tem secção de fontes?"""
    content_lower = content.lower()
    return {
        "agent_refused": any(kw in content_lower for kw in _REFUSAL_KEYWORDS),
        "has_calculation_in_response": any(
            kw in content_lower for kw in _CALCULATION_KEYWORDS
        ),
        "has_sources_section": "📚" in content or "fontes" in content_lower,
        "char_count": len(content),
        "word_count": len(content.split()),
    }


def _extract_domain(url: str) -> Optional[str]:
    """Extrai o domínio de uma URL. Retorna None se inválida."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lstrip("www.")
        return domain if domain else None
    except Exception:
        return None


def _extract_computed_summary(tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrai os valores-chave do resultado de uma tool de cálculo para o log.
    Evita replicar o JSON completo — apenas os campos de negócio mais relevantes.
    """
    if not isinstance(result, dict) or not result.get("success"):
        return {}

    if tool_name == "calculate_tsu":
        return {
            "employer_rate": result.get("employer", {}).get("rate"),
            "employer_amount_eur": result.get("employer", {}).get("amount"),
            "employee_rate": result.get("employee", {}).get("rate"),
            "employee_amount_eur": result.get("employee", {}).get("amount"),
            "liquid_salary_eur": result.get("liquid_salary"),
            "contract_type": result.get("contract_type"),
        }
    elif tool_name == "calculate_vacation_subsidy":
        return {
            "vacation_subsidy_eur": result.get("vacation_subsidy"),
            "daily_salary_eur": result.get("daily_salary"),
            "vacation_days": result.get("vacation_days"),
        }
    elif tool_name == "calculate_christmas_subsidy":
        return {
            "christmas_subsidy_eur": result.get("christmas_subsidy"),
            "is_proportional": result.get("is_proportional", False),
            "months_worked": result.get("months_worked"),
            "start_month": result.get("start_month"),
        }
    elif tool_name == "get_minimum_wage":
        return {
            "monthly_eur": result.get("monthly_amount"),
            "annual_eur": result.get("annual_amount"),
            "hourly_eur": result.get("hourly_amount"),
            "year": result.get("year"),
            "legal_basis": result.get("legal_basis"),
        }
    elif tool_name == "search_irs_tables":
        # Híbrido: tem tanto pesquisa web como cálculo local
        summary: Dict[str, Any] = {"year": result.get("year")}
        if result.get("tax_rate") is not None:
            summary["tax_rate"] = result["tax_rate"]
        if result.get("tax_amount") is not None:
            summary["tax_amount_eur"] = result["tax_amount"]
        if result.get("final_tax_amount") is not None:
            summary["final_tax_amount_eur"] = result["final_tax_amount"]
        if result.get("dependent_deduction") is not None:
            summary["dependent_deduction_eur"] = result["dependent_deduction"]
        return summary
    return {}


def _extract_source_urls(result: Dict[str, Any]) -> List[str]:
    """Extrai todas as URLs presentes no resultado de uma tool."""
    urls: List[str] = []
    # Fontes explícitas (calculation tools)
    for item in result.get("sources", []):
        if isinstance(item, dict) and item.get("url"):
            urls.append(item["url"])
    # Resultados de pesquisa Tavily
    for item in result.get("results", []):
        if isinstance(item, dict) and item.get("url"):
            urls.append(item["url"])
    return [u for u in urls if u]


def _trim_history(messages: List[Message]) -> List[Message]:
    """Mantém as últimas N trocas + mensagem actual."""
    max_messages = MAX_HISTORY_TURNS * 2  # cada turno = user + assistant
    if len(messages) <= max_messages:
        return messages
    # Preserva as mais recentes
    return messages[-max_messages:]


class LaborLawAgent:
    """Agente de Direito Laboral com tool calling e logging estruturado (wide events)."""

    def __init__(self):
        self.client = openai_client
        self.model = MODEL
        self.tools = TOOLS_SCHEMA
        self.tool_functions = TOOL_FUNCTIONS
        self._session_prompt_tokens = 0
        self._session_completion_tokens = 0

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return round(
            prompt_tokens * PRICING["prompt"]
            + completion_tokens * PRICING["completion"],
            6,
        )

    def get_session_usage(self) -> TokenUsage:
        total = self._session_prompt_tokens + self._session_completion_tokens
        return TokenUsage(
            prompt_tokens=self._session_prompt_tokens,
            completion_tokens=self._session_completion_tokens,
            total_tokens=total,
            estimated_cost_usd=self._calculate_cost(
                self._session_prompt_tokens, self._session_completion_tokens
            ),
        )

    def reset_session_usage(self) -> None:
        self._session_prompt_tokens = 0
        self._session_completion_tokens = 0

    def _write_log(self, log: Dict[str, Any]) -> None:
        """Persiste o wide event em arquivo JSON e imprime resumo no stdout."""
        try:
            log_path = LOGS_DIR / f"{log['timestamp'][:10]}_{log['request_id']}.json"
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(log, f, ensure_ascii=False, indent=2)

            usage = log.get("usage", {})
            output = log.get("output", {})
            timing = log.get("timing_ms", {})
            iters = len(log.get("iterations", []))
            tool_seq = output.get("tool_call_sequence", [])
            domains = output.get("unique_domains_consulted", [])
            refused = output.get("agent_refused", False)

            logging.info(
                f"[{log['request_id']}] "
                f"finish={output.get('finish_reason', '?')} | "
                f"iters={iters} | "
                f"tools={tool_seq} | "
                f"sources={output.get('sources_count', 0)} | "
                f"domains={domains} | "
                f"refused={refused} | "
                f"tokens={usage.get('total_tokens', '?')} "
                f"(prompt={usage.get('prompt_tokens', '?')}, compl={usage.get('completion_tokens', '?')}) | "
                f"cost=${usage.get('estimated_cost_usd', 0):.5f} | "
                f"time={timing.get('total', '?')}ms "
                f"(llm={timing.get('llm_total', '?')}ms, tools={timing.get('tools_total', '?')}ms) | "
                f"topics={log.get('input', {}).get('detected_topics', [])}"
            )
        except Exception as e:
            logging.warning(f"Falha ao escrever log: {e}")

    async def chat(
        self, messages: List[Message], stream: bool = False
    ) -> ChatResponse:  # stream: not yet implemented
        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]

        call_prompt_tokens = 0
        call_completion_tokens = 0

        # Trunca o histórico para os últimos MAX_HISTORY_TURNS pares
        user_turns = sum(1 for m in messages if m.role == "user")
        original_count = len(messages)
        messages = _trim_history(messages)
        trimmed_count = original_count - len(messages)
        if trimmed_count > 0:
            logging.info(
                f"[{request_id}] history truncated: {trimmed_count} mensagens removidas "
                f"({original_count} → {len(messages)})"
            )

        # Extrai e classifica a mensagem do utilizador
        user_message = next((m for m in reversed(messages) if m.role == "user"), None)
        user_text = user_message.content if user_message else ""
        question_meta = _classify_question(user_text)

        # --- Wide event: construído progressivamente, emitido uma vez no final ---
        log: Dict[str, Any] = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.model,
            # Contexto da sessão no momento do pedido (tokens acumulados antes deste call)
            "session_tokens_before": self._session_prompt_tokens
            + self._session_completion_tokens,
            # Configuração da chamada ao LLM
            "config": {
                "temperature": 0,
                "max_tokens": 1200,
                "max_iterations": AGENT_CONFIG["max_iterations"],
                "tool_choice": "auto",
                "parallel_tool_calls": False,
            },
            "input": {
                "message": user_text,
                **question_meta,
                # Turno actual do utilizador nesta conversa (antes do trim)
                "conversation_turn": user_turns,
                # Contagem original (antes do trim) e efectiva (após trim)
                "history_messages_received": original_count - 1,
                "history_messages_sent": len(messages) - 1,
                "history_trimmed": trimmed_count,
                # Contagem de mensagens por papel para perceber o contexto enviado
                "history_by_role": {
                    role: sum(1 for m in messages if m.role == role)
                    for role in ("user", "assistant", "system", "tool")
                    if any(m.role == role for m in messages)
                },
            },
            "iterations": [],
            "output": {},
            "usage": {},
            "timing_ms": {
                "total": 0,
                "llm_total": 0,  # soma de todas as chamadas LLM
                "tools_total": 0,  # soma de todas as execuções de tool
                "per_iteration": [],
            },
        }

        if not self.client:
            log["output"] = {"finish_reason": "no_api_key"}
            self._write_log(log)
            return ChatResponse(
                message=Message(
                    role="assistant", content="Erro: Groq API key nao configurada."
                ),
                sources=[],
                tool_calls=[],
                response_time_ms=(time.time() - start_time) * 1000,
                usage=TokenUsage(),
                execution_log=log,
            )

        openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in messages:
            msg_dict = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            if msg.name:
                msg_dict["name"] = msg.name
            openai_messages.append(msg_dict)

        all_sources: List[Source] = []
        all_tool_calls: List[ToolCallInfo] = []
        total_llm_ms = 0
        total_tools_ms = 0

        try:
            for iteration in range(AGENT_CONFIG["max_iterations"]):
                iter_start = time.time()

                iter_log: Dict[str, Any] = {
                    "index": iteration + 1,
                    "tokens": {},
                    "llm_latency_ms": 0,
                    "finish_reason": None,  # "tool_calls" | "stop" | "length"
                    "fallback_used": False,
                    "fallback_reason": None,
                    # Primeiros 300 chars do conteúdo textual gerado pelo modelo nesta
                    # iteração (útil para debug de raciocínio intermédio antes de tool calls)
                    "model_content_preview": None,
                    "tool_calls": [],
                }

                # --- Chamada LLM (com medição de latência isolada) ---
                llm_start = time.time()
                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=openai_messages,
                        tools=self.tools,
                        tool_choice="auto",
                        parallel_tool_calls=False,
                        temperature=0,
                        max_tokens=1200,
                    )
                except Exception as api_err:
                    if "tool_use_failed" in str(api_err) or "400" in str(api_err):
                        iter_log["fallback_used"] = True
                        iter_log["fallback_reason"] = str(api_err)[:200]
                        response = await self.client.chat.completions.create(
                            model=self.model,
                            messages=openai_messages,
                            temperature=0,
                            max_tokens=1200,
                        )
                    else:
                        raise api_err

                llm_ms = round((time.time() - llm_start) * 1000)
                iter_log["llm_latency_ms"] = llm_ms
                total_llm_ms += llm_ms

                # Tokens desta iteração
                if response.usage:
                    iter_prompt = response.usage.prompt_tokens
                    iter_completion = response.usage.completion_tokens
                    call_prompt_tokens += iter_prompt
                    call_completion_tokens += iter_completion
                    iter_log["tokens"] = {
                        "prompt": iter_prompt,
                        "completion": iter_completion,
                        "total": iter_prompt + iter_completion,
                    }

                choice = response.choices[0]
                message = choice.message
                iter_log["finish_reason"] = choice.finish_reason

                # Raciocínio textual do modelo nesta iteração (pode existir mesmo com tool_calls)
                iter_log["model_content_preview"] = (message.content or "")[
                    :300
                ] or None

                # --- Resposta final (sem tool calls) ---
                if not message.tool_calls:
                    iter_log["elapsed_ms"] = round((time.time() - iter_start) * 1000)
                    log["iterations"].append(iter_log)
                    log["timing_ms"]["per_iteration"].append(iter_log["elapsed_ms"])

                    self._session_prompt_tokens += call_prompt_tokens
                    self._session_completion_tokens += call_completion_tokens
                    response_time = (time.time() - start_time) * 1000

                    content = message.content or "Nao foi possivel gerar uma resposta."
                    response_meta = _classify_response(content)
                    usage = TokenUsage(
                        prompt_tokens=call_prompt_tokens,
                        completion_tokens=call_completion_tokens,
                        total_tokens=call_prompt_tokens + call_completion_tokens,
                        estimated_cost_usd=self._calculate_cost(
                            call_prompt_tokens, call_completion_tokens
                        ),
                    )

                    # Domínios únicos consultados (extraídos das fontes acumuladas)
                    unique_domains = sorted(
                        {d for s in all_sources for d in [_extract_domain(s.url)] if d}
                    )

                    # Enriquece output com contexto de negócio
                    log["output"] = {
                        "finish_reason": "completed",
                        "sources_count": len(all_sources),
                        "total_tool_calls": len(all_tool_calls),
                        # Sequência ordenada de tools invocadas (permite ver o "raciocínio" do agente)
                        "tool_call_sequence": [tc.name for tc in all_tool_calls],
                        # Nomes únicos de tools (sem duplicados), preservando ordem de 1ª ocorrência
                        "tools_used": list(
                            dict.fromkeys(tc.name for tc in all_tool_calls)
                        ),
                        # Lista detalhada das fontes com título e URL
                        "sources_detail": [
                            {
                                "title": s.title,
                                "url": s.url,
                                "domain": _extract_domain(s.url),
                            }
                            for s in all_sources
                        ],
                        # Domínios únicos consultados (para auditoria de cobertura das fontes)
                        "unique_domains_consulted": unique_domains,
                        # Preview da resposta final (primeiros 500 chars para diagnóstico rápido)
                        "response_preview": content[:500],
                        **response_meta,
                    }
                    log["usage"] = {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                        "estimated_cost_usd": usage.estimated_cost_usd,
                    }
                    log["timing_ms"]["total"] = round(response_time)
                    log["timing_ms"]["llm_total"] = total_llm_ms
                    log["timing_ms"]["tools_total"] = total_tools_ms
                    self._write_log(log)

                    return ChatResponse(
                        message=Message(role="assistant", content=content),
                        sources=all_sources,
                        tool_calls=all_tool_calls,
                        response_time_ms=response_time,
                        usage=usage,
                        execution_log=log,
                    )

                # --- Processa tool calls ---
                openai_messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [tc.model_dump() for tc in message.tool_calls],
                    }
                )

                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = (
                        json.loads(tool_call.function.arguments or "{}") or {}
                    )
                    tool_info = ToolCallInfo(
                        name=function_name, arguments=function_args
                    )

                    is_search = function_name in _SEARCH_TOOLS
                    is_calc = function_name in _CALCULATION_TOOLS

                    tool_log: Dict[str, Any] = {
                        "name": function_name,
                        "arguments": function_args,
                        # Categoria da tool: "search" (Tavily), "calculation" (local/determinístico),
                        # ou "hybrid" (search_irs_tables que faz ambos)
                        "tool_type": (
                            "hybrid"
                            if function_name == "search_irs_tables"
                            else "search" if is_search else "calculation"
                        ),
                        "execution_ms": 0,
                        # --- Métricas de resultado bruto ---
                        "result_chars_raw": 0,
                        "result_chars_sent": 0,
                        "result_truncated": False,
                        "result_preview": None,  # primeiros 300 chars para debug
                        # --- Detalhe de pesquisa (search / hybrid tools) ---
                        "search_query": (
                            function_args.get("query") if is_search else None
                        ),
                        "search_success": None,
                        "search_results_count": None,
                        "search_results_titles": None,  # lista de títulos dos resultados Tavily
                        # --- Detalhe de cálculo (calculation / hybrid tools) ---
                        "computed_summary": None,  # valores-chave extraídos do resultado
                        # --- Fontes ---
                        "sources_found": 0,
                        "source_urls": [],  # URLs das fontes (para auditoria)
                        "error": None,
                    }

                    if function_name in self.tool_functions:
                        try:
                            tool_start = time.time()
                            result = await self._execute_tool(
                                function_name, function_args
                            )
                            tool_ms = round((time.time() - tool_start) * 1000)
                            total_tools_ms += tool_ms
                            tool_log["execution_ms"] = tool_ms

                            raw = json.dumps(result, ensure_ascii=False)
                            truncated = raw[:6000]
                            tool_info.result = raw[:500]

                            tool_log["result_chars_raw"] = len(raw)
                            tool_log["result_chars_sent"] = len(truncated)
                            tool_log["result_truncated"] = len(raw) > 6000
                            tool_log["result_preview"] = truncated[:300]

                            # Enriquece com detalhe de pesquisa (Tavily)
                            if isinstance(result, dict):
                                if is_search or function_name == "search_irs_tables":
                                    tavily_results = result.get("results", [])
                                    tool_log["search_success"] = result.get(
                                        "success", False
                                    )
                                    tool_log["search_results_count"] = len(
                                        tavily_results
                                    )
                                    tool_log["search_results_titles"] = [
                                        r.get("title", "") for r in tavily_results
                                    ]

                                # Enriquece com resumo de cálculo (calculation / hybrid)
                                if is_calc or function_name == "search_irs_tables":
                                    tool_log["computed_summary"] = (
                                        _extract_computed_summary(function_name, result)
                                    )

                                # URLs das fontes (presente em todos os tipos de tool)
                                tool_log["source_urls"] = _extract_source_urls(result)

                            sources = self._extract_sources(result)
                            seen_urls = {s.url for s in all_sources}
                            for s in sources:
                                if s.url not in seen_urls:
                                    all_sources.append(s)
                                    seen_urls.add(s.url)
                            tool_log["sources_found"] = len(sources)

                        except Exception as e:
                            result = {"error": str(e)}
                            tool_info.error = str(e)
                            tool_log["error"] = str(e)
                            truncated = json.dumps(result, ensure_ascii=False)
                    else:
                        result = {"error": f"Funcao {function_name} nao encontrada"}
                        tool_info.error = result["error"]
                        tool_log["error"] = result["error"]
                        truncated = json.dumps(result, ensure_ascii=False)

                    all_tool_calls.append(tool_info)
                    iter_log["tool_calls"].append(tool_log)
                    openai_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": truncated,
                        }
                    )

                iter_log["elapsed_ms"] = round((time.time() - iter_start) * 1000)
                log["iterations"].append(iter_log)
                log["timing_ms"]["per_iteration"].append(iter_log["elapsed_ms"])

            # --- Max iterations atingido ---
            self._session_prompt_tokens += call_prompt_tokens
            self._session_completion_tokens += call_completion_tokens
            response_time = (time.time() - start_time) * 1000

            usage = TokenUsage(
                prompt_tokens=call_prompt_tokens,
                completion_tokens=call_completion_tokens,
                total_tokens=call_prompt_tokens + call_completion_tokens,
                estimated_cost_usd=self._calculate_cost(
                    call_prompt_tokens, call_completion_tokens
                ),
            )
            unique_domains = sorted(
                {d for s in all_sources for d in [_extract_domain(s.url)] if d}
            )
            log["output"] = {
                "finish_reason": "max_iterations",
                "sources_count": len(all_sources),
                "total_tool_calls": len(all_tool_calls),
                "tool_call_sequence": [tc.name for tc in all_tool_calls],
                "tools_used": list(dict.fromkeys(tc.name for tc in all_tool_calls)),
                "sources_detail": [
                    {"title": s.title, "url": s.url, "domain": _extract_domain(s.url)}
                    for s in all_sources
                ],
                "unique_domains_consulted": unique_domains,
            }
            log["usage"] = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "estimated_cost_usd": usage.estimated_cost_usd,
            }
            log["timing_ms"]["total"] = round(response_time)
            log["timing_ms"]["llm_total"] = total_llm_ms
            log["timing_ms"]["tools_total"] = total_tools_ms
            self._write_log(log)

            return ChatResponse(
                message=Message(
                    role="assistant",
                    content="Atingi o limite de iteracoes. Por favor, reformule a tua pergunta.",
                ),
                sources=all_sources,
                tool_calls=all_tool_calls,
                response_time_ms=response_time,
                usage=usage,
                execution_log=log,
            )

        except Exception as e:
            self._session_prompt_tokens += call_prompt_tokens
            self._session_completion_tokens += call_completion_tokens
            response_time = (time.time() - start_time) * 1000

            usage = TokenUsage(
                prompt_tokens=call_prompt_tokens,
                completion_tokens=call_completion_tokens,
                total_tokens=call_prompt_tokens + call_completion_tokens,
                estimated_cost_usd=self._calculate_cost(
                    call_prompt_tokens, call_completion_tokens
                ),
            )
            log["output"] = {"finish_reason": "error", "error": str(e)}
            log["usage"] = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "estimated_cost_usd": usage.estimated_cost_usd,
            }
            log["timing_ms"]["total"] = round(response_time)
            log["timing_ms"]["llm_total"] = total_llm_ms
            log["timing_ms"]["tools_total"] = total_tools_ms
            self._write_log(log)

            return ChatResponse(
                message=Message(
                    role="assistant",
                    content=f"Erro ao processar a solicitacao: {str(e)}",
                ),
                sources=all_sources,
                tool_calls=all_tool_calls,
                response_time_ms=response_time,
                usage=usage,
                execution_log=log,
            )

    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """Executa uma tool síncrona numa thread separada para não bloquear o event loop."""
        func = self.tool_functions[name]
        return await asyncio.to_thread(func, **args)

    def _extract_sources(self, result: Dict[str, Any]) -> List[Source]:
        sources = []
        if "results" in result and isinstance(result["results"], list):
            for item in result["results"]:
                if isinstance(item, dict):
                    sources.append(
                        Source(
                            title=item.get("title", "Fonte"),
                            url=item.get("url", ""),
                            snippet=item.get("content", "")[:200],
                        )
                    )
        if "sources" in result and isinstance(result["sources"], list):
            for item in result["sources"]:
                if isinstance(item, dict):
                    sources.append(
                        Source(
                            title=item.get("title", "Fonte"),
                            url=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                        )
                    )
        return sources


agent = LaborLawAgent()
