
from rag import BankingRAG

# --------------------------------------------------
# RAG Evaluation Dataset
# --------------------------------------------------

TEST_CASES = [
    {
        "id": "B01",
        "query": "How do I report a scam or fraudulent transaction?",
        "expected_source": "02_dbs_fraud_reporting.md",
    },
    {
        "id": "B02",
        "query": "What should I do if my banking credentials or OTP are compromised?",
        "expected_source": "02_dbs_fraud_reporting.md",
    },
    {
        "id": "B03",
        "query": "How do I activate the DBS Safety Switch?",
        "expected_source": "02_dbs_fraud_reporting.md",
    },
    {
        "id": "B04",
        "query": "How do I block a lost or stolen DBS credit card?",
        "expected_source": "04_dbs_lost_stolen_cards.md",
    },
    {
        "id": "B05",
        "query": "How do I dispute an unauthorised card transaction?",
        "expected_source": "03_dbs_transaction_disputes.md",
    },
    {
        "id": "B06",
        "query": "Can a pending card transaction be cancelled?",
        "expected_source": "03_dbs_transaction_disputes.md",
    },
    {
        "id": "B07",
        "query": "What fees apply when using a DBS debit card overseas?",
        "expected_source": "05_dbs_fees_and_charges.md",
    },
    {
        "id": "B08",
        "query": "What are some common DBS card-related questions?",
        "expected_source": "01_dbs_card_faqs.md",
    },
]


# --------------------------------------------------
# Run Evaluation
# --------------------------------------------------

def evaluate_rag():
    print("=" * 65)
    print("FINASSIST AI - RAG RETRIEVAL EVALUATION")
    print("=" * 65)

    print("\nInitialising RAG model...")
    rag = BankingRAG()

    print(f"Knowledge base chunks: {len(rag.chunks)}")

    passed = 0
    results = []

    for case in TEST_CASES:
        retrieved = rag.retrieve(case["query"], k=3)

        expected_source = case["expected_source"]

        # Check whether the expected document appears
        # within the top 3 retrieved chunks.
        matching_results = [
            item for item in retrieved
            if item["source"] == expected_source
        ]

        # Also check whether the matching result meets
        # the application's MIN_SIMILARITY threshold.
        qualified_results = [
            item for item in matching_results
            if item["score"] >= 0.25
        ]

        passed_test = len(qualified_results) > 0

        if passed_test:
            passed += 1

        results.append({
            "id": case["id"],
            "passed": passed_test,
        })

        print("\n" + "-" * 65)
        print(f"TEST: {case['id']}")
        print(f"Query: {case['query']}")
        print(f"Expected document: {expected_source}")

        print("\nRetrieved results:")

        for rank, item in enumerate(retrieved, start=1):
            marker = (
                " <-- EXPECTED DOCUMENT"
                if item["source"] == expected_source
                else ""
            )

            print(
                f"Rank {rank}: {item['source']} | "
                f"Chunk {item['chunk_id']} | "
                f"Score {item['score']:.3f}"
                f"{marker}"
            )

        print(
            "\nResult:",
            "PASS" if passed_test else "FAIL"
        )

    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    total = len(TEST_CASES)
    pass_rate = (passed / total) * 100

    print("\n" + "=" * 65)
    print("RAG EVALUATION SUMMARY")
    print("=" * 65)

    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Hit@3 with similarity >= 0.25: {pass_rate:.2f}%")

    print("\nIndividual results:")

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"{result['id']}: {status}")

    print("=" * 65)


if __name__ == "__main__":
    evaluate_rag()
