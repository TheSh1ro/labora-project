"""
Tools para o agente de direito laboral português.
Implementa pesquisa web e cálculos especializados.
"""
import os
import json
from typing import Dict, Any, List, Optional
from tavily import TavilyClient
from datetime import datetime

# Inicializa cliente Tavily
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

# Dados atualizados (2024-2025)
MINIMUM_WAGE_2025 = 870.0  # Euros mensais
MINIMUM_WAGE_2024 = 820.0  # Euros mensais

# Taxas TSU atualizadas
TSU_RATES = {
    "empregador": 0.2375,  # 23.75%
    "trabalhador": 0.11,   # 11%
    "total": 0.3475        # 34.75%
}

# Tabelas de retenção IRS 2025 (simplificado - valores aproximados)
IRS_TABLES_2025 = {
    "solteiro": [
        (0, 1000, 0),
        (1000, 1500, 0.13),
        (1500, 2000, 0.165),
        (2000, 2500, 0.22),
        (2500, 3000, 0.25),
        (3000, 4000, 0.32),
        (4000, 5000, 0.355),
        (5000, 8000, 0.3875),
        (8000, float('inf'), 0.45)
    ],
    "casado-unico": [
        (0, 1000, 0),
        (1000, 1500, 0.11),
        (1500, 2000, 0.145),
        (2000, 2500, 0.195),
        (2500, 3000, 0.225),
        (3000, 4000, 0.295),
        (4000, 5000, 0.33),
        (5000, 8000, 0.365),
        (8000, float('inf'), 0.43)
    ],
    "casado-dois": [
        (0, 1000, 0),
        (1000, 1500, 0.10),
        (1500, 2000, 0.135),
        (2000, 2500, 0.185),
        (2500, 3000, 0.215),
        (3000, 4000, 0.285),
        (4000, 5000, 0.32),
        (5000, 8000, 0.355),
        (8000, float('inf'), 0.425)
    ]
}


def search_labor_law(query: str, topic: Optional[str] = None) -> Dict[str, Any]:
    """
    Pesquisa informações no Código do Trabalho português.
    
    Args:
        query: Termos de pesquisa
        topic: Tópico específico (contratos, ferias, despedimento, layoff, nao-concorrencia, teletrabalho)
    
    Returns:
        Resultados da pesquisa com fontes
    """
    # Domínios oficiais portugueses
    domains = ["portal.act.gov.pt", "www.pgdlisboa.pt", "dre.pt", "www.cite.gov.pt"]
    
    # Refina query com tópico
    search_query = query
    if topic:
        topic_keywords = {
            "contratos": "contrato trabalho tipo contrato",
            "ferias": "férias anuais dias férias descanso",
            "despedimento": "despedimento justa causa aviso prévio",
            "layoff": "lay-off suspensão contrato redução",
            "nao-concorrencia": "cláusula não concorrência",
            "teletrabalho": "teletrabalho trabalho remoto"
        }
        if topic in topic_keywords:
            search_query = f"{query} {topic_keywords[topic]}"
    
    # Adiciona contexto de Portugal
    search_query = f"{search_query} Portugal Código Trabalho 2024 2025"
    
    try:
        if tavily_client:
            response = tavily_client.search(
                query=search_query,
                search_depth="advanced",
                include_domains=domains,
                max_results=5
            )
            return {
                "success": True,
                "results": response.get("results", []),
                "query": search_query
            }
        else:
            # Fallback sem API key
            return {
                "success": False,
                "error": "Tavily API key não configurada",
                "results": [],
                "query": search_query
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "query": search_query
        }


def search_irs_tables(
    year: int,
    income: Optional[float] = None,
    marital_status: Optional[str] = None,
    dependents: Optional[int] = None
) -> Dict[str, Any]:
    """
    Consulta tabelas de retenção na fonte de IRS.
    
    Args:
        year: Ano das tabelas (2024 ou 2025)
        income: Rendimento mensal bruto (opcional)
        marital_status: Estado civil (solteiro, casado-unico, casado-dois)
        dependents: Número de dependentes
    
    Returns:
        Informações sobre taxas de retenção
    """
    if year not in [2024, 2025]:
        return {
            "success": False,
            "error": f"Tabelas disponíveis apenas para 2024 e 2025. Ano solicitado: {year}",
            "year": year
        }
    
    # Para 2024, usamos as mesmas tabelas de 2025 (próximas)
    tables = IRS_TABLES_2025
    
    result = {
        "success": True,
        "year": year,
        "marital_status": marital_status,
        "income": income,
        "dependents": dependents,
        "tax_rate": None,
        "deduction_per_dependent": 21.43 if year == 2024 else 21.43,  # Valor mensal
        "sources": [
            {
                "title": "Tabelas de Retenção na Fonte IRS 2025",
                "url": "https://info.portaldasfinancas.gov.pt/pt/apoio_contribuinte/tabela_ret_doclib/"
            }
        ]
    }
    
    # Calcula taxa se tivermos income e marital_status
    if income and marital_status and marital_status in tables:
        for min_val, max_val, rate in tables[marital_status]:
            if min_val <= income < max_val:
                result["tax_rate"] = rate
                result["tax_amount"] = round(income * rate, 2)
                break
        
        # Aplica dedução por dependentes
        if dependents and dependents > 0:
            deduction = dependents * result["deduction_per_dependent"]
            result["dependent_deduction"] = round(deduction, 2)
            if result.get("tax_amount"):
                result["final_tax_amount"] = max(0, round(result["tax_amount"] - deduction, 2))
    
    return result


