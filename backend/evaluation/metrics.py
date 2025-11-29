"""
Metrics Calculator Module

Calculates overall evaluation metrics from individual test results.
"""

from typing import Dict, List, Any
from datetime import datetime


class MetricsCalculator:
    """
    Calculator for overall evaluation metrics.
    
    Aggregates individual test results into overall statistics including
    accuracy by category, average scores, and pass/fail counts.
    """
    
    @staticmethod
    def calculate_overall_metrics(results: List[Dict]) -> Dict[str, Any]:
        """
        Calculate overall evaluation metrics from individual test results.
        
        Args:
            results: List of test result dictionaries
            
        Returns:
            Dictionary containing:
            - total_tests: Total number of tests
            - passed_tests: Number of passed tests
            - failed_tests: Number of failed tests
            - overall_accuracy: Percentage of passed tests
            - average_score: Average score across all tests
            - by_category: Accuracy breakdown by test category
            - timestamp: ISO timestamp of evaluation
        """
        total = len(results)
        passed = sum(1 for r in results if r.get("passed", False))
        failed = total - passed
        
        scores = [r.get("score", 0) for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Group by category
        by_category = {}
        for result in results:
            category = result.get("category", "unknown")
            if category not in by_category:
                by_category[category] = {"total": 0, "passed": 0}
            by_category[category]["total"] += 1
            if result.get("passed", False):
                by_category[category]["passed"] += 1
        
        # Calculate accuracy per category
        for category in by_category:
            cat_data = by_category[category]
            cat_data["accuracy"] = (cat_data["passed"] / cat_data["total"] * 100) if cat_data["total"] > 0 else 0
        
        overall_accuracy = (passed / total * 100) if total > 0 else 0
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "overall_accuracy": overall_accuracy,
            "average_score": avg_score,
            "by_category": by_category,
            "timestamp": datetime.now().isoformat()
        }

