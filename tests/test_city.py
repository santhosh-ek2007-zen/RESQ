"""
tests/test_city.py — Unit tests for CityGraph and build_sample_city.
"""
import math
import pytest
from models.city import build_sample_city, CityGraph


@pytest.fixture
def city():
    return build_sample_city()


def test_sample_city_node_count(city):
    assert len(list(city._g.nodes())) == 11


def test_sample_city_edge_count(city):
    assert len(list(city._g.edges())) == 20


def test_block_road_marks_blocked(city):
    city.block_road("E", "H")
    d = city.to_dict()
    edge = next(e for e in d["edges"] if e["id"] == "E-H")
    assert edge["blocked"] is True


def test_block_removes_from_neighbors(city):
    city.block_road("E", "H")
    nbrs = dict(city.neighbors("E"))
    assert "H" not in nbrs


def test_block_symmetric(city):
    """block(H,E) is the same as block(E,H)."""
    city.block_road("H", "E")
    assert city.is_blocked("E", "H")
    assert city.is_blocked("H", "E")


def test_block_nonexistent_raises(city):
    with pytest.raises(ValueError):
        city.block_road("A", "Z")


def test_route_cost_basic(city):
    cost = city.route_cost(["A", "C", "E"])
    assert cost == pytest.approx(9.0)  # A-C:4 + C-E:5


def test_route_cost_blocked_raises(city):
    city.block_road("C", "E")
    with pytest.raises(ValueError):
        city.route_cost(["A", "C", "E"])


def test_version_increments_on_change(city):
    v0 = city.version
    city.block_road("A", "B")
    assert city.version == v0 + 1


def test_version_no_change_on_noop(city):
    city.block_road("A", "B")
    v1 = city.version
    city.block_road("A", "B")  # already blocked — idempotent
    assert city.version == v1


def test_reopen_road(city):
    city.block_road("A", "B")
    city.reopen_road("A", "B")
    assert not city.is_blocked("A", "B")
    nbrs = dict(city.neighbors("A"))
    assert "B" in nbrs


def test_reset_clears_all_blocks(city):
    city.block_road("A", "B")
    city.block_road("C", "E")
    city.reset()
    assert not city.is_blocked("A", "B")
    assert not city.is_blocked("C", "E")


def test_to_dict_edge_id_convention(city):
    """Edge IDs must be alphabetically sorted (A-B not B-A)."""
    d = city.to_dict()
    for edge in d["edges"]:
        u, v = edge["id"].split("-")
        assert u <= v, f"Edge id not sorted: {edge['id']}"


def test_single_node_route_cost(city):
    assert city.route_cost(["A"]) == 0.0

