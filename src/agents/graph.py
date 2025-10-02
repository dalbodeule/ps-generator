from typing import Callable, Any

# This file wires steps into a sequential pipeline.
# It is compatible with LangGraph style by exposing a simple run() that
# callers can adapt into LangGraph nodes/edges.

from .state import AuthoringState, AuthoringConfig
from .tools import Toolbelt
from .steps import (
    step_requirement,
    step_algo,
    step_statement,
    step_codegen,
    step_casegen,
    step_build,
    step_output_analysis,
    step_image,
    step_review,
    step_persist,
)


def build_authoring_graph() -> Callable[[AuthoringState, AuthoringConfig, Toolbelt], AuthoringState]:
    def run(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
        state = step_requirement(state, cfg, tb)
        state = step_algo(state, cfg, tb)
        state = step_statement(state, cfg, tb)
        state = step_codegen(state, cfg, tb)
        state = step_casegen(state, cfg, tb)
        state = step_build(state, cfg, tb)
        state = step_output_analysis(state, cfg, tb)
        state = step_image(state, cfg, tb)
        state = step_review(state, cfg, tb)
        state = step_persist(state, cfg, tb)
        return state

    return run
