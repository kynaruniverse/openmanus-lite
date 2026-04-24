"""Unit tests that don't require network access."""
from __future__ import annotations

import os
import tempfile

import pytest

from core.planner import PlanError, _parse_plan
from tools import file_tool, shell_tool


# ---- planner ----------------------------------------------------------------

def test_parse_plan_with_fences():
    raw = '```json\n{"thought":"x","steps":[{"action":"shell","command":"ls"}]}\n```'
    plan = _parse_plan(raw)
    assert plan.thought == "x"
    assert len(plan.steps) == 1
    assert plan.steps[0].action == "shell"
    assert plan.steps[0].params == {"command": "ls"}


def test_parse_plan_legacy_single_step():
    raw = '{"type":"write","file":"a.txt","content":"hi"}'
    plan = _parse_plan(raw)
    assert plan.steps[0].action == "write"
    assert plan.steps[0].params == {"file": "a.txt", "content": "hi"}


def test_parse_plan_rejects_garbage():
    with pytest.raises(PlanError):
        _parse_plan("not json at all")


def test_parse_plan_rejects_empty_steps():
    with pytest.raises(PlanError):
        _parse_plan('{"steps":[]}')


# ---- file tool --------------------------------------------------------------

def test_file_tool_round_trip(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("OMX_TARGET_PATH", tmp)
        out = file_tool.run({"action": "write", "file": "a.txt", "content": "hi"})
        assert out.startswith("SUCCESS")
        assert file_tool.run({"action": "read", "file": "a.txt"}) == "hi"


def test_file_tool_blocks_path_escape(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("OMX_TARGET_PATH", tmp)
        out = file_tool.run({"action": "read", "file": "../../etc/passwd"})
        assert "Security block" in out


# ---- shell tool -------------------------------------------------------------

def test_shell_tool_blocks_destructive():
    out = shell_tool.run({"action": "shell", "command": "rm -rf /"})
    assert out.startswith("BLOCKED")


def test_shell_tool_runs_simple_command(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("OMX_TARGET_PATH", tmp)
        out = shell_tool.run({"action": "shell", "command": "echo hello"})
        assert "hello" in out
