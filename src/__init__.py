"""
TNO AI Audit Document Scanner
Core package for semantic document classification and type verification.
"""

from .interfaces import Document, ComplianceResult
from .semantic_classifier import SemanticClassifier, classify_document_semantically
from .type_verification import TypeVerification, verify_document_types
from .results_visualizer import ResultsVisualizer, generate_visualization_reports

__version__ = "0.2.0"