"""Service for generating PDF reports."""
from typing import List, Dict
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generate_adverse_news_report(articles: List[Dict], search_name: str, months: int, output_path: str):
    """Generate a PDF report for adverse news search results."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    story.append(Paragraph(f"Adverse News Report: {search_name}", title_style))
    
    # Search Parameters
    story.append(Paragraph(f"Search Period: {months} months", styles["Heading2"]))
    story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 20))

    # Summary Statistics
    total_articles = len(articles)
    adverse_articles = sum(1 for a in articles if a['analysis'].get('is_adverse', False))
    avg_score = sum(a['analysis'].get('score', 0) for a in articles) / total_articles if total_articles > 0 else 0
    
    stats = [
        ["Total Articles Analyzed:", str(total_articles)],
        ["Adverse News Found:", str(adverse_articles)],
        ["Average Severity Score:", f"{avg_score:.1f}/100"]
    ]
    
    stats_table = Table(stats, colWidths=[200, 100])
    stats_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 20))

    # Detailed Results
    story.append(Paragraph("Detailed Analysis", styles["Heading2"]))
    
    for idx, article in enumerate(sorted(articles, key=lambda x: x['analysis'].get('score', 0), reverse=True), 1):
        analysis = article['analysis']
        
        # Article Header
        story.append(Paragraph(f"Article {idx}: {article['title']}", styles["Heading3"]))
        story.append(Paragraph(f"Source: {article['source']}", styles["Normal"]))
        story.append(Paragraph(f"Link: {article['link']}", styles["Normal"]))
        story.append(Spacer(1, 10))
        
        # Analysis Results
        data = [
            ["Adverse News:", "Yes" if analysis.get('is_adverse', False) else "No"],
            ["Severity Score:", f"{analysis.get('score', 0)}/100"],
            ["Summary:", analysis.get('summary', 'N/A')],
            ["Reasoning:", analysis.get('reason', 'N/A')]
        ]
        
        t = Table(data, colWidths=[100, 400])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

    doc.build(story)
