import pandas as pd
import os
import argparse
import logging

# ------------------ LOGGING SETUP ------------------
def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

# ------------------ VALIDATION ------------------
def validate_columns(df, column_name, file_name):
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in {file_name}")

# ------------------ LOAD REFERENCE DATA ------------------
def load_reference_data(reference_file, lookup_values, lookup_column, chunk_size=None):
    matched_rows = []

    file_ext = os.path.splitext(reference_file)[1].lower()

    # ----------- CSV SUPPORT WITH CHUNKING -----------
    if file_ext == ".csv" and chunk_size:
        logging.info("Using chunking for CSV reference file...")
        for chunk in pd.read_csv(reference_file, chunksize=chunk_size):
            validate_columns(chunk, lookup_column, reference_file)
            filtered = chunk[chunk[lookup_column].isin(lookup_values)]
            matched_rows.append(filtered)

    # ----------- EXCEL (NO CHUNKING) -----------
    elif file_ext in [".xlsx", ".xls"]:
        logging.info("Processing Excel file (no chunking support)...")
        ref_df = pd.read_excel(reference_file)
        validate_columns(ref_df, lookup_column, reference_file)
        filtered = ref_df[ref_df[lookup_column].isin(lookup_values)]
        matched_rows.append(filtered)

    # ----------- CSV WITHOUT CHUNKING -----------
    else:
        logging.info("Processing CSV file without chunking...")
        ref_df = pd.read_csv(reference_file)
        validate_columns(ref_df, lookup_column, reference_file)
        filtered = ref_df[ref_df[lookup_column].isin(lookup_values)]
        matched_rows.append(filtered)

    return matched_rows

# ------------------ MAIN FUNCTION ------------------
def map_data(raw_file, reference_file, output_file, lookup_column, chunk_size=None):
    try:
        logging.info("Loading raw data...")

        # Load raw data
        raw_df = pd.read_csv(raw_file)
        validate_columns(raw_df, lookup_column, raw_file)

        # Extract unique lookup values
        lookup_values = set(raw_df[lookup_column].dropna().unique())
        logging.info(f"Unique lookup values: {len(lookup_values)}")

        logging.info("Processing reference data...")

        matched_rows = load_reference_data(
            reference_file,
            lookup_values,
            lookup_column,
            chunk_size
        )

        # Combine results
        result_df = pd.concat(matched_rows, ignore_index=True)

        # Remove duplicates
        result_df = result_df.drop_duplicates()

        # Save output
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        result_df.to_csv(output_file, index=False)

        logging.info("Mapping completed successfully!")
        logging.info(f"Output saved to: {output_file}")
        logging.info(f"Total matched rows: {len(result_df)}")

    except Exception as e:
        logging.error(f"Error occurred: {e}")

# ------------------ CLI ------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Data Mapping Script")

    parser.add_argument("--raw", required=True, help="Path to raw_data.csv")
    parser.add_argument("--ref", required=True, help="Path to reference file (CSV or Excel)")
    parser.add_argument("--out", required=True, help="Output CSV path")
    parser.add_argument("--column", required=True, help="Lookup column name")
    parser.add_argument("--chunk", type=int, help="Chunk size (only for CSV reference)")

    return parser.parse_args()

# ------------------ ENTRY POINT ------------------
if __name__ == "__main__":
    setup_logger()
    args = parse_args()

    map_data(
        raw_file=args.raw,
        reference_file=args.ref,
        output_file=args.out,
        lookup_column=args.column,
        chunk_size=args.chunk
    )