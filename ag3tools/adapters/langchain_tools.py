from typing import List
from langchain.tools import StructuredTool
from ag3tools.core.registry import list_tools


def langchain_tools_from_registry() -> List[StructuredTool]:
    """Get LangChain tools for all registered tools."""
    tools = []
    for spec in list_tools():
        def _run(**kwargs):
            return spec.fn(spec.input_model(**kwargs))
        
        tool = StructuredTool.from_function(
            name=spec.name,
            description=spec.description,
            func=_run,
            args_schema=spec.input_model,
            return_direct=False,
        )
        tools.append(tool)
    return tools


