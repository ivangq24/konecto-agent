"""
Langfuse Manager Module

Handles all Langfuse integration for evaluation tracking and scoring.
"""

import os
import traceback
from typing import Dict, List, Any, Optional

# Langfuse for evaluation
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None


class LangfuseManager:
    """
    Manages Langfuse integration for evaluation tracking.
    
    Handles dataset creation, item management, and score submission
    for observability and tracking of evaluation results.
    """
    
    def __init__(self, dataset_name: str, settings):
        """
        Initialize Langfuse manager.
        
        Args:
            dataset_name: Name of the Langfuse dataset
            settings: Application settings containing Langfuse configuration
        """
        self.dataset_name = dataset_name
        self.settings = settings
        self.langfuse = None
        
        # Initialize Langfuse if available
        if LANGFUSE_AVAILABLE and self.settings.langfuse_enabled:
            try:
                os.environ['LANGFUSE_PUBLIC_KEY'] = self.settings.langfuse_public_key or ""
                os.environ['LANGFUSE_SECRET_KEY'] = self.settings.langfuse_secret_key or ""
                os.environ['LANGFUSE_HOST'] = self.settings.langfuse_host
                
                self.langfuse = Langfuse()
                print(f"✓ Langfuse connected for evaluation")
            except Exception as e:
                print(f"WARNING: Failed to initialize Langfuse: {e}")
                self.langfuse = None
    
    def create_dataset(self, test_cases: List[Dict]) -> Optional[str]:
        """
        Create or update a dataset in Langfuse with test cases.
        
        Args:
            test_cases: List of test case dictionaries
            
        Returns:
            Dataset name if successful, None otherwise
        """
        if not self.langfuse:
            return None
        
        try:
            # Try to get existing dataset
            try:
                dataset = self.langfuse.get_dataset(name=self.dataset_name)
                print(f"✓ Dataset '{self.dataset_name}' found, updating...")
            except:
                # Create new dataset
                dataset = self.langfuse.create_dataset(
                    name=self.dataset_name,
                    description="Evaluation dataset for Actuator Agent"
                )
                print(f"✓ Dataset '{self.dataset_name}' created")
            
            # Add items to the dataset
            items_added = 0
            for test_case in test_cases:
                # Prepare input
                input_data = {
                    "query": test_case["input"],
                    "category": test_case.get("category", "unknown"),
                    "expected_tool": test_case.get("expected_tool"),
                }
                
                # Prepare expected output (ground truth)
                expected_output = {}
                if "ground_truth" in test_case:
                    expected_output["ground_truth"] = test_case["ground_truth"]
                if "expected_part_number" in test_case:
                    expected_output["expected_part_number"] = test_case["expected_part_number"]
                if "expected_context_type_contains" in test_case:
                    expected_output["expected_context_type"] = test_case["expected_context_type_contains"]
                if "min_results" in test_case:
                    expected_output["min_results"] = test_case["min_results"]
                
                try:
                    self.langfuse.create_dataset_item(
                        dataset_name=self.dataset_name,
                        input=input_data,
                        expected_output=expected_output,
                        id=test_case["id"],
                        metadata={
                            "category": test_case.get("category", "unknown"),
                            "description": test_case.get("description", ""),
                        }
                    )
                    items_added += 1
                except Exception as e:
                    # If item already exists, skip it
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        pass  # Item already exists, that's fine
                    else:
                        print(f"  Warning: Error adding item {test_case['id']}: {e}")
            
            print(f"✓ Dataset '{self.dataset_name}' ready with {items_added} new items")
            return self.dataset_name
            
        except Exception as e:
            print(f"WARNING: Error creating dataset in Langfuse: {e}")
            traceback.print_exc()
            return None
    
    def submit_scores(self, trace_id: str, metrics: Dict[str, Any], score: float, passed: bool):
        """
        Submit evaluation scores to Langfuse.
        
        Args:
            trace_id: Trace ID for the evaluation run
            metrics: Dictionary of validation metrics
            score: Overall score (0-100)
            passed: Whether the test passed
        """
        if not self.langfuse or not trace_id:
            return
        
        try:
            # Add scores for each metric
            for metric_name, metric_value in metrics.items():
                if metric_name == "ground_truth":
                    # Ground truth is a dict, add its accuracy as a score
                    if isinstance(metric_value, dict) and metric_value.get("checked"):
                        try:
                            self.langfuse.score(
                                trace_id=trace_id,
                                name="ground_truth_accuracy",
                                value=metric_value["accuracy"] / 100.0,  # Normalize to 0-1
                                comment=f"Ground truth accuracy: {metric_value['accuracy']:.1f}%"
                            )
                        except Exception:
                            pass  # Score may fail if trace doesn't exist yet
                elif isinstance(metric_value, bool):
                    try:
                        self.langfuse.score(
                            trace_id=trace_id,
                            name=metric_name,
                            value=1.0 if metric_value else 0.0,
                            comment=f"{metric_name}: {'PASS' if metric_value else 'FAIL'}"
                        )
                    except Exception:
                        pass
            
            # Add overall score
            try:
                self.langfuse.score(
                    trace_id=trace_id,
                    name="overall_score",
                    value=score / 100.0,  # Normalize to 0-1
                    comment=f"Overall test score: {score:.1f}% - {'PASS' if passed else 'FAIL'}"
                )
            except Exception:
                pass
                
        except Exception as e:
            # Scores are optional, just continue
            pass
    
    def flush(self):
        """Flush pending Langfuse data."""
        if self.langfuse:
            self.langfuse.flush()

