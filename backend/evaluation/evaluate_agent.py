"""
Agent Evaluation Script using Langfuse

This script evaluates the accuracy of the ActuatorAgent by running a set of test cases
and measuring various metrics including tool usage, field presence, ground truth accuracy,
and clarification requests.

The script:
1. Loads test cases from a JSON dataset
2. Creates/updates a Langfuse dataset for tracking
3. Runs each test case through the agent
4. Validates responses against expected outcomes
5. Calculates accuracy metrics and scores
6. Sends results to Langfuse for observability
7. Saves detailed results to JSON files

Requirements:
- Langfuse API keys configured in settings (optional)
- SQLite database with processed actuator data
- Test dataset JSON file with test cases
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add backend directory to path for imports
script_dir = Path(__file__).parent
backend_dir = script_dir.parent  # Go up from evaluation/ to backend/
sys.path.insert(0, str(backend_dir))

from app.config import get_settings
from app.services.data_service import DataService
from app.agent.agent import ActuatorAgent

# Import refactored modules
# Add evaluation directory to path for script execution
sys.path.insert(0, str(script_dir))
from validators import ResponseValidators
from metrics import MetricsCalculator
from langfuse_manager import LangfuseManager
from io_handlers import DatasetLoader, ResultsSaver
from presentation import SummaryPrinter

from datetime import datetime


class AgentEvaluator:
    """
    Agent accuracy evaluator using Langfuse for observability.
    
    This class orchestrates the evaluation process by coordinating
    validators, metrics calculation, Langfuse integration, and I/O operations.
    
    Attributes:
        dataset_path: Path to the JSON dataset file containing test cases
        settings: Application settings configuration
        langfuse_manager: LangfuseManager instance for observability
        dataset_loader: DatasetLoader instance for loading test cases
        validators: ResponseValidators instance for validation
        metrics_calculator: MetricsCalculator instance for metrics
        results_saver: ResultsSaver instance for saving results
        summary_printer: SummaryPrinter instance for displaying results
    """
    
    def __init__(self, dataset_path: str, dataset_name: str = "actuator-agent-eval"):
        """
        Initialize the evaluator with dataset path and configuration.
        
        Args:
            dataset_path: Path to JSON file containing test cases
            dataset_name: Name for the Langfuse dataset (default: "actuator-agent-eval")
        """
        self.settings = get_settings()
        self.dataset_name = dataset_name
        
        # Initialize components
        self.dataset_loader = DatasetLoader(dataset_path)
        self.langfuse_manager = LangfuseManager(dataset_name, self.settings)
        self.validators = ResponseValidators()
        self.metrics_calculator = MetricsCalculator()
        self.results_saver = ResultsSaver()
        self.summary_printer = SummaryPrinter()
    
    def load_dataset(self) -> List[Dict]:
        """
        Load test cases from the evaluation dataset.
        
        Returns:
            List of test case dictionaries
            
        Raises:
            FileNotFoundError: If dataset file doesn't exist
            ValueError: If dataset structure is invalid
        """
        return self.dataset_loader.load()
    
    async def evaluate_test_case(
        self, 
        agent: ActuatorAgent, 
        test_case: Dict,
        trace_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single test case by running it through the agent and validating the response.
        
        Args:
            agent: ActuatorAgent instance to test
            test_case: Test case dictionary with input and expected outcomes
            trace_name: Optional trace name for Langfuse (unused, kept for compatibility)
            
        Returns:
            Dictionary containing:
            - test_id: Test case identifier
            - category: Test category
            - input: User query input
            - response: Agent's response text
            - conversation_id: Conversation ID for tracking
            - metrics: Dictionary of validation metrics (tool_usage_correct, etc.)
            - score: Overall score (0-100)
            - passed: Boolean indicating if test passed
            - langfuse_trace_id: Trace ID in Langfuse (if available)
        """
        try:
            response = await agent.process_message(
                test_case["input"],
                conversation_id=test_case["id"]
            )
            
            response_text = response["response"]
            conversation_id = response["conversation_id"]
            
            # Calculate metrics using validators
            metrics = {
                "tool_usage_correct": self.validators.check_tool_usage(response_text, test_case),
                "expected_fields_present": self.validators.check_expected_fields(response_text, test_case),
                "part_number_correct": self.validators.check_part_number(response_text, test_case),
                "context_type_correct": self.validators.check_context_type(response_text, test_case),
                "min_results_satisfied": self.validators.check_min_results(response_text, test_case),
                "clarification_asked": self.validators.check_clarification(response_text, test_case),
            }
            
            # Check ground truth if available
            ground_truth_result = self.validators.check_ground_truth(response_text, test_case, self.settings)
            metrics["ground_truth"] = ground_truth_result
            
            # Calculate overall pass/fail
            critical_checks = [
                metrics["tool_usage_correct"],
                metrics["expected_fields_present"],
                metrics["part_number_correct"],
                metrics["context_type_correct"],
                metrics["min_results_satisfied"],
            ]
            
            # If ground truth was checked, require high accuracy
            if ground_truth_result["checked"]:
                critical_checks.append(ground_truth_result["accuracy"] >= 80)
            
            # If should ask clarification, check that too
            if test_case.get("should_ask_clarification"):
                critical_checks.append(metrics["clarification_asked"])
            
            passed = all(critical_checks)
            
            # Calculate score (0-100)
            score = (sum(1 for check in critical_checks if check) / len(critical_checks)) * 100
            
            # Adjust score based on ground truth accuracy if available
            if ground_truth_result["checked"]:
                # Weight ground truth accuracy heavily (50% of total score)
                score = (score * 0.5) + (ground_truth_result["accuracy"] * 0.5)
            
            result = {
                "test_id": test_case["id"],
                "category": test_case["category"],
                "input": test_case["input"],
                "response": response_text,
                "conversation_id": conversation_id,
                "metrics": metrics,
                "score": score,
                "passed": passed
            }
            
            # Send scores to Langfuse
            self.langfuse_manager.submit_scores(conversation_id, metrics, score, passed)
            result["langfuse_trace_id"] = conversation_id
            
            return result
            
        except Exception as e:
            error_msg = f"Error evaluating test case: {str(e)}"
            print(f"  ERROR: {error_msg}")
            return {
                "test_id": test_case["id"],
                "category": test_case["category"],
                "input": test_case["input"],
                "response": error_msg,
                "conversation_id": None,
                "metrics": {},
                "score": 0,
                "passed": False,
                "error": str(e)
            }
    
    async def evaluate_all(self) -> Dict[str, Any]:
        """
        Evaluate all test cases in the dataset.
        
        This method:
        1. Loads test cases from the dataset
        2. Creates/updates Langfuse dataset
        3. Initializes data service and agent
        4. Runs each test case
        5. Calculates overall metrics
        
        Returns:
            Dictionary containing:
            - overall: Overall metrics (accuracy, scores, by category)
            - results: List of individual test results
            - dataset_name: Name of Langfuse dataset
        """
        test_cases = self.load_dataset()
        
        print(f"\nLoaded {len(test_cases)} test cases\n")
        
        # Create dataset in Langfuse
        dataset_name = self.langfuse_manager.create_dataset(test_cases)
        
        print("Initializing services...")
        data_service = DataService(self.settings)
        await data_service.initialize()
        
        agent = ActuatorAgent(settings=self.settings, data_service=data_service)
        
        print(f"\nRunning {len(test_cases)} tests...")
        print("=" * 80)
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] Test {test_case['id']}: {test_case.get('description', test_case['category'])}")
            print(f"   Input: {test_case['input']}")
            
            result = await self.evaluate_test_case(agent, test_case)
            results.append(result)
            
            status_icon = "✓" if result["passed"] else "✗"
            status_text = "PASS" if result["passed"] else "FAIL"
            print(f"   {status_icon} {status_text} (Score: {result['score']:.1f}%)")
            
            if not result["passed"]:
                failed_metrics = [k for k, v in result.get('metrics', {}).items() 
                                if isinstance(v, bool) and not v]
                if failed_metrics:
                    print(f"   Failed metrics: {failed_metrics}")
        
        await data_service.cleanup()
        
        # Calculate overall metrics
        overall = self.metrics_calculator.calculate_overall_metrics(results)
        overall["dataset_name"] = dataset_name
        
        return {
            "overall": overall,
            "results": results,
            "dataset_name": dataset_name
        }
    
    def print_summary(self, overall: Dict, results: List[Dict]):
        """
        Print a formatted summary of evaluation results.
        
        Args:
            overall: Overall metrics dictionary
            results: List of individual test results
        """
        self.summary_printer.print_summary(overall, results, self.langfuse_manager)
    
    def save_results(self, overall: Dict, results: List[Dict], run_name: str):
        """
        Save evaluation results to JSON files.
        
        Args:
            overall: Overall metrics dictionary
            results: List of individual test results
            run_name: Name for the results file (timestamp-based)
        """
        output_dir = Path(__file__).parent / "results"
        self.results_saver.save(overall, results, run_name, output_dir)


