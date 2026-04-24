"""Integration tests for the ReAct loop using a stub LLM.

No network access. The fake LLM returns canned JSON responses in order so we
can exercise plan parsing, tool dispatch, error recovery, and the budget
mechanism end-to-end.
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import List

import pytest

from core import plugins
from core.executor import Executor
from core.llm import BudgetExceeded, LLMError
from core.react import ReActLoop


class FakeLLM:
    """Stand-in for ``LLMClient`` that yields a scripted list of responses.

    Tracks ``call_count`` so budget assertions work the same as the real client.
    """

    def __init__(self, responses: List[str], max_calls: int = 0) -> None:
        self._responses = list(responses)
        self.call_count = 0
        self.max_calls = max_calls
        self.prompts: List[str] = []

    def reset_budget(self) -> None:
        self.call_count = 0

    def generate(self, prompt: str) -> str:
        if self.max_calls and self.call_count >= self.max_calls:
            raise BudgetExceeded(
                f"LLM budget exhausted: {self.call_count}/{self.max_calls}"
            )
        if not self._responses:
            raise LLMError("FakeLLM: ran out of scripted responses.")
        self.prompts.append(prompt)
        self.call_count += 1
        return self._responses.pop(0)


@pytest.fixture
def loaded_tools(monkeypatch):
    plugins.TOOLS.clear()
    plugins.load()
    tmp = tempfile.mkdtemp()
    monkeypatch.setenv("OMX_TARGET_PATH", tmp)
    yield plugins.TOOLS, tmp


def _react(llm: FakeLLM, tools, max_steps: int = 5) -> ReActLoop:
    return ReActLoop(llm=llm, executor=Executor(tools, max_steps=max_steps),
                     max_steps=max_steps)


# ---------------------------------------------------------------------------

def test_react_finishes_on_first_step(loaded_tools):
    tools, _ = loaded_tools
    llm = FakeLLM([
        json.dumps({
            "thought": "I can answer directly.",
            "action": "finish",
            "text": "42 is the answer.",
        }),
    ])
    result = _react(llm, tools).run("what is the answer?")
    assert result.ok is True
    assert result.finished is True
    assert "42" in result.answer
    assert llm.call_count == 1


def test_react_runs_shell_then_finishes(loaded_tools):
    tools, _ = loaded_tools
    llm = FakeLLM([
        json.dumps({
            "thought": "List files first.",
            "action": "shell",
            "command": "echo hello",
        }),
        json.dumps({
            "thought": "Done.",
            "action": "finish",
            "text": "Saw 'hello' in the output.",
        }),
    ])
    result = _react(llm, tools).run("inspect")
    assert result.ok is True and result.finished is True
    assert len(result.trace) == 1
    assert result.trace[0].step.action == "shell"
    assert "hello" in result.trace[0].observation
    # Second prompt must include the prior observation.
    assert "hello" in llm.prompts[1]


def test_react_recovers_from_bad_json(loaded_tools):
    tools, _ = loaded_tools
    llm = FakeLLM([
        "this is not json at all",
        json.dumps({
            "thought": "Retry.",
            "action": "finish",
            "text": "ok",
        }),
    ])
    result = _react(llm, tools).run("noop")
    assert result.ok is True and result.finished is True
    # The failed attempt should appear in the trace as feedback to the model.
    assert any("not valid JSON" in t.observation for t in result.trace)


def test_react_writes_then_reads_a_file(loaded_tools):
    tools, target = loaded_tools
    llm = FakeLLM([
        json.dumps({
            "thought": "Write a file.",
            "action": "file_write",
            "file": "note.txt",
            "content": "hi from omx",
        }),
        json.dumps({
            "thought": "Read it back.",
            "action": "file_read",
            "file": "note.txt",
        }),
        json.dumps({
            "thought": "Confirm.",
            "action": "finish",
            "text": "Wrote and read 'hi from omx'.",
        }),
    ])
    result = _react(llm, tools).run("file round trip")
    assert result.ok is True and result.finished is True
    assert os.path.exists(os.path.join(target, "note.txt"))
    assert "hi from omx" in result.trace[1].observation


def test_react_stops_when_budget_exhausted(loaded_tools):
    tools, _ = loaded_tools
    # Will keep planning shell calls forever, but the budget cuts it off.
    llm = FakeLLM(
        responses=[json.dumps({
            "thought": "loop",
            "action": "shell",
            "command": "echo x",
        })] * 10,
        max_calls=2,
    )
    result = _react(llm, tools, max_steps=10).run("infinite")
    assert result.ok is False
    assert "budget" in result.answer.lower()
    assert llm.call_count == 2


def test_react_stops_at_max_steps(loaded_tools):
    tools, _ = loaded_tools
    llm = FakeLLM(
        [json.dumps({
            "thought": "again",
            "action": "shell",
            "command": "echo x",
        })] * 5
    )
    result = _react(llm, tools, max_steps=3).run("loop")
    assert result.ok is False
    assert "budget reached" in result.answer.lower() or "step budget" in result.answer.lower()
    assert len(result.trace) == 3
