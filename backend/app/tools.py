# backend\app\tools.py

"""
Tools para o agente de direito laboral português.

Estratégias de retrieval (alinhadas ao challenge):
  1. search_labor_law      → Código do Trabalho (portal.act.gov.pt, pgdlisboa.pt)
  2. search_irs_tables     → Tabelas IRS (info.portaldasfinancas.gov.pt)
  3. search_social_security→ TSU / Seg. Social (diariodarepublica.pt, seg-social.pt)

Cada tool usa domínios específicos para a sua fonte — sem sobreposição.
As queries chegam limpas do LLM, sem sufixos ou augmentation.
"""

import os
from typing import Dict, Any, Optional
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Cliente Tavily
# ---------------------------------------------------------------------------
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

# ---------------------------------------------------------------------------
# Domínios por estratégia de retrieval (3 estratégias distintas)
# ---------------------------------------------------------------------------

# Fonte 1: Código do Trabalho — ACT + pgdlisboa (versão consolidada articulada)
DOMAINS_LABOR_LAW = [
    "portal.act.gov.pt",
    "www.pgdlisboa.pt",
]

# Fonte 2: IRS — exclusivamente Portal das Finanças
DOMAINS_IRS = [
    "info.portaldasfinancas.gov.pt",
    "www.portaldasfinancas.gov.pt",
]

# Fonte 3: TSU / Segurança Social — DRE (lei consolidada) + seg-social.pt
DOMAINS_SOCIAL_SECURITY = [
    "diariodarepublica.pt",
    "www.seg-social.pt",
]

# ---------------------------------------------------------------------------
# Dados estáticos atualizados (base legal fixa — alterados por portaria anual)
# ---------------------------------------------------------------------------
MINIMUM_WAGE_2025 = 870.0  # Portaria n.º 1/2025
MINIMUM_WAGE_2024 = 820.0

TSU_RATES = {
    "empregador": 0.2375,  # 23.75% — Lei n.º 110/2009
    "trabalhador": 0.11,  # 11%
    "total": 0.3475,  # 34.75%
}

# Tabelas de retenção IRS 2025 — Despacho n.º 236-A/2025
IRS_TABLES_2025 = {
    "solteiro": [
        (0, 1000, 0.00),
        (1000, 1500, 0.13),
        (1500, 2000, 0.165),
        (2000, 2500, 0.22),
        (2500, 3000, 0.25),
        (3000, 4000, 0.32),
        (4000, 5000, 0.355),
        (5000, 8000, 0.3875),
        (8000, float("inf"), 0.45),
    ],
    "casado-unico": [
        (0, 1000, 0.00),
        (1000, 1500, 0.11),
        (1500, 2000, 0.145),
        (2000, 2500, 0.195),
        (2500, 3000, 0.225),
        (3000, 4000, 0.295),
        (4000, 5000, 0.33),
        (5000, 8000, 0.365),
        (8000, float("inf"), 0.43),
    ],
    "casado-dois": [
        (0, 1000, 0.00),
        (1000, 1500, 0.10),
        (1500, 2000, 0.135),
        (2000, 2500, 0.185),
        (2500, 3000, 0.215),
        (3000, 4000, 0.285),
        (4000, 5000, 0.32),
        (5000, 8000, 0.355),
        (8000, float("inf"), 0.425),
    ],
}


# ---------------------------------------------------------------------------
# Helper de busca Tavily
# ---------------------------------------------------------------------------
def _tavily_search(query: str, domains: list, max_results: int = 3) -> Dict[str, Any]:
    """Executa busca Tavily nos domínios especificados. Query chega limpa do LLM."""
    if not tavily_client:
        return {
            "success": False,
            "error": "Tavily API key não configurada",
            "results": [],
            "query": query,
        }
    try:
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            include_domains=domains,
            max_results=max_results,
        )
        return {"success": True, "results": response.get("results", []), "query": query}
    except Exception as e:
        return {"success": False, "error": str(e), "results": [], "query": query}


# ---------------------------------------------------------------------------
# Estratégia 1: Código do Trabalho
# Fonte: portal.act.gov.pt + pgdlisboa.pt
# Cobre: contratos, férias, despedimento, lay-off, não concorrência, teletrabalho
# ---------------------------------------------------------------------------
def search_labor_law(query: str) -> Dict[str, Any]:
    """
    Pesquisa no Código do Trabalho português.
    Fontes: portal.act.gov.pt, pgdlisboa.pt
    """
    return _tavily_search(query, DOMAINS_LABOR_LAW)


