# backend\app\tools\search.py

"""
Tools de pesquisa (Tavily) para o agente de direito laboral português.

Estratégias de retrieval:
  1. search_labor_law      → Código do Trabalho (portal.act.gov.pt, pgdlisboa.pt)
  2. search_irs_tables     → Tabelas IRS (info.portaldasfinancas.gov.pt)
  3. search_social_security→ TSU / Seg. Social (diariodarepublica.pt, seg-social.pt)

Cada tool usa domínios específicos para a sua fonte — sem sobreposição.
As queries chegam limpas do LLM, sem sufixos ou augmentation.
"""

from typing import Dict, Any, Optional

from .data import (
    tavily_client,
    DOMAINS_LABOR_LAW,
    DOMAINS_IRS,
    DOMAINS_SOCIAL_SECURITY,
    IRS_TABLES_2025,
)


# ---------------------------------------------------------------------------
# Helper de busca Tavily
# ---------------------------------------------------------------------------
def _tavily_search(query: str, domains: list, max_results: int = 5) -> Dict[str, Any]:
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
