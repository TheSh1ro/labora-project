# backend\app\models.py

"""
Modelos Pydantic para o agente de direito laboral.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    """Mensagem no chat."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class ChatRequest(BaseModel):
    """Request para o endpoint de chat."""

    message: Message


class Source(BaseModel):
    """Fonte de informação."""

    title: str
    url: str
    snippet: Optional[str] = None
    relevance_score: float = 0.0
    is_current: bool = True


class ToolCallInfo(BaseModel):
    """Informação sobre uma tool call."""

    name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None
    error: Optional[str] = None


class TokenUsage(BaseModel):
    """Uso de tokens e custo estimado por chamada."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class ChatResponse(BaseModel):
    """Response do endpoint de chat."""

    message: Message
    sources: List[Source] = Field(default_factory=list)
    all_sources: List[Source] = Field(
        default_factory=list,
        description="Todas as fontes retornadas pelas tools (após dedup/rerank), incluindo as não citadas",
    )
    tool_calls: List[ToolCallInfo] = Field(default_factory=list)
    response_time_ms: float
    usage: TokenUsage = Field(default_factory=TokenUsage)
    execution_log: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Wide event estruturado da execução — disponível para copy no frontend",
    )


class EvaluationCase(BaseModel):
    """Caso de teste para avaliação."""

    id: str
    question: str
    category: Literal["Basic", "Medium", "Advanced", "Limit"]
    expected_topics: List[str]
    requires_calculation: bool = False
    requires_citation: bool = True


class EvaluationResult(BaseModel):
    """Resultado de um caso de teste."""

    case: EvaluationCase
    response: str
    sources: List[Source]
    tool_calls: List[ToolCallInfo]
    correctness_score: float
    citation_score: float
    refusal_score: float
    response_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class EvaluationSummary(BaseModel):
    """Resumo da avaliacao."""

    total_cases: int
    avg_correctness: float
    avg_citation: float
    avg_refusal: float
    avg_response_time_ms: float
    results_by_category: Dict[str, Dict[str, float]]
    detailed_results: List[EvaluationResult]
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Response do health check."""

    status: str
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.now)