def search_social_security(query: str) -> Dict[str, Any]:
    """
    Pesquisa informações sobre Segurança Social e contribuições.
    
    Args:
        query: Termos de pesquisa sobre TSU, contribuições, etc.
    
    Returns:
        Resultados da pesquisa
    """
    domains = ["www.seg-social.pt", "diariodarepublica.pt", "www.cite.gov.pt"]
    
    search_query = f"{query} Portugal Segurança Social TSU contribuições 2024 2025"
    
    try:
        if tavily_client:
            response = tavily_client.search(
                query=search_query,
                search_depth="advanced",
                include_domains=domains,
                max_results=5
            )
            return {
                "success": True,
                "results": response.get("results", []),
                "query": search_query
            }
        else:
            return {
                "success": False,
                "error": "Tavily API key não configurada",
                "results": [],
                "query": search_query
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "query": search_query
        }


def calculate_vacation_subsidy(monthly_salary: float, vacation_days: int = 22) -> Dict[str, Any]:
    """
    Calcula o valor do subsídio de férias.
    
    Fórmula: (Salário Base × 12) ÷ 365 × Dias de Férias
    
    Args:
        monthly_salary: Salário base mensal em EUR
        vacation_days: Dias de férias (padrão: 22)
    
    Returns:
        Valor calculado do subsídio de férias
    """
    daily_salary = (monthly_salary * 12) / 365
    subsidy = daily_salary * vacation_days
    
    return {
        "success": True,
        "monthly_salary": monthly_salary,
        "vacation_days": vacation_days,
        "daily_salary": round(daily_salary, 2),
        "vacation_subsidy": round(subsidy, 2),
        "formula": "(Salário Base × 12) ÷ 365 × Dias de Férias",
        "legal_basis": "Código do Trabalho, Art. 264º"
    }


