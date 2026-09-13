from unittest.mock import patch

from app.main import app


def test_health():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "ok"
    assert data["service"] == "CodeAtlas"


def test_chat_missing_question():
    client = app.test_client()

    response = client.post(
        "/chat",
        json={
            "repository_id": 4
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "question is required"


def test_chat_missing_repository_id():
    client = app.test_client()

    response = client.post(
        "/chat",
        json={
            "question": "What is Flask?"
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "repository_id is required"


def test_create_repository_missing_url():
    client = app.test_client()

    response = client.post(
        "/repositories",
        json={},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "repo_url is required"


def test_chat_success():
    client = app.test_client()

    with patch(
        "app.main.pipeline.answer",
        return_value="Mocked answer",
    ):
        response = client.post(
            "/chat",
            json={
                "question": "What is Flask?",
                "repository_id": 4,
            },
        )

    assert response.status_code == 200

    data = response.get_json()

    assert data["answer"] == "Mocked answer"
    assert data["repository_id"] == 4


def test_chat_invalid_conversation():
    client = app.test_client()

    with patch(
        "app.main.pipeline.answer",
        side_effect=ValueError("Conversation does not exist."),
    ):
        response = client.post(
            "/chat",
            json={
                "question": "What is Flask?",
                "repository_id": 4,
                "conversation_id": 999,
            },
        )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Conversation does not exist."


def test_create_repository_success():
    client = app.test_client()

    with patch(
        "app.main.ingest_repository",
        return_value=99,
    ):
        response = client.post(
            "/repositories",
            json={
                "repo_url": "https://github.com/example/test-repo",
            },
        )

    assert response.status_code == 202

    data = response.get_json()

    assert "job_id" in data
    assert data["job_id"]
    assert data["status"] == "queued"