"""
tests/test_pages.py — Verify all multi-page HTML views and endpoints return HTTP 200.
"""
from app import create_app
import pytest

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_page_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"City Network" in r.data
    assert b"cy" in r.data

def test_page_network(client):
    r = client.get("/network")
    assert r.status_code == 200
    assert b"Disaster Network Status" in r.data

def test_page_search(client):
    r = client.get("/search")
    assert r.status_code == 200
    assert b"Route Planning" in r.data

def test_page_optimize(client):
    r = client.get("/optimize")
    assert r.status_code == 200
    assert b"Multi-Stop Tour Planner" in r.data

def test_page_compare(client):
    r = client.get("/compare")
    assert r.status_code == 200
    assert b"Compare Algorithms Side-by-Side" in r.data

def test_page_benchmark(client):
    r = client.get("/benchmark")
    assert r.status_code == 200
    assert b"Rigorous Algorithm Benchmarking" in r.data

