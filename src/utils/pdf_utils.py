"""Utilities for PDF generation."""
import markdown
from weasyprint import HTML
from io import BytesIO

def convert_to_pdf(markdown_content: str) -> bytes:
    """Convert markdown content to PDF."""
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content)
    
    # Add some basic styling
    styled_html = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 2cm;
                }}
                h1 {{
                    color: #4B4BC8;
                    border-bottom: 2px solid #4B4BC8;
                    padding-bottom: 10px;
                    text-align: center;
                }}
                h2 {{
                    color: #3939A2;
                    margin-top: 30px;
                }}
                h3 {{
                    color: #2F2F8C;
                    margin-top: 25px;
                    border-left: 3px solid #4B4BC8;
                    padding-left: 10px;
                }}
                a {{
                    color: #4B4BC8;
                    text-decoration: none;
                }}
                .risk-score {{
                    font-weight: bold;
                    color: #E50050;
                }}
                .date {{
                    color: #666;
                    font-style: italic;
                }}
                ul {{
                    list-style-type: none;
                    padding-left: 0;
                }}
                li {{
                    margin-bottom: 8px;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
    </html>
    """
    
    # Convert to PDF
    pdf_buffer = BytesIO()
    HTML(string=styled_html).write_pdf(pdf_buffer)
    
    return pdf_buffer.getvalue()
