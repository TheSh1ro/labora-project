# backend\app\main.py

"""
FastAPI Backend - Agente Q&A de Direito Laboral Português
"""

import json
import os
from pathlib import Path
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
    TokenUsage,
)
from .agent import agent
from .evaluation import evaluation_harness

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    print("Iniciando Agente de Direito Laboral Português...")
    yield
    # Shutdown
    print("Encerrando servidor...")


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

    Recebe a nova mensagem do utilizador e devolve a resposta do agente.
    O histórico da conversa é mantido no servidor até DELETE /session.
    """
    try:
        response = await agent.chat(user_message=request.message, stream=request.stream)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")


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


@app.get("/agent/info")
async def agent_info():
    """Retorna informacoes sobre o agente e modelo em uso."""
    from .agent import AGENT_CONFIG

    return AGENT_CONFIG


@app.get("/agent/usage", response_model=TokenUsage)
async def agent_usage():
    """Retorna o consumo acumulado de tokens e custo estimado da sessao."""
    return agent.get_session_usage()


@app.delete("/session")
async def reset_session():
    """
    Inicia uma nova conversa: limpa o histórico de mensagens da sessão activa.
    Os contadores de tokens acumulados são preservados até ao reinício do servidor.
    """
    agent.reset_session()
    return {"status": "reset"}


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


@app.get("/logs")
async def list_logs():
    """Lista os logs de execução disponíveis."""
    logs_dir = Path(__file__).parent.parent / "logs"
    if not logs_dir.exists():
        return {"logs": []}
    files = sorted(logs_dir.glob("*.json"), reverse=True)[:50]  # últimos 50
    return {
        "logs": [f.stem for f in files],
        "count": len(files),
        "logs_dir": str(logs_dir),
    }


@app.get("/logs/{request_id}")
async def get_log(request_id: str):
    logs_dir = Path(__file__).parent.parent / "logs"
    matches = list(logs_dir.glob(f"*{request_id}*.json"))
    if not matches:
        raise HTTPException(
            status_code=404, detail=f"Log '{request_id}' não encontrado"
        )
    with open(matches[0], encoding="utf-8") as f:
        return json.load(f)


@app.delete("/logs")
async def clear_logs():
    logs_dir = Path(__file__).parent.parent / "logs"
    count = sum(1 for f in logs_dir.glob("*.json") if f.unlink() or True)
    return {"deleted": count}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
