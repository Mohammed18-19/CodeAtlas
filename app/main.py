import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import text

from app.database import SessionLocal
from app.logging_config import setup_logging
from app.ingestion.ingest import ingest_repository
from app.ingestion.rag.pipeline import RAGPipeline
from app.ingestion.rag.conversation_manager import ConversationManager

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
        }
    },
)

setup_logging()
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# RAG pipeline
# -------------------------------------------------------------------

class LazyPipeline:
    """
    Loads the RAG pipeline only when the first chat request arrives.
    """

    def __init__(self):
        self._pipeline = None
        self._lock = threading.Lock()

    def _get(self):
        if self._pipeline is None:
            with self._lock:
                if self._pipeline is None:
                    self._pipeline = RAGPipeline()

        return self._pipeline

    def answer(self, *args, **kwargs):
        return self._get().answer(*args, **kwargs)


pipeline = LazyPipeline()


# -------------------------------------------------------------------
# Background ingestion
# -------------------------------------------------------------------

executor = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="codeatlas-ingestion",
)

jobs = {}
jobs_lock = threading.Lock()


def update_job(job_id, **updates):
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id].update(updates)


def get_job(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return None

        return dict(job)


def run_ingestion(job_id, repo_url):
    try:
        update_job(
            job_id,
            status="running",
            phase="validating",
            progress=5,
            message="Validating repository URL...",
        )

        parsed = urlparse(repo_url)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Repository URL must use http or https.")

        if parsed.netloc.lower() not in {
            "github.com",
            "www.github.com",
        }:
            raise ValueError(
                "Only public GitHub repositories are supported."
            )

        update_job(
            job_id,
            phase="ingesting",
            progress=10,
            message="Starting repository ingestion...",
        )

        def progress_callback(**updates):
            update_job(job_id, **updates)

        repository = ingest_repository(
            repo_url,
            progress_callback=progress_callback,
        )

        repository_id = repository["id"]
        repository_name = repository["name"]
        file_count = repository["file_count"]

        update_job(
            job_id,
            status="completed",
            phase="ready",
            progress=100,
            message="Repository is ready.",
            repository_id=repository_id,
            name=repository_name,
            file_count=file_count,
            error=None,
        )

        logger.info(
            "Repository ingestion completed: job_id=%s repository_id=%s",
            job_id,
            repository_id,
        )

    except Exception as exc:
        logger.exception(
            "Repository ingestion failed: job_id=%s",
            job_id,
        )

        update_job(
            job_id,
            status="failed",
            phase="failed",
            progress=0,
            message="Repository ingestion failed.",
            error=str(exc),
        )


# -------------------------------------------------------------------
# Health
# -------------------------------------------------------------------

@app.get("/health")
def health():
    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))

        return jsonify({
            "service": "CodeAtlas",
            "status": "ok",
            "database": "ok",
        })

    except Exception:
        logger.exception("Health check failed")

        return jsonify({
            "service": "CodeAtlas",
            "status": "degraded",
            "database": "unavailable",
        }), 503

    finally:
        db.close()


# -------------------------------------------------------------------
# Repository ingestion
# -------------------------------------------------------------------

@app.post("/repositories")
def create_repository():
    data = request.get_json(silent=True) or {}

    repo_url = data.get("repo_url")

    if not repo_url or not isinstance(repo_url, str):
        return jsonify({
            "error": "repo_url is required"
        }), 400

    repo_url = repo_url.strip()

    job_id = str(uuid.uuid4())

    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "phase": "queued",
            "progress": 0,
            "message": "Repository ingestion queued.",
            "repository_id": None,
            "name": None,
            "file_count": None,
            "error": None,
        }

    executor.submit(
        run_ingestion,
        job_id,
        repo_url,
    )

    logger.info(
        "Repository ingestion queued: job_id=%s url=%s",
        job_id,
        repo_url,
    )

    return jsonify({
        "job_id": job_id,
        "status": "queued",
    }), 202


@app.get("/repositories/status/<job_id>")
def repository_status(job_id):
    job = get_job(job_id)

    if job is None:
        return jsonify({
            "error": "Ingestion job not found."
        }), 404

    return jsonify(job), 200


