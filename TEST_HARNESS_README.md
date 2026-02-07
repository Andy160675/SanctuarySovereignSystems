# Assistive Intelligence Test Harness (LOCAL / OLLAMA)

This folder contains tools for testing and evaluating assistive intelligence behaviors using a local Ollama instance.

## Files

- `assistive_test.py`: A simple, repeatable unit test for LLM behavior (Local).
- `assistive_harness.py`: An extended version that supports:
    - Multi-model comparison (e.g., `llama3`, `mistral`, `phi3`)
    - JSON structured output validation
    - Performance tracking (duration)
    - Automated result logging to JSON files

## Setup

1. **Install Ollama**:
   Download and install from [ollama.com](https://ollama.com/).

2. **Pull Models**:
   ```bash
   ollama pull llama3
   ollama pull mistral
   ollama pull phi3
   ```

3. **Install Python dependencies**:
   ```bash
   pip install openai
   ```

## Usage

### Simple Test
```bash
python assistive_test.py
```

### Multi-Model Harness
```bash
python assistive_harness.py
```
This will run the test against multiple local models and save the results to `harness_results_[timestamp].json`.

## Configuration
The scripts are configured to use:
- **Base URL**: `http://localhost:11434/v1`
- **Models**: Edit the `MODELS` list in `assistive_harness.py` or `MODEL` in `assistive_test.py` to match your local inventory.

## Evaluation Criteria
The tests are designed to verify the following assistive intelligence rules:
1. Do NOT make final decisions for the user.
2. Explicitly mark uncertainty.
3. Prefer clarification over guessing.
4. Structure output for readability.
5. Return control to the human.
