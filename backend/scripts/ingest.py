"""
PDF Table Extraction Script using Google Gemini AI

This script extracts all tables from a PDF document using Google's Gemini AI model.
Each extracted table is saved as a separate CSV file in the specified output directory.

The script:
1. Uploads the PDF to Google Gemini
2. Uses Gemini to extract all tables from the document
3. Adds a "Context_Type" column as the first column to each table
4. Saves each table as a separate CSV file with naming pattern: <pdf_name>_table_<N>.csv
5. Returns a list of DataFrames for further processing

Requirements:
- GOOGLE_API_KEY environment variable must be set
- PDF file must exist at the specified path
"""

import google.generativeai as genai
from pathlib import Path
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# For display in Jupyter notebooks
try:
    from IPython.display import display
except ImportError:
    def display(df):
        print(df.to_markdown(index=False, numalign="left", stralign="left"))


# --- CONFIG API KEY ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Make sure it's set in your .env file")

genai.configure(api_key=GOOGLE_API_KEY)


def extract_and_split_tables(pdf_path: str, output_dir: str):
    """
    Uploads a PDF to Gemini, extracts ALL tables as CSV files,
    and saves each table in a separate file:
        <pdf_name>_table_<N>.csv

    Returns a list of DataFrames (one per successfully parsed table).
    
    Args:
        pdf_path: Path to the PDF file to process
        output_dir: Directory where CSV files will be saved
        
    Returns:
        List of pandas DataFrames, one for each extracted table
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    
    # 1. Verification and preparation
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Uploading PDF: {pdf_path.name}...")
    try:
        file = genai.upload_file(path=str(pdf_path))
        print("File uploaded:", file.uri)
    except Exception as e:
        print(f"Error uploading file to Gemini: {e}")
        return []

    # 2. Prompt for multiple tables
    prompt = """
    Extract ALL tables from this document.
    
    For each table found:
    1.  **Add Context Column:** Create a new column as the FIRST column in the CSV. Name this column "Context_Type".
    2.  **Format:** Generate the data as raw, comma-separated CSV text (NO markdown, NO code blocks, NO text preamble).
    3.  **Delimiter:** Use a comma (,) as the separator.
    4.  **Numbers:** Write ALL numeric values WITHOUT thousand separators. For example, write "1330" not "1,330", write "15000" not "15,000".
    5.  **Identification:** Immediately before the raw CSV text for each table, you MUST insert a unique identifier on its own line: ---TABLE_START_[N]---, where [N] is the sequential number of the table (starting at 1).

    CRITICAL: Do NOT use commas as thousand separators in numeric values. Only use commas to separate CSV fields.

    The final output MUST consist ONLY of the numbered table separators and the raw CSV text blocks.
    """

    # 3. Call the model
    print("Processing PDF with Gemini (gemini-2.5-pro)...")
    model = genai.GenerativeModel("gemini-2.5-pro")

    try:
        response = model.generate_content([prompt, file])
        csv_output = response.text.strip()
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return []
    finally:
        # Try to delete the remote file 
        try:
            genai.delete_file(file.name)
            print("Remote file deleted.")
        except Exception as e_del:
            print(f"Warning: Could not delete remote file: {e_del}")

    # 4. Parse output and save tables
    tables = csv_output.split("---TABLE_START_")
    
    print(f"\nSaving tables to: {output_dir}")
    extracted_dfs = []
    
    for block in tables:
        if not block.strip():
            continue

        try:
            # Expected format: "1---\ncol1,col2,..."
            parts = block.split("---", 1)
            if len(parts) < 2:
                continue

            table_number = parts[0].strip()        # "1", "2", etc.
            csv_data = parts[1].strip()            # CSV content

            base_name = pdf_path.stem              # filename without extension
            output_filename = output_dir / f"{base_name}_table_{table_number}.csv"
            
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(csv_data)
                
            print(f"Table {table_number} saved as {output_filename.name}")

            # Try to load with pandas
            try:
                df = pd.read_csv(output_filename)
                extracted_dfs.append(df)
            except Exception as e_pandas:
                print(f"   Warning: Pandas could not parse table {table_number}: {e_pandas}")

        except Exception as e:
            print(f"Error processing a table block: {e}")

    print("\nExtraction process completed.")

    if extracted_dfs:
        print("Preview of the first table:")
        display(extracted_dfs[0].head())

    return extracted_dfs


def main():
    """Main entry point for the script"""
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Extract tables from PDF using Google Gemini AI"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default=None,
        help="Path to PDF file (default: ../data/raw/series_75_data.pdf)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for CSV files (default: data/processed)"
    )
    
    args = parser.parse_args()
    
    # Use relative paths from the script location
    script_dir = Path(__file__).parent
    
    # Set default paths if not provided
    # In Docker, WORKDIR is /app, so we need to go up from scripts/ to app/ then to data/
    if args.pdf:
        pdf_path = Path(args.pdf)
    else:
        # Resolve relative to app root (go up from scripts/ to app/)
        pdf_path = script_dir.parent / "data/raw/series_75_data.pdf"
    
    if args.output:
        output_dir = Path(args.output)
    else:
        # Resolve relative to app root (go up from scripts/ to app/)
        output_dir = script_dir.parent / "data/processed"
    
    # Resolve paths to absolute for consistency
    pdf_path = pdf_path.resolve()
    output_dir = output_dir.resolve()
    
    # Try to show relative paths for display (relative to app root)
    try:
        app_root = script_dir.parent
        pdf_display = pdf_path.relative_to(app_root) if pdf_path.is_relative_to(app_root) else pdf_path
        output_display = output_dir.relative_to(app_root) if output_dir.is_relative_to(app_root) else output_dir
    except (ValueError, AttributeError):
        # Fallback to absolute paths if relative doesn't work
        pdf_display = pdf_path
        output_display = output_dir
    
    # Convert to strings for the function (use absolute paths)
    pdf_path_str = str(pdf_path)
    output_dir_str = str(output_dir)
    
    print(f"PDF file: {pdf_display}")
    print(f"Output directory: {output_display}")
    print()
    
    # Extract tables
    dataframes = extract_and_split_tables(pdf_path_str, output_dir_str)
    
    if dataframes:
        print(f"\nSuccessfully extracted {len(dataframes)} table(s)")
    else:
        print("\nNo tables were extracted")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())