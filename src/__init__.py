"""
AI Agents package initializer.

This package provides LangChain/LangGraph-based agents for a multi-step
problem authoring workflow:
1) Requirement analysis
2) Algorithm type analysis
3) Problem statement construction
4) Code generation (solve + judge)
5) Input case generation
6) Build with gcc tool
7) Output case analysis
8) Image generation using OpenAI nano-banana
9) Problem review
10) Persist to /problem/{id}

Note: Actual LLM/tool clients must be injected; this package defines prompts,
state, and graph wiring only.
"""

from pathlib import Path

# Public exports
__all__ = [
    "ensure_dirs",
]

ROOT_DIR = Path(__file__).resolve().parent.parent
PROBLEM_ROOT = ROOT_DIR / "problem"
TOOLS_ROOT = ROOT_DIR / "src" / "tools"
AGENTS_ROOT = ROOT_DIR / "src" / "agents"


def ensure_dirs() -> None:
    """
    Ensure base directories exist for problem outputs and tools.
    """
    PROBLEM_ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "src" / "agents").mkdir(parents=True, exist_ok=True)
    TOOLS_ROOT.mkdir(parents=True, exist_ok=True)
