"""
Agente Conversacional de Direito Laboral Português.
Implementa tool calling com Groq (llama-3.3-70b-versatile).
"""

import os
import json
import time
from typing import List, Dict, Any
from groq import AsyncGroq

from .tools import TOOLS_SCHEMA, TOOL_FUNCTIONS
from .models import Message, Source, ToolCallInfo, ChatResponse, TokenUsage

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
openai_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

MODEL = "llama-3.3-70b-versatile"

PRICING = {
    "prompt": 0.59 / 1_000_000,
    "completion": 0.79 / 1_000_000,
}

AGENT_CONFIG = {
    "model": MODEL,
    "provider": "Groq",
    "provider_url": "https://groq.com",
    "display_name": "LLaMA 3.3 70B",
    "tool_calling": True,
    "max_iterations": 5,
    "temperature": 0.3,
    "features": ["tool_calling", "web_search", "citations", "calculations"],
    "pricing_usd_per_1m": {
        "prompt": 0.59,
        "completion": 0.79,
    },
}

# System prompt
SYSTEM_PROMPT = """Tu és um Agente de Direito Laboral Português especializado. A tua função é responder a questões sobre direito laboral e processamento salarial em Portugal com precisão factual.

DIRETRIZES:
1. Sê preciso e factual - o direito laboral exige exatidão
2. Cita sempre as fontes oficiais (Portal das Finanças, CITE, DRE, Código do Trabalho)
3. Usa as tools disponíveis para obter informações atualizadas
4. Quando não tiveres certeza, recusa graciosamente em vez de inventar
5. Para cálculos, mostra sempre a fórmula e o passo a passo
6. Responde em português europeu
7. Estrutura as respostas de forma clara com markdown

TOOLS DISPONÍVEIS:
- search_labor_law: Pesquisa no Código do Trabalho
- search_irs_tables: Consulta tabelas de retenção IRS
- search_social_security: Pesquisa TSU e Segurança Social
- calculate_vacation_subsidy: Calcula subsídio de férias
- calculate_christmas_subsidy: Calcula subsídio de Natal
- get_minimum_wage: Retorna salário mínimo nacional
- calculate_tsu: Calcula contribuições TSU

QUANDO RECUSAR:
- Questões fora do âmbito do direito laboral português
- Situações que requerem aconselhamento jurídico personalizado
- Questões sobre outros países sem relação com Portugal
- Questões ambíguas onde não podes ter certeza da resposta

FORMATO DAS RESPOSTAS:
- Responde diretamente à pergunta
- Inclui cálculos detalhados quando aplicável
- Termina sempre com uma secção "📚 Fontes" listando o link das referências usadas
"""


class LaborLawAgent:
    """Agente de Direito Laboral com tool calling."""

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

    async def chat(self, messages: List[Message], stream: bool = False) -> ChatResponse:
        start_time = time.time()

        call_prompt_tokens = 0
        call_completion_tokens = 0

        if not self.client:
            return ChatResponse(
                message=Message(
                    role="assistant",
                    content="Erro: Groq API key nao configurada.",
                ),
                sources=[],
                tool_calls=[],
                response_time_ms=(time.time() - start_time) * 1000,
                usage=TokenUsage(),
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
        max_iterations = 5

        try:
            for iteration in range(max_iterations):
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=openai_messages,
                    tools=self.tools,
                    tool_choice="auto",
                    parallel_tool_calls=False,  # Evita problemas no free tier do Groq
                    temperature=0.3,
                    max_tokens=2000,
                )

                if response.usage:
                    call_prompt_tokens += response.usage.prompt_tokens
                    call_completion_tokens += response.usage.completion_tokens

                message = response.choices[0].message

                if not message.tool_calls:
                    self._session_prompt_tokens += call_prompt_tokens
                    self._session_completion_tokens += call_completion_tokens

                    response_time = (time.time() - start_time) * 1000
                    return ChatResponse(
                        message=Message(
                            role="assistant",
                            content=message.content
                            or "Nao foi possivel gerar uma resposta.",
                        ),
                        sources=all_sources,
                        tool_calls=all_tool_calls,
                        response_time_ms=response_time,
                        usage=TokenUsage(
                            prompt_tokens=call_prompt_tokens,
                            completion_tokens=call_completion_tokens,
                            total_tokens=call_prompt_tokens + call_completion_tokens,
                            estimated_cost_usd=self._calculate_cost(
                                call_prompt_tokens, call_completion_tokens
                            ),
                        ),
                    )

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

                    if function_name in self.tool_functions:
                        try:
                            result = await self._execute_tool(
                                function_name, function_args
                            )
                            tool_info.result = json.dumps(result, ensure_ascii=False)[
                                :500
                            ]
                            sources = self._extract_sources(result)
                            all_sources.extend(sources)
                        except Exception as e:
                            result = {"error": str(e)}
                            tool_info.error = str(e)
                    else:
                        result = {"error": f"Funcao {function_name} nao encontrada"}
                        tool_info.error = result["error"]

                    all_tool_calls.append(tool_info)
                    openai_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )

            self._session_prompt_tokens += call_prompt_tokens
            self._session_completion_tokens += call_completion_tokens

            response_time = (time.time() - start_time) * 1000
            return ChatResponse(
                message=Message(
                    role="assistant",
                    content="Atingi o limite de iteracoes. Por favor, reformule a tua pergunta.",
                ),
                sources=all_sources,
                tool_calls=all_tool_calls,
                response_time_ms=response_time,
                usage=TokenUsage(
                    prompt_tokens=call_prompt_tokens,
                    completion_tokens=call_completion_tokens,
                    total_tokens=call_prompt_tokens + call_completion_tokens,
                    estimated_cost_usd=self._calculate_cost(
                        call_prompt_tokens, call_completion_tokens
                    ),
                ),
            )

        except Exception as e:
            self._session_prompt_tokens += call_prompt_tokens
            self._session_completion_tokens += call_completion_tokens

            response_time = (time.time() - start_time) * 1000
            return ChatResponse(
                message=Message(
                    role="assistant",
                    content=f"Erro ao processar a solicitacao: {str(e)}",
                ),
                sources=all_sources,
                tool_calls=all_tool_calls,
                response_time_ms=response_time,
                usage=TokenUsage(
                    prompt_tokens=call_prompt_tokens,
                    completion_tokens=call_completion_tokens,
                    total_tokens=call_prompt_tokens + call_completion_tokens,
                    estimated_cost_usd=self._calculate_cost(
                        call_prompt_tokens, call_completion_tokens
                    ),
                ),
            )

    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> Any:
        func = self.tool_functions[name]
        return func(**args)

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
