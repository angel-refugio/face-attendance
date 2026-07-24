import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture
def app():
    app = create_app(
        config_override={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
        }
    )
    yield app


@pytest.fixture
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture
def client(app, db):
    return app.test_client()


@pytest.fixture
def auth_client(app, db):
    from app.models.user import User

    with app.app_context():
        user = User(username="testadmin", is_admin=True)
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()

    client = app.test_client()
    client.post(
        "/auth/login",
        data={"username": "testadmin", "password": "testpass"},
        follow_redirects=True,
    )
    return client
