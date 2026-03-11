# backend\app\evaluation\harness.py

"""
Harness de avaliação do agente de direito laboral.
"""

import asyncio
import time
from typing import List, Dict, Any

from ..agent import agent
from ..models import EvaluationResult, EvaluationSummary, Message

from .cases import (
    TEST_CASES,
    _evaluate_correctness,
    _evaluate_citations,
    _evaluate_refusal,
)


class EvaluationHarness:
    """Harness para executar avaliações do agente."""

    def __init__(self):
        self.test_cases = TEST_CASES

    async def run_evaluation(
        self, selected_cases: List[str] = None
    ) -> EvaluationSummary:
        """
        Executa a suite de avaliação.

        Args:
            selected_cases: IDs dos casos a executar (None = todos)

        Returns:
            Resumo da avaliação com métricas
        """
        cases = self.test_cases
        if selected_cases:
            cases = [c for c in cases if c.id in selected_cases]

        results: List[EvaluationResult] = []

        for case in cases:
            result = await self._evaluate_case(case)
            results.append(result)
            await asyncio.sleep(2)  # evita 429 em cascata

        # Calcula métricas agregadas
        return self._calculate_summary(results)

    async def _evaluate_case(self, case) -> EvaluationResult:
        """Avalia um caso de teste individual."""
        start_time = time.time()

        # Reinicia a sessão para isolar cada caso de teste (evita contaminação de contexto)
        agent.reset_session()

        # Executa o agente — passa um único Message, como esperado pela assinatura de chat()
        response = await agent.chat(
            user_message=Message(role="user", content=case.question)
        )

        response_time = (time.time() - start_time) * 1000

        # Avalia corretude (heurística simples)
        correctness = _evaluate_correctness(
            response.message.content, case.expected_topics
        )

        # Avalia citações
        citation = _evaluate_citations(response.sources, case.requires_citation)

        # Avalia recusa graciosa
        refusal = _evaluate_refusal(response.message.content, case)

        return EvaluationResult(
            case=case,
            response=response.message.content,
            sources=response.sources,
            tool_calls=response.tool_calls,
            correctness_score=correctness,
            citation_score=citation,
            refusal_score=refusal,
            response_time_ms=response_time,
        )

    def _calculate_summary(self, results: List[EvaluationResult]) -> EvaluationSummary:
        """Calcula métricas agregadas da avaliação."""
        if not results:
            return EvaluationSummary(
                total_cases=0,
                avg_correctness=0.0,
                avg_citation=0.0,
                avg_refusal=0.0,
                avg_response_time_ms=0.0,
                results_by_category={},
                detailed_results=[],
            )

        # Médias gerais
        avg_correctness = sum(r.correctness_score for r in results) / len(results)
        avg_citation = sum(r.citation_score for r in results) / len(results)
        avg_refusal = sum(r.refusal_score for r in results) / len(results)
        avg_response_time = sum(r.response_time_ms for r in results) / len(results)

        # Métricas por categoria
        by_category: Dict[str, List[EvaluationResult]] = {}
        for r in results:
            cat = r.case.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(r)

        results_by_category = {}
        for cat, cat_results in by_category.items():
            results_by_category[cat] = {
                "count": len(cat_results),
                "avg_correctness": sum(r.correctness_score for r in cat_results)
                / len(cat_results),
                "avg_citation": sum(r.citation_score for r in cat_results)
                / len(cat_results),
                "avg_response_time_ms": sum(r.response_time_ms for r in cat_results)
                / len(cat_results),
            }

        return EvaluationSummary(
            total_cases=len(results),
            avg_correctness=round(avg_correctness, 3),
            avg_citation=round(avg_citation, 3),
            avg_refusal=round(avg_refusal, 3),
            avg_response_time_ms=round(avg_response_time, 2),
            results_by_category=results_by_category,
            detailed_results=results,
        )
