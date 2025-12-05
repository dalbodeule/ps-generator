from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProblemIOBundle:
    example_inputs: List[str] = field(default_factory=list)
    grading_inputs: List[str] = field(default_factory=list)
    example_outputs: List[str] = field(default_factory=list)
    grading_outputs: List[str] = field(default_factory=list)


@dataclass
class AuthoringConfig:
    model_name: str = "gpt-5"
    temperature: float = 0.2
    problem_id: Optional[int] = None  # auto-increment upstream
    gcc_tool_path: str = "/src/tools/gcc_build.sh"  # to be created by tools
    # Default image model for generation (OpenAI Nano Banana Pro)
    image_model: str = "openai-nano-banana-pro"
    cpp_std: str = "c++17"
    # Language for problem statement and natural-language text ("en", "ko", ...)
    target_language: str = "en"
    # Preferred example programming language for solutions (e.g., "C++/17", "Python 3.12")
    example_prog_lang: str = "C++/17"


@dataclass
class AuthoringState:
    # Inputs
    user_seed: str = ""
    # Results per step
    requirement: Dict[str, Any] = field(default_factory=dict)
    algo: Dict[str, Any] = field(default_factory=dict)
    statement: Dict[str, Any] = field(default_factory=dict)
    code: Dict[str, Any] = field(default_factory=dict)
    io: ProblemIOBundle = field(default_factory=ProblemIOBundle)
    build: Dict[str, Any] = field(default_factory=dict)
    output_analysis: Dict[str, Any] = field(default_factory=dict)
    images: Dict[str, Any] = field(default_factory=dict)
    review: Dict[str, Any] = field(default_factory=dict)
    persist_plan: Dict[str, Any] = field(default_factory=dict)

    # Artifacts resolved during run
    solve_source_path: Optional[str] = None
    judge_source_path: Optional[str] = None
    binary_path: Optional[str] = None
