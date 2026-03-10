"""
FastAPI Backend - Agente Q&A de Direito Laboral Português
"""

import os
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from .models import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    EvaluationSummary,
    EvaluationCase,
)
from .agent import agent
from .evaluation import evaluation_harness

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    print("🚀 Iniciando Agente de Direito Laboral Português...")
    yield
    # Shutdown
    print("👋 Encerrando servidor...")


# Create FastAPI app
app = FastAPI(
    title="Agente Q&A de Direito Laboral Português",
    description="Agente conversacional para responder questões sobre direito laboral e processamento salarial português",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Endpoint raiz - health check."""
    return HealthResponse(status="online")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="healthy")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal de chat.

    Recebe uma lista de mensagens e retorna a resposta do agente.
    """
    try:
        response = await agent.chat(messages=request.messages, stream=request.stream)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Endpoint de chat com streaming (simplificado - não implementado).
    """
    # Para simplificar, retornamos a resposta completa
    # Em uma implementação completa, usaríamos SSE ou WebSockets
    response = await agent.chat(messages=request.messages, stream=False)

    async def generate():
        yield f"data: {response.message.content}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/evaluation/cases", response_model=List[EvaluationCase])
async def get_evaluation_cases():
    """
    Retorna a lista de casos de teste disponíveis.
    """
    return evaluation_harness.test_cases


@app.post("/evaluation/run", response_model=EvaluationSummary)
async def run_evaluation(case_ids: Optional[List[str]] = None):
    """
    Executa a suite de avaliação.

    Args:
        case_ids: IDs dos casos a executar (None = todos)

    Returns:
        Resumo da avaliação com métricas
    """
    try:
        summary = await evaluation_harness.run_evaluation(selected_cases=case_ids)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na avaliação: {str(e)}")


@app.get("/tools")
async def list_tools():
    """
    Lista as tools disponíveis no agente.
    """
    from .tools import TOOLS_SCHEMA

    return {"tools": TOOLS_SCHEMA}


@app.get("/sources")
async def list_sources():
    """
    Lista as fontes oficiais consultadas pelo agente.
    """
    return {
        "sources": [
            {
                "name": "Código do Trabalho",
                "url": "https://portal.act.gov.pt",
                "description": "Código do Trabalho consolidado atualizado",
            },
            {
                "name": "Portal das Finanças - IRS",
                "url": "https://info.portaldasfinancas.gov.pt",
                "description": "Tabelas de retenção na fonte de IRS",
            },
            {
                "name": "Segurança Social",
                "url": "https://www.seg-social.pt",
                "description": "Informações sobre TSU e contribuições",
            },
            {
                "name": "Diário da República",
                "url": "https://diariodarepublica.pt",
                "description": "Legislação oficial portuguesa",
            },
            {
                "name": "CITE",
                "url": "https://www.cite.gov.pt",
                "description": "Comissão para a Igualdade no Trabalho e no Emprego",
            },
        ]
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
