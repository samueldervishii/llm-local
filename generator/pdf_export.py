"""PDF export utility for converting markdown reviews to PDF."""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path


# Professional CSS styling for PDF
PDF_STYLES = """
@page {
    size: A4;
    margin: 2cm;
    @top-right {
        content: "CONFIDENTIAL";
        font-size: 9px;
        color: #888;
    }
    @bottom-center {
        content: counter(page) " of " counter(pages);
        font-size: 9px;
        color: #888;
    }
}

body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

h1 {
    color: #1a365d;
    border-bottom: 3px solid #2b6cb0;
    padding-bottom: 10px;
    font-size: 22pt;
}

h2 {
    color: #2b6cb0;
    margin-top: 25px;
    font-size: 14pt;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 5px;
}

h3 {
    color: #4a5568;
    font-size: 12pt;
    margin-top: 15px;
}

p {
    margin-bottom: 10px;
    text-align: justify;
}

ul, ol {
    margin-left: 20px;
    margin-bottom: 15px;
}

li {
    margin-bottom: 5px;
}

strong {
    color: #1a365d;
}

hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 20px 0;
}

blockquote {
    border-left: 4px solid #2b6cb0;
    padding-left: 15px;
    margin-left: 0;
    color: #4a5568;
    font-style: italic;
}

code {
    background-color: #f7fafc;
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 10pt;
}

.header-meta {
    background-color: #f7fafc;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}

.notice {
    background-color: #fff5f5;
    border: 1px solid #fc8181;
    padding: 15px;
    border-radius: 5px;
    margin-top: 30px;
}

.notice strong {
    color: #c53030;
}
"""

# Template-specific style overrides
TEMPLATE_STYLES = {
    "formal": """
        body { font-family: 'Times New Roman', Times, serif; }
        h1 { color: #1a1a1a; border-bottom-color: #333; }
        h2 { color: #333; }
    """,
    "casual": """
        body { font-family: 'Segoe UI', Tahoma, sans-serif; }
        h1 { color: #2d3748; border-bottom-color: #4299e1; }
        h2 { color: #4299e1; }
        blockquote { border-left-color: #4299e1; }
    """,
    "technical": """
        body { font-family: 'Consolas', 'Monaco', monospace; font-size: 10pt; }
        h1 { color: #0d1117; border-bottom-color: #238636; }
        h2 { color: #238636; }
        code { background-color: #f6f8fa; border: 1px solid #d0d7de; }
    """,
}


def markdown_to_pdf(
    markdown_content: str,
    output_path: str,
    template: str = "formal"
) -> str:
    """
    Convert markdown content to a styled PDF.

    Args:
        markdown_content: Markdown text to convert.
        output_path: Path for the output PDF file.
        template: Style template ('formal', 'casual', 'technical').

    Returns:
        Path to the generated PDF file.
    """
    # Convert markdown to HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=['tables', 'fenced_code', 'toc']
    )

    # Wrap in HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Performance Review</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Combine base styles with template-specific styles
    template_style = TEMPLATE_STYLES.get(template, "")
    combined_css = PDF_STYLES + template_style

    # Generate PDF
    html_doc = HTML(string=full_html)
    css = CSS(string=combined_css)
    html_doc.write_pdf(output_path, stylesheets=[css])

    return output_path


def convert_existing_review(
    markdown_path: str,
    template: str = "formal"
) -> str:
    """
    Convert an existing markdown review file to PDF.

    Args:
        markdown_path: Path to the markdown file.
        template: Style template to use.

    Returns:
        Path to the generated PDF file.
    """
    md_path = Path(markdown_path)
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    # Read markdown content
    content = md_path.read_text(encoding="utf-8")

    # Generate PDF path (same name, .pdf extension)
    pdf_path = md_path.with_suffix(".pdf")

    return markdown_to_pdf(content, str(pdf_path), template)
