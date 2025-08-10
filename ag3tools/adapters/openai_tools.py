import json
from ag3tools.core.registry import list_tools, get_tool_spec


def openai_tool_specs_from_registry():
    """Get OpenAI tool specs for all registered tools."""
    specs = []
    for spec in list_tools():
        tags_line = f"\nTags: {', '.join(spec.tags)}" if spec.tags else ""
        specs.append({
            "type": "function",
            "function": {
                "name": spec.name,
                "description": f"{spec.description}{tags_line}",
                "parameters": spec.input_model.model_json_schema(),
            },
        })
    return specs


def run_openai_tool_call_from_registry(tool_call):
    """Run an OpenAI tool call using the registry."""
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments or "{}")
    spec = get_tool_spec(name)
    return spec.fn(spec.input_model(**args))


