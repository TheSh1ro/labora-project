# backend\app\agent\__init__.py

from .core import LaborLawAgent
from .prompts import AGENT_CONFIG

agent = LaborLawAgent()
