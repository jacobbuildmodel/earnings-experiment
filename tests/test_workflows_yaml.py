"""Every GitHub Actions workflow must parse as YAML and carry an `on:` trigger and at least one job. An unparseable
workflow fails silently on GitHub (a 0-second 'push' failure, no dispatch) - caught twice on 2026-10-13."""
import glob
import os

import pytest
import yaml

FILES = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", ".github", "workflows", "*.yml")))


@pytest.mark.parametrize("path", FILES, ids=[os.path.basename(p) for p in FILES])
def test_workflow_parses(path):
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    assert isinstance(doc, dict) and doc.get("jobs")
    assert True in doc or "on" in doc          # YAML 1.1 reads the bare key `on` as True
