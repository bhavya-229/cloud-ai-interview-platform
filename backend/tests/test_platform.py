import json
from app.core.config import settings


def register_user(client, name, email, password, role):
    return client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password, "role": role}
    )


def login_user(client, email, password):
    return client.post(
        "/api/auth/login",
        json={"email": email, "password": password}
    )


def test_auth_workflow(client):
    # 1. Register candidate
    res_cand = register_user(client, "Jane Candidate", "jane@example.com", "secret123", "candidate")
    assert res_cand.status_code == 201
    cand_data = res_cand.json()
    assert cand_data["role"] == "candidate"
    assert "access_token" in cand_data

    # 2. Register recruiter
    res_rec = register_user(client, "Bob Recruiter", "bob@example.com", "recruiter123", "recruiter")
    assert res_rec.status_code == 201
    rec_data = res_rec.json()
    assert rec_data["role"] == "recruiter"

    # 3. Duplicate email rejected
    res_dup = register_user(client, "Jane 2", "jane@example.com", "secret123", "candidate")
    assert res_dup.status_code == 400

    # 4. Login with correct credentials
    res_login = login_user(client, "jane@example.com", "secret123")
    assert res_login.status_code == 200
    assert res_login.json()["email"] == "jane@example.com"

    # 5. Login with invalid password
    res_bad = login_user(client, "jane@example.com", "wrongpass")
    assert res_bad.status_code == 401