@app.get("/repositories")
def list_repositories():
    manager = ConversationManager()

    try:
        repositories = manager.list_repositories()

        return jsonify({
            "repositories": [
                {
                    "id": repository.id,
                    "name": repository.name,
                    "file_count": repository.file_count,
                    "metadata": repository.repo_metadata,
                }
                for repository in repositories
            ]
        }), 200

    except Exception:
        logger.exception("Repository listing failed")
        return jsonify({
            "error": "Failed to load repositories."
        }), 500

    finally:
        manager.close()


@app.get("/conversations")
def list_conversations():
    manager = ConversationManager()

    try:
        conversations = manager.list_conversations()

        return jsonify({
            "conversations": [
                {
                    "id": conversation.id,
                    "repository_id": conversation.repository_id,
                    "repository_name": (
                        conversation.repository.name
                        if conversation.repository
                        else None
                    ),
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat(),
                }
                for conversation in conversations
            ]
        }), 200

    except Exception:
        logger.exception("Conversation listing failed")
        return jsonify({
            "error": "Failed to load conversations."
        }), 500

    finally:
        manager.close()


@app.get("/conversations/<int:conversation_id>")
def get_conversation(conversation_id):
    manager = ConversationManager()

    try:
        conversation = manager.get_conversation_with_messages(
            conversation_id
        )

        if conversation is None:
            return jsonify({
                "error": "Conversation not found."
            }), 404

        return jsonify({
            "id": conversation.id,
            "repository_id": conversation.repository_id,
            "repository_name": (
                conversation.repository.name
                if conversation.repository
                else None
            ),
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "messages": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                }
                for message in conversation.messages
            ],
        }), 200

    except Exception:
        logger.exception(
            "Conversation retrieval failed: id=%s",
            conversation_id,
        )
        return jsonify({
            "error": "Failed to load conversation."
        }), 500

    finally:
        manager.close()


# -------------------------------------------------------------------
# Conversations
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Chat
# -------------------------------------------------------------------

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

        return jsonify({
            "answer": answer,
            "repository_id": repository_id,
        }), 200

    except ValueError as exc:
        logger.warning(
            "Invalid chat request: %s",
            exc,
        )

        return jsonify({
            "error": str(exc)
        }), 400

    except Exception:
        logger.exception("Chat request failed")

        return jsonify({
            "error": "Failed to process chat request."
        }), 500



@app.get("/github/search")
def github_search_repositories():
    """
    Search public GitHub repositories through GitHub's public REST API.

    No GitHub credentials are required for public repositories.
    """
    from urllib.parse import quote
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    import json

    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"repositories": []})

    if len(query) > 200:
        return jsonify({"error": "Search query is too long."}), 400

    try:
        encoded = quote(query)
        url = (
            "https://api.github.com/search/repositories"
            f"?q={encoded}&sort=stars&order=desc&per_page=8"
        )

        req = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "CodeAtlas",
            },
        )

        with urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))

        repositories = []

        for repo in payload.get("items", []):
            repositories.append(
                {
                    "id": repo.get("id"),
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "html_url": repo.get("html_url"),
                    "clone_url": repo.get("clone_url"),
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "stargazers_count": repo.get("stargazers_count", 0),
                    "forks_count": repo.get("forks_count", 0),
                    "owner": {
                        "login": (repo.get("owner") or {}).get("login"),
                        "avatar_url": (repo.get("owner") or {}).get("avatar_url"),
                    },
                }
            )

        return jsonify({"repositories": repositories})

    except HTTPError as exc:
        if exc.code == 403:
            return jsonify(
                {
                    "error": (
                        "GitHub search rate limit reached. "
                        "You can still analyze a repository by pasting its URL."
                    )
                }
            ), 429

        return jsonify({"error": f"GitHub returned HTTP {exc.code}."}), 502

    except URLError:
        return jsonify(
            {"error": "Could not reach GitHub right now."}
        ), 502

    except Exception as exc:
        app.logger.exception("GitHub search failed")
        return jsonify({"error": str(exc)}), 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False,
    )
