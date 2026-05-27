"""
Evaluation framework for FinMate.

Metrics:
1. Intent Classification Accuracy - Does the system correctly identify user intent?
2. Response Relevance (LLM-as-Judge) - Is the response relevant and helpful?
3. Faithfulness - Does the response stay grounded in retrieved context?

Also includes A/B testing framework for comparing configurations.
"""

import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from backend.agents.finance_graph import run_finance_agent
from backend.utils.config import OPENAI_API_KEY, DEFAULT_MODEL


def load_golden_dataset() -> list[dict]:
    """Load the golden evaluation dataset."""
    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    with open(dataset_path) as f:
        return json.load(f)


def evaluate_intent_accuracy(results: list[dict]) -> dict:
    """Metric 1: Intent Classification Accuracy."""
    correct = 0
    total = len(results)

    for r in results:
        if r["actual_intent"] == r["expected_intent"]:
            correct += 1

    return {
        "metric": "intent_accuracy",
        "score": correct / total if total > 0 else 0,
        "correct": correct,
        "total": total,
        "incorrect_cases": [
            {"id": r["id"], "expected": r["expected_intent"], "actual": r["actual_intent"]}
            for r in results
            if r["actual_intent"] != r["expected_intent"]
        ],
    }


def evaluate_response_relevance(results: list[dict]) -> dict:
    """Metric 2: LLM-as-Judge for response relevance."""
    llm = ChatOpenAI(model=DEFAULT_MODEL, openai_api_key=OPENAI_API_KEY, temperature=0)

    scores = []
    for r in results:
        judge_prompt = f"""Rate the following AI response on a scale of 1-5 for relevance and helpfulness.

User Question: {r['query']}
AI Response: {r['response'][:500]}

Scoring criteria:
5 - Directly addresses the question with specific, actionable advice
4 - Addresses the question well but could be more specific
3 - Partially relevant, misses key aspects
2 - Mostly irrelevant or generic
1 - Completely off-topic or unhelpful

Respond with ONLY a number (1-5)."""

        judge_response = llm.invoke([HumanMessage(content=judge_prompt)])
        try:
            score = int(judge_response.content.strip())
            score = max(1, min(5, score))
        except ValueError:
            score = 3
        scores.append(score)
        r["relevance_score"] = score

    avg_score = sum(scores) / len(scores) if scores else 0

    return {
        "metric": "response_relevance",
        "average_score": round(avg_score, 2),
        "max_possible": 5,
        "normalized_score": round(avg_score / 5, 3),
        "score_distribution": {str(i): scores.count(i) for i in range(1, 6)},
        "low_scoring": [
            {"id": r["id"], "query": r["query"], "score": r["relevance_score"]}
            for r in results
            if r.get("relevance_score", 5) <= 2
        ],
    }


def evaluate_contains_keywords(results: list[dict]) -> dict:
    """Metric 3: Check if responses contain expected key information."""
    scores = []
    for r in results:
        expected = r.get("expected_contains", [])
        if not expected:
            scores.append(1.0)
            continue

        response_lower = r["response"].lower()
        found = sum(1 for kw in expected if kw.lower() in response_lower)
        scores.append(found / len(expected))

    avg_score = sum(scores) / len(scores) if scores else 0

    return {
        "metric": "keyword_faithfulness",
        "average_score": round(avg_score, 3),
        "description": "Fraction of expected keywords found in responses",
    }