async def main():
    """
    Main entry point for the evaluation script.
    
    Orchestrates the entire evaluation process:
    1. Loads test dataset
    2. Runs all test cases
    3. Calculates metrics
    4. Prints summary
    5. Saves results
    6. Sends to Langfuse
    """
    # Dataset is in the same directory as this script
    dataset_path = Path(__file__).parent / "dataset.json"
    
    evaluator = AgentEvaluator(str(dataset_path))
    
    print("=" * 80)
    print("AGENT ACCURACY EVALUATION")
    print("=" * 80)
    
    evaluation_results = await evaluator.evaluate_all()
    
    overall = evaluation_results["overall"]
    results = evaluation_results["results"]
    
    evaluator.print_summary(overall, results)
    
    # Save results
    run_name = f"agent_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    evaluator.save_results(overall, results, run_name)
    
    # Check if accuracy goal is met
    accuracy_goal = 80.0
    if overall["overall_accuracy"] >= accuracy_goal:
        print(f"\n✓ Accuracy goal met: {overall['overall_accuracy']:.1f}%")
    else:
        print(f"\n⚠️  Accuracy below goal ({accuracy_goal}%): {overall['overall_accuracy']:.1f}%")
    
    # Flush Langfuse
    if evaluator.langfuse_manager.langfuse:
        evaluator.langfuse_manager.flush()
        print("\n✓ Results sent to Langfuse")


if __name__ == "__main__":
    asyncio.run(main())
