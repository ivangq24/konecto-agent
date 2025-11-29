"""
Presentation Module

Handles formatting and printing of evaluation results.
"""

from typing import Dict, List, Any


class SummaryPrinter:
    """
    Prints formatted summaries of evaluation results.
    """
    
    @staticmethod
    def print_summary(overall: Dict, results: List[Dict], langfuse_manager=None):
        """
        Print a formatted summary of evaluation results.
        
        Args:
            overall: Overall metrics dictionary
            results: List of individual test results
            langfuse_manager: Optional LangfuseManager for displaying Langfuse info
        """
        print("\n" + "=" * 80)
        print("EVALUATION RESULTS SUMMARY")
        print("=" * 80)
        print(f"Total tests: {overall['total_tests']}")
        print(f"Passed tests: {overall['passed_tests']}")
        print(f"Failed tests: {overall['failed_tests']}")
        print(f"Overall accuracy: {overall['overall_accuracy']:.2f}%")
        print(f"Average score: {overall['average_score']:.2f}%")
        
        print("\n" + "-" * 80)
        print("ACCURACY BY CATEGORY")
        print("-" * 80)
        for category, data in overall["by_category"].items():
            print(f"{category:20s} {data['passed']:2d}/{data['total']:2d} ({data['accuracy']:.1f}%)")
        
        failed_tests = [r for r in results if not r.get("passed", False)]
        if failed_tests:
            print("\n" + "-" * 80)
            print("FAILED TESTS")
            print("-" * 80)
            for test in failed_tests:
                print(f"\n{test['test_id']}: {test['category']}")
                print(f"   Input: {test['input']}")
                failed_metrics = [k for k, v in test.get('metrics', {}).items() 
                                if isinstance(v, bool) and not v]
                if failed_metrics:
                    print(f"   Failed: {', '.join(failed_metrics)}")
        else:
            print("\n✓ All tests passed!")
        
        print("\n" + "=" * 80)
        
        # Langfuse info
        if langfuse_manager and langfuse_manager.langfuse and overall.get("dataset_name"):
            print(f"\n✓ Dataset '{overall['dataset_name']}' available in Langfuse")
            print(f"  Visit {langfuse_manager.settings.langfuse_host} to view detailed results")

