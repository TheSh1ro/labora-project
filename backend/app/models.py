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

    messages: List[Message]
    stream: bool = False


class Source(BaseModel):
    """Fonte de informação."""

    title: str
    url: str
    snippet: Optional[str] = None


class ToolCallInfo(BaseModel):
    """Informação sobre uma tool call."""

    name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None
    error: Optional[str] = None


class ChatResponse(BaseModel):
    """Response do endpoint de chat."""

    message: Message
    sources: List[Source] = Field(default_factory=list)
    tool_calls: List[ToolCallInfo] = Field(default_factory=list)
    response_time_ms: float


class EvaluationCase(BaseModel):
    """Caso de teste para avaliação."""

    id: str
    question: str
    category: Literal["básico", "intermédio", "avançado", "limite"]
    expected_topics: List[str]
    requires_calculation: bool = False
    requires_citation: bool = True


class EvaluationResult(BaseModel):
    """Resultado de um caso de teste."""

    case: EvaluationCase
    response: str
    sources: List[Source]
    tool_calls: List[ToolCallInfo]
    correctness_score: float  # 0-1
    citation_score: float  # 0-1
    refusal_score: float  # 0-1 (1 = recusou apropriadamente)
    response_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class EvaluationSummary(BaseModel):
    """Resumo da avaliação."""

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