def test_role_authorization_and_job_management(client):
    # Setup candidate and recruiter
    c_res = register_user(client, "Candidate User", "candidate1@example.com", "pwd12345", "candidate")
    candidate_token = c_res.json()["access_token"]

    r_res = register_user(client, "Recruiter User", "recruiter1@example.com", "pwd12345", "recruiter")
    recruiter_token = r_res.json()["access_token"]

    # Candidate attempts to create a job -> Forbidden (403)
    cand_job_res = client.post(
        "/api/jobs",
        json={"title": "Dev", "description": "Backend dev", "required_skills": "Python"},
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert cand_job_res.status_code == 403

    # Recruiter creates a job -> Created (201)
    rec_job_res = client.post(
        "/api/jobs",
        json={
            "title": "Senior Cloud Engineer",
            "description": "Architect and scale distributed microservices.",
            "required_skills": "Python, Docker, FastAPI"
        },
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert rec_job_res.status_code == 201
    job_id = rec_job_res.json()["id"]

    # Candidate lists jobs -> Success (200)
    list_res = client.get("/api/jobs", headers={"Authorization": f"Bearer {candidate_token}"})
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["title"] == "Senior Cloud Engineer"

    # Recruiter updates job -> Success (200)
    update_res = client.put(
        f"/api/jobs/{job_id}",
        json={"title": "Lead Cloud Architect"},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Lead Cloud Architect"


def test_resume_upload(client, sample_pdf_bytes):
    # Register candidate
    c_res = register_user(client, "Alice Smith", "alice@example.com", "alicepass", "candidate")
    candidate_token = c_res.json()["access_token"]

    # Upload PDF resume
    files = {"file": ("alice_resume.pdf", sample_pdf_bytes, "application/pdf")}
    res = client.post(
        "/api/resumes/upload",
        files=files,
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["file_name"] == "alice_resume.pdf"
    assert "id" in data

    # Retrieve latest resume
    latest_res = client.get(
        "/api/resumes/latest",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert latest_res.status_code == 200
    assert latest_res.json()["file_name"] == "alice_resume.pdf"


def test_complete_interview_flow(client, sample_pdf_bytes, monkeypatch):
    # Set interview question count to 2 for quick end-to-end testing
    monkeypatch.setattr(settings, "INTERVIEW_QUESTION_COUNT", 2)

    # 1. Register Recruiter and Candidate
    r_res = register_user(client, "Google Recruiter", "grecruiter@example.com", "pass1234", "recruiter")
    recruiter_token = r_res.json()["access_token"]

    c_res = register_user(client, "John Doe", "john@example.com", "pass1234", "candidate")
    candidate_token = c_res.json()["access_token"]

    # 2. Recruiter posts job
    job_res = client.post(
        "/api/jobs",
        json={
            "title": "Backend Python Developer",
            "description": "Design clean APIs and handle data workflows.",
            "required_skills": "Python, FastAPI, SQL"
        },
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    job_id = job_res.json()["id"]

    # 3. Candidate uploads resume
    client.post(
        "/api/resumes/upload",
        files={"file": ("john_cv.pdf", sample_pdf_bytes, "application/pdf")},
        headers={"Authorization": f"Bearer {candidate_token}"}
    )

    # 4. Candidate starts interview
    start_res = client.post(
        "/api/interviews",
        json={"job_id": job_id},
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert start_res.status_code == 201
    interview = start_res.json()
    interview_id = interview["id"]
    assert interview["status"] == "in_progress"
    assert len(interview["questions"]) == 1
    q1 = interview["questions"][0]
    assert q1["sequence_number"] == 1
    assert "Python" in q1["question_text"]

    # 5. Candidate submits answer to Question 1
    ans1_res = client.post(
        f"/api/interviews/{interview_id}/answer",
        json={
            "question_id": q1["id"],
            "answer_text": "I have built REST APIs with Python and FastAPI for 3 years, optimizing database queries with SQLAlchemy."
        },
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert ans1_res.status_code == 200
    ans1_data = ans1_res.json()
    assert ans1_data["is_completed"] is False
    assert ans1_data["answered_count"] == 1
    assert ans1_data["evaluation"]["score"] == 8.5
    assert ans1_data["next_question"] is not None
    q2 = ans1_data["next_question"]
    assert q2["sequence_number"] == 2

    # 6. Candidate submits answer to Question 2 (target reached -> completed)
    ans2_res = client.post(
        f"/api/interviews/{interview_id}/answer",
        json={
            "question_id": q2["id"],
            "answer_text": "To optimize latency, I use connection pooling, add indexes on filtered foreign keys, and cache read-heavy queries."
        },
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert ans2_res.status_code == 200
    ans2_data = ans2_res.json()
    assert ans2_data["is_completed"] is True
    assert ans2_data["overall_score"] == 8.5
    assert ans2_data["final_feedback"]["recommendation"] == "Hire"

    # 7. Candidate views final results
    results_res = client.get(
        f"/api/interviews/{interview_id}/results",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert results_res.status_code == 200
    results = results_res.json()
    assert results["overall_score"] == 8.5
    assert len(results["breakdown"]) == 2
    assert results["assessment_report"]["recommendation"] == "Hire"

    # 8. Recruiter views candidate results
    rec_results_res = client.get(
        f"/api/interviews/{interview_id}/results",
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert rec_results_res.status_code == 200
    assert rec_results_res.json()["candidate_name"] == "John Doe"

    # 9. Recruiter dashboard stats update
    dash_res = client.get("/api/recruiters/dashboard", headers={"Authorization": f"Bearer {recruiter_token}"})
    assert dash_res.status_code == 200
    assert dash_res.json()["stats"]["completed_assessments"] == 1


def test_unauthorized_and_forbidden_access(client):
    # Unauthenticated request
    res = client.get("/api/jobs")
    assert res.status_code == 401

    # Candidate trying recruiter-only endpoint
    c_res = register_user(client, "Cand", "cand@test.com", "pass123", "candidate")
    c_token = c_res.json()["access_token"]
    res_rec = client.get("/api/recruiters/dashboard", headers={"Authorization": f"Bearer {c_token}"})
    assert res_rec.status_code == 403

    # Recruiter trying candidate-only endpoint
    r_res = register_user(client, "Rec", "rec@test.com", "pass123", "recruiter")
    r_token = r_res.json()["access_token"]
    res_cand = client.get("/api/candidates/dashboard", headers={"Authorization": f"Bearer {r_token}"})
    assert res_cand.status_code == 403


def test_resume_error_validation(client):
    c_res = register_user(client, "Cand Resume Test", "candres@test.com", "pass123", "candidate")
    c_token = c_res.json()["access_token"]

    # Upload non-PDF file
    res = client.post(
        "/api/resumes/upload",
        files={"file": ("notes.txt", b"plain text content", "text/plain")},
        headers={"Authorization": f"Bearer {c_token}"}
    )
    assert res.status_code == 400

    # Upload empty PDF
    res_empty = client.post(
        "/api/resumes/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
        headers={"Authorization": f"Bearer {c_token}"}
    )
    assert res_empty.status_code == 400


def test_missing_entities_error_handling(client):
    c_res = register_user(client, "Cand Errors", "canderrors@test.com", "pass123", "candidate")
    c_token = c_res.json()["access_token"]

    # Start interview for non-existent job
    res = client.post(
        "/api/interviews",
        json={"job_id": 99999},
        headers={"Authorization": f"Bearer {c_token}"}
    )
    assert res.status_code == 404

    # View non-existent interview
    res_inv = client.get(
        "/api/interviews/99999",
        headers={"Authorization": f"Bearer {c_token}"}
    )
    assert res_inv.status_code == 404

