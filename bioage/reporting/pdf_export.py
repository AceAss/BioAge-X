"""
PDF Export Utility for BioAge-X.
Generates styled scientific PDF research reports using ReportLab.
"""

from pathlib import Path
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from bioage.utils.logger import get_logger

logger = get_logger("bioage.reporting.pdf")


def export_report_to_pdf(report_data: Dict[str, Any], output_path: str | Path) -> str:
    """Generates a PDF research summary document from report data."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    
    # Custom palette
    primary_color = colors.HexColor("#0f172a")
    teal_accent = colors.HexColor("#0d9488")
    dark_gray = colors.HexColor("#334155")
    light_bg = colors.HexColor("#f8fafc")

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=teal_accent,
    )

    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=dark_gray,
    )

    story = []

    # Title & Metadata
    meta = report_data.get("metadata", {})
    story.append(Paragraph("BIOAGE-X RESEARCH REPORT", title_style))
    story.append(Paragraph("Explainable Multi-Omics Biological Age Estimation Platform", subtitle_style))
    story.append(Spacer(1, 8))

    meta_text = (
        f"<b>Experiment:</b> {meta.get('experiment_id', 'N/A')} | "
        f"<b>Dataset:</b> {meta.get('dataset_name', 'N/A')} | "
        f"<b>Date:</b> {meta.get('generated_at', 'N/A')} | "
        f"<b>Hash:</b> <code>{meta.get('reproducibility_hash', 'N/A')}</code>"
    )
    story.append(Paragraph(meta_text, body_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=teal_accent, spaceBefore=4, spaceAfter=10))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary & Benchmark Metrics", h2_style))
    perf = report_data.get("model_performance", {})
    accel = report_data.get("age_acceleration", {})

    exec_table_data = [
        ["Model Evaluated", meta.get("model_name", "N/A"), "Sample Count", str(perf.get("sample_count", "N/A"))],
        ["Mean Absolute Error (MAE)", f"{perf.get('mae', 'N/A')} years", "Root Mean Sq Error (RMSE)", f"{perf.get('rmse', 'N/A')} years"],
        ["Coefficient of Det. (R²)", str(perf.get("r2", "N/A")), "Pearson Correlation (r)", str(perf.get("pearson_r", "N/A"))],
        ["Mean Age Acceleration", f"{accel.get('mean_acceleration', 0.0)} yrs", "Accelerated / Decelerated", f"{accel.get('accelerated_count', 0)} / {accel.get('decelerated_count', 0)}"],
    ]

    exec_table = Table(exec_table_data, colWidths=[150, 110, 150, 110])
    exec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TEXTCOLOR", (0, 0), (0, -1), primary_color),
        ("TEXTCOLOR", (2, 0), (2, -1), primary_color),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
    ]))
    story.append(exec_table)
    story.append(Spacer(1, 10))

    # Top Biomarkers
    story.append(Paragraph("2. Top Biomolecular Drivers (SHAP Attribution)", h2_style))
    biomarkers = report_data.get("shap_biomarkers", [])[:6]
    bio_table_data = [["Rank", "Feature / Gene", "Mean |SHAP|", "Effect", "Biological Annotation"]]
    
    for idx, bm in enumerate(biomarkers, 1):
        bio_table_data.append([
            str(idx),
            bm.get("gene_symbol", bm.get("feature", "N/A")),
            str(bm.get("mean_abs_shap", "N/A")),
            bm.get("direction", "N/A"),
            Paragraph(bm.get("biological_role", "Covariate")[:90] + "...", body_style),
        ])

    bio_table = Table(bio_table_data, colWidths=[35, 95, 70, 85, 235])
    bio_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(bio_table)
    story.append(Spacer(1, 10))

    # Enriched Pathways
    story.append(Paragraph("3. Functional Aging Pathway Over-Representation", h2_style))
    pathways = report_data.get("pathway_enrichment", [])[:5]
    pw_table_data = [["Pathway Name", "Category", "Overlap", "P-Value", "Adj. FDR"]]
    for pw in pathways:
        pw_table_data.append([
            pw.get("pathway_name", "N/A"),
            pw.get("category", "N/A"),
            f"{pw.get('overlap_count', 0)}/{pw.get('pathway_size', 0)}",
            f"{pw.get('p_value', 1.0):.2e}",
            f"{pw.get('fdr_adjusted_p', 1.0):.4f}",
        ])

    pw_table = Table(pw_table_data, colWidths=[180, 110, 70, 80, 80])
    pw_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), teal_accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(pw_table)
    story.append(Spacer(1, 10))

    # Limitations & Disclaimers
    story.append(Paragraph("4. Scientific Rigor & Platform Limitations", h2_style))
    for lim in report_data.get("scientific_limitations", []):
        story.append(Paragraph(f"• {lim}", body_style))
        story.append(Spacer(1, 2))

    doc.build(story)
    logger.info(f"Generated PDF research report at: {path}")
    return str(path)
