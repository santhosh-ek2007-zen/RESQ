"""
app/routes.py — Flask Blueprint with all page routes and API endpoints.

Multi-Page Layout:
- GET /            -> City Network & Road Management
- GET /network     -> City Network & Road Management
- GET /search      -> Dedicated Route Finder (Single-Goal Search)
- GET /optimize    -> Dedicated Tour Optimizer (Multi-Stop Rescue TSP)
- GET /compare     -> Algorithm Comparison Matrix & Interactive Graph
- GET /benchmark   -> Performance Benchmarks & Chart.js Visualizations

API Endpoints:
- GET  /api/city
- POST /api/roads/block
- POST /api/roads/reopen
- POST /api/roads/reset
- POST /api/search
- POST /api/optimise
- POST /api/benchmark
- GET  /api/results.csv
- GET  /api/algorithms
"""
from __future__ import annotations
import os
import io
import traceback
from flask import Blueprint, render_template, request, jsonify, Response, send_file

from app import services
from app.validation import require_json

bp = Blueprint("main", __name__)


# ------------------------------------------------------------------ #
# Multi-Page Navigation Views
# ------------------------------------------------------------------ #

@bp.route("/")
@bp.route("/network")
def page_network():
    return render_template("network.html", active_page="network")


@bp.route("/search")
def page_search():
    return render_template("search.html", active_page="search")


@bp.route("/optimize")
def page_optimize():
    return render_template("optimize.html", active_page="optimize")


@bp.route("/compare")
def page_compare():
    return render_template("compare.html", active_page="compare")


@bp.route("/benchmark")
def page_benchmark():
    return render_template("benchmark.html", active_page="benchmark")


# ------------------------------------------------------------------ #
# City graph API
# ------------------------------------------------------------------ #

@bp.route("/api/city", methods=["GET"])
def api_city():
    return jsonify(services.get_city_dict())


@bp.route("/api/roads/block", methods=["POST"])
def api_block():
    data, err = require_json(request)
    if err:
        return jsonify({"status": "invalid_input", "message": err}), 400

    source = data.get("source", "").strip()
    target = data.get("target", "").strip()
    if not source or not target:
        return jsonify({"status": "invalid_input", "message": "Fields 'source' and 'target' are required."}), 400

    try:
        city_dict = services.block_road(source, target)
        return jsonify(city_dict)
    except ValueError as e:
        return jsonify({"status": "invalid_input", "message": str(e)}), 400


@bp.route("/api/roads/reopen", methods=["POST"])
def api_reopen():
    data, err = require_json(request)
    if err:
        return jsonify({"status": "invalid_input", "message": err}), 400

    source = data.get("source", "").strip()
    target = data.get("target", "").strip()
    if not source or not target:
        return jsonify({"status": "invalid_input", "message": "Fields 'source' and 'target' are required."}), 400

    try:
        city_dict = services.reopen_road(source, target)
        return jsonify(city_dict)
    except ValueError as e:
        return jsonify({"status": "invalid_input", "message": str(e)}), 400


@bp.route("/api/roads/reset", methods=["POST"])
def api_reset():
    city_dict = services.reset_city()
    return jsonify(city_dict)


# ------------------------------------------------------------------ #
# Search API
# ------------------------------------------------------------------ #

@bp.route("/api/search", methods=["POST"])
def api_search():
    data, err = require_json(request)
    if err:
        return jsonify({"status": "invalid_input", "message": err}), 400

    result, status_code = services.run_search(data)
    return jsonify(result), status_code


# ------------------------------------------------------------------ #
# Optimization API
# ------------------------------------------------------------------ #

@bp.route("/api/optimise", methods=["POST"])
def api_optimise():
    data, err = require_json(request)
    if err:
        return jsonify({"status": "invalid_input", "message": err}), 400

    result, status_code = services.run_optimise(data)
    return jsonify(result), status_code


# ------------------------------------------------------------------ #
# Benchmark API
# ------------------------------------------------------------------ #

@bp.route("/api/benchmark", methods=["POST"])
def api_benchmark():
    data, err = require_json(request)
    if err:
        return jsonify({"status": "invalid_input", "message": err}), 400

    result, status_code = services.run_benchmark(data)
    return jsonify(result), status_code


@bp.route("/api/results.csv", methods=["GET"])
def api_results_csv():
    csv_str, err = services.get_results_csv()
    if err:
        return jsonify({"status": "not_found", "message": err}), 404

    # Also write a copy to experiments/results/
    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "experiments", "results")
    os.makedirs(results_dir, exist_ok=True)
    csv_path = os.path.join(results_dir, "benchmark_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        f.write(csv_str)

    return Response(
        csv_str,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=benchmark_results.csv"},
    )


# ------------------------------------------------------------------ #
# Algorithm metadata (for frontend dropdowns)
# ------------------------------------------------------------------ #

@bp.route("/api/algorithms", methods=["GET"])
def api_algorithms():
    return jsonify({
        "search": services.SEARCH_LABELS,
        "optimise": services.OPT_LABELS,
    })
