from ag3tools import invoke_tool

techs = [
    "langgraph", "fastapi", "numpy", "pandas", "react", "django"
]

for t in techs:
    base = invoke_tool("find_docs", technology=t)
    val = invoke_tool("find_docs_validated", technology=t)
    reason = getattr(val, 'reason', None)
    print(f"{t}: base={base.url} -> validated={val.url} reason={reason}")
