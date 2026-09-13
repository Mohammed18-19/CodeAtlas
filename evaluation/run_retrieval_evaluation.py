from app.ingestion.rag.pipeline import RAGPipeline
from evaluation.dataset import EVALUATION_DATASET
from evaluation.metrics import calculate_rate, retrieval_hit


def main():
    repository_id = 4

    pipeline = RAGPipeline()

    results = []

    for test_case in EVALUATION_DATASET:
        question = test_case["question"]
        expected_files = test_case["expected_files"]

        print()
        print("=" * 70)
        print(f"Evaluating {test_case['id']}")
        print(question)
        print("=" * 70)

        ranked_results = pipeline.retrieve(
            question=question,
            repository_id=repository_id,
            retrieval_top_k=30,
            final_top_k=5,
        )

        passed = retrieval_hit(
            results=ranked_results,
            expected_files=expected_files,
        )

        print(
            f"Retrieval: {'PASS' if passed else 'FAIL'}"
        )

        print()
        print("Retrieved sources:")

        if not ranked_results:
            print("  No results.")

        for index, result in enumerate(
            ranked_results,
            start=1,
        ):
            chunk = result["chunk"]

            print(
                f"{index}. "
                f"{chunk.file.path}:"
                f"{chunk.start_line}-"
                f"{chunk.end_line} "
                f"(score={result['rerank_score']:.4f})"
            )

        results.append(passed)

    total = len(results)
    successful = sum(results)

    rate = calculate_rate(
        successful,
        total,
    )

    print()
    print()
    print("=" * 70)
    print("CodeAtlas Retrieval Evaluation")
    print("=" * 70)
    print(f"Questions:          {total}")
    print(f"Retrieval Passes:   {successful}")
    print(f"Retrieval Hit Rate: {rate * 100:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()