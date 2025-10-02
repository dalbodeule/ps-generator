import json
from typing import Dict, Any, Tuple

from .prompts import (
    REQUIREMENT_ANALYSIS_PROMPT,
    ALGO_ANALYSIS_PROMPT,
    PROBLEM_STATEMENT_PROMPT,
    CODEGEN_PROMPT,
    CASEGEN_PROMPT,
    BUILD_PROMPT,
    OUTPUT_ANALYSIS_PROMPT,
    IMAGE_GEN_PROMPT,
    REVIEW_PROMPT,
    PERSIST_PROMPT,
)
from .state import AuthoringState, AuthoringConfig, ProblemIOBundle
from .tools import Toolbelt


def _call_llm_json(toolbelt: Toolbelt, prompt: str, system: str | None = None) -> Dict[str, Any]:
    raw = toolbelt.llm_chat(prompt, system)
    if isinstance(raw, str):
        txt = raw
    else:
        txt = json.dumps(raw)
    # try parse json from response
    try:
        return json.loads(txt)
    except Exception:
        # fallback: attempt to extract JSON block
        start = txt.find("{")
        end = txt.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(txt[start : end + 1])
        raise


def step_requirement(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    payload = f"{REQUIREMENT_ANALYSIS_PROMPT}\n\nUser seed:\n{state.user_seed}"
    state.requirement = _call_llm_json(tb, payload, "You are a precise problem analyst.")
    return state


def step_algo(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    context = json.dumps(state.requirement, ensure_ascii=False)
    payload = f"{ALGO_ANALYSIS_PROMPT}\n\nRequirement JSON:\n{context}"
    state.algo = _call_llm_json(tb, payload, "You are an algorithm taxonomist.")
    return state


def step_statement(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    ctx = {
        "requirement": state.requirement,
        "algo": state.algo,
    }
    payload = f"{PROBLEM_STATEMENT_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    state.statement = _call_llm_json(tb, payload, "You write clear ICPC-style statements.")
    return state


def step_codegen(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    ctx = {
        "requirement": state.requirement,
        "algo": state.algo,
        "statement": state.statement,
        "cpp_std": cfg.cpp_std,
    }
    payload = f"{CODEGEN_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    state.code = _call_llm_json(tb, payload, "You output only the requested JSON.")
    # persist sources
    solve_code = state.code.get("solve_code", "")
    needs_judge = bool(state.code.get("needs_judge", False))
    problem_id = state.requirement.get("id") or 0
    solve_path = f"/problem/{problem_id or 'pending'}/solve.cpp"
    tb.ensure_dir(f"/problem/{problem_id or 'pending'}")
    tb.write_file(solve_path, solve_code)
    state.solve_source_path = solve_path
    if needs_judge:
        judge_code = state.code.get("judge_code", "")
        judge_path = f"/problem/{problem_id or 'pending'}/judge.py"
        tb.write_file(judge_path, judge_code)
        state.judge_source_path = judge_path
    return state


def step_casegen(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    ctx = {
        "constraints": state.statement.get("constraints", ""),
        "examples": state.statement.get("examples", []),
    }
    payload = f"{CASEGEN_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    result = _call_llm_json(tb, payload, "You create diverse and valid test cases.")
    state.io = ProblemIOBundle(
        example_inputs=result.get("example_inputs", []),
        grading_inputs=result.get("grading_inputs", []),
        example_outputs=result.get("example_outputs", []),
        grading_outputs=result.get("grading_outputs", []),
    )
    return state


def step_build(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    ctx = {
        "solve_path": state.solve_source_path,
        "cpp_std": cfg.cpp_std,
    }
    payload = f"{BUILD_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    state.build = _call_llm_json(tb, payload, "Return only commands and artifacts JSON.")
    # Run compile with provided tool (delegated to /src/tools)
    commands = state.build.get("compile_commands", [])
    if commands:
        tb.run_shell(commands)
    artifacts = state.build.get("artifacts", [])
    if artifacts:
        state.binary_path = artifacts[0]
    return state


def step_output_analysis(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    ctx = {
        "inputs": state.io.grading_inputs,
        "binary": state.binary_path,
    }
    payload = f"{OUTPUT_ANALYSIS_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    state.output_analysis = _call_llm_json(tb, payload, "You are a strict judge.")
    return state


def step_image(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    ctx = {
        "requirement": state.requirement,
        "statement": state.statement,
    }
    payload = f"{IMAGE_GEN_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    prompts = _call_llm_json(tb, payload, "Return JSON only.").get("prompts", [])
    images: list[Tuple[str, int]] = []
    for i, p in enumerate(prompts):
        img_bytes = tb.generate_image(cfg.image_model, p)
        rel = f"/problem/{state.requirement.get('id') or 'pending'}/images/img_{i + 1}.png"
        tb.ensure_dir(f"/problem/{state.requirement.get('id') or 'pending'}/images")
        # naive write via write_file expecting str; we base64 bypass not allowed, so assume caller writes bytes
        # Provide alternate path: inject write_file that handles bytes or implement separate writer upstream.
        # Here we just record intended path.
        images.append((rel, len(img_bytes)))
    state.images = {"count": len(images), "paths": [p for p, _ in images]}
    return state


def step_review(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    ctx = {
        "requirement": state.requirement,
        "statement": state.statement,
        "cases": {
            "examples": state.io.example_inputs,
            "grading": state.io.grading_inputs,
        },
        "labels": {
            "interactive": state.requirement.get("is_interactive", False),
            "special_judge": state.requirement.get("has_special_judge", False),
        },
    }
    payload = f"{REVIEW_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    state.review = _call_llm_json(tb, payload, "You are a careful editor.")
    return state


def step_persist(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    pid = state.requirement.get("id") or state.algo.get("id") or state.code.get("id") or 0
    base = f"/tmp/problem/{pid or 'pending'}"
    ctx = {
        "problem_id": pid,
        "base_dir": base,
        "statement": state.statement,
        "io": {
            "example_inputs": state.io.example_inputs,
            "grading_inputs": state.io.grading_inputs,
            "example_outputs": state.io.example_outputs,
            "grading_outputs": state.io.grading_outputs,
        },
    }
    payload = f"{PERSIST_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    state.persist_plan = _call_llm_json(tb, payload, "Output only JSON.")
    # Write problem.md and cases skeleton
    tb.ensure_dir(f"{base}/cases")
    problem_md_path = f"{base}/problem.md"
    cases_in_path = f"{base}/cases/[caseID].in"
    cases_out_path = f"{base}/cases/[caseID].out"
    # Render markdown
    st = state.statement
    examples = st.get("examples", [])
    md = [
        f"# Problem {pid}",
        "",
        f"## Abstract\n{st.get('abstract','')}",
        "",
        f"## Statement\n{st.get('body','')}",
        "",
        f"## Input\n{st.get('input_spec','')}",
        "",
        f"## Output\n{st.get('output_spec','')}",
        "",
        f"## Constraints\n{st.get('constraints','')}",
        "",
        "## Examples",
    ]
    for i, ex in enumerate(examples, 1):
        md.append(f"### Example {i}")
        md.append("Input:")
        md.append("```")
        md.append(ex.get("input", "").strip())
        md.append("```")
        md.append("Output:")
        md.append("```")
        md.append(ex.get("output", "").strip())
        md.append("```")
        if ex.get("explanation"):
            md.append("Explanation:")
            md.append(ex["explanation"])
        md.append("")
    if state.images.get("paths"):
        md.append("## Illustrations")
        for p in state.images["paths"]:
            md.append(f"![figure]({p})")
    tb.write_file(problem_md_path, "\n".join(md))
    # Cases content (aggregate grading inputs; outputs may be filled later by judge/runner)
    tb.write_file(cases_in_path, "\n\n".join(state.io.grading_inputs))
    tb.write_file(cases_out_path, "\n\n".join(state.io.grading_outputs or []))
    return state
