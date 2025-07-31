import pytest
import responses
import json
import configparser
import os
from unittest import mock
from transit_notification import create_app, db
from transit_notification.models import Operator
from transit_notification import db_commands, routes


test_url = "https://api.511.org/Transit/"
test_key = "fake-key"

""" Test Setup Page"""


def test_setup_render(client):
    response = client.get('/setup')
    assert response.status_code == 200
    assert b"Directions on setting up Transit Notification" in response.data


""" Test Index Page"""
@responses.activate
@mock.patch.dict(os.environ, {'API_KEY': test_key})
def test_operators_with_proper_setup(client, app):
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_json = json.load(f)
    responses.add(
        responses.GET,
        "https://api.511.org/Transit/Operators?api_key=fake-key&Format=json",
        body=json.dumps(operators_json),
        status=200,
        content_type="application/json",
    )
    with app.app_context():
        response = client.get('/operators', follow_redirects=True)
        assert response.status_code == 200
        assert b"Please select an operator from the list below." in response.data
        # check that monitored=True exists in output
        assert b'<a href="/operator/SF">San Francisco Municipal Transportation Agency</a>' in response.data
        # check that monitored = False is not in output
        assert b"Altamont Corridor Express" not in response.data


@responses.activate
@mock.patch.dict(os.environ, {'API_KEY': test_key})
def test_operators_with_improper_setup(client, app):
    response = client.get('/operators', follow_redirects=True)
    assert response.status_code == 200
    assert b"Directions on setting up Transit Notification" in response.data


@responses.activate
@mock.patch.dict(os.environ, {'API_KEY': test_key})
def test_api_error_error(client):
    responses.add(
        responses.GET,
        "https://api.511.org/Transit/Operators?api_key=fake-key&Format=json",
        status=400,
        body="400 Error",
    )
    response = client.get('/operators', follow_redirects=True)
    assert b"This API key provided is invalid" in response.data


def test_operator_before_index(client, app):
    with app.app_context():
        response = client.get('/operator/SF', follow_redirects=True)
        assert response.status_code == 200
        assert b'Operator SF is not in database or database not initialized.' in response.data
        assert b'<a href="/operator/SF">San Francisco Municipal Transportation Agency</a>' in response.data



""" Check valid commands"""
@responses.activate
@mock.patch.dict(os.environ, {'API_KEY': test_key})
def test_valid_operator(client, app):
    with open("test_input_jsons/operators.json", 'r') as f:
        operators_json = json.load(f)
    with open("test_input_jsons/lines.json", 'r') as f:
        lines_json = json.load(f)
    responses.add(
        responses.GET,
        "https://api.511.org/Transit/Operators?api_key=fake-key&Format=json",
        body=json.dumps(operators_json),
        status=200,
        content_type="application/json",
    )
    responses.add(
        responses.GET,
        "https://api.511.org/Transit/lines?api_key=fake-key&Format=json&Operator_id=SF",
        body=json.dumps(lines_json),
        status=200,
        content_type="application/json",
    )

    with app.app_context():
        response = client.get('/operators', follow_redirects=True)
        assert b'Please select an operator from the list below.' in response.data
        response = client.get('/operator/abc', follow_redirects=True)
        assert response.status_code == 200
        assert b'Operator abc is not in database or database not initialized.' in response.data
        response = client.get('/operator/SF', follow_redirects=True)
        assert response.status_code == 200
        assert b'VAN NESS-MISSION' in response.data
