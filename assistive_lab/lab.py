import argparse
import sys
import json
import os
import time
from openai import OpenAI

from .prompts import PROMPTS
from .rubric import score_response
from .validator import validate_json
from .governor import cognitive_governor
from .logger import log_run, log_event

# ---- CONFIG FOR LOCAL OLLAMA ----
DEFAULT_MODELS = ["llama3", "mistral"]
BASE_URL = "http://localhost:11434/v1"
API_KEY = "ollama"

def run_model(client, model, prompt, temperature=0):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"

def main():
    parser = argparse.ArgumentParser(description="Assistive Intelligence Test Lab")
    parser.add_argument("--runs", type=int, default=1, help="Number of load loops")
    parser.add_argument("--provider", type=str, default="ollama", choices=["ollama", "openai"], help="API provider")
    parser.add_argument("--api-key", type=str, help="API key (defaults to environment)")
    parser.add_argument("--models", type=str, help="Comma-separated model names")
    parser.add_argument("--prompt", type=str, default="v1_assistive_baseline", help="Prompt key from prompts.py")
    parser.add_argument("--temperature", "--temp", type=float, default=0.0, help="Temperature (default 0 for determinism)")
    parser.add_argument("--sleep", type=float, default=1.0, help="Sleep between runs")
    parser.add_argument("--truncate", type=int, default=300, help="Truncate output for display")
    parser.add_argument("--gate", action="store_true", help="Fail fast on drift/low scores")
    parser.add_argument("--min-score", type=int, default=2, help="Minimum score for gating")
    parser.add_argument("--expect-json", action="store_true", help="Require JSON output")

    args = parser.parse_args()

    # Provider logic
    if args.provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", BASE_URL)
        api_key = args.api_key or os.getenv("OLLAMA_API_KEY", API_KEY)
        models = args.models.split(",") if args.models else DEFAULT_MODELS
    else:
        base_url = "https://api.openai.com/v1"
        api_key = args.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OpenAI API key required (--api-key or OPENAI_API_KEY env)")
            sys.exit(1)
        models = args.models.split(",") if args.models else ["gpt-4o"]

    prompt_key = args.prompt
    if prompt_key not in PROMPTS:
        print(f"Error: Prompt '{prompt_key}' not found in prompts.py")
        sys.exit(1)
    
    prompt = PROMPTS[prompt_key]
    
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    print("\n=== Assistive Lab Start ===\n")
    print(f"Provider: {args.provider}, Models: {models}")
    print(f"Runs: {args.runs}, Temp: {args.temperature}")

    for i in range(args.runs):
        print(f"\n--- Load Loop {i+1} ---")

        for model in models:
            print(f"\nRunning model: {model}")

            start_time = time.time()
            output = run_model(client, model, prompt, temperature=args.temperature)
            latency = time.time() - start_time
            
            display_output = output[:args.truncate] + ("..." if len(output) > args.truncate else "")
            print(f"\nOutput:\n{display_output}")

            score = score_response(output)
            print(f"Score: {score} | Latency: {latency:.2f}s")

            governor_result = cognitive_governor(score, min_total=args.min_score)
            
            is_json = validate_json(output)
            if is_json:
                print("JSON valid")
            elif args.expect_json:
                print("FAILED: JSON expected but not found")
                if args.gate:
                    sys.exit(1)
            else:
                print("Not JSON (optional)")

            log_run(model, score)
            log_event({
                "loop": i + 1,
                "model": model,
                "provider": args.provider,
                "score": score,
                "min_score": args.min_score,
                "latency": latency,
                "is_json": is_json,
                "output_text": output,
                "governor_status": governor_result["status"],
                "governor_result": governor_result
            })

            if args.gate and not governor_result["ok"]:
                print(f"GATE TRIGGERED: Model {model} failed with score {score['total']} (min: {args.min_score})")
                sys.exit(1)

            time.sleep(args.sleep)

    print("\n=== Lab Complete ===")

if __name__ == "__main__":
    main()
