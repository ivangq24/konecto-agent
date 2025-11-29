"""
I/O Handlers Module

Handles loading datasets and saving evaluation results.
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class DatasetLoader:
    """
    Loads test cases from JSON dataset files.
    """
    
    def __init__(self, dataset_path: str):
        """
        Initialize dataset loader.
        
        Args:
            dataset_path: Path to JSON file containing test cases
        """
        self.dataset_path = Path(dataset_path)
    
    def load(self) -> List[Dict]:
        """
        Load test cases from the evaluation dataset JSON file.
        
        Returns:
            List of test case dictionaries, each containing:
            - id: Unique test case identifier
            - category: Test category (exact_search, semantic_search, etc.)
            - input: User query input
            - expected_tool: Tool that should be used
            - expected_part_number: Expected part number (if applicable)
            - ground_truth: Expected field values (if applicable)
            - Other validation fields
            
        Raises:
            FileNotFoundError: If dataset file doesn't exist
            ValueError: If dataset structure is invalid
        """
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        test_cases = data.get("test_cases", [])
        if not test_cases:
            raise ValueError(f"Dataset file '{self.dataset_path}' contains no test cases")
        
        return test_cases


class ResultsSaver:
    """
    Saves evaluation results to JSON files.
    """
    
    @staticmethod
    def save(overall: Dict, results: List[Dict], run_name: str, output_dir: Path):
        """
        Save evaluation results to JSON files.
        
        Args:
            overall: Overall metrics dictionary
            results: List of individual test results
            run_name: Name for the results file (timestamp-based)
            output_dir: Directory where results will be saved
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{run_name}.json"
        
        output = {
            "run_name": run_name,
            "overall_metrics": overall,
            "detailed_results": results,
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_file}")
        
        # Also save as latest.json
        latest_file = output_dir / "latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Latest results: {latest_file}")

