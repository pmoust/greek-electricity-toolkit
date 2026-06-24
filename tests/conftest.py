"""Shared test fixtures. Puts the skill's engine on the import path and loads
the synthetic example data (the only data in the repo — no real customer data)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT, ".claude", "skills", "greek-electricity-bill-analysis")
EXAMPLES = os.path.join(ROOT, "examples")
sys.path.insert(0, SKILL_DIR)

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture(scope="session")
def example_bills():
    return json.load(open(os.path.join(EXAMPLES, "example_bills.json")))


@pytest.fixture(scope="session")
def example_offers():
    return json.load(open(os.path.join(EXAMPLES, "example_offers.json")))
