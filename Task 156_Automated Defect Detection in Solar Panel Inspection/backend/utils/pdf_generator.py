import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from backend.utils.logger import setup_logger

logger = setup_logger("pdf_generator")


def generate_pdf_report(
    pdf_path: str,
    original_img_path: str,
    annotated_img_path: str,
    detections: list,
    stats: dict,
    severity_summary: Optional[dict] = None,
    maintenance_summary: Optional[dict] = None,
    tickets: Optional[list] = None,
    run_dir: Optional[Path] = None
) -> bool:
    """
    Generate a certified engineering report in PDF format including:
    - Original image & Annotated image
    - Metadata and Inference Statistics
    - Severity Analysis Breakdown
    - Maintenance Recommendations & Automated Tickets
    - Anomaly Detection Table with Severity & Recommended Action
    - Defect evidence crops
    """
    logger.info(f"Generating certified PDF engineering report at {pdf_path}...")
    try:
        doc = SimpleDocTemplate(
            pdf_path, 
            pagesize=letter, 
            rightMargin=36, 
            leftMargin=36, 
            topMargin=36, 
            bottomMargin=36
        )
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=10
        )
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=10,
            spaceAfter=4
        )
        text_style = ParagraphStyle(
            'TextStyle',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#334155')
        )
        
        # Header / Title
        story.append(Paragraph("SolarLens AI - Certified Engineering Inspection Report", title_style))
        story.append(Spacer(1, 6))
        
        # Metadata and Stats Table
        class_dist_str = ", ".join([f"{k} ({v})" for k, v in stats.get('class_distribution', {}).items()]) or "None"
            
        meta_data = [
            [Paragraph("<b>Inspection Metadata</b>", section_style), Paragraph("<b>Inference Statistics</b>", section_style)],
            [
                Paragraph(
                    f"<b>Model Filename:</b> {stats.get('model_filename', 'N/A')}<br/>"
                    f"<b>Device:</b> {stats.get('device', 'cpu')}<br/>"
                    f"<b>Input Resolution:</b> {stats.get('input_resolution', 'N/A')}<br/>"
                    f"<b>Inference Time:</b> {stats.get('inference_time_ms', 0.0)} ms", 
                    text_style
                ),
                Paragraph(
                    f"<b>Total Detections:</b> {stats.get('total_detections', 0)}<br/>"
                    f"<b>Average Confidence:</b> {round(stats.get('average_confidence', 0.0) * 100, 1)}%<br/>"
                    f"<b>Highest Confidence:</b> {round(stats.get('highest_confidence', 0.0) * 100, 1)}%<br/>"
                    f"<b>Class Distribution:</b> {class_dist_str}", 
                    text_style
                )
            ]
        ]
        
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 8))
        
        # Severity & Maintenance Breakdown Section
        if severity_summary and maintenance_summary:
            sev_data = [
                [Paragraph("<b>Severity Summary</b>", section_style), Paragraph("<b>Maintenance Summary</b>", section_style)],
                [
                    Paragraph(
                        f"<b>Low Severity:</b> {severity_summary.get('low', 0)}<br/>"
                        f"<b>Medium Severity:</b> {severity_summary.get('medium', 0)}<br/>"
                        f"<b>High Severity:</b> {severity_summary.get('high', 0)}<br/>"
                        f"<b>Critical Severity:</b> {severity_summary.get('critical', 0)}",
                        text_style
                    ),
                    Paragraph(
                        f"<b>Monitor:</b> {maintenance_summary.get('monitor_count', 0)}<br/>"
                        f"<b>Review:</b> {maintenance_summary.get('review_count', 0)}<br/>"
                        f"<b>Maintenance Required:</b> {maintenance_summary.get('maintenance_required_count', 0)}<br/>"
                        f"<b>Priority Maintenance:</b> {maintenance_summary.get('priority_maintenance_count', 0)}",
                        text_style
                    )
                ]
            ]
            sev_table = Table(sev_data, colWidths=[270, 270])
            sev_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(sev_table)
            story.append(Spacer(1, 8))

        # Side-by-side Visual Images (Original vs. Annotated)
        story.append(Paragraph("<b>Visual Analytics (Original vs. Annotated YOLO Detections)</b>", section_style))
        try:
            if os.path.exists(original_img_path) and os.path.exists(annotated_img_path):
                img1 = Image(original_img_path, width=250, height=185)
                img2 = Image(annotated_img_path, width=250, height=185)
                img_table = Table([[img1, img2]], colWidths=[270, 270])
                img_table.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ]))
                story.append(img_table)
            else:
                story.append(Paragraph("[Error: Visual image files missing on disk]", text_style))
        except Exception as e:
            logger.error(f"Error adding images to PDF: {str(e)}")
            story.append(Paragraph(f"[Error rendering visual images: {str(e)}]", text_style))
            
        story.append(Spacer(1, 10))
        
        # Anomaly Detection Table with Extended Fields
        story.append(Paragraph("<b>Anomaly Detections & Severity Scoring Table</b>", section_style))
        
        table_data = [["ID", "Class", "Confidence", "Severity", "Action", "Ticket ID"]]
        for det in detections:
            conf_val = det.get("confidence", 0.0)
            conf_str = f"{round(conf_val * 100, 1)}%"
            sev_score = det.get("severity_score", round(conf_val * 100, 1))
            sev_level = det.get("severity_level", "LOW")
            action = det.get("recommended_action", "MONITOR")
            ticket_id = det.get("ticket_id") or "N/A"

            table_data.append([
                str(det.get("detection_id", "")),
                det.get("class_name", "Unknown"),
                conf_str,
                f"{sev_score} ({sev_level})",
                action,
                ticket_id
            ])
            
        if not detections:
            table_data.append(["-", "No anomalies detected", "-", "-", "-", "-"])
            
        det_table = Table(table_data, colWidths=[35, 120, 65, 95, 135, 90])
        det_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0f172a')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 4),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
        ]))
        story.append(det_table)
        
        # Maintenance Tickets Section if tickets exist
        if tickets and len(tickets) > 0:
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>Automated Maintenance Tickets</b>", section_style))
            ticket_table_data = [["Ticket ID", "Defect Class", "Priority", "Status", "Recommended Action"]]
            for t in tickets:
                ticket_table_data.append([
                    t.get("ticket_id", ""),
                    t.get("class_name", ""),
                    t.get("priority", ""),
                    t.get("status", "OPEN"),
                    t.get("recommended_action", "")
                ])
            t_table = Table(ticket_table_data, colWidths=[95, 125, 70, 70, 180])
            t_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#fef3c7')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#78350f')),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#fde68a')),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(t_table)

        # Build Document
        doc.build(story)
        logger.info(f"PDF report successfully created at {pdf_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {str(e)}")
        return False
