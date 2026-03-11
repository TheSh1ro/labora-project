# backend\app\evaluation.py

"""
Suite de Avaliação do Agente de Direito Laboral.
Implementa casos de teste e métricas de qualidade.
"""

import re
import time
from typing import List, Dict, Any

from .agent import agent
from .models import EvaluationCase, EvaluationResult, EvaluationSummary, Message

TEST_CASES: List[EvaluationCase] = [
    # Básico
    EvaluationCase(
        id="basic_001",
        question="Qual é o salário mínimo nacional atual em Portugal?",
        category="básico",
        expected_topics=["salário mínimo", "870", "2025"],
        requires_citation=True,
    ),
    EvaluationCase(
        id="basic_002",
        question="A quantos dias de férias tem direito um trabalhador a tempo inteiro?",
        category="básico",
        expected_topics=["22 dias", "férias", "direito"],
        requires_citation=True,
    ),
    # Intermédio
    EvaluationCase(
        id="intermediate_001",
        question="Como se calcula o subsídio de férias para um trabalhador que ganha 1.500 EUR/mês?",
        category="intermédio",
        expected_topics=["subsídio", "férias", "cálculo", "1500", "fórmula"],
        requires_calculation=True,
        requires_citation=True,
    ),
    EvaluationCase(
        id="intermediate_002",
        question="Quais são as taxas de contribuição TSU do empregador e do trabalhador num contrato sem termo?",
        category="intermédio",
        expected_topics=["TSU", "23.75%", "11%", "empregador", "trabalhador"],
        requires_citation=True,
    ),
    EvaluationCase(
        id="intermediate_003",
        question="Que prazo de aviso prévio é necessário para despedir um trabalhador com 3 anos de antiguidade?",
        category="intermédio",
        expected_topics=["aviso prévio", "30 dias", "antiguidade", "despedimento"],
        requires_citation=True,
    ),
    # Avançado
    EvaluationCase(
        id="advanced_001",
        question="Como difere o cálculo do subsídio de Natal para um trabalhador contratado a meio do ano?",
        category="avançado",
        expected_topics=["subsídio de Natal", "proporcional", "cálculo", "meses"],
        requires_calculation=True,
        requires_citation=True,
    ),
    EvaluationCase(
        id="advanced_002",
        question="Quais as taxas de retenção na fonte de IRS para um contribuinte solteiro com 2.200 EUR brutos/mês em 2024?",
        category="avançado",
        expected_topics=["IRS", "retenção", "taxa", "solteiro", "2200"],
        requires_calculation=True,
        requires_citation=True,
    ),
    EvaluationCase(
        id="advanced_003",
        question="Em que condições pode um empregador implementar lay-off ao abrigo da lei portuguesa?",
        category="avançado",
        expected_topics=["lay-off", "condições", "crise", "dificuldades"],
        requires_citation=True,
    ),
    # Limite
    EvaluationCase(
        id="limit_001",
        question="A minha empresa está em Portugal mas o trabalhador trabalha remotamente a partir de Espanha. Qual a lei laboral aplicável?",
        category="limite",
        expected_topics=["teletrabalho", "internacional", "Espanha", "lei aplicável"],
        requires_citation=True,
    ),
    EvaluationCase(
        id="limit_002",
        question="É legal incluir uma cláusula de não concorrência de 3 anos num contrato de trabalho português?",
        category="limite",
        expected_topics=["não concorrência", "cláusula", "3 anos", "legalidade"],
        requires_citation=True,
    ),
    # Casos adicionais
    EvaluationCase(
        id="extra_001",
        question="Quanto recebe de subsídio de Natal um trabalhador com salário de 2000€ contratado em julho?",
        category="intermédio",
        expected_topics=["subsídio de Natal", "proporcional", "2000", "6 meses"],
        requires_calculation=True,
        requires_citation=True,
    ),
    EvaluationCase(
        id="extra_002",
        question="Qual o valor líquido mensal de um trabalhador que ganha 1800€ brutos?",
        category="intermédio",
        expected_topics=["líquido", "TSU", "IRS", "1800"],
        requires_calculation=True,
        requires_citation=True,
    ),
]


