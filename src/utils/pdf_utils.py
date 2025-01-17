"""PDF generation utilities."""
import logging
from datetime import datetime
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

def create_paragraph(text: str, style) -> Paragraph:
    """Create a paragraph with proper text wrapping."""
    return Paragraph(text.replace('\n', '<br/>'), style)

def convert_to_pdf(results: List[Dict], fi_name: str, output_path: str) -> str:
    """Convert search results to PDF.
    
    Args:
        results: List of search results
        fi_name: Financial institution name
        output_path: Path to save the PDF
        
    Returns:
        Path to the generated PDF file
    """
    try:
        logging.info(f"Converting results to PDF for {fi_name}")
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Create custom styles
        risk_style = ParagraphStyle(
            'RiskStyle',
            parent=normal_style,
            textColor=colors.red,
            spaceAfter=12
        )
        
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=normal_style,
            fontSize=9,
            leading=12,
            spaceBefore=6,
            spaceAfter=6
        )
        
        link_style = ParagraphStyle(
            'LinkStyle',
            parent=cell_style,
            textColor=colors.blue,
            underline=True
        )
        
        # Build the document content
        content = []
        
        # Title
        content.append(Paragraph(f"Adverse News Report - {fi_name}", title_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Date
        content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Summary if available
        if results and len(results) > 0:
            content.append(Paragraph("Risk Summary", heading_style))
            content.append(Spacer(1, 0.1*inch))
            
            # Calculate summary stats
            highest_score = max(float(r['analysis']['score']) for r in results)
            content.append(Paragraph(f"Number of Articles: {len(results)}", normal_style))
            content.append(Paragraph(f"Highest Risk Score: {highest_score}", risk_style))
            content.append(Spacer(1, 0.25*inch))
        
        # Individual results
        content.append(Paragraph("Detailed Findings", heading_style))
        content.append(Spacer(1, 0.1*inch))
        
        for i, result in enumerate(results, 1):
            # Article header with risk score
            content.append(Paragraph(
                f"Article {i} - Risk Score: {result['analysis']['score']}",
                heading_style
            ))
            
            # Article details with wrapped text
            data = [
                ["Title:", create_paragraph(result['title'], cell_style)],
                ["Source:", create_paragraph(result['source'], cell_style)],
                ["Date:", create_paragraph(result.get('date', 'Not available'), cell_style)],
                ["Link:", create_paragraph(
                    f'<link href="{result["link"]}">{result["link"]}</link>',
                    link_style
                )],
                ["Analysis:", create_paragraph(
                    result['analysis'].get('reason', 
                    result['analysis'].get('summary', 'No analysis available')),
                    cell_style
                )]
            ]
            
            # Create table with auto-width columns
            available_width = 6.5 * inch  # Total available width
            label_width = 0.8 * inch      # Width for labels
            content_width = available_width - label_width
            
            table = Table(data, colWidths=[label_width, content_width])
            table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
                ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            
            content.append(table)
            content.append(Spacer(1, 0.25*inch))
        
        # Build the PDF
        doc.build(content)
        logging.info(f"PDF generated successfully at {output_path}")
        return output_path
        
    except Exception as e:
        logging.error(f"Error generating PDF: {str(e)}")
        raise
