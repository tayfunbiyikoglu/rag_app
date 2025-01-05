"""Service for generating reports in various formats."""
import logging
from typing import List, Dict
from datetime import datetime
import markdown
from weasyprint import HTML

def generate_markdown_report(fi_name: str, analyses: List[Dict], include_scoring_explanation: bool = True) -> str:
    """Generate final report in markdown format.
    
    Args:
        fi_name: Name of the financial institution
        analyses: List of analysis results
        include_scoring_explanation: Whether to include the scoring system explanation (default: True)
    """
    if not analyses:
        return "No analyses available to generate report."

    # Calculate overall score
    valid_scores = [(a['reliability_score'] * a['relevancy_score']) / 100
                   for a in analyses
                   if a['reliability_score'] and a['relevancy_score']]

    overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0

    # Build report sections
    report = _build_header_section(fi_name, overall_score, len(analyses))
    report += _build_key_findings_section(analyses)
    report += _build_detailed_analysis_section(analyses)
    report += _build_metadata_section(len(analyses))
    
    # Add scoring explanation at the end with a page break (only for PDF)
    if include_scoring_explanation:
        report += "\n\n<div style='page-break-before: always;'></div>\n\n"
        report += _build_scoring_explanation()

    return report

def convert_to_pdf(markdown_content: str, fi_name: str) -> bytes:
    """Convert markdown report to PDF format."""
    try:
        html_content = markdown.markdown(markdown_content)
        styled_html = _apply_pdf_styling(html_content)
        return HTML(string=styled_html).write_pdf()
    except Exception as e:
        logging.error(f"Error converting to PDF: {str(e)}")
        return None

def _build_header_section(fi_name: str, overall_score: float, num_sources: int) -> str:
    """Build the report header section."""
    return f"""
# Adverse News Report: {fi_name}

## Risk Assessment Summary
- **Institution**: {fi_name}
- **Overall Risk Score**: {overall_score:.2f}/100
- **Number of Sources Analyzed**: {num_sources}
"""

def _build_scoring_explanation() -> str:
    """Build the scoring system explanation section."""
    return """
## Understanding Our Two-Phase Analysis System

Our adverse news analysis employs a sophisticated two-phase approach to ensure accurate and relevant results:

### Phase 1: Initial Screening
• Performs Google search for adverse news
• Quick analysis of each result with composite scoring:
  - Risk Score (60%): Analyzes content for risk terms
  - Domain Score (25%): Rates source credibility
  - Recency Score (15%): Considers publication date

### Phase 2: Detailed Analysis
• In-depth content analysis of top results
• Evaluates relevancy with threshold of 50
• Final score combines:
  - Content relevancy (80%)
  - Source reliability (20%)

### Understanding Individual Scores

📊 **Overall Risk Score** (0-100):
- Combines Phase 1 and Phase 2 analysis
- Higher scores indicate more significant adverse news
- Weighted balance of content relevancy and source reliability

🎯 **Relevancy Score** (0-100):
- Measures how significant the adverse news content is
- Primary factor (80%) in determining overall risk
- Threshold of 50 required for significant findings

⭐ **Reliability Score** (0-100):
- Based on domain credibility and source quality
- Secondary factor (20%) in final scoring
- Helps prioritize reliable sources while not excluding others

### Key Benefits
✓ Smart scoring prioritizes important findings
✓ Considers both content and source quality
✓ Balances recency with relevance
"""

def _build_key_findings_section(analyses: List[Dict]) -> str:
    """Build the key findings section."""
    section = "\n## Key Findings Summary\n"
    
    high_risk_findings = []
    for analysis in analyses:
        if analysis['relevancy_score'] > 70:
            high_risk_findings.extend(analysis['key_findings'])

    if high_risk_findings:
        section += "\n### High-Risk Findings:\n"
        for finding in high_risk_findings:
            section += f"- {finding}\n"

    return section

def _build_detailed_analysis_section(analyses: List[Dict]) -> str:
    """Build the detailed analysis section."""
    section = "\n## Detailed Source Analysis\n"
    
    for i, analysis in enumerate(analyses, 1):
        section += f"\n### {i}. {analysis['url']}\n"
        section += f"- **Overall Risk Score**: {analysis['overall_risk_score']:.2f}\n"
        section += f"- **Reliability Score**: {analysis['reliability_score']}\n"
        section += f"- **Relevancy Score**: {analysis['relevancy_score']}\n"
        
        if analysis['key_findings']:
            section += "\n**Key Findings**:\n"
            for finding in analysis['key_findings']:
                section += f"- {finding}\n"
        
        # Add horizontal rule between analyses, except for the last one
        if i < len(analyses):
            section += "\n---\n"
    
    return section

def _build_metadata_section(num_sources: int) -> str:
    """Build the report metadata section."""
    return f"""
## Report Metadata
- **Generation Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total Sources**: {num_sources}
"""

def _apply_pdf_styling(html_content: str) -> str:
    """Apply styling to the PDF content."""
    css = """
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 40px;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #2c3e50;
                padding-bottom: 10px;
            }
            h2 {
                color: #34495e;
                margin-top: 30px;
            }
            h3 {
                color: #445566;
                margin-top: 25px;
            }
            h4 {
                color: #556677;
                margin-top: 20px;
            }
            .metadata {
                color: #666;
                font-size: 0.9em;
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }
            ul {
                margin-left: 20px;
                padding-left: 0;
            }
            li {
                margin-bottom: 10px;
            }
            /* Ensure page breaks work properly */
            div[style*='page-break-before: always'] {
                page-break-before: always;
                margin-top: 50px;
            }
            /* Add some spacing before the scoring explanation section */
            #understanding-our-two-phase-analysis-system {
                margin-top: 40px;
            }
        </style>
    """
    return f"<html><head>{css}</head><body>{html_content}</body></html>"
