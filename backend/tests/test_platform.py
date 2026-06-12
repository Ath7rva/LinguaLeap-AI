from tests.conftest import register


def test_registration_assigns_consented_participant(client):
    data = register(client)
    assert data["user"]["anonymous_id"].startswith("LL-")
    assert data["user"]["experiment_group"] in {"llm_tutor", "structured_baseline"}
    assert data["user"]["delivery_group"] in {"text_only", "multimodal"}


def test_registration_without_consent_is_not_enrolled(client):
    data = register(client, consent=False)
    assert data["user"]["experiment_group"] == "not_enrolled"
    assert data["user"]["delivery_group"] == "not_enrolled"


def test_login_returns_token(client):
    register(client, "login@example.com")
    response = client.post("/auth/login", data={"username": "login@example.com", "password": "SecurePass123!"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_researcher_role_requires_private_code(client):
    denied = client.post("/auth/register", json={
        "name": "Unauthorized Researcher",
        "email": "denied@admin.local",
        "password": "SecurePass123!",
    })
    allowed = register(
        client,
        "allowed@admin.local",
        consent=False,
        researcher_access_code="test-researcher-code",
    )
    assert denied.status_code == 403
    assert allowed["user"]["role"] == "researcher"


def test_lesson_completion_awards_xp_once(client, learner):
    _, headers = learner
    first = client.post("/platform/lessons/hi-foundations/complete", headers=headers)
    second = client.post("/platform/lessons/hi-foundations/complete", headers=headers)
    assert first.status_code == 200
    assert first.json()["xp_awarded"] == 35
    assert second.json()["xp_awarded"] == 0
    assert second.json()["xp"] == 35


def test_lesson_prerequisite_is_enforced(client, learner):
    _, headers = learner
    response = client.get("/platform/lessons/hi-vocabulary", headers=headers)
    assert response.status_code == 409


def test_quiz_scoring_and_analytics_are_computed(client, learner):
    _, headers = learner
    correct = client.post("/platform/exercises/submit", headers=headers, json={
        "exercise_id": "hi-mcq-hello",
        "answer": "नमस्ते",
        "engagement_seconds": 20,
    })
    incorrect = client.post("/platform/exercises/submit", headers=headers, json={
        "exercise_id": "hi-match-water",
        "answer": "रोटी",
        "engagement_seconds": 40,
    })
    analytics = client.get("/platform/analytics", headers=headers).json()
    assert correct.json()["correct"] is True
    assert incorrect.json()["correct"] is False
    assert analytics["metrics"]["total_interactions"] == 2
    assert analytics["metrics"]["accuracy"] == 50.0
    assert analytics["metrics"]["average_score"] == 62.5
    assert analytics["metrics"]["engagement"] == 30


def test_research_route_is_role_protected(client, learner):
    _, headers = learner
    assert client.get("/platform/research", headers=headers).status_code == 403


def test_research_export_is_anonymous_and_consent_gated(client):
    participant = register(client, "participant@example.com", consent=True)
    participant_headers = {"Authorization": f"Bearer {participant['access_token']}"}
    client.post("/platform/exercises/submit", headers=participant_headers, json={
        "exercise_id": "hi-mcq-hello", "answer": "नमस्ते", "engagement_seconds": 20,
    })

    excluded = register(client, "excluded@example.com", consent=False)
    excluded_headers = {"Authorization": f"Bearer {excluded['access_token']}"}
    client.post("/platform/exercises/submit", headers=excluded_headers, json={
        "exercise_id": "hi-mcq-hello", "answer": "नमस्ते", "engagement_seconds": 20,
    })

    researcher = register(client, "reviewer@admin.local", consent=False, researcher_access_code="test-researcher-code")
    researcher_headers = {"Authorization": f"Bearer {researcher['access_token']}"}
    response = client.get("/platform/research/export", headers=researcher_headers)
    assert response.status_code == 200
    assert participant["user"]["anonymous_id"] in response.text
    assert "participant@example.com" not in response.text
    assert excluded["user"]["anonymous_id"] not in response.text


def test_consent_withdrawal_excludes_previous_interactions(client, learner):
    data, headers = learner
    client.post("/platform/exercises/submit", headers=headers, json={
        "exercise_id": "hi-mcq-hello", "answer": "नमस्ते", "engagement_seconds": 20,
    })
    response = client.patch("/platform/privacy/consent", headers=headers, json={"research_consent": False})
    assert response.json()["user"]["experiment_group"] == "not_enrolled"

    researcher = register(client, "analyst@admin.local", consent=False, researcher_access_code="test-researcher-code")
    export = client.get(
        "/platform/research/export",
        headers={"Authorization": f"Bearer {researcher['access_token']}"},
    )
    assert data["user"]["anonymous_id"] not in export.text
