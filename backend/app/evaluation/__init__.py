# backend\app\evaluation\__init__.py

"""
Suite de Avaliação do Agente de Direito Laboral.
Implementa casos de teste e métricas de qualidade.
"""

from .harness import EvaluationHarness

# Instância global
evaluation_harness = EvaluationHarness()
