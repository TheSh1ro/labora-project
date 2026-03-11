# backend\app\tools\calculations.py

"""
Cálculos locais (sem I/O — resultados determinísticos).
"""

from typing import Dict, Any, Optional

from .data import MINIMUM_WAGE_2025, TSU_RATES


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
