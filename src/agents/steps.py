import json
from typing import Dict, Any, Tuple
from itertools import zip_longest

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
    system = (
        "You are a precise problem analyst. "
        f"Write all natural-language text in the language indicated by code '{cfg.target_language}' "
        "(for example: 'en' for English, 'ko' for Korean)."
    )
    state.requirement = _call_llm_json(tb, payload, system)
    return state


def step_algo(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    context = json.dumps(state.requirement, ensure_ascii=False)
    payload = f"{ALGO_ANALYSIS_PROMPT}\n\nRequirement JSON:\n{context}"
    system = (
        "You are an algorithm taxonomist. "
        f"Write all natural-language text in the language indicated by code '{cfg.target_language}'."
    )
    state.algo = _call_llm_json(tb, payload, system)
    return state


def step_statement(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    ctx = {
        "requirement": state.requirement,
        "algo": state.algo,
        "language": cfg.target_language,
    }
    payload = f"{PROBLEM_STATEMENT_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    system = (
        "You write clear ICPC-style statements. "
        f"Write the entire problem statement and all natural-language text in the language "
        f"indicated by code '{cfg.target_language}' (e.g., 'en', 'ko')."
    )
    state.statement = _call_llm_json(tb, payload, system)
    return state


def step_codegen(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    ctx = {
        "requirement": state.requirement,
        "algo": state.algo,
        "statement": state.statement,
        "cpp_std": cfg.cpp_std,
        "example_prog_lang": cfg.example_prog_lang,
    }
    payload = f"{CODEGEN_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    system = (
        "You output only the requested JSON. "
        "Prefer to generate the solution in the example programming language indicated in the context "
        f"(field 'example_prog_lang', currently '{cfg.example_prog_lang}'), "
        "while still following any explicit rules in the prompt."
    )
    state.code = _call_llm_json(tb, payload, system)
    # persist sources
    solve_code = state.code.get("solve_code", "")
    needs_judge = bool(state.code.get("needs_judge", False))
    # Resolve a stable problem id: prefer cfg.problem_id, then any id from previous steps,
    # and finally fall back to the string "pending".
    problem_id = (
        cfg.problem_id
        or state.requirement.get("id")
        or state.algo.get("id")
        or state.code.get("id")
        or "pending"
    )
    base_dir = f"problems/{problem_id}"
    solve_path = f"{base_dir}/solve.cpp"
    tb.ensure_dir(base_dir)
    tb.write_file(solve_path, solve_code)
    state.solve_source_path = solve_path
    if needs_judge:
        judge_code = state.code.get("judge_code", "")
        judge_path = f"{base_dir}/judge.py"
        tb.write_file(judge_path, judge_code)
        state.judge_source_path = judge_path
    return state


def step_casegen(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    ctx = {
        "constraints": state.statement.get("constraints", ""),
        "examples": state.statement.get("examples", []),
        "language": cfg.target_language,
    }
    payload = f"{CASEGEN_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    system = (
        "You create diverse and valid test cases. "
        "Any explanatory natural-language text must use the same language as the problem statement, "
        f"indicated by code '{cfg.target_language}'."
    )
    result = _call_llm_json(tb, payload, system)
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
    # Use the same stable problem id resolution as in other steps
    problem_id = (
        cfg.problem_id
        or state.requirement.get("id")
        or state.algo.get("id")
        or state.code.get("id")
        or "pending"
    )
    for i, p in enumerate(prompts):
        img_bytes = tb.generate_image(cfg.image_model, p)
        img_base = f"problems/{problem_id}/images"
        rel = f"{img_base}/img_{i + 1}.png"
        tb.ensure_dir(img_base)
        # 실제 파일 저장: write_bytes가 주입되어 있으면 바이너리로 저장한다.
        write_bytes = getattr(tb, "write_bytes", None)
        if callable(write_bytes):
            write_bytes(rel, img_bytes)
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
        "language": cfg.target_language,
    }
    payload = f"{REVIEW_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    system = (
        "You are a careful editor. "
        f"Write all issues and fix_suggestions in the language indicated by code '{cfg.target_language}'."
    )
    state.review = _call_llm_json(tb, payload, system)
    return state


def step_persist(state: AuthoringState, cfg: AuthoringConfig, tb: Toolbelt) -> AuthoringState:
    pid = (
        cfg.problem_id
        or state.requirement.get("id")
        or state.algo.get("id")
        or state.code.get("id")
        or "pending"
    )
    base = f"problems/{pid}"
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
        "language": cfg.target_language,
    }
    payload = f"{PERSIST_PROMPT}\n\nContext:\n{json.dumps(ctx, ensure_ascii=False)}"
    state.persist_plan = _call_llm_json(tb, payload, "Output only JSON.")
    # Write problem.md and per-case files
    tb.ensure_dir(f"{base}/cases")
    problem_md_path = f"{base}/problem.md"
    cases_dir = f"{base}/cases"
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
    # Cases content: split each grading case into its own {caseID}.in / {caseID}.out
    for idx, (inp, out) in enumerate(
        zip_longest(state.io.grading_inputs, state.io.grading_outputs or [], fillvalue=""),
        start=1,
    ):
        case_in_path = f"{cases_dir}/case_{idx}.in"
        case_out_path = f"{cases_dir}/case_{idx}.out"
        tb.write_file(case_in_path, inp)
        tb.write_file(case_out_path, out)
    return state