def _normalize(text: str) -> str:
    """
    Normaliza separadores decimais e de milhar para comparação de tópicos.
    Ex: "1.500 €" -> "1500 €", "23,75%" -> "23.75%"
    """
    text = re.sub(r"(\d)\.(\d{3})", r"\1\2", text)
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)
    return text


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

        # Calcula métricas agregadas
        return self._calculate_summary(results)

    async def _evaluate_case(self, case: EvaluationCase) -> EvaluationResult:
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
        correctness = self._evaluate_correctness(
            response.message.content, case.expected_topics
        )

        # Avalia citações
        citation = self._evaluate_citations(response.sources, case.requires_citation)

        # Avalia recusa graciosa
        refusal = self._evaluate_refusal(response.message.content, case)

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

    def _evaluate_correctness(self, response: str, expected_topics: List[str]) -> float:
        """
        Avalia corretude heurística baseada em tópicos esperados.
        Normaliza separadores decimais e de milhar antes de comparar,
        para evitar falsos negativos entre "23.75%" (tópico) e "23,75%" (resposta).

        Returns:
            Score entre 0 e 1
        """
        if not response:
            return 0.0

        response_normalized = _normalize(response.lower())
        matches = 0

        for topic in expected_topics:
            topic_normalized = _normalize(topic.lower())
            if topic_normalized in response_normalized:
                matches += 1

        return matches / len(expected_topics) if expected_topics else 0.5

    def _evaluate_citations(self, sources: List[Any], required: bool) -> float:
        """
        Avalia qualidade das citações.

        Returns:
            Score entre 0 e 1
        """
        if not required:
            return 1.0

        if not sources:
            return 0.0

        # Pontua baseado no número de fontes
        num_sources = len(sources)
        if num_sources >= 2:
            return 1.0
        elif num_sources == 1:
            return 0.7
        else:
            return 0.3

    def _evaluate_refusal(self, response: str, case: "EvaluationCase") -> float:
        """
        Avalia comportamento apropriado face à pergunta:
        - Casos "limite": pontuação alta se o agente recusar ou adicionar caveats epistémicos.
        - Outros casos: pontuação alta se o agente responder com base legal fundamentada.

        A lógica anterior penalizava respostas corretas (com "artigo", "lei") e premiava
        recusas indiscriminadas — o inverso do comportamento desejado para casos normais.

        Returns:
            Score entre 0 e 1
        """
        response_lower = response.lower()

        # Indicadores de recusa ou incerteza epistémica
        refusal_indicators = [
            "não tenho certeza",
            "não posso confirmar",
            "não tenho informação",
            "recomendo consultar",
            "aconselho a consultar",
            "fora do meu âmbito",
            "não posso ajudar",
            "advogado",
            "jurista",
        ]

        # Indicadores de resposta fundamentada em base legal
        grounded_indicators = [
            "segundo",
            "de acordo",
            "conforme",
            "artigo",
            "código",
            "lei",
            "portaria",
            "decreto",
        ]

        has_refusal = any(ind in response_lower for ind in refusal_indicators)
        has_grounded = any(ind in response_lower for ind in grounded_indicators)

        if case.category == "limite":
            # Para casos limite: esperamos recusa ou caveats com recomendação de especialista.
            if has_refusal:
                return 1.0
            elif has_grounded:
                # Respondeu com base legal mas sem humildade epistémica — parcialmente aceitável.
                return 0.5
            else:
                return 0.2
        else:
            # Para casos normais: esperamos resposta fundamentada, não recusa.
            if has_grounded and not has_refusal:
                return 1.0
            elif has_grounded and has_refusal:
                # Respondeu com base legal mas com incerteza excessiva — ok, não ideal.
                return 0.7
            elif has_refusal and not has_grounded:
                # Recusou quando não devia — falha.
                return 0.0
            else:
                return 0.4

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


# Instância global
evaluation_harness = EvaluationHarness()
