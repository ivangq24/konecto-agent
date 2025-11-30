"""
Script to rename CSV files based on Context_Type and Enclosure_Type

This script reads existing CSV files and renames them using the format:
Context_Type_Enclosure_Type.csv

It extracts the Context_Type and Enclosure_Type from the first data row
and creates a sanitized filename.
"""

import pandas as pd
from pathlib import Path


def sanitize_filename(text: str) -> str:
    """
    Sanitize text to be a valid filename.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text suitable for filename
    """
    if not text or pd.isna(text):
        return "Unknown"
    
    text = str(text).strip()
    text = text.replace(" ", "_")
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '-', ',', '&']
    for char in invalid_chars:
        text = text.replace(char, "_")
    while "__" in text:
        text = text.replace("__", "_")
    text = text.strip("_")
    
    return text if text else "Unknown"


def _reconstruct_enclosure_type_from_pandas(df: pd.DataFrame) -> str:
    """
    Reconstruct Enclosure_Type from pandas DataFrame if it was split.
    
    Args:
        df: DataFrame with Enclosure_Type column
        
    Returns:
        Reconstructed Enclosure_Type string
    """
    if "Enclosure_Type" not in df.columns or df.empty:
        return "Unknown"
    
    enclosure_type_raw = str(df.iloc[0]["Enclosure_Type"]).strip() if pd.notna(df.iloc[0]["Enclosure_Type"]) else "Unknown"
    enclosure_parts = [enclosure_type_raw] if enclosure_type_raw and enclosure_type_raw != "Unknown" else []
    enclosure_col_idx = df.columns.get_loc("Enclosure_Type")
    
    for offset in range(1, 3):
        if enclosure_col_idx + offset < len(df.columns):
            next_col_name = df.columns[enclosure_col_idx + offset]
            next_col_value = str(df.iloc[0][next_col_name]).strip() if pd.notna(df.iloc[0][next_col_name]) else ""
            
            if next_col_value and next_col_value != "nan":
                is_part_number = (next_col_value.startswith("76") or 
                                 (len(next_col_value) > 0 and next_col_value[0].isdigit() and 
                                  "CE" not in next_col_value and "UKCA" not in next_col_value))
                
                if not is_part_number and ("CE" in next_col_value or "UKCA" in next_col_value or 
                                           next_col_name.strip() in ["CE", "& UKCA"]):
                    enclosure_parts.append(next_col_value)
                elif is_part_number or next_col_value == "N/A":
                    break
    
    if len(enclosure_parts) > 1:
        return ", ".join(enclosure_parts).strip()
    elif len(enclosure_parts) == 1:
        return enclosure_parts[0]
    else:
        return enclosure_type_raw if enclosure_type_raw else "Unknown"


