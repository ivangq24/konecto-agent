"""
SQLite Database Builder Script

This script processes CSV files containing actuator data and creates a SQLite database
with a flexible JSON structure for efficient exact-match queries by part number.

The script:
1. Reads all CSV files from the processed data directory
2. Extracts Base Part Number from each row
3. Stores all row data as JSON in a single table
4. Creates indexes for fast part number lookups
5. Handles duplicate part numbers by replacing existing records

Database Structure:
- Table: actuators
  - id: Auto-increment primary key
  - base_part_number: Unique identifier (indexed)
  - data_json: All row data stored as JSON string

Requirements:
- CSV files must exist in the processed data directory
- CSV files must contain "Base Part Number" column
"""

import os
import sys
import json
from pathlib import Path
import pandas as pd
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend directory to path for imports
script_dir = Path(__file__).parent
backend_dir = script_dir.parent  # Go up from scripts/ to backend/
sys.path.insert(0, str(backend_dir))
from app.config import get_settings

# Common columns that exist in all/most tables
BASE_PART_NUMBER_COL = "Base Part Number"
CONTEXT_TYPE_COL = "Context_Type"


def normalize_column_name(col_name: str) -> str:
    """
    Normalizes column names for use in JSON metadata.
    
    Converts column names to lowercase and replaces special characters
    with underscores or removes them to create valid JSON keys.
    
    Args:
        col_name: Original column name to normalize
        
    Returns:
        Normalized column name suitable for JSON keys
    """
    return (
        col_name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("[", "")
        .replace("]", "")
        .replace("%", "pct")
        .replace("/", "_")
    )


def process_csv_files_to_sqlite(csv_directory: str, db_path: str):
    """
    Processes all CSV files and stores them in SQLite with JSON structure.
    
    Reads all CSV files from the specified directory, extracts Base Part Numbers,
    and stores each row's data as JSON in the SQLite database. Handles duplicates
    by replacing existing records with the same part number.
    
    Args:
        csv_directory: Path to directory containing CSV files
        db_path: Path where SQLite database will be created
        
    Returns:
        None
    """
    csv_dir = Path(csv_directory)
    db_path_obj = Path(db_path)
    
    # Create directory if needed
    db_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to SQLite using context manager
    with sqlite3.connect(str(db_path_obj)) as conn:
        cursor = conn.cursor()
        
        # Create table with flexible JSON structure
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actuators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_part_number TEXT NOT NULL,
                data_json TEXT NOT NULL,
                UNIQUE(base_part_number)
            )
        """)
        
        # Create index for fast searches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_base_part_number ON actuators(base_part_number)")
        
        # Process all CSV files
        csv_files = list(csv_dir.glob("*.csv"))
        
        if not csv_files:
            print(f"WARNING: No CSV files found in {csv_directory}")
            return
        
        print(f"Processing {len(csv_files)} CSV file(s) for SQLite...\n")
        
        total_rows = 0
        
        for csv_file in csv_files:
            try:
                print(f"  Processing: {csv_file.name}")
                df = pd.read_csv(csv_file)
                
                if df.empty:
                    print(f"    WARNING: Empty file: {csv_file.name}")
                    continue
                
                source_table = csv_file.stem
                rows_processed = 0
                
                for idx, row in df.iterrows():
                    # Extract base part number
                    base_part = str(row.get(BASE_PART_NUMBER_COL, "")).strip()
                    
                    # Skip if no base part number
                    if not base_part or base_part == "nan" or pd.isna(row.get(BASE_PART_NUMBER_COL)):
                        continue
                    
                    # Convert entire row to dict (everything goes in JSON)
                    row_dict = row.to_dict()
                    
                    # Add source_table to the data
                    row_dict['source_table'] = source_table
                    
                    # Clean up the data (remove NaN values and normalize)
                    data_dict = {}
                    for key, value in row_dict.items():
                        if pd.notna(value) and str(value).strip() != "" and str(value).lower() != "nan":
                            # Normalize column name for JSON
                            normalized_key = normalize_column_name(key)
                            # Convert value to appropriate type
                            if isinstance(value, (int, float)):
                                data_dict[normalized_key] = value
                            else:
                                data_dict[normalized_key] = str(value).strip()
                    
                    # Convert to JSON
                    data_json = json.dumps(data_dict, ensure_ascii=False)
                    
                    # Insert or replace (only base_part_number is unique)
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO actuators 
                            (base_part_number, data_json)
                            VALUES (?, ?)
                        """, (base_part, data_json))
                        rows_processed += 1
                    except Exception as e:
                        print(f"    ERROR inserting row {idx}: {e}")
                        continue
                
                print(f"    Processed {rows_processed} rows")
                total_rows += rows_processed
                
            except Exception as e:
                print(f"    ERROR: Error processing {csv_file.name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Commit all changes
        conn.commit()
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM actuators")
        count = cursor.fetchone()[0]
        
        # Show statistics
        cursor.execute("SELECT COUNT(DISTINCT base_part_number) FROM actuators")
        unique_parts = cursor.fetchone()[0]
        
        # Count unique source tables from JSON (SQLite 3.9+ supports JSON functions)
        try:
            cursor.execute("""
                SELECT COUNT(DISTINCT json_extract(data_json, '$.source_table')) 
                FROM actuators
            """)
            unique_tables = cursor.fetchone()[0]
        except Exception:
            # Fallback: use the number of CSV files processed
            unique_tables = len(csv_files)
        
        print(f"\nSQLite database created successfully!")
        print(f"Location: {db_path}")
        print(f"Total records: {count}")
        print(f"Unique part numbers: {unique_parts}")
        print(f"Tables processed: {unique_tables}")


def main():
    """
    Main entry point for the script.
    
    Orchestrates the entire SQLite database building process:
    1. Loads application settings
    2. Verifies processed data directory exists
    3. Processes all CSV files and stores them in SQLite
    4. Displays success message and statistics
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print("=" * 60)
    print("Build SQLite Database - Konecto AI Agent")
    print("=" * 60)
    print()
    
    try:
        settings = get_settings()
        print(f"Configuration loaded")
        print(f"   - SQLite path: {settings.sqlite_db_path}")
        print(f"   - Processed data path: {settings.processed_data_path}")
        print()
    except Exception as e:
        print(f"ERROR: Error loading configuration: {e}")
        print("   Make sure you have a .env file with required settings")
        return 1
    
    # Resolve paths relative to backend directory (parent of scripts/)
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent  # Go up from scripts/ to backend/
    
    # Resolve processed_data_path (can be relative or absolute)
    processed_dir = Path(settings.processed_data_path)
    if not processed_dir.is_absolute():
        processed_dir = (backend_dir / processed_dir).resolve()
    
    # Resolve sqlite_db_path (can be relative or absolute)
    db_path = Path(settings.sqlite_db_path)
    if not db_path.is_absolute():
        db_path = (backend_dir / db_path).resolve()
    
    if not processed_dir.exists():
        print(f"ERROR: Directory not found: {processed_dir}")
        return 1
    
    try:
        process_csv_files_to_sqlite(str(processed_dir), str(db_path))
        
        print("\n" + "=" * 60)
        print("Process completed!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\nERROR: Error during process: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
