# backend\app\tools\data.py

"""
Dados estáticos e cliente Tavily para as tools do agente.
"""

import os
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

# Fonte 1: Código do Trabalho — ACT + pgdlisboa (versão consolidada articulada) + CITE
DOMAINS_LABOR_LAW = [
    "portal.act.gov.pt",
    "www.pgdlisboa.pt",
    "www.cite.gov.pt",
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