def rename_csv_files(csv_directory: str):
    """
    Rename CSV files based on Context_Type and Enclosure_Type.
    
    Args:
        csv_directory: Directory containing CSV files to rename
    """
    csv_dir = Path(csv_directory)
    
    if not csv_dir.exists():
        print(f"ERROR: Directory not found: {csv_directory}")
        return
    
    csv_files = list(csv_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {csv_directory}")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to rename\n")
    
    renamed_count = 0
    
    for csv_file in csv_files:
        try:
            context_type = None
            enclosure_type = None
            
            # Read the file line by line to handle commas within Enclosure_Type
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    print(f"  Skipping {csv_file.name}: Not enough lines")
                    continue
                
                header_line = lines[0].strip()
                header_cols = [col.strip() for col in header_line.split(',')]
                
                try:
                    context_type_idx = header_cols.index("Context_Type")
                    enclosure_type_idx = header_cols.index("Enclosure_Type")
                except ValueError:
                    first_row_cols = [col.strip() for col in lines[0].strip().split(',')]
                    if len(first_row_cols) >= 2:
                        context_type = first_row_cols[0] if first_row_cols[0] else "Unknown"
                        enclosure_type = first_row_cols[1] if len(first_row_cols) > 1 and first_row_cols[1] else "Unknown"
                    else:
                        print(f"  Skipping {csv_file.name}: Not enough columns")
                        continue
                else:
                    data_line = lines[1].strip()
                    data_cols = [col.strip() for col in data_line.split(',')]
                    
                    if len(data_cols) > context_type_idx:
                        context_type = data_cols[context_type_idx] if data_cols[context_type_idx] else "Unknown"
                    else:
                        context_type = "Unknown"
                    
                    if len(data_cols) > enclosure_type_idx:
                        enclosure_type = data_cols[enclosure_type_idx] if data_cols[enclosure_type_idx] else "Unknown"
                        
                        enclosure_parts = [enclosure_type]
                        idx = enclosure_type_idx + 1
                        
                        base_part_idx = len(data_cols)
                        for i, col in enumerate(data_cols):
                            if col.strip().startswith("76") and len(col.strip()) > 5:
                                base_part_idx = i
                                break
                        
                        while idx < len(data_cols) and idx < base_part_idx:
                            part = data_cols[idx].strip()
                            if part.startswith("76") and len(part) > 5:
                                break
                            if ("CE" in part or "UKCA" in part) or (len(part) > 0 and len(part) < 20 and not part[0].isdigit() and part != "N/A"):
                                enclosure_parts.append(part)
                                idx += 1
                            else:
                                break
                        
                        if len(enclosure_parts) > 1:
                            enclosure_type = ", ".join(enclosure_parts).strip()
                        elif len(enclosure_parts) == 1:
                            enclosure_type = enclosure_parts[0]
                    else:
                        enclosure_type = "Unknown"
            
            # Fallback: try pandas if we still don't have values
            if not context_type or context_type == "Unknown" or not enclosure_type or enclosure_type == "Unknown":
                try:
                    df = pd.read_csv(csv_file)
                    if "Context_Type" in df.columns and "Enclosure_Type" in df.columns and not df.empty:
                        if not context_type or context_type == "Unknown":
                            context_type = str(df.iloc[0]["Context_Type"]).strip() if pd.notna(df.iloc[0]["Context_Type"]) else "Unknown"
                        if not enclosure_type or enclosure_type == "Unknown":
                            enclosure_type = _reconstruct_enclosure_type_from_pandas(df)
                except Exception:
                    pass
            
            if not context_type or context_type == "Unknown":
                context_type = "Unknown"
            if not enclosure_type or enclosure_type == "Unknown":
                enclosure_type = "Unknown"
            
            context_safe = sanitize_filename(context_type)
            enclosure_safe = sanitize_filename(enclosure_type)
            
            new_filename = csv_dir / f"{context_safe}_{enclosure_safe}.csv"
            
            if new_filename.exists() and new_filename != csv_file:
                original_stem = csv_file.stem
                if "_table_" in original_stem:
                    table_num = original_stem.split("_table_")[-1]
                    new_filename = csv_dir / f"{context_safe}_{enclosure_safe}_{table_num}.csv"
                else:
                    counter = 1
                    while new_filename.exists():
                        new_filename = csv_dir / f"{context_safe}_{enclosure_safe}_{counter}.csv"
                        counter += 1
            
            if csv_file != new_filename:
                csv_file.rename(new_filename)
                print(f"  Renamed: {csv_file.name} → {new_filename.name}")
                print(f"    Context_Type: {context_type}")
                print(f"    Enclosure_Type: {enclosure_type}")
                renamed_count += 1
            else:
                print(f"  Skipping {csv_file.name}: Already has correct name")
                
        except Exception as e:
            print(f"  ERROR processing {csv_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\nRenamed {renamed_count} file(s)")


def main():
    """Main entry point"""
    print("=" * 60)
    print("Rename CSV Files - Konecto AI Agent")
    print("=" * 60)
    print()
    
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    processed_dir = backend_dir / "data" / "processed"
    
    if not processed_dir.exists():
        print(f"ERROR: Directory not found: {processed_dir}")
        return 1
    
    print(f"Processing directory: {processed_dir}")
    print()
    
    try:
        rename_csv_files(str(processed_dir))
        
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

