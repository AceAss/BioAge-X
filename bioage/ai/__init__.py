"""
BioAge-X AI Research Assistant Module.
Provides optional, evidence-grounded natural language interpretation
of computational biology results using Google Gemini.
Operates strictly downstream of statistical, ML, SHAP, and network computations.
"""

from bioage.ai.gemini_client import GeminiAssistantClient, GeminiInterpretation

__all__ = ["GeminiAssistantClient", "GeminiInterpretation"]
