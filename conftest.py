"""
conftest.py — pytest configuration: adds the project root to sys.path
so all modules (app, models, search, optimization, experiments) are importable.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

