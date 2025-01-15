"""Service for generating reports in various formats."""
import logging
from typing import List, Dict
from datetime import datetime
import markdown
from weasyprint import HTML

def generate_markdown_report(fi_name: str, analyses: List[Dict], include_scoring_explanation: bool = True, months_interval: int = 6) -> str:
    """Generate final report in markdown format.
    
    Args:
        fi_name: Name of the financial institution
        analyses: List of analysis results
        include_scoring_explanation: Whether to include the scoring system explanation (default: True)
        months_interval: Time period for the analysis (default: 6 months)
    """
    if not analyses:
        return "No analyses available to generate report."

    # Calculate average adversity score
    valid_scores = [a['adversity_score'] for a in analyses if a['adversity_score']]
    avg_adversity = sum(valid_scores) / len(valid_scores) if valid_scores else 0

    # Build report sections
    report = _build_header_section(fi_name, avg_adversity, len(analyses), months_interval)
    report += _build_key_findings_section(analyses)
    report += _build_detailed_analysis_section(analyses)
    report += _build_metadata_section(len(analyses))
    
    # Add scoring explanation at the end with a page break (only for PDF)
    if include_scoring_explanation:
        report += "\n\n<div style='page-break-before: always;'></div>\n\n"
        report += _build_scoring_explanation(months_interval)

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

def _build_header_section(fi_name: str, avg_adversity: float, num_sources: int, months_interval: int) -> str:
    """Build the report header section."""
    severity_level = "Low"
    if avg_adversity >= 8:
        severity_level = "Critical"
    elif avg_adversity >= 6:
        severity_level = "High"
    elif avg_adversity >= 4:
        severity_level = "Moderate"
    
    return f"""
# Adverse News Report: {fi_name}

## Risk Assessment Summary
- **Institution**: {fi_name}
- **Average Adversity Score**: {avg_adversity:.1f}/10 ({severity_level} Risk)
- **Number of Sources Analyzed**: {num_sources}
- **Time Period**: Last {months_interval} months
"""

def _build_scoring_explanation(months_interval: int) -> str:
    """Build the scoring system explanation section."""
    return f"""
## Understanding Our Analysis System

Our adverse news analysis employs a two-phase approach to identify and evaluate potential risks:

### Phase 1: Initial Screening
• Performs Google search for adverse news within the specified time period
• Quick analysis of each result with composite scoring:
  - Risk Score (60%): Analyzes content for risk indicators
  - Domain Score (25%): Rates source credibility
  - Recency Score (15%): Considers publication date

### Phase 2: Detailed Analysis
• In-depth AI analysis of top 10 most relevant results
• Each article is evaluated for adverse content
• Assigns an Adversity Score (1-10) based on severity

### Adversity Score Interpretation

🟢 **Low Risk (1-2)**
- Policy documents or non-adverse content
- Routine news or standard disclosures
- No significant adverse findings

🟡 **Potential Risk (3-4)**
- Minor concerns or potential issues
- Early-stage investigations
- Non-material regulatory inquiries

🟠 **Moderate Risk (5-6)**
- Notable concerns identified
- Ongoing regulatory attention
- Potential compliance issues

🔴 **High Risk (7-8)**
- Confirmed incidents
- Regulatory actions or fines
- Material compliance violations

⛔ **Critical Risk (9-10)**
- Major confirmed violations
- Significant legal actions
- Severe regulatory breaches

### Analysis Benefits
✓ Time-based search ensures relevance
✓ Smart filtering prioritizes important findings
✓ Simple, intuitive scoring system
✓ Focus on actual adverse events
✓ Clear risk level categorization

### Note on Time Period
This report covers news and events from the last {months_interval} months. Older events may exist but are not included to maintain focus on current risks."""

def _build_key_findings_section(analyses: List[Dict]) -> str:
    """Build the key findings section."""
    if not analyses:
        return "\n## Key Findings\nNo significant findings to report.\n"

    findings = []
    for analysis in sorted(analyses, key=lambda x: x['adversity_score'], reverse=True):
        if analysis['key_findings']:
            findings.extend(analysis['key_findings'])

    if not findings:
        return "\n## Key Findings\nNo significant findings to report.\n"

    findings = list(dict.fromkeys(findings))  # Remove duplicates
    findings_text = "\n".join(f"- {finding}" for finding in findings[:10])
    
    return f"""
## Key Findings
{findings_text}
"""

def _build_detailed_analysis_section(analyses: List[Dict]) -> str:
    """Build the detailed analysis section."""
    if not analyses:
        return "\n## Detailed Analysis\nNo detailed analysis available.\n"

    sections = []
    for idx, analysis in enumerate(sorted(analyses, key=lambda x: x['adversity_score'], reverse=True)):
        severity = "Critical" if analysis['adversity_score'] >= 8 else \
                  "High" if analysis['adversity_score'] >= 6 else \
                  "Moderate" if analysis['adversity_score'] >= 4 else "Low"
        
        section = f"""
### Source {idx + 1}: {severity} Risk
- **Adversity Score**: {analysis['adversity_score']}/10
- **Summary**: {analysis['summary']}
- **Key Points**:"""
        
        for finding in analysis['key_findings']:
            section += f"\n  - {finding}"
        
        sections.append(section)

    return "\n## Detailed Analysis\n" + "\n".join(sections)

def _build_metadata_section(num_sources: int) -> str:
    """Build the report metadata section."""
    return f"""
## Report Metadata
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Sources Analyzed**: {num_sources}
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
