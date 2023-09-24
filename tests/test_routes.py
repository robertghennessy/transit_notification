import pytest
from transit_notification import create_app, db
from transit_notification.models import Operators
from transit_notification import db_commands, routes
import responses
import json
import configparser
import os



test_url = "https://api.511.org/Transit/"
test_key = "fake-key"


def test_index_before_setup(client):
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b"siri_base_url" in response.data
    assert b"api_key" in response.data
    assert b"Need to provide api address and api key before using"

def test_setup_render(client):
    response = client.get('/setup')
    assert response.status_code == 200
    assert b"siri_base_url" in response.data
    assert b"api_key" in response.data

def test_setup_missing_key_and_url(client):
    response = client.post("/setup", data={"siri_base_url": "", "api_key": ""})
    assert response.status_code == 200
    assert b"SIRI Base URL and API key are required!" in response.data

def test_setup_missing_url(client):
    response = client.post("/setup", data={"siri_base_url": "", "api_key": test_key})
    assert response.status_code == 200
    assert b"SIRI Base URL is required!" in response.data

def test_setup_missing_key(client):
    response = client.post("/setup", data={"siri_base_url": test_url, "api_key": ""})
    assert response.status_code == 200
    assert b"API Key is required!" in response.data

@responses.activate
def test_setup(client, app):
    with open("test_input_jsons/operators.json", 'r') as f:
        test_json = json.load(f)

    responses.add(
        responses.GET,
        "https://api.511.org/Transit/Operators?api_key=fake-key&Format=json",
        body=json.dumps(test_json),
        status=200,
        content_type="application/json",
    )
    response = client.post("/setup", data={"siri_base_url": test_url,
                                           "api_key": test_key}, follow_redirects=True)
    #Check that configuration file was written correctly
    config = configparser.ConfigParser()
    config.read(os.environ.get("KEY_API _FILE", "test_key_api.ini"))
    assert config["SIRI"]["base_url"] == test_url
    assert config["SIRI"]["api_key"] == test_key
    # Check the was redirected to the operators page
    assert response.status_code == 200
    assert b"Select Operator" in response.data
    # test that operator was inserted into the database
    with app.app_context():
        select = db.select(Operators).filter_by(operator_id="SF")
        operator = db.session.execute(select).scalar()
        assert operator is not None


def test_index_after_setup(client, app):
    with open("test_input_jsons/operators.json", 'r') as f:
        test_json = json.load(f)
    with app.app_context():
        db_commands.save_operators(db, test_json)
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        # check that monitored=True exists in output
        assert b'<a href="/operator/SF">San Francisco Municipal Transportation Agency</a>' in response.data
        # check that monitored = False is not in output
        assert b"Altamont Corridor Express" not in response.data


def test_lines_before_setup(client, app):
    response = client.get('/operator/SF', follow_redirects=True)
    assert response.status_code == 200
    assert b"siri_base_url" in response.data
    assert b"api_key" in response.data
    assert b"Need to provide api address and api key before using"

