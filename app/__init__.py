"""
app/__init__.py — Flask application factory.
"""
from __future__ import annotations
import traceback
from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Register blueprint
    from app.routes import bp
    app.register_blueprint(bp)

    # Global error handler — never expose stack traces to the client
    @app.errorhandler(Exception)
    def handle_exception(e):
        traceback.print_exc()  # developer log in terminal only
        return jsonify({"status": "error", "message": "Unexpected server error."}), 500

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"status": "not_found", "message": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"status": "error", "message": "Method not allowed."}), 405

    return app

