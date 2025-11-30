"""
Data Processing Orchestrator Script

This script orchestrates the complete data transformation pipeline:
1. Extracts tables from PDF using Google Gemini (ingest.py)
2. Renames CSV files with descriptive names based on Context_Type and Enclosure_Type (rename_csv_files.py)
3. Builds SQLite database from CSV files (build_sqlite_db.py)
4. Builds vector database with embeddings (build_vector_db.py)

The script ensures each step completes successfully before proceeding to the next,
providing clear progress feedback and error handling.

Usage:
    python process_data.py [--pdf PDF_PATH] [--output OUTPUT_DIR] [--skip-ingest] [--skip-sqlite] [--skip-vector]

Options:
    --pdf: Path to PDF file (default: ../data/raw/series_75_data.pdf)
    --output: Output directory for CSV files (default: data/processed)
    --skip-ingest: Skip PDF extraction step
    --skip-sqlite: Skip SQLite database building step
    --skip-vector: Skip vector database building step
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional


def run_script(script_name: str, description: str, args: Optional[list] = None) -> int:
    """
    Execute a Python script and return its exit code.
    
    Args:
        script_name: Name of the script to execute (e.g., "ingest.py")
        description: Human-readable description of what the script does
        args: Optional list of additional command-line arguments
        
    Returns:
        Exit code from the script (0 for success, non-zero for failure)
    """
    script_dir = Path(__file__).parent
    script_path = script_dir / script_name
    
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return 1
    
    print("\n" + "=" * 80)
    print(f"STEP: {description}")
    print("=" * 80)
    print(f"Executing: {script_name}")
    if args:
        print(f"Arguments: {' '.join(args)}")
    print()
    
    try:
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        result = subprocess.run(cmd, cwd=str(script_dir))
        
        if result.returncode == 0:
            print(f"\n✓ {description} completed successfully")
        else:
            print(f"\n✗ {description} failed with exit code {result.returncode}")
        
        return result.returncode
        
    except Exception as e:
        print(f"\nERROR: Failed to execute {script_name}: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """
    Main entry point for the data processing orchestrator.
    
    Orchestrates the execution of ingest.py, rename_csv_files.py, build_sqlite_db.py, and build_vector_db.py
    in sequence, with error handling and progress reporting.
    """
    parser = argparse.ArgumentParser(
        description="Orchestrate complete data transformation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline with default paths
  python process_data.py
  
  # Run with custom PDF path
  python process_data.py --pdf /path/to/data.pdf
  
  # Skip PDF extraction (if CSVs already exist)
  python process_data.py --skip-ingest
  
  # Only build vector database (skip ingest and SQLite)
  python process_data.py --skip-ingest --skip-sqlite
        """
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
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip PDF extraction step (ingest.py)"
    )
    parser.add_argument(
        "--skip-sqlite",
        action="store_true",
        help="Skip SQLite database building step (build_sqlite_db.py)"
    )
    parser.add_argument(
        "--skip-vector",
        action="store_true",
        help="Skip vector database building step (build_vector_db.py)"
    )
    
    args = parser.parse_args()
    
    ingest_args = []
    if args.pdf:
        ingest_args.extend(["--pdf", args.pdf])
    if args.output:
        ingest_args.extend(["--output", args.output])
    
    print("=" * 80)
    print("DATA PROCESSING PIPELINE - Konecto AI Agent")
    print("=" * 80)
    print("\nThis script will execute the following steps:")
    print("  1. Extract tables from PDF (ingest.py)")
    print("  2. Rename CSV files with descriptive names (rename_csv_files.py)")
    print("  3. Build SQLite database (build_sqlite_db.py)")
    print("  4. Build vector database (build_vector_db.py)")
    print()
    
    if args.skip_ingest:
        print("⚠️  Skipping: PDF extraction (ingest.py)")
    if args.skip_sqlite:
        print("⚠️  Skipping: SQLite database building (build_sqlite_db.py)")
    if args.skip_vector:
        print("⚠️  Skipping: Vector database building (build_vector_db.py)")
    print()
    
    if not args.skip_ingest:
        exit_code = run_script(
            "ingest.py",
            "PDF Table Extraction",
            ingest_args
        )
        if exit_code != 0:
            print("\n" + "=" * 80)
            print("PIPELINE FAILED: PDF extraction step failed")
            print("=" * 80)
            return exit_code
        
        print("\n" + "=" * 80)
        print("STEP: Rename CSV Files")
        print("=" * 80)
        print("Renaming CSV files to use descriptive names based on Context_Type and Enclosure_Type")
        print()
        
        exit_code = run_script(
            "rename_csv_files.py",
            "CSV File Renaming"
        )
        if exit_code != 0:
            print("\n" + "=" * 80)
            print("WARNING: CSV renaming step had issues, but continuing...")
            print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("SKIPPED: PDF Table Extraction")
        print("=" * 80)
    
    if not args.skip_sqlite:
        exit_code = run_script(
            "build_sqlite_db.py",
            "SQLite Database Building"
        )
        if exit_code != 0:
            print("\n" + "=" * 80)
            print("PIPELINE FAILED: SQLite database building step failed")
            print("=" * 80)
            return exit_code
    else:
        print("\n" + "=" * 80)
        print("SKIPPED: SQLite Database Building")
        print("=" * 80)
    
    if not args.skip_vector:
        exit_code = run_script(
            "build_vector_db.py",
            "Vector Database Building"
        )
        if exit_code != 0:
            print("\n" + "=" * 80)
            print("PIPELINE FAILED: Vector database building step failed")
            print("=" * 80)
            return exit_code
    else:
        print("\n" + "=" * 80)
        print("SKIPPED: Vector Database Building")
        print("=" * 80)
    
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\nAll data processing steps completed successfully.")
    print("\nNext steps:")
    print("  1. Verify that all databases were created correctly")
    print("  2. Test the agent with sample queries")
    print("  3. Configure DATA_STORAGE in your .env if needed")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