# ---------------------------------------------------------------------------
# Estratégia 2: Tabelas de Retenção IRS
# Fonte: info.portaldasfinancas.gov.pt
# Cobre: taxas de retenção mensais, escalões, deduções por dependente, IRS Jovem
# ---------------------------------------------------------------------------
def search_irs_tables(
    year: int,
    income: Optional[float] = None,
    marital_status: Optional[str] = None,
    dependents: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Consulta tabelas de retenção IRS.
    Calcula taxa local se income+marital_status fornecidos (apenas 2025).
    Para outros anos, faz fallback para pesquisa Tavily em vez de retornar erro.
    """
    if year != 2025:
        # Dados estáticos só cobrem 2025 — pesquisa web para anos anteriores/futuros
        query = f"tabelas retenção IRS {year} trabalhadores dependentes escalões"
        if income:
            query += f" rendimento {income} EUR"
        web = _tavily_search(query, DOMAINS_IRS, max_results=3)
        return {
            "success": web.get("success", False),
            "year": year,
            "note": f"Tabelas locais disponíveis apenas para 2025. Resultados obtidos via pesquisa web para {year}.",
            "income": income,
            "marital_status": marital_status,
            "dependents": dependents,
            "results": web.get("results", []),
            "sources": [
                {
                    "title": f"Tabelas de Retenção na Fonte IRS {year} — Portal das Finanças",
                    "url": "https://info.portaldasfinancas.gov.pt/pt/apoio_contribuinte/tabela_ret_doclib/",
                }
            ],
        }

    result: Dict[str, Any] = {
        "success": True,
        "year": year,
        "marital_status": marital_status,
        "income": income,
        "dependents": dependents,
        "tax_rate": None,
        "deduction_per_dependent": 21.43,
        "sources": [
            {
                "title": "Tabelas de Retenção na Fonte IRS 2025 — Despacho n.º 236-A/2025",
                "url": "https://info.portaldasfinancas.gov.pt/pt/apoio_contribuinte/tabela_ret_doclib/",
            }
        ],
    }

    if income and marital_status and marital_status in IRS_TABLES_2025:
        for min_val, max_val, rate in IRS_TABLES_2025[marital_status]:
            if min_val <= income < max_val:
                result["tax_rate"] = rate
                result["tax_amount"] = round(income * rate, 2)
                break

        if dependents and dependents > 0:
            deduction = round(dependents * result["deduction_per_dependent"], 2)
            result["dependent_deduction"] = deduction
            if result.get("tax_amount"):
                result["final_tax_amount"] = max(
                    0, round(result["tax_amount"] - deduction, 2)
                )

    web = _tavily_search(
        f"tabelas retenção IRS {year} trabalhadores dependentes",
        DOMAINS_IRS,
        max_results=2,
    )
    if web.get("results"):
        result["web_context"] = web["results"]

    return result


# ---------------------------------------------------------------------------
# Estratégia 3: Segurança Social / TSU
# Fonte: diariodarepublica.pt + seg-social.pt
# Cobre: taxas TSU, regimes especiais, isenções, base de incidência
# ---------------------------------------------------------------------------
def search_social_security(query: str) -> Dict[str, Any]:
    """
    Pesquisa contribuições e TSU — Lei n.º 110/2009 (Código dos Regimes Contributivos).
    Fontes: diariodarepublica.pt, seg-social.pt
    """
    return _tavily_search(query, DOMAINS_SOCIAL_SECURITY)


# ---------------------------------------------------------------------------
# Cálculos locais (sem I/O — resultados determinísticos)
# ---------------------------------------------------------------------------
def calculate_vacation_subsidy(
    monthly_salary: float, vacation_days: int = 22
) -> Dict[str, Any]:
    """Calcula subsídio de férias — Art. 264º Código do Trabalho."""
    daily_salary = (monthly_salary * 12) / 365
    subsidy = daily_salary * vacation_days
    return {
        "success": True,
        "monthly_salary": monthly_salary,
        "vacation_days": vacation_days,
        "daily_salary": round(daily_salary, 2),
        "vacation_subsidy": round(subsidy, 2),
        "formula": "(Salário Base × 12) ÷ 365 × Dias de Férias",
        "legal_basis": "Código do Trabalho, Art. 264º",
        "sources": [
            {
                "title": "Código do Trabalho, Art. 264º",
                "url": "https://portal.act.gov.pt",
            }
        ],
    }


def calculate_christmas_subsidy(
    monthly_salary: float,
    months_worked: Optional[int] = None,
    start_month: Optional[int] = None,
) -> Dict[str, Any]:
    """Calcula subsídio de Natal — Art. 263º Código do Trabalho. Inclui proporcional."""
    result: Dict[str, Any] = {
        "success": True,
        "monthly_salary": monthly_salary,
        "christmas_subsidy": monthly_salary,
        "formula": "1 mês de salário base",
        "is_proportional": False,
        "legal_basis": "Código do Trabalho, Art. 263º",
        "sources": [
            {
                "title": "Código do Trabalho, Art. 263º",
                "url": "https://portal.act.gov.pt",
            }
        ],
    }

    if months_worked:
        proportional = round((monthly_salary / 12) * months_worked, 2)
        result.update(
            {
                "christmas_subsidy": proportional,
                "formula": "(Salário Base ÷ 12) × Meses Trabalhados",
                "months_worked": months_worked,
                "is_proportional": True,
            }
        )
    elif start_month and 1 <= start_month <= 12:
        months = 13 - start_month
        proportional = round((monthly_salary / 12) * months, 2)
        result.update(
            {
                "christmas_subsidy": proportional,
                "formula": "(Salário Base ÷ 12) × Meses desde início",
                "start_month": start_month,
                "months_worked": months,
                "is_proportional": True,
            }
        )

    return result


def get_minimum_wage() -> Dict[str, Any]:
    """Retorna o salário mínimo nacional atual — Portaria n.º 1/2025."""
    return {
        "success": True,
        "year": 2025,
        "monthly_amount": MINIMUM_WAGE_2025,
        "annual_amount": round(MINIMUM_WAGE_2025 * 14, 2),  # 14 meses
        "daily_amount": round(MINIMUM_WAGE_2025 / 22, 2),  # ~22 dias úteis
        "hourly_amount": round(MINIMUM_WAGE_2025 / 160, 2),  # ~160h/mês
        "currency": "EUR",
        "legal_basis": "Portaria n.º 1/2025",
        "sources": [
            {
                "title": "Portaria n.º 1/2025 — Salário Mínimo Nacional",
                "url": "https://info.portaldasfinancas.gov.pt",
            },
            {"title": "Código do Trabalho", "url": "https://portal.act.gov.pt"},
        ],
    }


def calculate_tsu(
    monthly_salary: float, contract_type: str = "sem_termo"
) -> Dict[str, Any]:
    """Calcula contribuições TSU — Lei n.º 110/2009."""
    employer = round(monthly_salary * TSU_RATES["empregador"], 2)
    employee = round(monthly_salary * TSU_RATES["trabalhador"], 2)
    total = round(employer + employee, 2)
    return {
        "success": True,
        "monthly_salary": monthly_salary,
        "contract_type": contract_type,
        "employer": {"rate": "23.75%", "amount": employer},
        "employee": {"rate": "11%", "amount": employee},
        "total": {"rate": "34.75%", "amount": total},
        "liquid_salary": round(monthly_salary - employee, 2),
        "legal_basis": "Lei n.º 110/2009 — Código dos Regimes Contributivos",
        "sources": [
            {
                "title": "Lei n.º 110/2009 — Código dos Regimes Contributivos",
                "url": "https://diariodarepublica.pt/dr/legislacao-consolidada/lei/2009-34514575",
            },
            {
                "title": "Segurança Social — Taxas Contributivas",
                "url": "https://www.seg-social.pt",
            },
        ],
    }


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
                        "description": "Ano fiscal (2024 ou 2025)",
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
                "Pesquisa TSU e contribuições — Lei n.º 110/2009 (diariodarepublica.pt, seg-social.pt). "
                "Usa para: taxas TSU, regimes especiais, isenções, base de incidência. "
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
            "description": "Calcula contribuições TSU: empregador 23.75%, trabalhador 11% (Lei n.º 110/2009).",
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
