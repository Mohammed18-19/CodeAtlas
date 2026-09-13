from evaluation.dataset import EVALUATION_DATASET
from evaluation.evaluator import Evaluator


def main():
    repository_id = 1

    evaluator = Evaluator(
        repository_id=repository_id
    )

    report = evaluator.evaluate(
        EVALUATION_DATASET
    )

    print()
    print()
    print("=" * 70)
    print("CodeAtlas Evaluation Report")
    print("=" * 70)

    print(
        f"Questions:           "
        f"{report['total']}"
    )

    print(
        f"Retrieval Hit Rate:  "
        f"{report['retrieval_rate'] * 100:.1f}%"
    )

    print(
        f"Generation Success:  "
        f"{report['generation_rate'] * 100:.1f}%"
    )

    print(
        f"Answer Accuracy:     "
        f"{report['answer_rate'] * 100:.1f}%"
    )

    print(
        f"Citation Accuracy:   "
        f"{report['citation_rate'] * 100:.1f}%"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
