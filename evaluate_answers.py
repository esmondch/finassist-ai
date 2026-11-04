
import csv
import re
import time
from datetime import datetime

from app import respond


# --------------------------------------------------
# 1. Answer Grounding Evaluation Dataset
# --------------------------------------------------

TEST_CASES = [
    {
        "id": "C01",
        "query": "What is the process for submitting a card transaction dispute?",
    },
    {
        "id": "C02",
        "query": "What happens after I report a card transaction dispute?",
    },
    {
        "id": "C03",
        "query": "What does the DBS Safety Switch do?",
    },
    {
        "id": "C04",
        "query": "What are the steps for replacing a card through digibank?",
    },
    {
        "id": "C05",
        "query": "What is a pending card transaction, and what happens next?",
    },
    {
        "id": "C06",
        "query": "What information should I prepare before submitting a transaction dispute?",
    },
    {
        "id": "C07",
        "query": "What fees might apply to overseas debit card usage?",
    },
    {
        "id": "C08",
        "query": "What are DBS's published contact channels for general enquiries?",
    },
]


# --------------------------------------------------
# 2. Evaluation Settings
# --------------------------------------------------

CUSTOMER_ID = "CUST001"

OUTPUT_FILE = "answer_evaluation_results.csv"

# Delay between completed test cases.
# Increase to 15-20 seconds if TPM errors continue.
REQUEST_DELAY_SECONDS = 15


# --------------------------------------------------
# 3. Run Tests
# --------------------------------------------------

def evaluate_answers():

    print("=" * 70)
    print("FINASSIST AI - ANSWER GROUNDING EVALUATION")
    print("=" * 70)

    print(f"\nSelected demo customer: {CUSTOMER_ID}")
    print(f"Total test cases: {len(TEST_CASES)}")
    print(f"Delay between requests: {REQUEST_DELAY_SECONDS} seconds")

    results = []

    for index, case in enumerate(TEST_CASES):

        test_id = case["id"]
        query = case["query"]

        print("\n" + "=" * 70)
        print(f"TEST {test_id}")
        print("=" * 70)

        print(f"\nQuestion: {query}")

        try:
            # Reuse the existing FinAssist agent.
            answer, trace = respond(
                query,
                [],
                CUSTOMER_ID,
            )

            # Detect which route and tools were used.
            policy_tool_called = (
                "Selected tool: search_policies" in trace
            )

            transaction_tool_called = (
                "Selected tool: lookup_transactions" in trace
            )

            safety_gate_used = (
                "ROUTE: Safety gate" in trace
            )

            # Extract retrieved policy source information.
            retrieved_sources = re.findall(
                r"- ([\w.-]+\.md) \| chunk (\d+) \| similarity ([0-9.]+)",
                trace,
            )

            # Determine whether policy chunks were retrieved.
            policy_chunks_found = len(retrieved_sources) > 0

            # Check whether the expected policy tool was used.
            tool_pass = (
                policy_tool_called
                and policy_chunks_found
                and not transaction_tool_called
                and not safety_gate_used
            )

            print("\n--- GENERATED ANSWER ---")
            print(answer)

            print("\n--- EVALUATION TRACE ---")
            print(trace)

            print("\n--- AUTOMATED CHECKS ---")
            print(
                "Policy tool:",
                "PASS" if policy_tool_called else "FAIL",
            )
            print(
                "Policy chunks retrieved:",
                "PASS" if policy_chunks_found else "FAIL",
            )
            print(
                "No transaction tool used:",
                "PASS" if not transaction_tool_called else "FAIL",
            )

            print(
                "\nTool and retrieval result:",
                "PASS" if tool_pass else "FAIL",
            )

            # Save successful execution results.
            results.append({
                "test_id": test_id,
                "query": query,
                "answer": answer,
                "execution_status": "SUCCESS",
                "policy_tool_called": policy_tool_called,
                "transaction_tool_called": transaction_tool_called,
                "safety_gate_used": safety_gate_used,
                "policy_chunks_found": policy_chunks_found,
                "retrieved_sources": "; ".join(
                    f"{source} (chunk {chunk}, score {score})"
                    for source, chunk, score in retrieved_sources
                ),
                "tool_retrieval_pass": tool_pass,
                "grounding_score": "",
                "reviewer_notes": "",
                "developer_trace": trace,
            })

        except Exception as exc:

            error_message = f"{type(exc).__name__}: {exc}"

            # Identify API rate-limit errors separately.
            is_rate_limit = (
                "429" in str(exc)
                or "RateLimitError" in type(exc).__name__
                or "rate_limit_exceeded" in str(exc)
            )

            if is_rate_limit:
                execution_status = "RATE_LIMIT_ERROR"
            else:
                execution_status = "EXECUTION_ERROR"

            print(f"\nERROR: {error_message}")
            print(f"Execution status: {execution_status}")

            # Do not treat an API failure as a retrieval failure.
            results.append({
                "test_id": test_id,
                "query": query,
                "answer": "",
                "execution_status": execution_status,
                "policy_tool_called": "",
                "transaction_tool_called": "",
                "safety_gate_used": "",
                "policy_chunks_found": "",
                "retrieved_sources": "",
                "tool_retrieval_pass": "",
                "grounding_score": "",
                "reviewer_notes": error_message,
                "developer_trace": "",
            })

        # Wait between test cases to reduce TPM pressure.
        if index < len(TEST_CASES) - 1:

            print(
                f"\nWaiting {REQUEST_DELAY_SECONDS} seconds "
                "before the next test..."
            )

            time.sleep(REQUEST_DELAY_SECONDS)

    # --------------------------------------------------
    # 4. Save CSV Results
    # --------------------------------------------------

    fieldnames = list(results[0].keys())

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)

    # --------------------------------------------------
    # 5. Evaluation Summary
    # --------------------------------------------------

    total = len(results)

    successful = sum(
        1 for result in results
        if result["execution_status"] == "SUCCESS"
    )

    rate_limit_errors = sum(
        1 for result in results
        if result["execution_status"] == "RATE_LIMIT_ERROR"
    )

    execution_errors = sum(
        1 for result in results
        if result["execution_status"] == "EXECUTION_ERROR"
    )

    passed = sum(
        1 for result in results
        if result["tool_retrieval_pass"] is True
    )

    failed = sum(
        1 for result in results
        if result["tool_retrieval_pass"] is False
    )

    print("\n" + "=" * 70)
    print("ANSWER EVALUATION SUMMARY")
    print("=" * 70)

    print(f"Total tests: {total}")
    print(f"Successful executions: {successful}")
    print(f"Rate-limit errors: {rate_limit_errors}")
    print(f"Other execution errors: {execution_errors}")

    print(f"\nTool and retrieval passed: {passed}")
    print(f"Tool and retrieval failed: {failed}")

    if successful > 0:
        print(
            "Tool and retrieval pass rate among successful tests: "
            f"{passed / successful * 100:.2f}%"
        )
    else:
        print("No successful executions to calculate pass rate.")

    print("\nIndividual results:")

    for result in results:

        status = result["execution_status"]

        if status == "SUCCESS":
            result_label = (
                "PASS"
                if result["tool_retrieval_pass"]
                else "FAIL"
            )
        else:
            result_label = status

        print(f"{result['test_id']}: {result_label}")

    print(f"\nResults saved to: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    evaluate_answers()
