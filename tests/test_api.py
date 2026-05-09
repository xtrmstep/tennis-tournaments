from __future__ import annotations

import pytest

from backend import create_app


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test",
            "WTF_CSRF_ENABLED": False,
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _signup(client, email="test@example.com", password="password123"):
    return client.post(
        "/api/auth/signup",
        json={"email": email, "password": password},
    )


def _login(client, email="test@example.com", password="password123"):
    return client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )


def _auth_client(client):
    """Sign up + log in, returning client with active session."""
    _signup(client)
    return client


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def test_signup_success(client):
    r = _signup(client)
    assert r.status_code == 201
    assert "id" in r.get_json()


def test_signup_duplicate_email(client):
    _signup(client)
    r = _signup(client)
    assert r.status_code == 400


def test_signup_missing_email(client):
    r = client.post("/api/auth/signup", json={"password": "password123"})
    assert r.status_code == 400


def test_signup_missing_password(client):
    r = client.post("/api/auth/signup", json={"email": "a@b.com"})
    assert r.status_code == 400


def test_signup_short_password(client):
    r = client.post("/api/auth/signup", json={"email": "a@b.com", "password": "abc"})
    assert r.status_code == 400


def test_login_success(client):
    _signup(client)
    r = _login(client)
    assert r.status_code == 200
    assert "id" in r.get_json()


def test_login_wrong_password(client):
    _signup(client)
    r = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert r.status_code == 401


def test_logout(client):
    _signup(client)
    r = client.post("/api/auth/logout")
    assert r.status_code == 200


def test_me_authenticated(client):
    _auth_client(client)
    r = client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.get_json()["email"] == "test@example.com"


def test_me_unauthenticated(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# People - unauthenticated
# ---------------------------------------------------------------------------

def test_list_people_unauthenticated(client):
    r = client.get("/api/people/")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# People - authenticated
# ---------------------------------------------------------------------------

def test_list_people_authenticated(client):
    _auth_client(client)
    r = client.get("/api/people/")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_create_person_valid(client):
    _auth_client(client)
    r = client.post(
        "/api/people/",
        data={"name": "Alice", "skill": "backhand"},
        content_type="multipart/form-data",
    )
    assert r.status_code == 201
    data = r.get_json()
    assert data["name"] == "Alice"
    assert data["skill"] == "backhand"


def test_create_person_missing_name(client):
    _auth_client(client)
    r = client.post(
        "/api/people/",
        data={"skill": "serve"},
        content_type="multipart/form-data",
    )
    assert r.status_code == 400


def test_get_person(client):
    _auth_client(client)
    r = client.post(
        "/api/people/",
        data={"name": "Bob"},
        content_type="multipart/form-data",
    )
    person_id = r.get_json()["id"]
    r2 = client.get(f"/api/people/{person_id}")
    assert r2.status_code == 200
    assert r2.get_json()["name"] == "Bob"


def test_get_person_not_found(client):
    _auth_client(client)
    r = client.get("/api/people/9999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Rating
# ---------------------------------------------------------------------------

def _create_person(client, name="TestPerson"):
    r = client.post(
        "/api/people/",
        data={"name": name},
        content_type="multipart/form-data",
    )
    return r.get_json()["id"]


def test_update_rating_valid(client):
    _auth_client(client)
    pid = _create_person(client)
    r = client.put(f"/api/people/{pid}/rating", json={"rating": 7})
    assert r.status_code == 200
    assert r.get_json()["rating"] == 7


def test_update_rating_zero(client):
    _auth_client(client)
    pid = _create_person(client)
    r = client.put(f"/api/people/{pid}/rating", json={"rating": 0})
    assert r.status_code == 400


def test_update_rating_eleven(client):
    _auth_client(client)
    pid = _create_person(client)
    r = client.put(f"/api/people/{pid}/rating", json={"rating": 11})
    assert r.status_code == 400


def test_update_rating_string(client):
    _auth_client(client)
    pid = _create_person(client)
    r = client.put(f"/api/people/{pid}/rating", json={"rating": "abc"})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def _add_people(client, count: int):
    for i in range(count):
        client.post(
            "/api/people/",
            data={"name": f"Player{i}"},
            content_type="multipart/form-data",
        )
        pid = i + 1
        client.put(f"/api/people/{pid}/rating", json={"rating": (i % 10) + 1})


def test_sorting_run_singles(client):
    _auth_client(client)
    _add_people(client, 4)
    r = client.post("/api/sorting/run", json={"mode": "singles"})
    assert r.status_code == 200
    assert r.get_json()["mode"] == "singles"


def test_sorting_run_doubles(client):
    _auth_client(client)
    _add_people(client, 4)
    r = client.post("/api/sorting/run", json={"mode": "doubles"})
    assert r.status_code == 200
    assert r.get_json()["mode"] == "doubles"


def test_sorting_run_unknown_mode(client):
    _auth_client(client)
    r = client.post("/api/sorting/run", json={"mode": "triples"})
    assert r.status_code == 400


def test_sorting_result_after_run(client):
    _auth_client(client)
    _add_people(client, 2)
    client.post("/api/sorting/run", json={"mode": "singles"})
    r = client.get("/api/sorting/result")
    assert r.status_code == 200


def test_sorting_result_no_prior_run(client):
    _auth_client(client)
    r = client.get("/api/sorting/result")
    assert r.status_code == 404


def test_sorting_doubles_odd_count_returns_400(client):
    _auth_client(client)
    _add_people(client, 3)
    r = client.post("/api/sorting/run", json={"mode": "doubles"})
    assert r.status_code == 400
