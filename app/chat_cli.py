from app.database import SessionLocal
from app.models import Repository
from app.ingestion.rag.conversation_manager import ConversationManager
from app.ingestion.rag.pipeline import RAGPipeline


def main():
    db = SessionLocal()

    try:
        repositories = (
            db.query(Repository)
            .order_by(Repository.id)
            .all()
        )

        if not repositories:
            print("No repositories found.")
            return

        print("\nAvailable repositories:\n")

        for repo in repositories:
            print(f"[{repo.id}] {repo.name}")

        print()

        repository_id = int(
            input("Repository ID: ").strip()
        )

        repository = (
            db.query(Repository)
            .filter(Repository.id == repository_id)
            .first()
        )

        if repository is None:
            print("Repository not found.")
            return

    finally:
        db.close()

    manager = ConversationManager()

    try:
        conversation = manager.create_conversation(
            repository_id=repository_id,
            title=f"Chat with {repository.name}",
        )

        print()
        print("=" * 60)
        print(f"CodeAtlas Chat - {repository.name}")
        print(f"Conversation ID: {conversation.id}")
        print("Type 'exit' or 'quit' to leave.")
        print("=" * 60)

        pipeline = RAGPipeline()

        while True:
            print()
            question = input("You: ").strip()

            if not question:
                continue

            if question.lower() in {"exit", "quit"}:
                print("\nGoodbye.")
                break

            try:
                answer = pipeline.answer(
                    question=question,
                    repository_id=repository.id,
                    conversation_id=conversation.id
                )

                print()
                print("CodeAtlas:")
                print(answer)

            except Exception as exc:
                print()
                print(f"Error: {exc}")

    finally:
        manager.close()


if __name__ == "__main__":
    main()
