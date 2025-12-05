from typing import Any
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


def real_llm(prompt: str, system: str | None = None) -> Any:
    """LLM 호출 래퍼.

    - LangChain ChatOpenAI를 사용해 gpt-5.1 모델을 호출한다.
    - system 프롬프트가 있으면 SystemMessage로 선행한다.
    """
    logging.info("Starting LLM step...")
    llm = ChatOpenAI(
        model="gpt-5.1",
        temperature=0.2,
    )

    messages = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))

    response = llm.invoke(messages)
    logging.info("LLM step completed")
    return response.content