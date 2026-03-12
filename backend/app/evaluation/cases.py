# backend\app\evaluation\cases.py

"""
Casos de teste e funções de avaliação para o agente.
"""

import re
from typing import List, Any

from ..models import EvaluationCase


TEST_CASES: List[EvaluationCase] = [
    EvaluationCase(
        id="basic_001",
        question="Qual é o salário mínimo nacional atual em Portugal?",
        category="Basic",
        expected_topics=["salário mínimo", "870", "2025"],
        requires_citation=True,
    ),
    EvaluationCase(
        id="basic_002",
        question="A quantos dias de férias tem direito um trabalhador a tempo inteiro?",
        category="Basic",
        expected_topics=["22 dias", "férias", "direito"],
        requires_citation=True,
    ),
    EvaluationCase(
        id="intermediate_001",
        question="Como se calcula o subsídio de férias para um trabalhador que ganha 1.500 EUR/mês?",
        category="Medium",
        expected_topics=["subsídio", "férias", "cálculo", "1500", "fórmula"],
        requires_calculation=True,
        requires_citation=True,
    ),
    EvaluationCase(
        id="intermediate_002",
        question="Quais são as taxas de contribuição TSU do empregador e do trabalhador num contrato sem termo?",
        category="Medium",
        expected_topics=["TSU", "23.75%", "11%", "empregador", "trabalhador"],
        requires_citation=True,
    ),
    EvaluationCase(
        id="intermediate_003",
        question="Que prazo de aviso prévio é necessário para despedir um trabalhador com 3 anos de antiguidade?",
        category="Medium",
        expected_topics=["aviso prévio", "30 dias", "antiguidade", "despedimento"],
        requires_citation=True,
    ),
    EvaluationCase(
        id="advanced_001",
        question="Como difere o cálculo do subsídio de Natal para um trabalhador contratado a meio do ano?",
        category="Advanced",
        expected_topics=["subsídio de Natal", "proporcional", "cálculo", "meses"],
        requires_calculation=True,
        requires_citation=True,
    ),
    EvaluationCase(
        id="advanced_002",
        question="Quais as taxas de retenção na fonte de IRS para um contribuinte solteiro com 2.200 EUR brutos/mês em 2024?",
        category="Advanced",
        expected_topics=["IRS", "retenção", "taxa", "solteiro", "2200"],
        requires_calculation=True,
        requires_citation=True,
    ),
    EvaluationCase(
        id="advanced_003",
        question="Em que condições pode um empregador implementar lay-off ao abrigo da lei portuguesa?",
        category="Advanced",
        expected_topics=["lay-off", "condições", "mercado", "trabalhadores"],
        requires_citation=True,
    ),
    EvaluationCase(
        id="limit_001",
        question="A minha empresa está em Portugal mas o trabalhador trabalha remotamente a partir de Espanha. Qual a lei laboral aplicável?",
        category="Limit",
        expected_topics=["teletrabalho", "internacional", "Espanha", "legislação"],
        requires_citation=True,
    ),
    EvaluationCase(
        id="limit_002",
        question="É legal incluir uma cláusula de não concorrência de 3 anos num contrato de trabalho português?",
        category="Limit",
        expected_topics=["não concorrência", "cláusula", "3 anos", "nula"],
        requires_citation=True,
    ),
    EvaluationCase(
        id="limit_003",
        question=(
            "A minha empresa está em Portugal e o trabalhador está a ser despedido. "
            "Ele trabalha remotamente a partir de Espanha. "
            "1) Qual a lei laboral aplicável? "
            "2) A cláusula de não concorrência de 2 anos é válida em Espanha? "
            "3) Que compensação lhe é devida ao abrigo da lei portuguesa?"
        ),
        category="Limit",
        expected_topics=[
            "compensação",
            "fora do âmbito",
            "advogado",
            "código do trabalho",
        ],
        requires_citation=True,
    ),
    EvaluationCase(
        id="extra_001",
        question="Quanto recebe de subsídio de Natal um trabalhador com salário de 2000€ contratado em julho?",
        category="Medium",
        expected_topics=["subsídio de Natal", "proporcional", "2000", "1000"],
        requires_calculation=True,
        requires_citation=True,
    ),
    EvaluationCase(
        id="extra_002",
        question="Qual o valor líquido mensal de um trabalhador que ganha 1800€ brutos?",
        category="Medium",
        expected_topics=["líquido", "TSU", "IRS", "1800"],
        requires_calculation=True,
        requires_citation=True,
    ),
]


def _normalize(text: str) -> str:
    """
    Normaliza separadores decimais, de milhar e símbolo de moeda para
    comparação de tópicos.

    Transformações:
      "1.500" → "1500", "23,75" → "23.75", "€1800" / "1800€" → "1800"
    """
    text = re.sub(r"(\d)\.(\d{3})", r"\1\2", text)
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)
    text = re.sub(r"€\s*(\d)", r"\1", text)
    text = re.sub(r"(\d)\s*€", r"\1", text)
    return text


def _evaluate_correctness(response: str, expected_topics: List[str]) -> float:
    """
    Avalia corretude heurística baseada em tópicos esperados.
    Normaliza separadores antes de comparar para evitar falsos negativos
    entre "23.75%" (tópico) e "23,75%" (resposta).

    Returns: score entre 0 e 1
    """
    if not response:
        return 0.0

    response_normalized = _normalize(response.lower())
    matches = sum(
        1
        for topic in expected_topics
        if _normalize(topic.lower()) in response_normalized
    )
    return matches / len(expected_topics) if expected_topics else 0.5


def _evaluate_citations(sources: List[Any], required: bool) -> float:
    """
    Avalia qualidade das citações.
    Returns: score entre 0 e 1
    """
    if not required:
        return 1.0
    if not sources:
        return 0.0

    num_sources = len(sources)
    if num_sources >= 2:
        return 1.0
    elif num_sources == 1:
        return 0.7
    else:
        return 0.3


def _evaluate_refusal(response: str, case: "EvaluationCase") -> float:
    """
    Avalia comportamento apropriado face à pergunta:
    - Casos "Limit": pontuação alta se o agente recusar ou adicionar caveats epistémicos.
    - Outros casos: pontuação alta se o agente responder com base legal fundamentada.

    Returns: score entre 0 e 1
    """
    response_lower = response.lower()

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
        "recomendável",
        "aconselhável",
        "recomendo que consulte",
        "é aconselhável",
        "é recomendável",
        "especialista",
        "consulte um",
        "aconselha-se",
    ]

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

    if case.category == "Limit":
        # Ideal: responde ao que pode (grounded) + recusa o que extravasa o âmbito
        if has_refusal and has_grounded:
            return 1.0
        elif has_refusal:
            return 1.0
        elif has_grounded:
            # Respondeu com base legal mas sem humildade epistémica — parcialmente aceitável
            return 0.5
        else:
            return 0.2
    else:
        if has_grounded and not has_refusal:
            return 1.0
        elif has_grounded and has_refusal:
            # Respondeu com base legal mas com incerteza excessiva — ok, não ideal
            return 0.7
        elif has_refusal and not has_grounded:
            # Recusou quando não devia — falha
            return 0.0
        else:
            return 0.4
