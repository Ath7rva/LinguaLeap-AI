from app.services import ai
from app.services.pronunciation import compare_words
from tests.conftest import register


def auth_headers(data):
    return {"Authorization": f"Bearer {data['access_token']}"}


def researcher(client, email="advanced@admin.local"):
    return register(client, email, consent=False, researcher_access_code="test-researcher-code")


def test_refresh_token_rotates_and_rejects_reuse(client):
    data = register(client, "refresh@example.com", consent=False)
    rotated = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != data["refresh_token"]
    assert client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]}).status_code == 401


def test_email_verification_and_password_reset(client):
    data = register(client, "security@example.com", consent=False)
    assert client.post("/auth/verify-email", json={"token": data["verification_token"]}).json()["verified"] is True
    forgot = client.post("/auth/forgot-password", json={"email": "security@example.com"}).json()
    assert client.post("/auth/reset-password", json={
        "token": forgot["reset_token"],
        "password": "NewSecurePass123!",
    }).status_code == 200
    assert client.post("/auth/login", data={
        "username": "security@example.com",
        "password": "NewSecurePass123!",
    }).status_code == 200


def test_registration_preserves_selected_language(client):
    response = client.post("/auth/register", json={
        "name": "German Learner",
        "email": "selected-language@example.com",
        "password": "SecurePass123!",
        "selected_language": "de",
    })
    assert response.status_code == 201
    assert response.json()["user"]["selected_language"] == "de"


def test_placement_sets_cefr_and_mastery(client):
    data = register(client, "placement@example.com", consent=False)
    response = client.post("/advanced/placement", headers=auth_headers(data), json={"answers": {
        "meaning": "hello",
        "order": "correct",
        "listen": "partly",
        "write": "complete",
    }})
    assert response.status_code == 200
    assert response.json()["cefr_level"] == "B1"
    path = client.get("/advanced/learning-path", headers=auth_headers(data)).json()
    assert any(item["attempts"] == 1 for item in path["mastery"])
    assert path["recommendation"]["reason"]


def test_listening_attempt_updates_mastery(client):
    data = register(client, "listen@example.com", consent=False)
    response = client.post("/advanced/listening", headers=auth_headers(data), json={
        "exercise_id": "hi-listen-a1",
        "answer": "How are you?",
        "playback_count": 1,
        "transcript_revealed": False,
    })
    assert response.status_code == 200
    assert response.json()["correct"] is True
    assert response.json()["score"] == 100


def test_pronunciation_feedback_labels_word_differences():
    result = compare_words("Guten Morgen mein Freund", "Guten Abend Freund extra")
    statuses = {item["status"] for item in result["words"]}
    assert "matched" in statuses
    assert "substituted" in statuses or "missed" in statuses
    assert "phoneme-level" in result["disclaimer"]


def test_async_pronunciation_job_returns_word_feedback(client, monkeypatch):
    monkeypatch.setattr(ai, "transcribe_audio", lambda *_args, **_kwargs: "Guten Morgen")
    data = register(client, "pronunciation-job@example.com", consent=False)
    response = client.post(
        "/advanced/pronunciation-jobs",
        headers=auth_headers(data),
        files={"audio": ("speech.webm", b"sample-audio", "audio/webm")},
        data={
            "target": "Guten Morgen",
            "language_code": "de",
            "engagement_seconds": "12",
            "idempotency_key": "pronunciation-test-key",
        },
    )
    assert response.status_code == 202
    job = client.get(f"/advanced/jobs/{response.json()['job_id']}", headers=auth_headers(data)).json()
    assert job["status"] == "completed"
    assert job["result"]["score"] == 100
    assert job["result"]["word_feedback"]


def test_personalized_practice_schema_has_safe_fallback(monkeypatch):
    monkeypatch.setattr(ai.settings, "groq_api_key", "")
    result = ai.generate_personalized_practice("de", "A1", ["grammar"], ["das Buch"])
    assert len(result["exercises"]) >= 2
    assert all(item["answer"] for item in result["exercises"])
    assert result["fallback"] is True
    assert result["exercises"][0]["skill"] == "grammar"
    assert "sentence" in result["exercises"][0]["prompt"].lower()


def test_tutor_fallback_awards_no_xp_or_mastery(client, monkeypatch):
    monkeypatch.setattr(ai.settings, "groq_api_key", "")
    data = register(client, "fallback-tutor@example.com", consent=False)
    response = client.post("/platform/tutor", headers=auth_headers(data), json={
        "message": "Is this sentence correct?",
        "language_code": "de",
        "skill": "grammar",
        "engagement_seconds": 20,
    })
    assert response.status_code == 200
    assert response.json()["fallback"] is True
    assert response.json()["xp_awarded"] == 0
    assert response.json()["total_xp"] == 0


def test_personalized_practice_provider_failure_has_usable_fallback(monkeypatch):
    monkeypatch.setattr(ai.settings, "groq_api_key", "configured")
    monkeypatch.setattr(ai, "get_json", lambda _key: None)
    monkeypatch.setattr(ai, "set_json", lambda *_args: None)

    def provider_failure(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(ai.client.chat.completions, "create", provider_failure)
    result = ai.generate_personalized_practice("de", "A1", ["grammar"], ["das Buch"])
    assert len(result["exercises"]) >= 2
    assert result["fallback"] is True
    assert result["fallback_reason"] == "RuntimeError"


def test_account_deletion_removes_advanced_records(client):
    data = register(client, "delete-advanced@example.com", consent=True)
    headers = auth_headers(data)
    assert client.post("/advanced/listening", headers=headers, json={
        "exercise_id": "hi-listen-a1",
        "answer": "How are you?",
        "playback_count": 1,
        "transcript_revealed": False,
    }).status_code == 200
    response = client.delete("/platform/account", headers=headers)
    assert response.status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_researcher_invitation_allows_researcher_registration(client):
    owner = researcher(client, "owner@admin.local")
    invitation = client.post("/advanced/researcher-invitations", headers=auth_headers(owner), json={
        "email": "invited@example.edu",
    }).json()
    invited = client.post("/auth/register", json={
        "name": "Invited Researcher",
        "email": "invited@example.edu",
        "password": "SecurePass123!",
        "invitation_token": invitation["invitation_token"],
    })
    assert invited.status_code == 201
    assert invited.json()["user"]["role"] == "researcher"
    assert invited.json()["user"]["email_verified"] is True


def test_experiment_configuration_freezes_and_assignment_is_stable(client):
    owner = researcher(client, "experiment-owner@admin.local")
    headers = auth_headers(owner)
    created = client.post("/advanced/experiments", headers=headers, json={
        "name": "Tutor modality trial",
        "hypothesis": "Multimodal practice improves observed task scores.",
    }).json()
    activated = client.post(f"/advanced/experiments/{created['id']}/activate", headers=headers)
    assert activated.json()["status"] == "active"

    participant = register(client, "experiment-participant@example.com", consent=True)
    participant_headers = auth_headers(participant)
    first = client.post(f"/advanced/experiments/{created['id']}/enroll", headers=participant_headers).json()
    second = client.post(f"/advanced/experiments/{created['id']}/enroll", headers=participant_headers).json()
    assert first == second
    assert second["assignment_locked"] is True


def test_research_quality_marks_small_samples(client):
    owner = researcher(client, "quality@admin.local")
    response = client.get("/advanced/research-quality", headers=auth_headers(owner))
    assert response.status_code == 200
    assert response.json()["warnings"]
    assert "completion_funnel" in response.json()
