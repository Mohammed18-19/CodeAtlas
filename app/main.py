import logging

from flask import Flask, jsonify, request

from app.logging_config import setup_logging
from app.ingestion.ingest import ingest_repository
from app.ingestion.rag.pipeline import RAGPipeline
from app.ingestion.rag.conversation_manager import ConversationManager

app = Flask(__name__)

setup_logging()
logger = logging.getLogger(__name__)


class LazyPipeline:
    """
    Create the RAG pipeline only when it is actually needed.
    This prevents model loading during Flask startup and keeps
    pipeline.answer patchable in tests.
    """

    def __init__(self):
        self._pipeline = None

    def _get(self):
        if self._pipeline is None:
            self._pipeline = RAGPipeline()

        return self._pipeline

    def answer(self, *args, **kwargs):
        return self._get().answer(*args, **kwargs)


pipeline = LazyPipeline()


@app.get("/health")
def health():
    return jsonify({
        "service": "CodeAtlas",
        "status": "ok",
    })


@app.post("/repositories")
def create_repository():
    data = request.get_json(silent=True) or {}

    repo_url = data.get("repo_url")

    if not repo_url:
        return jsonify({
            "error": "repo_url is required"
        }), 400

    logger.info("Starting repository ingestion: %s", repo_url)


    try:
        repository = ingest_repository(repo_url)

        # Normal application case:
        # ingest_repository returns a Repository object.
        if hasattr(repository, "id"):
            return jsonify({
                "repository_id": repository.id,
                "status": "ingested",
                "name": repository.name,
                "file_count": repository.file_count,
            }), 201

        # Test/mock or simplified return case:
        # ingest_repository returns the repository ID directly.
        return jsonify({
            "repository_id": repository,
            "status": "ingested",
        }), 201

    except Exception:
        logger.exception("Repository ingestion failed")
        return jsonify({
            "error": "Failed to ingest repository."
        }), 500


@app.post("/conversations")
def create_conversation():
    data = request.get_json(silent=True) or {}

    repository_id = data.get("repository_id")
    title = data.get("title", "New Conversation")

    if repository_id is None:
        return jsonify({
            "error": "repository_id is required"
        }), 400

    manager = ConversationManager()

    try:
        conversation = manager.create_conversation(
            repository_id=repository_id,
            title=title,
        )

        return jsonify({
            "conversation_id": conversation.id,
            "repository_id": conversation.repository_id,
            "title": conversation.title,
        }), 201

    except Exception:
        logger.exception("Conversation creation failed")
        return jsonify({
            "error": "Failed to create conversation."
        }), 500

    finally:
        manager.close()


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}

    question = data.get("question")
    repository_id = data.get("repository_id")
    conversation_id = data.get("conversation_id")

    if not question:
        return jsonify({
            "error": "question is required"
        }), 400

    if not repository_id:
        return jsonify({
            "error": "repository_id is required"
        }), 400

    logger.info(
        "Processing chat request: repository_id=%s conversation_id=%s",
        repository_id,
        conversation_id,
    )

    try:
        answer = pipeline.answer(
            question=question,
            repository_id=repository_id,
            conversation_id=conversation_id,
        )

        logger.info(
            "Chat request completed: repository_id=%s conversation_id=%s",
            repository_id,
            conversation_id,
        )

        return jsonify({
            "answer": answer,
            "repository_id": repository_id,
        }), 200

    except ValueError as exc:
        logger.warning("Invalid chat request: %s", exc)
        return jsonify({
            "error": str(exc)
        }), 400

    except Exception:
        logger.exception("Chat request failed")
        return jsonify({
            "error": "Failed to process chat request."
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False,
    )