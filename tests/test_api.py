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
    data = r.get_json()
    assert data["email"] == "test@example.com"
    assert data["profile_complete"] is False


def test_me_unauthenticated(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def _complete_profile(client, full_name="Alice Smith", username="alice", skill_level=5, gender="female"):
    return client.put(
        "/api/auth/profile",
        json={"full_name": full_name, "username": username, "skill_level": skill_level, "gender": gender},
    )


def test_update_profile_success(client):
    _auth_client(client)
    r = _complete_profile(client)
    assert r.status_code == 200
    data = r.get_json()
    assert data["full_name"] == "Alice Smith"
    assert data["username"] == "alice"
    assert data["skill_level"] == 5
    assert data["gender"] == "female"
    assert data["profile_complete"] is True


def test_update_profile_missing_full_name(client):
    _auth_client(client)
    r = client.put("/api/auth/profile", json={"username": "alice", "skill_level": 5, "gender": "female"})
    assert r.status_code == 400


def test_update_profile_invalid_skill_level(client):
    _auth_client(client)
    r = client.put("/api/auth/profile", json={"full_name": "Alice", "username": "alice", "skill_level": 11, "gender": "female"})
    assert r.status_code == 400


def test_update_profile_duplicate_username(client):
    _signup(client, email="user1@example.com")
    _complete_profile(client, username="taken")
    client.post("/api/auth/logout")
    _signup(client, email="user2@example.com")
    r = client.put("/api/auth/profile", json={"full_name": "Bob", "username": "taken", "skill_level": 3, "gender": "male"})
    assert r.status_code == 400


def test_update_profile_unauthenticated(client):
    r = client.put("/api/auth/profile", json={"full_name": "Alice", "username": "alice", "skill_level": 5, "gender": "female"})
    assert r.status_code == 401


def test_me_profile_complete_after_update(client):
    _auth_client(client)
    _complete_profile(client)
    r = client.get("/api/auth/me")
    assert r.get_json()["profile_complete"] is True


# ---------------------------------------------------------------------------
# People - unauthenticated
# ---------------------------------------------------------------------------

def test_list_people_unauthenticated(client):
    r = client.get("/api/people/")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Users (public browse)
# ---------------------------------------------------------------------------

def test_list_users_unauthenticated(client):
    r = client.get("/api/users/")
    assert r.status_code == 401


def test_list_users_authenticated_empty(client):
    _auth_client(client)
    r = client.get("/api/users/")
    assert r.status_code == 200
    # user without a complete profile is not included
    assert r.get_json() == []


def test_list_users_returns_completed_profiles_only(client):
    _auth_client(client)
    _complete_profile(client)
    r = client.get("/api/users/")
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 1
    assert data[0]["username"] == "alice"


def test_list_users_public_fields_only(client):
    _auth_client(client)
    _complete_profile(client)
    user = client.get("/api/users/").get_json()[0]
    for field in ("id", "username", "full_name", "skill_level", "gender", "photo_url"):
        assert field in user
    for private in ("email", "is_admin", "is_active", "password_hash"):
        assert private not in user


def test_list_users_excludes_disabled(client, app):
    _signup(client, email="disabled@example.com", password="password123")
    _complete_profile(client, username="disabled_user")
    client.post("/api/auth/logout")
    _signup(client)
    _make_admin(app)
    users = client.get("/api/admin/users").get_json()
    target = next(u for u in users if u["email"] == "disabled@example.com")
    client.patch(f"/api/admin/users/{target['id']}", json={"is_active": False})
    r = client.get("/api/users/")
    assert all(u["username"] != "disabled_user" for u in r.get_json())


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


# ---------------------------------------------------------------------------
# Admin helpers
# ---------------------------------------------------------------------------

def _make_admin(app, email="test@example.com"):
    """Directly set is_admin=True for the given user via DB."""
    from backend.models import User
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        user.is_admin = True
        from backend.extensions import db
        db.session.commit()


def _admin_client(client, app):
    _signup(client)
    _make_admin(app)
    return client


# ---------------------------------------------------------------------------
# Admin - users
# ---------------------------------------------------------------------------

def test_admin_list_users_unauthenticated(client):
    r = client.get("/api/admin/users")
    assert r.status_code == 401


def test_admin_list_users_non_admin(client):
    _auth_client(client)
    r = client.get("/api/admin/users")
    assert r.status_code == 403


def test_admin_list_users_as_admin(client, app):
    _admin_client(client, app)
    r = client.get("/api/admin/users")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    assert any(u["email"] == "test@example.com" for u in data)


def test_admin_user_has_expected_fields(client, app):
    _admin_client(client, app)
    r = client.get("/api/admin/users")
    user = r.get_json()[0]
    for field in ("id", "email", "profile_complete", "is_active", "is_admin", "updated_at", "created_at"):
        assert field in user


def test_admin_disable_user(client, app):
    _signup(client, email="target@example.com", password="password123")
    client.post("/api/auth/logout")
    _signup(client)
    _make_admin(app)
    users = client.get("/api/admin/users").get_json()
    target = next(u for u in users if u["email"] == "target@example.com")
    r = client.patch(f"/api/admin/users/{target['id']}", json={"is_active": False})
    assert r.status_code == 200
    assert r.get_json()["is_active"] is False


def test_admin_enable_user(client, app):
    _signup(client, email="target@example.com", password="password123")
    client.post("/api/auth/logout")
    _signup(client)
    _make_admin(app)
    users = client.get("/api/admin/users").get_json()
    target = next(u for u in users if u["email"] == "target@example.com")
    client.patch(f"/api/admin/users/{target['id']}", json={"is_active": False})
    r = client.patch(f"/api/admin/users/{target['id']}", json={"is_active": True})
    assert r.status_code == 200
    assert r.get_json()["is_active"] is True


def test_admin_cannot_disable_self(client, app):
    _admin_client(client, app)
    users = client.get("/api/admin/users").get_json()
    me = next(u for u in users if u["email"] == "test@example.com")
    r = client.patch(f"/api/admin/users/{me['id']}", json={"is_active": False})
    assert r.status_code == 403


def test_admin_delete_user(client, app):
    _signup(client, email="victim@example.com", password="password123")
    client.post("/api/auth/logout")
    _signup(client)
    _make_admin(app)
    users = client.get("/api/admin/users").get_json()
    target = next(u for u in users if u["email"] == "victim@example.com")
    r = client.delete(f"/api/admin/users/{target['id']}")
    assert r.status_code == 204
    users_after = client.get("/api/admin/users").get_json()
    assert all(u["email"] != "victim@example.com" for u in users_after)


def test_admin_cannot_delete_self(client, app):
    _admin_client(client, app)
    users = client.get("/api/admin/users").get_json()
    me = next(u for u in users if u["email"] == "test@example.com")
    r = client.delete(f"/api/admin/users/{me['id']}")
    assert r.status_code == 403


def test_admin_delete_nonexistent_user(client, app):
    _admin_client(client, app)
    r = client.delete("/api/admin/users/99999")
    assert r.status_code == 404


def test_disabled_user_cannot_login(client, app):
    _signup(client, email="disabled@example.com", password="password123")
    client.post("/api/auth/logout")
    _signup(client)
    _make_admin(app)
    users = client.get("/api/admin/users").get_json()
    target = next(u for u in users if u["email"] == "disabled@example.com")
    client.patch(f"/api/admin/users/{target['id']}", json={"is_active": False})
    client.post("/api/auth/logout")
    r = _login(client, email="disabled@example.com", password="password123")
    assert r.status_code == 403
