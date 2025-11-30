# Agent Accuracy Evaluation

This directory contains the evaluation system for measuring the accuracy of the actuator agent.

## Files

- `dataset.json`: Dataset with 20 test cases
- `results/`: Directory with past evaluation results

## Test Cases (20 total)

### By category:
- **exact_search** (4 cases): Exact part number searches
- **semantic_search** (12 cases): Semantic searches with different requirements
- **incomplete_spec** (2 cases): Incomplete specifications requiring clarification
- **context_memory** (2 cases): Contextual memory tests

## Run Evaluation

```bash
docker-compose exec backend python evaluate_agent.py
```

## Evaluated Metrics

For each test case, the following are evaluated:

1. **tool_usage_correct**: Was the correct tool used?
2. **expected_fields_present**: Are the expected fields present? (80% threshold)
3. **part_number_correct**: Is the part number correct?
4. **context_type_correct**: Is the voltage/power type correct?
5. **min_results_satisfied**: Were enough results returned?
6. **clarification_asked**: Was clarification requested when necessary?
7. **ground_truth**: Do numeric values match ground truth? (5% tolerance)
8. **response_contains_all**: Does the response contain all required strings? (e.g., all voltage options)

### Ground Truth Validation

For cases with `ground_truth` defined, the following are validated:
- Exact numeric values (torque, power, speed, etc.)
- ±5% tolerance for numeric values
- Exact text values (context_type, part number)
- Overall data accuracy score (0-100%)

## Scoring

- **Individual Score**: 0-100% based on passed metrics
- **Overall Accuracy**: % of tests that passed all checks
- **Average Score**: Average of individual scores

## Langfuse Integration

The evaluation script is fully integrated with Langfuse and uses its native tools:

### Dataset in Langfuse

The script automatically:
1. **Creates a dataset** named `actuator-agent-eval` in Langfuse (or updates it if it already exists)
2. **Adds all test cases** as dataset items with:
   - Input: user query, category, expected tool
   - Expected Output: ground truth, expected part numbers, context types, etc.
   - Metadata: category and test description

You can view and manage the dataset in the Langfuse dashboard:
- Navigate to **Datasets** in the menu
- Search for `actuator-agent-eval`
- You'll see all test cases with their inputs and expected outputs

### Traces and Scores

Each agent execution during evaluation:
- Is automatically recorded as a **trace** (thanks to the `CallbackHandler` in the agent)
- Receives multiple **scores**:
  - `tool_usage_correct`: 1.0 if the correct tool was used, 0.0 otherwise
  - `expected_fields_present`: 1.0 if expected fields are present
  - `part_number_correct`: 1.0 if the part number is correct
  - `context_type_correct`: 1.0 if the context type is correct
  - `min_results_satisfied`: 1.0 if enough results were returned
  - `clarification_asked`: 1.0 if clarification was requested when necessary
  - `ground_truth_accuracy`: Ground truth accuracy (0.0-1.0)
  - `overall_score`: Overall test score (0.0-1.0)

### Visualization in Langfuse

After running the script, visit your Langfuse dashboard to see:

1. **Traces**: Each agent execution during evaluation
   - Filter by `test_case_id` in metadata to find specific cases
   - Review inputs, outputs, and tool calls

2. **Scores**: Evaluation metrics attached to each trace
   - See agent performance on each metric
   - Identify which tests are failing and why

3. **Datasets**: The `actuator-agent-eval` dataset with all test cases
   - Manage your test cases from the UI
   - Run evaluations directly from Langfuse (if available in your plan)

4. **Analytics**: Aggregated metrics
   - Accuracy by category
   - Trends over time
   - Comparison between different agent versions

### Dashboard Access

1. Go to https://cloud.langfuse.com (or your local instance)
2. Open your project
3. Navigate to:
   - **Datasets** → `actuator-agent-eval` to see test cases
   - **Traces** → Filter by metadata `test_case_id` to see specific executions
   - **Scores** → View all evaluation metrics

## Results

Results are saved in:
- `evaluation/results/{run_name}.json`: Complete results
- `evaluation/results/latest.json`: Latest evaluation

## Interpreting Results

### Target Accuracy
- **≥ 90%**: Excellent
- **80-89%**: Good
- **70-79%**: Acceptable, requires improvements
- **< 70%**: Requires urgent optimization

### Most Common Failure Categories
1. Incorrect tool used
2. Missing fields in response
3. Does not ask for clarification when it should
4. Insufficient results

## Adding New Test Cases

### Example with ground_truth (recommended for exact_search):

```json
{
  "id": "test_XXX",
  "category": "exact_search",
  "input": "I need actuator 763A00-11330C00/A",
  "expected_tool": "search_by_part_number",
  "expected_part_number": "763A00-11330C00/A",
  "ground_truth": {
    "base_part_number": "763A00-11330C00/A",
    "context_type": "220V 3 Phase Power",
    "output_torque_nm": 300.0,
    "duty_cycle_54pct": 70.0,
    "motor_power_watts": 40.0,
    "operating_speed_sec_60_hz": 26.0,
    "cycles_per_hour_cycles": 39.0,
    "starts_per_hour_starts": 1200.0
  },
  "description": "Exact part number search with full spec verification"
}
```

### Example without ground_truth (for semantic_search):

```json
{
  "id": "test_XXX",
  "category": "semantic_search",
  "input": "I need high torque actuator",
  "expected_tool": "semantic_search",
  "min_results": 3,
  "validate_high_torque": true,
  "description": "Vague query - high torque"
}
```

### Available Fields:

- `id`: Unique identifier (required)
- `category`: exact_search|semantic_search|incomplete_spec|context_memory (required)
- `input`: User message (required)
- `expected_tool`: Expected tool (optional)
- `expected_part_number`: Expected part number (optional)
- `expected_context_type_contains`: Expected text in context_type (optional)
- `ground_truth`: Exact expected values (optional, recommended for exact_search)
- `min_results`: Minimum results (optional)
- `max_results`: Maximum results (optional)
- `should_ask_clarification`: Whether clarification should be requested (optional)
- `response_contains_all`: List of strings that MUST appear in response (optional)
- `validate_*`: Special validations (optional)
- `description`: Test description (required)

## Example Output

```
EVALUATION SUMMARY
================================================================================

Total tests: 20
Passed: 18 (90.0%)
Failed: 2
Average score: 92.5%

ACCURACY BY CATEGORY
--------------------------------------------------------------------------------
exact_search          4/ 4 (100.0%)
semantic_search      11/12 (91.7%)
incomplete_spec       2/ 2 (100.0%)
context_memory        1/ 2 (50.0%)

FAILED TESTS
--------------------------------------------------------------------------------
test_016: context_memory
   Input: single phase
   Failed: context_type_correct
```

