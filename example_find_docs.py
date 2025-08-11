#!/usr/bin/env python3
"""
Example showing how to use ag3tools to find documentation.
Tests the main find_docs tool in different modes.

Usage:
    export OPENAI_API_KEY=...  # needed for cracked mode
    python example_find_docs.py
"""
from ag3tools import find_docs, FindDocsInput

# Test technologies
TECHS = [
    "langgraph",      # new framework
    "fastapi",        # popular framework
    "pydantic",       # popular library
    "langchain",      # complex docs structure
]

def main():
    print("Testing ag3tools find_docs...")
    print()
    
    # Test each tech
    for tech in TECHS:
        print(f"=== {tech} ===")
        
        # Fast mode (heuristic ranking)
        result = find_docs(FindDocsInput(
            technology=tech,
            mode="fast"
        ))
        print(f"Fast      -> {result.url}")
        
        # Validated mode (fetch + validate)
        result = find_docs(FindDocsInput(
            technology=tech,
            mode="validated"
        ))
        print(f"Validated -> {result.url}")
        
        # Cracked mode (LLM re-rank + validate)
        result = find_docs(FindDocsInput(
            technology=tech,
            mode="cracked",
            top_k=6
        ))
        print(f"Cracked   -> {result.url}")
        print()

if __name__ == "__main__":
    main()
