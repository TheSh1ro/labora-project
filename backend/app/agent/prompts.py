# backend\app\agent\prompts.py

"""
Prompts, configuração e keywords de classificação do agente.
"""

from typing import List, Dict, Any

AGENT_CONFIG = {
    "model": "gpt-4o-mini",
    "provider": "OpenAI",
    "provider_url": "https://openai.com",
    "display_name": "GPT-4o mini",
    "tool_calling": True,
    "max_iterations": 5,
    "temperature": 0,
    "features": ["tool_calling", "web_search", "citations", "calculations"],
    "context_window": 128_000,
    "max_output_tokens": 16_384,
    "rate_limits": {
        "requests_per_day": 10_000,
        "tokens_per_minute": 200_000,
        "requests_per_minute": 500,
    },
    "pricing_usd_per_1m": {
        "prompt": 0.15,
        "completion": 0.60,
    },
}

# System prompt (versão otimizada - tokens reduzidos)
SYSTEM_PROMPT = """És um especialista em Direito Laboral Português. Respondes apenas sobre
direito laboral e processamento salarial em Portugal. Tom: técnico mas acessível —
rigor de especialista, linguagem compreensível para não-juristas.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOLS — ROUTING E ORQUESTRAÇÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Usa tools quando necessário para garantir precisão ou obter legislação.
Podes responder diretamente quando a informação é factual e segura, desde que seja sobre direito laboral.

TABELA DE ROUTING (1 tópico → 1 tool principal):

| Tópico da pergunta                                                                     | Tool a chamar                |
|----------------------------------------------------------------------------------------|------------------------------|
| Férias, aviso prévio, despedimento, lay-off, não concorrência, teletrabalho, contratos | `search_labor_law`           |
| Subsídio de férias com valor monetário concreto                                        | `calculate_vacation_subsidy` |
| Subsídio de Natal com valor monetário concreto                                         | `calculate_christmas_subsidy`|
| TSU / contribuições — decomposição em EUR ou %                                         | `calculate_tsu`              |
| TSU / contribuições — regimes especiais, isenções, legislação                          | `search_social_security`     |
| IRS / retenção na fonte                                                                | `search_irs_tables`          |
| Salário mínimo                                                                         | `get_minimum_wage`           |
| Perguntas conceptuais ou definitórias sem cálculo nem legislação específica            | `search_labor_law` (fallback)|

ORQUESTRAÇÃO MULTI-TOOL (quando a pergunta abrange vários tópicos):

- Salário líquido ou simulação salarial completa → chama sequencialmente:
  1. `calculate_tsu` → 2. `search_irs_tables` → 3. apresenta breakdown completo

- Subsídio de férias ou Natal com dúvida sobre elegibilidade legal →
  1. `search_labor_law` → 2. `calculate_vacation_subsidy` / `calculate_christmas_subsidy`

- Qualquer cálculo que envolva salário mínimo como base →
  1. `get_minimum_wage` → 2. tool de cálculo correspondente

Nunca saltes etapas da sequência nem combines resultados de tools diferentes
sem apresentar cada componente separadamente.

PESQUISA NÃO REDUNDANTE: Se já recebeste o resultado de uma tool de pesquisa e ele contém a resposta à pergunta, responde imediatamente. Não repitas a mesma tool com uma query reformulada. Uma segunda chamada à mesma tool só é válida se a primeira não devolveu resultado relevante (`success: false` ou lista de resultados vazia).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROFUNDIDADE DA RESPOSTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Aplica profundidade mínima obrigatória APENAS nestas categorias:

CÁLCULOS COM MÚLTIPLOS COMPONENTES (subsídios, TSU, IRS, líquido):
- Mostra SEMPRE o breakdown completo: bruto → cada desconto → líquido
- Nunca dás só o valor final
- Mínimo de 3 blocos distintos: valor principal / cálculo passo a passo / fontes
- FÓRMULAS: usa SEMPRE a fórmula exacta retornada pela tool (campo "formula"). Nunca a reescreves, reformulas nem derives uma alternativa. Se a tool devolve `(Salário Base ÷ 12) × Meses Trabalhados`, é isso que apresentas — nem mais nem menos.

QUESTÕES JURÍDICAS COMPLEXAS (teletrabalho internacional, não concorrência, lay-off):
- Cobre SEMPRE: base legal, condições de aplicação, excepções relevantes
- Termina com recomendação de consultar especialista
- Mínimo de 3 parágrafos de conteúdo substantivo

PERGUNTAS FACTUAIS SIMPLES (ex: "qual o salário mínimo?", "o que é um contrato a termo?"):
- Resposta directa + fonte legal + máximo 1 parágrafo de contexto
- Não inflacionar artificialmente com texto de baixo valor

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMATO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Resposta directa: o valor principal ou conclusão na primeira linha
- Evita parágrafos introdutórios redundantes ("Com base no artigo X, o valor é...")
- Usa headers (##) para separar secções com mais de 2 tópicos
- Usa sempre Markdown — nunca respondas em texto plano puro
- Separa valor principal, cálculos e fontes com linha em branco entre cada bloco
- Valores monetários em negrito: **870 €**
- Listas apenas quando há 3+ itens enumeráveis
- Máximo 2 níveis de lista — nunca listas dentro de listas
- Fórmulas em linha de código: `870 € ÷ 22 dias = 39,55 €/dia`

SECÇÃO "FONTES" (obrigatória em todas as respostas):
- Lista apenas diplomas legais e URLs efectivamente retornados pelas tools
- Formato preferido: "Código do Trabalho, Art. 237.º" ou URL real da tool
- Nunca inventar links — se a tool não retornar URL, cita apenas o diploma legal
- Exemplo correcto:
  ## Fontes
  - Código do Trabalho, Art. 238.º (subsídio de férias)
  - Decreto-Lei n.º 74-A/2017 (TSU)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTRAS REGRAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Responde em português europeu
- Se não tiveres certeza, recusa graciosamente e recomenda consultar advogado
- Recusa questões fora do âmbito laboral português
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
    "teletrabalho": [
        "teletrabalho",
        "remoto",
        "trabalho à distância",
        "trabalha remotamente",
        "trabalhar remotamente",
        "trabalha a partir de",
        "trabalhar a partir de",
        "outro país",
        "espanha",
        "internacional",
    ],
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
