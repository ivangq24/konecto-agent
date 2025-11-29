"""
Vector Database Builder Script

This script processes CSV files containing actuator data and creates a vector database
using ChromaDB with OpenAI embeddings for semantic search capabilities.

The script:
1. Reads all CSV files from the processed data directory
2. Converts each row into a text document with format "Column: Value"
3. Extracts metadata from each row (part numbers, specifications, etc.)
4. Generates embeddings using OpenAI's embedding model
5. Stores embeddings in ChromaDB for fast semantic similarity search

Requirements:
- OPENAI_API_KEY environment variable must be set
- CSV files must exist in the processed data directory
- CSV files must contain "Base Part Number" column
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Add backend directory to path for imports
script_dir = Path(__file__).parent
backend_dir = script_dir.parent  # Go up from scripts/ to backend/
sys.path.insert(0, str(backend_dir))
from app.config import get_settings


def normalize_column_name(col_name: str) -> str:
    """
    Normalizes column names for use in metadata.
    
    Converts column names to lowercase and replaces special characters
    with underscores or removes them to create valid metadata keys.
    
    Args:
        col_name: Original column name to normalize
        
    Returns:
        Normalized column name suitable for metadata keys
    """
    return (
        col_name.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("[", "")
        .replace("]", "")
        .replace("%", "pct")
        .replace("/", "_")
        .replace("-", "_")
    )


# Base Part Number column name
BASE_PART_NUMBER_COL = "Base Part Number"

def format_value(value: Any) -> Optional[str]:
    """
    Formats values for text representation.
    
    Converts values to strings and strips whitespace. Returns None
    for empty, null, or NaN values.
    
    Args:
        value: Value to format (can be any type)
        
    Returns:
        Formatted string value, or None if value is empty/null/NaN
    """
    if pd.isna(value) or str(value).strip() == "":
        return None
    return str(value).strip()


def create_narrative_text(row: pd.Series) -> str:
    """
    Creates narrative text from a DataFrame row.
    
    Converts each column-value pair into a "Column: Value." format
    and joins them into a single text string. Only includes non-empty values.
    
    Args:
        row: pandas Series representing a single row from a DataFrame
        
    Returns:
        Formatted text string with all column-value pairs
    """
    parts = []

    for col in row.index:
        val = format_value(row[col])
        if val:
            parts.append(f"{col}: {val}.")

    return " ".join(parts)


def create_metadata(row: pd.Series, source_table: str) -> Dict[str, Any]:
    """
    Creates structured metadata dictionary from a DataFrame row.
    
    Extracts all column values and normalizes them for metadata storage.
    Special handling for "Base Part Number" and "Context_Type" columns.
    Numeric values are stored as floats, strings are truncated to 100 chars.
    
    Args:
        row: pandas Series representing a single row from a DataFrame
        source_table: Name of the source table/file for tracking
        
    Returns:
        Dictionary containing normalized metadata with all column values
    """
    metadata = {"source_table": source_table}
    
    # Process all columns in a single pass
    for col in row.index:
        if pd.isna(row[col]):
            continue
            
        # Base Part Number
        if col == BASE_PART_NUMBER_COL:
            base_part = format_value(row[col])
            if base_part:
                metadata["base_part_number"] = base_part
                metadata["identifier"] = base_part
            continue
            
        # Context_Type
        if col == "Context_Type":
            context_type = format_value(row[col])
            if context_type:
                metadata["context_type"] = context_type
            continue
        
        # Numeric or string values
        try:
            val = pd.to_numeric(row[col], errors="raise")
            if not pd.isna(val):
                normalized_name = normalize_column_name(col)
                metadata[normalized_name] = float(val)
        except (ValueError, TypeError):
            normalized_name = normalize_column_name(col)
            val_str = str(row[col])[:100]
            metadata[normalized_name] = val_str
    
    return metadata


def create_chunks_from_dataframe(df: pd.DataFrame, source_table: str) -> List[Document]:
    """
    Creates document chunks dynamically from a DataFrame.
    
    Converts each row in the DataFrame into a LangChain Document object.
    Each document contains the row data as text and structured metadata.
    Empty rows are skipped.
    
    Args:
        df: pandas DataFrame to process
        source_table: Name of the source table/file for metadata tracking
        
    Returns:
        List of LangChain Document objects, one per non-empty row
    """
    if df.empty:
        return []

    chunks = []

    # Reset index to ensure numeric indices, or use enumerate
    df_reset = df.reset_index(drop=True)
    
    for row_idx, (idx, row) in enumerate(df_reset.iterrows()):
        # Skip completely empty rows
        if row.isna().all():
            continue

        # Create simple text: column: value
        text = create_narrative_text(row)

        # Skip if no text
        if not text.strip():
            continue

        # Create metadata
        metadata = create_metadata(row, source_table)
        metadata["row_index"] = row_idx  # Use enumerate index instead

        # Create Document
        doc = Document(page_content=text, metadata=metadata)

        chunks.append(doc)

    return chunks


def process_csv_files(csv_directory: str, settings) -> List[Document]:
    """
    Processes all CSV files in a directory and creates document chunks.
    
    Scans the specified directory for CSV files, reads each one,
    and converts all rows into document chunks. Handles errors
    gracefully and continues processing remaining files.
    
    Args:
        csv_directory: Path to directory containing CSV files
        settings: Application settings object (for future use)
        
    Returns:
        List of LangChain Document objects from all processed CSV files
    """
    csv_dir = Path(csv_directory)
    all_chunks = []

    # Find all CSV files
    csv_files = list(csv_dir.glob("*.csv"))

    if not csv_files:
        print(f"WARNING: No CSV files found in {csv_directory}")
        return all_chunks

    print(f"Processing {len(csv_files)} CSV file(s)...\n")

    for csv_file in csv_files:
        try:
            print(f"  Processing: {csv_file.name}")

            # Read CSV
            df = pd.read_csv(csv_file)

            if df.empty:
                print(f"    WARNING: Empty file: {csv_file.name}")
                continue

            # Create chunks
            source_name = csv_file.stem  # Filename without extension
            chunks = create_chunks_from_dataframe(df, source_name)

            print(f"    Created {len(chunks)} chunks from {len(df)} rows")

            all_chunks.extend(chunks)

        except Exception as e:
            print(f"    ERROR: Error processing {csv_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\nTotal chunks created: {len(all_chunks)}")
    return all_chunks


def create_embeddings_and_store(chunks: List[Document], settings, chroma_path: str):
    """
    Creates embeddings and stores them in ChromaDB.
    
    Generates vector embeddings for all document chunks using OpenAI's
    embedding model and stores them in a persistent ChromaDB vectorstore.
    Cleans existing vectorstore before creating a new one.
    
    Args:
        chunks: List of LangChain Document objects to embed
        settings: Application settings object containing:
            - openai_api_key: OpenAI API key
            - openai_embedding_model: Embedding model name
        chroma_path: Resolved absolute path for ChromaDB storage
            
    Returns:
        Chroma vectorstore object, or None if no chunks provided
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set
        Exception: If embedding generation or storage fails
    """
    if not chunks:
        print("WARNING: No chunks to process")
        return None

    print(f"\nGenerating embeddings for {len(chunks)} chunks...")
    print(f"   Model: {settings.openai_embedding_model}")

    # Verify API key
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    try:
        embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key,
        )

        # Create directory if it doesn't exist
        os.makedirs(chroma_path, exist_ok=True)

        # Clean existing directory if it exists
        if os.path.exists(chroma_path):
            import shutil
            print(f"   Cleaning existing directory: {chroma_path}")
            shutil.rmtree(chroma_path)

        # Create vectorstore
        print(f"   Creating vectorstore in: {chroma_path}")
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=chroma_path,
        )

        # ChromaDB persists automatically, but we can force a flush
        # In recent versions, persist() is no longer necessary

        print(f"   Embeddings stored successfully!")
        print(f"   Location: {chroma_path}")

        # Show statistics
        print(f"\nStatistics:")
        print(f"   - Total documents: {len(chunks)}")
        
        # Get vectorstore information
        try:
            collection_count = vectorstore._collection.count()
            print(f"   - Documents in ChromaDB: {collection_count}")
        except Exception:
            pass

        return vectorstore

    except Exception as e:
        print(f"   ERROR: Error creating embeddings: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """
    Main entry point for the script.
    
    Orchestrates the entire vector database building process:
    1. Loads application settings
    2. Processes all CSV files in the processed data directory
    3. Creates embeddings and stores them in ChromaDB
    4. Displays success message and next steps
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print("=" * 60)
    print("Build Vector Database - Konecto AI Agent")
    print("=" * 60)
    print()

    # Load configuration
    try:
        settings = get_settings()
        print(f"Configuration loaded")
        print(f"   - Embedding model: {settings.openai_embedding_model}")
        print(f"   - ChromaDB path: {settings.chroma_persist_directory}")
        print()
    except Exception as e:
        print(f"ERROR: Error loading configuration: {e}")
        print("   Make sure you have a .env file with OPENAI_API_KEY")
        return 1

    # Resolve paths relative to backend directory (parent of scripts/)
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent  # Go up from scripts/ to backend/
    
    # Resolve processed_data_path (can be relative or absolute)
    processed_dir = Path(settings.processed_data_path)
    if not processed_dir.is_absolute():
        processed_dir = (backend_dir / processed_dir).resolve()

    if not processed_dir.exists():
        print(f"ERROR: Directory not found: {processed_dir}")
        return 1

    # Resolve chroma_persist_directory (can be relative or absolute)
    chroma_persist_dir = Path(settings.chroma_persist_directory)
    if not chroma_persist_dir.is_absolute():
        chroma_persist_dir = (backend_dir / chroma_persist_dir).resolve()

    # Process all CSVs
    chunks = process_csv_files(str(processed_dir), settings)

    if not chunks:
        print("\nERROR: No chunks were generated. Verify that CSV files exist.")
        return 1

    # Create embeddings and store
    try:
        vectorstore = create_embeddings_and_store(chunks, settings, str(chroma_persist_dir))
        
        if vectorstore:
            print("\n" + "=" * 60)
            print("Process completed successfully!")
            print("=" * 60)
            print("\nNext steps:")
            print("   1. Verify that the vectorstore was created correctly")
            print("   2. Configure DATA_STORAGE=chroma in your .env")
            print("   3. Test searches with the agent")
            return 0
        else:
            print("\nERROR: Could not create vectorstore")
            return 1
            
    except Exception as e:
        print(f"\nERROR: Error during process: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

