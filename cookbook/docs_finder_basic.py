from ag3tools import invoke_tool

techs = [
    "langgraph", "fastapi", "numpy", "pandas", "react", "django"
]

for t in techs:
    out = invoke_tool("find_docs", technology=t)
    print(f"{t}: {out.url}")
