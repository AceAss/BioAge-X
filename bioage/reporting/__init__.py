"""Reporting module for BioAge-X."""
from bioage.reporting.report_generator import ResearchReportGenerator
from bioage.reporting.pdf_export import export_report_to_pdf
from bioage.reporting.manuscript_report import ManuscriptReportGenerator
from bioage.reporting.figures import (
    plot_predicted_vs_chronological_age,
    plot_residuals_age_bias,
    plot_model_comparison_with_ci,
    plot_shap_feature_importance,
    plot_pathway_enrichment,
)

__all__ = [
    "ResearchReportGenerator",
    "export_report_to_pdf",
    "ManuscriptReportGenerator",
    "plot_predicted_vs_chronological_age",
    "plot_residuals_age_bias",
    "plot_model_comparison_with_ci",
    "plot_shap_feature_importance",
    "plot_pathway_enrichment",
]
