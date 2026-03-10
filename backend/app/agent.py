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
from .models import Message, Source, ToolCallInfo, ChatResponse

# Inicializa cliente Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
openai_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Modelo a usar
MODEL = "llama-3.3-70b-versatile"

# Configuração do agente — derivada do MODEL, sem duplicação
AGENT_CONFIG = {
    "model": MODEL,
    "provider": "Groq",
    "provider_url": "https://groq.com",
    "framework": MODEL,
    "tool_calling": True,
    "max_iterations": 5,
    "temperature": 0.3,
    "features": ["tool_calling", "web_search", "citations", "calculations"],
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
- Termina sempre com uma secção "📚 Fontes" listando as referências
"""


class LaborLawAgent:
    """Agente de Direito Laboral com tool calling."""

    def __init__(self):
        self.client = openai_client
        self.model = MODEL
        self.tools = TOOLS_SCHEMA
        self.tool_functions = TOOL_FUNCTIONS

    async def chat(self, messages: List[Message], stream: bool = False) -> ChatResponse:
        """
        Processa uma conversação com o agente.

        Args:
            messages: Lista de mensagens
            stream: Se deve fazer streaming da resposta

        Returns:
            Resposta do agente com fontes e tool calls
        """
        start_time = time.time()

        if not self.client:
            return ChatResponse(
                message=Message(
                    role="assistant",
                    content="❌ Erro: Groq API key não configurada. Por favor, configure a variável de ambiente GROQ_API_KEY.",
                ),
                sources=[],
                tool_calls=[],
                response_time_ms=(time.time() - start_time) * 1000,
            )

        # Prepara mensagens para OpenAI
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
                # Chama Groq com tools
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=openai_messages,
                    tools=self.tools,
                    tool_choice="auto",
                    parallel_tool_calls=False,  # Evita problemas no free tier do Groq
                    temperature=0.3,
                    max_tokens=2000,
                )

                message = response.choices[0].message

                # Se não há tool calls, retorna a resposta
                if not message.tool_calls:
                    response_time = (time.time() - start_time) * 1000
                    return ChatResponse(
                        message=Message(
                            role="assistant",
                            content=message.content
                            or "Não foi possível gerar uma resposta.",
                        ),
                        sources=all_sources,
                        tool_calls=all_tool_calls,
                        response_time_ms=response_time,
                    )

                # Processa tool calls
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

                    # Registra a tool call
                    tool_info = ToolCallInfo(
                        name=function_name, arguments=function_args
                    )

                    # Executa a função
                    if function_name in self.tool_functions:
                        try:
                            result = await self._execute_tool(
                                function_name, function_args
                            )
                            tool_info.result = json.dumps(result, ensure_ascii=False)[
                                :500
                            ]  # Limita tamanho

                            # Extrai fontes dos resultados
                            sources = self._extract_sources(result)
                            all_sources.extend(sources)

                        except Exception as e:
                            result = {"error": str(e)}
                            tool_info.error = str(e)
                    else:
                        result = {"error": f"Função {function_name} não encontrada"}
                        tool_info.error = result["error"]

                    all_tool_calls.append(tool_info)

                    # Adiciona resultado às mensagens
                    openai_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )

            # Se atingiu o máximo de iterações, retorna o que tem
            response_time = (time.time() - start_time) * 1000
            return ChatResponse(
                message=Message(
                    role="assistant",
                    content="⚠️ Atingi o limite de iterações. Por favor, reformule a tua pergunta.",
                ),
                sources=all_sources,
                tool_calls=all_tool_calls,
                response_time_ms=response_time,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ChatResponse(
                message=Message(
                    role="assistant",
                    content=f"❌ Erro ao processar a solicitação: {str(e)}",
                ),
                sources=all_sources,
                tool_calls=all_tool_calls,
                response_time_ms=response_time,
            )

    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """Executa uma tool de forma assíncrona."""
        func = self.tool_functions[name]
        # As funções são síncronas, mas podemos executá-las
        return func(**args)

    def _extract_sources(self, result: Dict[str, Any]) -> List[Source]:
        """Extrai fontes do resultado de uma tool."""
        sources = []

        # Extrai de 'results' (Tavily)
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

        # Extrai de 'sources'
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


# Instância global do agente
agent = LaborLawAgent()