def calculate_christmas_subsidy(
    monthly_salary: float,
    months_worked: Optional[int] = None,
    start_month: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calcula o valor do subsídio de Natal.
    
    Fórmula normal: 1 mês de salário
    Fórmula proporcional: (Salário ÷ 12) × Meses Trabalhados
    
    Args:
        monthly_salary: Salário base mensal em EUR
        months_worked: Meses trabalhados no ano (para cálculo proporcional)
        start_month: Mês de início do contrato (1-12)
    
    Returns:
        Valor calculado do subsídio de Natal
    """
    result = {
        "success": True,
        "monthly_salary": monthly_salary,
        "formula": "1 mês de salário base",
        "legal_basis": "Código do Trabalho, Art. 263º",
        "christmas_subsidy": monthly_salary
    }
    
    # Cálculo proporcional para trabalhadores contratados a meio do ano
    if months_worked:
        proportional = (monthly_salary / 12) * months_worked
        result["christmas_subsidy"] = round(proportional, 2)
        result["formula"] = "(Salário Base ÷ 12) × Meses Trabalhados"
        result["months_worked"] = months_worked
        result["is_proportional"] = True
    elif start_month and 1 <= start_month <= 12:
        months = 13 - start_month  # De start_month até dezemmbro
        proportional = (monthly_salary / 12) * months
        result["christmas_subsidy"] = round(proportional, 2)
        result["formula"] = "(Salário Base ÷ 12) × Meses desde início"
        result["start_month"] = start_month
        result["months_worked"] = months
        result["is_proportional"] = True
    
    return result


def get_minimum_wage() -> Dict[str, Any]:
    """
    Retorna o salário mínimo nacional atual.
    
    Returns:
        Informações sobre o salário mínimo nacional
    """
    current_year = 2025
    
    return {
        "success": True,
        "year": current_year,
        "monthly_amount": MINIMUM_WAGE_2025,
        "annual_amount": round(MINIMUM_WAGE_2025 * 14, 2),  # 14 meses
        "daily_amount": round(MINIMUM_WAGE_2025 / 22, 2),  # ~22 dias úteis
        "hourly_amount": round(MINIMUM_WAGE_2025 / 160, 2),  # ~160 horas/mês
        "currency": "EUR",
        "legal_basis": "Portaria n.º 1/2025",
        "sources": [
            {
                "title": "Portal das Finanças - Salário Mínimo Nacional",
                "url": "https://info.portaldasfinancas.gov.pt"
            },
            {
                "title": "Código do Trabalho",
                "url": "https://portal.act.gov.pt"
            }
        ]
    }


def calculate_tsu(monthly_salary: float, contract_type: str = "sem_termo") -> Dict[str, Any]:
    """
    Calcula as contribuições TSU (Taxa Social Única).
    
    Args:
        monthly_salary: Salário base mensal em EUR
        contract_type: Tipo de contrato (sem_termo, termo_certo, tempo_parcial)
    
    Returns:
        Valores de contribuição do empregador e trabalhador
    """
    employer_contribution = monthly_salary * TSU_RATES["empregador"]
    employee_contribution = monthly_salary * TSU_RATES["trabalhador"]
    total_contribution = employer_contribution + employee_contribution
    
    return {
        "success": True,
        "monthly_salary": monthly_salary,
        "contract_type": contract_type,
        "employer": {
            "rate": "23.75%",
            "rate_decimal": TSU_RATES["empregador"],
            "amount": round(employer_contribution, 2)
        },
        "employee": {
            "rate": "11%",
            "rate_decimal": TSU_RATES["trabalhador"],
            "amount": round(employee_contribution, 2)
        },
        "total": {
            "rate": "34.75%",
            "rate_decimal": TSU_RATES["total"],
            "amount": round(total_contribution, 2)
        },
        "liquid_salary": round(monthly_salary - employee_contribution, 2),
        "legal_basis": "Código dos Regimes Contributivos da Segurança Social"
    }


# Schema das tools para OpenAI Functions
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_labor_law",
            "description": "Pesquisa informações no Código do Trabalho português, incluindo contratos, férias, despedimento, lay-off, cláusulas de não concorrência e teletrabalho.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termos de pesquisa sobre direito laboral"
                    },
                    "topic": {
                        "type": "string",
                        "enum": ["contratos", "ferias", "despedimento", "layoff", "nao-concorrencia", "teletrabalho"],
                        "description": "Tópico específico para refinar a pesquisa"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_irs_tables",
            "description": "Consulta as tabelas oficiais de retenção na fonte de IRS para trabalhadores dependentes em Portugal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Ano das tabelas de IRS (2024 ou 2025)"
                    },
                    "income": {
                        "type": "number",
                        "description": "Rendimento mensal bruto em EUR"
                    },
                    "marital_status": {
                        "type": "string",
                        "enum": ["solteiro", "casado-unico", "casado-dois"],
                        "description": "Estado civil do contribuinte"
                    },
                    "dependents": {
                        "type": "integer",
                        "description": "Número de dependentes do contribuinte"
                    }
                },
                "required": ["year"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_social_security",
            "description": "Pesquisa informações sobre Segurança Social, TSU (Taxa Social Única), contribuições e regimes contributivos em Portugal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termos de pesquisa sobre Segurança Social"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_vacation_subsidy",
            "description": "Calcula o valor do subsídio de férias de acordo com o Código do Trabalho português.",
            "parameters": {
                "type": "object",
                "properties": {
                    "monthly_salary": {
                        "type": "number",
                        "description": "Salário base mensal em euros"
                    },
                    "vacation_days": {
                        "type": "integer",
                        "description": "Número de dias de férias (padrão: 22 dias)",
                        "default": 22
                    }
                },
                "required": ["monthly_salary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_christmas_subsidy",
            "description": "Calcula o valor do subsídio de Natal, incluindo cálculo proporcional para trabalhadores contratados a meio do ano.",
            "parameters": {
                "type": "object",
                "properties": {
                    "monthly_salary": {
                        "type": "number",
                        "description": "Salário base mensal em euros"
                    },
                    "months_worked": {
                        "type": "integer",
                        "description": "Número de meses trabalhados no ano (opcional, para cálculo proporcional)"
                    },
                    "start_month": {
                        "type": "integer",
                        "description": "Mês de início do contrato (1-12, opcional)"
                    }
                },
                "required": ["monthly_salary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_minimum_wage",
            "description": "Retorna o salário mínimo nacional atual em Portugal.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_tsu",
            "description": "Calcula as contribuições TSU (Taxa Social Única) do empregador e trabalhador.",
            "parameters": {
                "type": "object",
                "properties": {
                    "monthly_salary": {
                        "type": "number",
                        "description": "Salário base mensal em euros"
                    },
                    "contract_type": {
                        "type": "string",
                        "enum": ["sem_termo", "termo_certo", "tempo_parcial"],
                        "description": "Tipo de contrato de trabalho",
                        "default": "sem_termo"
                    }
                },
                "required": ["monthly_salary"]
            }
        }
    }
]


# Mapeamento de nomes para funções
TOOL_FUNCTIONS = {
    "search_labor_law": search_labor_law,
    "search_irs_tables": search_irs_tables,
    "search_social_security": search_social_security,
    "calculate_vacation_subsidy": calculate_vacation_subsidy,
    "calculate_christmas_subsidy": calculate_christmas_subsidy,
    "get_minimum_wage": get_minimum_wage,
    "calculate_tsu": calculate_tsu
}