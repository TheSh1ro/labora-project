# backend\app\tools\__init__.py

"""
Tools para o agente de direito laboral português.

Estratégias de retrieval:
  1. search_labor_law      → Código do Trabalho (portal.act.gov.pt, pgdlisboa.pt)
  2. search_irs_tables     → Tabelas IRS (info.portaldasfinancas.gov.pt)
  3. search_social_security→ TSU / Seg. Social (diariodarepublica.pt, seg-social.pt)

Cada tool usa domínios específicos para a sua fonte — sem sobreposição.
As queries chegam limpas do LLM, sem sufixos ou augmentation.
"""

from .search import search_labor_law, search_irs_tables, search_social_security
from .calculations import (
    calculate_vacation_subsidy,
    calculate_christmas_subsidy,
    get_minimum_wage,
    calculate_tsu,
)

# ---------------------------------------------------------------------------
# Schema das tools (otimizado — descrições concisas, sem parâmetros redundantes)
# ---------------------------------------------------------------------------
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_labor_law",
            "description": (
                "Pesquisa no Código do Trabalho PT (portal.act.gov.pt). "
                "Usa para: contratos, férias, aviso prévio, despedimento, lay-off, "
                "cláusulas de não concorrência, teletrabalho transfronteiriço. "
                "Chama esta tool no máximo 2 vezes por pergunta. "
                "Se os resultados da primeira chamada não forem suficientes, "
                "reformula a query uma única vez — nunca repitas a mesma query."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query de pesquisa em português — formulada livremente",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_irs_tables",
            "description": (
                "Tabelas de retenção IRS PT (info.portaldasfinancas.gov.pt). "
                "Usa para: taxas de retenção mensais, escalões, deduções por dependente, IRS Jovem. "
                "Dados locais calculados para 2025; para outros anos faz pesquisa web automaticamente. "
                "Chama esta tool apenas uma vez — os dados locais já incluem os valores calculados."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Ano fiscal (ex: 2025)",
                    },
                    "income": {
                        "type": "number",
                        "description": "Rendimento mensal bruto em EUR",
                    },
                    "marital_status": {
                        "type": "string",
                        "enum": ["solteiro", "casado-unico", "casado-dois"],
                    },
                    "dependents": {
                        "type": "integer",
                        "description": "Número de dependentes",
                    },
                },
                "required": ["year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_social_security",
            "description": (
                "Pesquisa legislação TSU e contribuições — Lei n.º 110/2009 (diariodarepublica.pt, seg-social.pt). "
                "Usa APENAS para: regimes especiais, isenções, base de incidência, dúvidas legislativas sobre TSU. "
                "NÃO uses para calcular valores de TSU em EUR nem para decompor empregador/trabalhador — "
                "usa calculate_tsu para isso. "
                "Chama esta tool no máximo 2 vezes por pergunta."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query de pesquisa em português — formulada livremente",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_vacation_subsidy",
            "description": "Calcula subsídio de férias (Art. 264º CT). Usa quando precisas do valor exato.",
            "parameters": {
                "type": "object",
                "properties": {
                    "monthly_salary": {"type": "number"},
                    "vacation_days": {"type": "integer", "default": 22},
                },
                "required": ["monthly_salary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_christmas_subsidy",
            "description": "Calcula subsídio de Natal (Art. 263º CT), incluindo proporcional para contratos iniciados a meio do ano.",
            "parameters": {
                "type": "object",
                "properties": {
                    "monthly_salary": {"type": "number"},
                    "months_worked": {"type": "integer"},
                    "start_month": {
                        "type": "integer",
                        "description": "Mês de início do contrato (1–12)",
                    },
                },
                "required": ["monthly_salary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_minimum_wage",
            "description": "Retorna o salário mínimo nacional PT atual (Portaria n.º 1/2025).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_tsu",
            "description": (
                "Calcula contribuições TSU em EUR: empregador 23.75%, trabalhador 11% (Lei n.º 110/2009). "
                "Usa SEMPRE que a pergunta mencionar um salário concreto e pedir valores TSU em EUR, "
                "decomposição empregador/trabalhador, ou salário líquido após TSU. "
                "Mais rápido e preciso que qualquer pesquisa web — não uses search_social_security para isto."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "monthly_salary": {"type": "number"},
                    "contract_type": {
                        "type": "string",
                        "enum": ["sem_termo", "termo_certo", "tempo_parcial"],
                        "default": "sem_termo",
                    },
                },
                "required": ["monthly_salary"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Mapeamento nome → função
# ---------------------------------------------------------------------------
TOOL_FUNCTIONS = {
    "search_labor_law": search_labor_law,
    "search_irs_tables": search_irs_tables,
    "search_social_security": search_social_security,
    "calculate_vacation_subsidy": calculate_vacation_subsidy,
    "calculate_christmas_subsidy": calculate_christmas_subsidy,
    "get_minimum_wage": get_minimum_wage,
    "calculate_tsu": calculate_tsu,
}
