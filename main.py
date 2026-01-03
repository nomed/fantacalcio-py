# main.py
import os
from loguru import logger
import pandas as pd
import json

import data_retriever
import data_processor
import convenienza_calculator
import fuzzy_matcher
import config


def save_analysis_results(df, base_name, source_name):
    """Save analysis results in Excel, JSON, and HTML formats"""

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
        "players": df.fillna("").to_dict("records")
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # HTML output
    html_path = os.path.join(config.OUTPUT_DIR, f"{base_name}.html")
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
        .numeric {{
            text-align: right;
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
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    return excel_path, json_path, html_path


def merge_datasets_with_mapping(
    df_fpedia_final, df_fstats_final, mapping_file=fuzzy_matcher.OUTPUT_FILE
):
    """
    Unisce i due dataset usando il mapping dei nomi generato dal fuzzymatcher
    """
    logger.info("Starting dataset merge with fuzzy mapping...")

    # carica il mapping
    if not os.path.exists(mapping_file):
        logger.warning(f"Mapping file {mapping_file} not found. Skipping merge.")
        return pd.DataFrame()

    with open(mapping_file, "r", encoding="utf-8") as f:
        mapping_data = json.load(f)

    mapping = mapping_data.get("mapping", {})
    probably_mapped_ns = mapping_data.get("probably_mapped_ns", {})

    # unisci i dizionari di mapping
    all_mapping = {**mapping, **probably_mapped_ns}

    logger.info(f"Found {len(all_mapping)} player mappings")

    # MERGING
    df_fpedia_merge = df_fpedia_final.copy()
    df_fstats_merge = df_fstats_final.copy()

    fpedia_cols = {
        col: f"fpedia_{col}"
        for col in df_fpedia_merge.columns
        if col not in ["Nome", "Ruolo", "Squadra"]
    }
    fstats_cols = {
        col: f"fstats_{col}"
        for col in df_fstats_merge.columns
        if col not in ["Nome", "Ruolo", "Squadra"]
    }

    df_fpedia_merge = df_fpedia_merge.rename(columns=fpedia_cols)
    df_fstats_merge = df_fstats_merge.rename(columns=fstats_cols)

    df_fpedia_merge["mapped_name"] = df_fpedia_merge["Nome"].map(all_mapping)
    df_fstats_merge["mapped_name"] = (
        df_fstats_merge["fstats_firstname"].fillna("")
        + " "
        + df_fstats_merge["fstats_lastname"].fillna("")
    ).str.strip()


    df_merged = pd.merge(
        df_fpedia_merge,
        df_fstats_merge,
        on="mapped_name",
        how="inner",
        suffixes=("_fpedia", "_fstats"),
    )

    priority_cols = [
        "Nome_fpedia",  # Nome originale FPEDIA
        "mapped_name",  # Nome mappato FSTATS
        "Ruolo",
        "Squadra",
        "fpedia_Convenienza Potenziale",
        "fstats_Convenienza Potenziale",
        "fpedia_Convenienza",
        "fstats_Convenienza",
        "fpedia_Punteggio",
        "fstats_fantacalcioFantaindex",
        "fstats_fanta_avg",
        "fstats_presences",
    ]
    remaining_cols = [col for col in df_merged.columns if col not in priority_cols]
    final_col_order = [
        col for col in priority_cols if col in df_merged.columns
    ] + remaining_cols

    df_merged = df_merged[final_col_order]

    logger.info(f"Merged dataset contains {df_merged.shape[0]} players")
    return df_merged


def main():
    """
    Main script to run the entire Fantacalcio analysis pipeline.
    It now runs two separate pipelines for FPEDIA and FSTATS,
    generates both performance-based and potential-based convenience indexes,
    and creates a unified analysis using fuzzy matching.
    """
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    logger.info("Starting Fantacalcio analysis pipeline...")
    logger.info("Step 1: Retrieving data from all sources...")
    data_retriever.scrape_fpedia(force=config.FORCE_SCRAPING_MAIN)
    data_retriever.fetch_FSTATS_data(force=config.FORCE_SCRAPING_MAIN)
    logger.info("Data retrieval complete.")

    # 2. Generate fuzzy mapping
    logger.info("Step 2: Generating fuzzy name mapping...")
    try:
        fuzzy_matcher.start_matching(
            df_giocatori_path=config.GIOCATORI_CSV,
            df_players_path=config.PLAYERS_CSV,
        )
        logger.info("Fuzzy mapping complete.")
    except Exception as e:
        logger.error(f"Error in fuzzy matching: {e}")

    # 3. Load dataframes
    df_fpedia, df_FSTATS = data_processor.load_dataframes()

    df_fpedia_final = None
    df_fstats_final = None

    # --- Pipeline for FPEDIA ---
    if not df_fpedia.empty:
        logger.info("--- Starting FPEDIA Pipeline ---")

        df_processed = data_processor.process_fpedia_data(df_fpedia)
        df_final = convenienza_calculator.calcola_convenienza_fpedia(df_processed)

        df_final = df_final.sort_values(by="Convenienza Potenziale", ascending=False)

        # Define a comprehensive and ordered list of columns for the final output
        output_columns = [
            # Key Info
            "Nome",
            "Ruolo",
            "Squadra",
            # Calculated Indexes
            "Convenienza Potenziale",
            "Convenienza",
            "Punteggio",
            # Current Season Stats
            f"Fantamedia anno {config.ANNO_CORRENTE-1}-{config.ANNO_CORRENTE}",
            f"Presenze campionato corrente",
            # Previous Season Stats
            f"Fantamedia anno {config.ANNO_CORRENTE-2}-{config.ANNO_CORRENTE-1}",
            "Partite giocate",
            # Qualitative Info
            "Trend",
            "Skills",
            "Consigliato prossima giornata",
            "Buon investimento",
            "Resistenza infortuni",
            "Infortunato",
            # Legacy
            f"FM su tot gare {config.ANNO_CORRENTE-1}-{config.ANNO_CORRENTE}",
            "Presenze previste",
            "Gol previsti",
            "Assist previsti",
            "Nuovo acquisto",
        ]
        final_columns = [col for col in output_columns if col in df_final.columns]

        # Save Excel, JSON, and HTML
        excel_path, json_path, html_path = save_analysis_results(
            df_final[final_columns], "fpedia_analysis", "fpedia"
        )

        df_fpedia_final = df_final.copy()  # Salva per il merge

        logger.info(f"FPEDIA analysis complete. Results saved to {excel_path}")
        logger.info(f"FPEDIA JSON export saved to {json_path}")
        logger.info(f"FPEDIA HTML export saved to {html_path}")
    else:
        logger.warning("FPEDIA DataFrame is empty. Pipeline skipped.")

    # --- Pipeline for FSTATS ---
    if not df_FSTATS.empty:
        logger.info("--- Starting FSTATS Pipeline ---")

        df_processed = data_processor.process_FSTATS_data(df_FSTATS)
        df_final = convenienza_calculator.calcola_convenienza_FSTATS(df_processed)

        df_final = df_final.sort_values(by="Convenienza Potenziale", ascending=False)

        # Define a comprehensive and ordered list of columns for the final output
        output_columns = [
            # Key Info
            "Nome",
            "Ruolo",
            "Squadra",
            # Calculated Indexes
            "Convenienza Potenziale",
            "Convenienza",
            "fantacalcioFantaindex",
            # Key Performance Indicators
            "fanta_avg",
            "avg",
            "presences",
            # Core Stats
            "goals",
            "assists",
            # Potential Stats
            "xgFromOpenPlays",
            "xA",
            # Disciplinary
            "yellowCards",
            "redCards",
            # Legacy
            "injured",
            "banned",
            "mantra_position",
            "fantacalcio_position",
            "birth_date",
            "foot_name",
            "fantacalcioPlayerId",
            "fantacalcioTeamName",
            "appearances",
            "matchesInStart",
            "mins_played",
            "pagella",
            "fantacalcioRanking",
            "fantacalcioFantaindex",
            "fantacalcioPosition",
            "goals90min",
            "goalsFromOpenPlays",
            "xgFromOpenPlays/90min",
            "xA90min",
            "successfulPenalties",
            "penalties",
            "gkPenaltiesSaved",
            "gkCleanSheets",
            "gkConcededGoals",
            "openPlaysGoalsConceded",
            "openPlaysXgConceded",
            "fantamediaPred",
            "fantamediaPredRoundId",
            "matchConvocation",
            "matchesWithGrade",
            "perc_matchesStarted",
            "perc_matchesWithGrade",
            "percMinsPlayed",
            "expectedFantamediaMean",
            "External_breakout_Index",
            "Shot_on_goal_Index",
            "Offensive_actions_Index",
            "Pass_forward_accuracy_Index",
            "Air_challenge_offensive_Index",
            "Cross_accuracy_Index",
            "Converge_in_the_center_Index",
            "Accompany_the_offensive_action_Index",
            "Offensive_verticalization_Index",
            "Received_pass_Index",
            "Attacking_area_Index",
            "Offensive_field_presence_Index",
            "Pass_accuracy_Index",
            "Pass_leading_chances_Index",
            "Deep_runs_Index",
            "Defense_solidity_Index",
            "Set_piece_attack_Index",
            "Shot_on_target_Index",
            "Dribbles_successful_Index",
            "firstname",
            "lastname",
        ]
        final_columns = [col for col in output_columns if col in df_final.columns]

        # Save Excel, JSON, and HTML
        excel_path, json_path, html_path = save_analysis_results(
            df_final[final_columns], "FSTATS_analysis", "fstats"
        )

        df_fstats_final = df_final.copy()  # Salva per il merge

        logger.info(f"FSTATS analysis complete. Results saved to {excel_path}")
        logger.info(f"FSTATS JSON export saved to {json_path}")
        logger.info(f"FSTATS HTML export saved to {html_path}")
    else:
        logger.warning("FSTATS DataFrame is empty. Pipeline skipped.")

    # 4. Create unified analysis if both datasets are available
    if df_fpedia_final is not None and df_fstats_final is not None:
        logger.info("--- Creating Unified Analysis ---")
        df_unified = merge_datasets_with_mapping(df_fpedia_final, df_fstats_final)

        if not df_unified.empty:
            # Save Excel, JSON, and HTML
            excel_path, json_path, html_path = save_analysis_results(
                df_unified, "unified_analysis", "unified"
            )
            logger.info(f"Unified analysis complete. Results saved to {excel_path}")
            logger.info(f"Unified JSON export saved to {json_path}")
            logger.info(f"Unified HTML export saved to {html_path}")
        else:
            logger.warning("Unified analysis resulted in empty DataFrame.")

    logger.info("Fantacalcio analysis pipeline finished.")


if __name__ == "__main__":
    main()
