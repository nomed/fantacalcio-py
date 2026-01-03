"""
Shared HTML template for Fantacalcio analysis output
"""
import pandas as pd


def generate_html_output(df, source_name):
    """
    Generate a styled HTML page from a DataFrame.
    
    Args:
        df: pandas DataFrame with player data
        source_name: Name of the data source (e.g., 'fpedia', 'fstats', 'unified')
    
    Returns:
        str: Complete HTML page as a string
    """
    html_content = df.to_html(index=False, classes='table table-striped table-hover', border=0)
    
    # Create a complete HTML page with styling
    full_html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fantacalcio Analysis - {source_name.upper()}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 100%;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        h1 {{
            color: #333;
            margin-top: 0;
        }}
        .metadata {{
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border-left: 4px solid #007bff;
        }}
        .metadata p {{
            margin: 5px 0;
            color: #666;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #007bff;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        td {{
            padding: 10px 8px;
            border-bottom: 1px solid #dee2e6;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        tr:nth-child(even) {{
            background-color: #fafafa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 Fantacalcio Analysis - {source_name.upper()}</h1>
        <div class="metadata">
            <p><strong>Source:</strong> {source_name}</p>
            <p><strong>Total Players:</strong> {len(df)}</p>
            <p><strong>Generated:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        {html_content}
    </div>
</body>
</html>"""
    
    return full_html
