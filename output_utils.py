"""
Shared utilities for saving analysis results
"""
import os
import json
import pandas as pd
import config
from html_template import generate_html_output


def save_analysis_results(df, base_name, source_name):
    """
    Save analysis results in Excel, JSON, and HTML formats.
    
    Args:
        df: pandas DataFrame with player data
        base_name: Base filename (without extension) for output files
        source_name: Name of the data source (e.g., 'fpedia', 'fstats', 'unified')
    
    Returns:
        tuple: (excel_path, json_path, html_path) - paths to the generated files
    """
    # Excel output
    excel_path = os.path.join(config.OUTPUT_DIR, f"{base_name}.xlsx")
    df.to_excel(excel_path, index=False)

    # JSON output
    json_path = os.path.join(config.OUTPUT_DIR, f"{base_name}.json")
    data = {
        "metadata": {
            "source": source_name,
            "total_players": len(df),
            "generated_at": pd.Timestamp.now().isoformat(),
            "columns": list(df.columns)
        },
        "players": df.where(pd.notnull(df), None).to_dict("records")
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # HTML output
    html_path = os.path.join(config.OUTPUT_DIR, f"{base_name}.html")
    full_html = generate_html_output(df, source_name)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    return excel_path, json_path, html_path
