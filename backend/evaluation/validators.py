"""
Response Validators Module

Contains all validation logic for agent responses during evaluation.
Each validator checks a specific aspect of the agent's response against
the expected test case outcomes.
"""

import json
import re
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional


class ResponseValidators:
    """
    Collection of response validation methods.
    
    Provides static methods for validating different aspects of agent responses
    against test case expectations.
    """
    
    @staticmethod
    def check_tool_usage(response: str, test_case: Dict) -> bool:
        """
        Verify that the correct tool was used based on the response.
        
        Args:
            response: Agent's response text
            test_case: Test case dictionary with expected_tool field
            
        Returns:
            True if correct tool was used (or tool usage cannot be determined), False otherwise
        """
        expected_tool = test_case.get("expected_tool")
        if not expected_tool:
            return True
        
        response_lower = response.lower()
        
        # Verify part number mentions for exact search
        if expected_tool == "search_by_part_number":
            expected_pn = test_case.get("expected_part_number", "")
            if expected_pn:
                return expected_pn in response
            # If no expected part number, verify that there are detailed specs
            return "spec" in response_lower or "torque" in response_lower or "voltage" in response_lower
        
        # For semantic search, verify that there are results OR clarification was requested
        if expected_tool == "semantic_search":
            # The agent can use different formats:
            # - "Part Number:" (most common in formatted responses)
            # - "Base Part Number" (in raw tool format)
            # - "Result X:" (in raw tool format)
            # - Numbered list (1., 2., 3.)
            # - Or can ask for clarification if no results found
            
            # Indicators that semantic_search was used and there are results
            part_number_indicators = [
                "part number",
                "base part number",
                "result 1",
                "result 2",
                "result 3",
            ]
            
            # Count how many indicators appear
            found_indicators = sum(1 for indicator in part_number_indicators if indicator in response_lower)
            
            # Also verify that there are part numbers (format "Part Number: XXX")
            part_number_matches = len(re.findall(r'part number[:\s]+[a-z0-9\-]+/[a-z]', response_lower, re.IGNORECASE))
            
            # Indicators that the agent is responding to a semantic search
            semantic_indicators = [
                "here are",
                "found",
                "matching",
                "actuators",
                "options",
                "recommendations",
            ]
            
            # If there are results (part numbers or indicators)
            has_results = part_number_matches >= 1 or found_indicators >= 1 or any(ind in response_lower for ind in semantic_indicators)
            
            # Or if asking for clarification (also indicates tool was used)
            asking_clarification = any(phrase in response_lower for phrase in [
                "could you please",
                "please specify",
                "please confirm",
                "could you clarify",
                "what",
                "which",
            ]) and ("voltage" in response_lower or "power" in response_lower or "phase" in response_lower)
            
            return has_results or asking_clarification
        
        return True
    
    @staticmethod
    def check_expected_fields(response: str, test_case: Dict) -> bool:
        """
        Verify that the response contains expected fields.
        
        Args:
            response: Agent's response text
            test_case: Test case dictionary with expected_fields list
            
        Returns:
            True if at least 80% of expected fields are present, False otherwise
        """
        expected_fields = test_case.get("expected_fields", [])
        if not expected_fields:
            return True
        
        # Check if at least 80% of expected fields are mentioned
        found_count = 0
        for field in expected_fields:
            # Normalize field name for checking
            field_variants = [
                field,
                field.replace("_", " ").title(),
                field.replace("_", " "),
            ]
            
            if any(variant.lower() in response.lower() for variant in field_variants):
                found_count += 1
        
        return (found_count / len(expected_fields)) >= 0.8
    
    @staticmethod
    def check_ground_truth(response: str, test_case: Dict, settings) -> Dict[str, Any]:
        """
        Verify exact values against ground truth data.
        
        This method validates that numeric and string values in the response
        match the expected ground truth values with appropriate tolerance.
        
        Args:
            response: Agent's response text
            test_case: Test case dictionary with ground_truth field
            settings: Application settings for database path access
            
        Returns:
            Dictionary containing:
            - checked: Boolean indicating if ground truth validation was performed
            - accuracy: Percentage of correct fields (0-100)
            - total_fields: Total number of fields checked
            - correct_fields: Number of correct fields
            - details: Dictionary with validation status for each field
        """
        ground_truth = test_case.get("ground_truth", {})
        if not ground_truth:
            return {"checked": False, "accuracy": 100, "details": {}}
        
        response_lower = response.lower()
        total_fields = 0
        correct_fields = 0
        details = {}
        
        # First, verify the record exists in DB and has these fields
        # This helps us know which fields are actually available
        db_data = {}
        try:
            # Use settings to get the correct database path
            db_path = Path(settings.sqlite_db_path)
            if not db_path.is_absolute():
                # If relative path, make it relative to backend directory
                # Get backend directory from script location
                script_dir = Path(__file__).parent
                backend_dir = script_dir.parent  # Go up from evaluation/ to backend/
                db_path = backend_dir / db_path
            
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                part_number = ground_truth.get("base_part_number")
                if part_number:
                    cursor.execute('SELECT data_json FROM actuators WHERE base_part_number = ?', (part_number,))
                    row = cursor.fetchone()
                    if row:
                        db_data = json.loads(row[0])
                conn.close()
        except Exception as e:
            # If DB access fails, continue without DB validation
            print(f"  Warning: Could not access database for ground truth validation: {e}")
            db_data = {}
        
        for field, expected_value in ground_truth.items():
            if field == "base_part_number":
                continue  # Already checked separately
            
            # Skip fields that don't exist in the database record
            # This handles cases where different tables have different columns
            if db_data and field not in db_data:
                # Field doesn't exist in this record, skip it
                details[field] = "not_available"
                continue
            
            total_fields += 1
            
            # Extract numeric values from response
            if isinstance(expected_value, (int, float)):
                # First, try direct value match (most reliable)
                expected_str = str(expected_value)
                if expected_str in response:
                    correct_fields += 1
                    details[field] = "correct"
                    continue
                
                # For specific fields, check context around the field name
                field_context = None
                if "duty_cycle" in field.lower():
                    # Handle "Duty Cycle 54%: 70.0" format
                    field_context = "duty cycle"
                elif "torque" in field.lower():
                    field_context = "torque"
                elif "power" in field.lower() and "motor" in field.lower():
                    field_context = "motor power"
                elif "power" in field.lower():
                    field_context = "power"
                elif "speed" in field.lower() and "60" in field.lower():
                    field_context = "60hz"
                elif "speed" in field.lower():
                    field_context = "speed"
                elif "cycles" in field.lower():
                    field_context = "cycles"
                elif "starts" in field.lower():
                    field_context = "starts"
                
                # If we have context, look for the value near the context
                if field_context:
                    # More flexible pattern: look for context followed by value
                    # Handle formats like "Duty Cycle 54%: 70.0" or "Output Torque: 300.0"
                    patterns = [
                        rf'{field_context}[^:]*:\s*([\d.,]+)',  # "Field: value"
                        rf'{field_context}[^:]*\([^)]*\)[^:]*:\s*([\d.,]+)',  # "Field (unit): value"
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, response_lower, re.IGNORECASE)
                        for match in matches:
                            try:
                                # Clean the match (remove commas, etc.)
                                clean_match = match.replace(',', '').strip()
                                match_value = float(clean_match)
                                tolerance = abs(expected_value * 0.05) if expected_value != 0 else 0.1
                                if abs(match_value - expected_value) <= tolerance:
                                    correct_fields += 1  # Full credit for context match
                                    details[field] = "correct"
                                    break
                            except (ValueError, TypeError):
                                pass
                        if field in details:
                            break
                
                # If still not found, check with tolerance for any numbers
                if field not in details:
                    try:
                        # Try to find numbers near the expected value
                        numbers = re.findall(r'\b\d+\.?\d*\b', response)
                        numbers_float = [float(n) for n in numbers]
                        
                        # Check if expected value is within 5% tolerance
                        tolerance = abs(expected_value * 0.05) if expected_value != 0 else 0.1
                        if any(abs(float(n) - expected_value) <= tolerance for n in numbers_float):
                            correct_fields += 0.8  # Partial credit
                            details[field] = "close"
                        else:
                            details[field] = "missing"
                    except (ValueError, TypeError):
                        details[field] = "missing"
            else:
                # For string values, check presence
                if str(expected_value).lower() in response_lower:
                    correct_fields += 1
                    details[field] = "correct"
                else:
                    details[field] = "missing"
        
        accuracy = (correct_fields / total_fields * 100) if total_fields > 0 else 100
        
        return {
            "checked": True,
            "accuracy": accuracy,
            "total_fields": total_fields,
            "correct_fields": correct_fields,
            "details": details
        }
    
    @staticmethod
    def check_part_number(response: str, test_case: Dict) -> bool:
        """
        Verify that the expected part number is present in the response.
        
        Args:
            response: Agent's response text
            test_case: Test case dictionary with expected_part_number
            
        Returns:
            True if expected part number is found, False otherwise
        """
        expected_pn = test_case.get("expected_part_number")
        if not expected_pn:
            return True
        
        return expected_pn in response
    
    @staticmethod
    def check_context_type(response: str, test_case: Dict) -> bool:
        """
        Verify that the expected context_type (voltage/power) is present in the response.
        
        Args:
            response: Agent's response text
            test_case: Test case dictionary with expected_context_type or expected_context_type_contains
            
        Returns:
            True if expected context type is found, False otherwise
        """
        expected_ct = test_case.get("expected_context_type")
        expected_ct_contains = test_case.get("expected_context_type_contains")
        
        response_lower = response.lower()
        
        if expected_ct:
            return expected_ct.lower() in response_lower
        
        if expected_ct_contains:
            return expected_ct_contains.lower() in response_lower
        
        return True
    
    @staticmethod
    def check_min_results(response: str, test_case: Dict) -> bool:
        """
        Verify that the minimum number of results is present in the response.
        
        Args:
            response: Agent's response text
            test_case: Test case dictionary with min_results field
            
        Returns:
            True if minimum results are found or clarification is being asked, False otherwise
        """
        min_results = test_case.get("min_results", 0)
        if min_results == 0:
            return True
        
        # If agent is asking for clarification, don't penalize for min_results
        response_lower = response.lower()
        asking_clarification = any(phrase in response_lower for phrase in [
            "could you please",
            "please specify",
            "please confirm",
            "could you clarify",
        ])
        
        if asking_clarification:
            return True
        
        # Count occurrences of "Base Part Number:" or numbered results
        part_number_count = response.count("Base Part Number:")
        numbered_results = len(re.findall(r'\n\d+\.\s', response))
        
        count = max(part_number_count, numbered_results)
        return count >= min_results
    
    @staticmethod
    def check_clarification(response: str, test_case: Dict) -> bool:
        """
        Verify that clarification is requested when required.
        
        Args:
            response: Agent's response text
            test_case: Test case dictionary with should_ask_clarification field
            
        Returns:
            True if clarification is asked (when required) or not required, False otherwise
        """
        should_ask = test_case.get("should_ask_clarification", False)
        if not should_ask:
            return True
        
        clarification_phrases = [
            "what voltage",
            "which voltage",
            "what phase",
            "which phase",
            "need more",
            "please specify",
            "could you please",
            "please confirm",
        ]
        
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in clarification_phrases)

