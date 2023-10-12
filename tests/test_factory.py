from transit_notification import create_app
import os
from unittest import mock

def test_config():
    """ Test create_app without passing test config. """
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_hello(client):
    response = client.get('/hello')
    assert response.data == b'Hello World!'


@mock.patch.dict(os.environ, {"DATABASE_URI": "sqlite:///environ"})
def test_db_url_environ(monkeypatch):
    """Test DATABASE_URL environment variable."""
    app = create_app()
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///environ"


def test_init_db_command(runner, monkeypatch):
    called = False

    def fake_init_db():
        nonlocal called
        called = True

    monkeypatch.setattr("transit_notification.init_db", fake_init_db)
    result = runner.invoke(args=["init-db"])
    assert "Initialized" in result.output
    assert called
