from app.ingestion.rag.pipeline import RAGPipeline
from app.ingestion.retrievalreranking.hybrid_search import HybridSearch
from app.ingestion.retrievalreranking.reranker import Reranker

from evaluation.metrics import (
    answer_contains_keywords,
    calculate_rate,
    citation_hit,
    retrieval_hit,
)


class Evaluator:
    def __init__(self, repository_id: int):
        self.repository_id = repository_id

        self.hybrid_search = HybridSearch()
        self.reranker = Reranker()
        self.pipeline = RAGPipeline()

    def retrieve(self, question: str) -> list[dict]:
        candidates = self.hybrid_search.search(
            query=question,
            top_k=10,
            repository_id=self.repository_id,
        )

        return self.reranker.rerank(
            query=question,
            candidates=candidates,
            top_k=5,
        )

    def evaluate_question(self, test_case: dict) -> dict:
        question = test_case["question"]
        expected_files = test_case["expected_files"]
        expected_keywords = test_case["expected_keywords"]

        print()
        print("=" * 70)
        print(f"Evaluating {test_case['id']}")
        print(question)
        print("=" * 70)

        # ---------------------------------------------------------
        # 1. Retrieval + Reranking
        # ---------------------------------------------------------

        ranked_results = self.retrieve(question)

        retrieval_ok = retrieval_hit(
            results=ranked_results,
            expected_files=expected_files,
        )

        print(
            f"Retrieval: {'PASS' if retrieval_ok else 'FAIL'}"
        )

        print("\nRetrieved sources:")

        for index, result in enumerate(ranked_results, start=1):
            chunk = result["chunk"]

            print(
                f"{index}. "
                f"{chunk.file.path}:"
                f"{chunk.start_line}-{chunk.end_line} "
                f"(score={result['rerank_score']:.4f})"
            )

        # ---------------------------------------------------------
        # 2. Generation
        # ---------------------------------------------------------

        answer = None
        generation_ok = False

        try:
            answer = self.pipeline.answer(
                question=question,
                repository_id=self.repository_id,
            )

            generation_ok = True

        except Exception as exc:
            print()
            print(
                "Generation: FAIL"
            )
            print(
                f"Generation error: {type(exc).__name__}: {exc}"
            )

        # ---------------------------------------------------------
        # 3. Answer + Citation
        # ---------------------------------------------------------

        answer_ok = False
        citation_ok = False

        if generation_ok and answer:
            answer_ok = answer_contains_keywords(
                answer=answer,
                expected_keywords=expected_keywords,
            )

            citation_ok = citation_hit(
                answer=answer,
                expected_files=expected_files,
            )

            print(
                f"Answer:    {'PASS' if answer_ok else 'FAIL'}"
            )

            print(
                f"Citation:  {'PASS' if citation_ok else 'FAIL'}"
            )

            print()
            print("Answer:")
            print(answer)

        return {
            "id": test_case["id"],
            "question": question,
            "retrieval": retrieval_ok,
            "generation": generation_ok,
            "answer": answer_ok,
            "citation": citation_ok,
            "answer_text": answer,
        }

    def evaluate(self, dataset: list[dict]) -> dict:
        results = []

        for test_case in dataset:
            result = self.evaluate_question(test_case)
            results.append(result)

        total = len(results)

        retrieval_success = sum(
            result["retrieval"]
            for result in results
        )

        generation_success = sum(
            result["generation"]
            for result in results
        )

        answer_success = sum(
            result["answer"]
            for result in results
        )

        citation_success = sum(
            result["citation"]
            for result in results
        )

        return {
            "total": total,

            "retrieval_rate": calculate_rate(
                retrieval_success,
                total,
            ),

            "generation_rate": calculate_rate(
                generation_success,
                total,
            ),

            "answer_rate": calculate_rate(
                answer_success,
                total,
            ),

            "citation_rate": calculate_rate(
                citation_success,
                total,
            ),

            "results": results,
        }