def run_ab_test(dataset: list[dict], config_a: dict, config_b: dict) -> dict:
    """
    A/B Test: Compare two configurations.
    Config format: {"model": "gpt-4o", "temperature": 0.3}
    """
    results_a = []
    results_b = []

    sample = dataset[:10]  # Use subset for A/B testing (cost efficiency)

    print(f"\nRunning Config A: {config_a}")
    for item in sample:
        start = time.time()
        result = run_finance_agent(user_message=item["query"])
        latency = time.time() - start
        results_a.append({
            **item,
            "response": result["response"],
            "actual_intent": result["intent"],
            "latency": latency,
        })

    print(f"\nRunning Config B: {config_b}")
    os.environ["DEFAULT_MODEL"] = config_b.get("model", DEFAULT_MODEL)
    for item in sample:
        start = time.time()
        result = run_finance_agent(user_message=item["query"])
        latency = time.time() - start
        results_b.append({
            **item,
            "response": result["response"],
            "actual_intent": result["intent"],
            "latency": latency,
        })

    intent_a = evaluate_intent_accuracy(results_a)
    intent_b = evaluate_intent_accuracy(results_b)

    avg_latency_a = sum(r["latency"] for r in results_a) / len(results_a)
    avg_latency_b = sum(r["latency"] for r in results_b) / len(results_b)

    return {
        "test_name": f"{config_a.get('model', 'A')} vs {config_b.get('model', 'B')}",
        "sample_size": len(sample),
        "config_a": {
            "config": config_a,
            "intent_accuracy": intent_a["score"],
            "avg_latency_seconds": round(avg_latency_a, 2),
        },
        "config_b": {
            "config": config_b,
            "intent_accuracy": intent_b["score"],
            "avg_latency_seconds": round(avg_latency_b, 2),
        },
        "winner": "A" if intent_a["score"] >= intent_b["score"] else "B",
        "conclusion": "",
    }


def run_full_evaluation(use_llm_judge: bool = True, sample_size: int = None) -> dict:
    """Run complete evaluation suite."""
    dataset = load_golden_dataset()
    if sample_size:
        dataset = dataset[:sample_size]

    print(f"Running evaluation on {len(dataset)} examples...")
    results = []

    for i, item in enumerate(dataset):
        print(f"  [{i+1}/{len(dataset)}] {item['query'][:50]}...")
        start = time.time()
        result = run_finance_agent(user_message=item["query"])
        latency = time.time() - start

        results.append({
            **item,
            "response": result["response"],
            "actual_intent": result["intent"],
            "latency": latency,
        })

    intent_metrics = evaluate_intent_accuracy(results)
    keyword_metrics = evaluate_contains_keywords(results)

    eval_results = {
        "timestamp": datetime.now().isoformat(),
        "dataset_size": len(dataset),
        "model": DEFAULT_MODEL,
        "metrics": {
            "intent_accuracy": intent_metrics,
            "keyword_faithfulness": keyword_metrics,
        },
        "average_latency": round(sum(r["latency"] for r in results) / len(results), 2),
    }

    if use_llm_judge:
        print("Running LLM-as-Judge evaluation...")
        relevance_metrics = evaluate_response_relevance(results)
        eval_results["metrics"]["response_relevance"] = relevance_metrics

    output_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(output_path, "w") as f:
        json.dump(eval_results, f, indent=2)

    print(f"\nResults saved to {output_path}")
    print(f"\n{'='*50}")
    print(f"EVALUATION RESULTS")
    print(f"{'='*50}")
    print(f"Intent Accuracy: {intent_metrics['score']:.1%}")
    print(f"Keyword Faithfulness: {keyword_metrics['average_score']:.1%}")
    if use_llm_judge:
        print(f"Response Relevance: {relevance_metrics['average_score']}/5.0")
    print(f"Average Latency: {eval_results['average_latency']}s")

    return eval_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run FinMate evaluations")
    parser.add_argument("--full", action="store_true", help="Run full eval with LLM judge")
    parser.add_argument("--quick", action="store_true", help="Quick eval (10 samples, no LLM judge)")
    parser.add_argument("--ab", action="store_true", help="Run A/B test")
    parser.add_argument("--sample", type=int, default=None, help="Number of samples to evaluate")
    args = parser.parse_args()

    if args.ab:
        dataset = load_golden_dataset()
        ab_results = run_ab_test(
            dataset,
            config_a={"model": "gpt-4o", "temperature": 0.3},
            config_b={"model": "gpt-4o-mini", "temperature": 0.3},
        )
        print(json.dumps(ab_results, indent=2))
    elif args.quick:
        run_full_evaluation(use_llm_judge=False, sample_size=10)
    else:
        run_full_evaluation(use_llm_judge=args.full, sample_size=args.sample)
