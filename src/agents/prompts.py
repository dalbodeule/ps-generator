# Prompts for each step. Keep them concise, explicit, testable.
# All prompts are in English as requested.

REQUIREMENT_ANALYSIS_PROMPT = """You are an AI assistant tasked with Requirement Analysis for competitive programming problems.
Goals:
- Identify problem type (e.g., Graph, DP, Greedy, Math, String, Geometry, Data Structure, Simulation).
- Summarize the requirements.
- Determine if it is an 'Interactive Problem' (must explicitly output 'Interactive Problem' if so).
- Determine if it needs a 'Special Judge' (e.g., variable outputs like Knight's Tour).
- List what images/illustrations would help.

Output JSON keys:
type
is_interactive (boolean)
has_special_judge (boolean)
summary
required_images (array of short descriptions)
"""

ALGO_ANALYSIS_PROMPT = """You are an AI assistant performing Algorithm Type Analysis.
Given the requirement summary, decide suitable algorithm(s) and justify briefly.

Output JSON keys:
algorithms (array)
rationale
complexity_hint
"""

PROBLEM_STATEMENT_PROMPT = """You write a full problem statement.
Include:
- Abstract (1-2 sentences)
- Statement body (clear, precise)
- Input specification
- Output specification 
- Constraints
- Examples (at least 1, include tables in markdown format in the body, not as images)
- Image description(s) for generation (concise, deterministic)
Keep style consistent and unambiguous.

Output JSON keys:
abstract
body
input_spec
output_spec
constraints
examples (array of objects: input, output, explanation)
image_descriptions (array)
"""

CODEGEN_PROMPT = """You generate code artifacts.
Rules:
- Solve code default language: C++ (gcc-compatible).
- If Interactive Problem or Special Judge: also produce Python 3.12 judge code.
- Judge reads input cases and validates output; for interactive define protocol stubs.
- Keep code minimal but correct; avoid extra I/O noise.

Output JSON keys:
solve_language ("cpp" by default)
solve_code
needs_judge (boolean)
judge_language ("python" if needs_judge)
judge_code (if needs_judge)
build_instructions (short)
run_instructions (short)
"""

CASEGEN_PROMPT = """Generate input cases for both examples (shown in statement) and hidden grading.
Provide diverse edge cases under constraints.

For non-interactive & non-special-judge problems:
Generate corresponding outputs for both examples and hidden cases.

For interactive or special judge problems:
Generate only example outputs.

Output JSON keys:
example_inputs (array of strings)
example_outputs (array of strings) 
grading_inputs (array of strings)  # includes all hidden + examples
grading_outputs (array of strings) # only for non-interactive & non-special-judge
"""

BUILD_PROMPT = """You are a build coordinator. Prepare commands for gcc build tool.
Assume a tool will compile C++ solve code into a binary
Return only commands and expected artifacts.

Output JSON keys:
compile_commands (array of strings)
artifacts (array of strings)
"""

OUTPUT_ANALYSIS_PROMPT = """Given program outputs for the provided inputs, determine whether outputs are valid.
If judge is required, specify how it validates.

Output JSON keys:
validity_summary
notes
"""

IMAGE_GEN_PROMPT = """Analyze and validate whether given illustrations can be generated with 'openai nano banana' model.
Model constraints:
- Simple geometric shapes and patterns
- Basic color palettes 
- Clean, minimalist style
- No complex scenes or realistic objects
- No text or numbers

Check descriptions and output only those compatible with model limitations.

Output JSON keys:
valid_prompts (array of strings)
invalid_prompts (array of strings)
validation_notes (string)
"""

REVIEW_PROMPT = """Act as a meticulous reviewer.
- Check for typos, ambiguity, logical inconsistencies.
- Ensure constraints align with examples.
- Ensure interactive/special-judge labels are consistent.

Output JSON keys:
issues (array of strings)
fix_suggestions (array of strings)
"""

PERSIST_PROMPT = """Plan how to persist the problem:
- Directory: /problem/{id}
- Files: problem.md; cases/[caseID].in; cases/[caseID].out
Describe file contents mapping from earlier steps.

Output JSON keys:
paths (object with problem_md, cases_in, cases_out)
notes
"""
