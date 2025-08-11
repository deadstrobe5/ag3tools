#!/usr/bin/env python3
"""
Example: use ag3tools to find documentation across modes.

Usage:
  export OPENAI_API_KEY=...  # needed for cracked mode
  python cookbook/example_find_docs.py
"""
from ag3tools.core.registry import invoke_tool

TECHS = [
    "langgraph",
    "fastapi",
    "pydantic",
    "langchain",
]

LLM_MODEL = "gpt-4o-mini"


def main():
    print("Testing ag3tools find_docs...")
    for tech in TECHS:
        print(f"=== {tech} ===")
        # fast
        out = invoke_tool("find_docs", technology=tech, mode="fast")
        print(f"Fast      -> {out.url}")
        # validated
        out = invoke_tool("find_docs", technology=tech, mode="validated", llm_model=LLM_MODEL)
        print(f"Validated -> {out.url}")
        # cracked
        out = invoke_tool("find_docs", technology=tech, mode="cracked", top_k=6, llm_model=LLM_MODEL)
        print(f"Cracked   -> {out.url}")

if __name__ == "__main__":
    main()
