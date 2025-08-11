import os, json, tempfile, time, sys, types
import importlib
from ag3tools.core.registry import invoke_tool
from ag3tools.core import settings
from ag3tools.core import llm_instrumentation as inst


class DummyUsage:
    def __init__(self, p, c):
        self.prompt_tokens = p
        self.completion_tokens = c


class DummyResp:
    def __init__(self):
        self.usage = DummyUsage(100, 20)
        self.choices = [type('X', (object,), {'message': type('M', (object,), {'content': 'https://example.com'})()})()]


class Completions:
    def create(self, *args, **kwargs):
        return DummyResp()


def test_invoke_llm_logs_costs(monkeypatch, tmp_path):
    # Reset instrumentation
    inst._patched = False
    
    # Configure cost logging
    monkeypatch.setenv('AG3TOOLS_COST_LOG_ENABLED', 'true')
    log_file = tmp_path / 'cost.jsonl'
    log_file.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    monkeypatch.setenv('AG3TOOLS_COST_LOG_PATH', str(log_file))
    
    # Reload settings to pick up env vars
    importlib.reload(settings)

    # Setup fake OpenAI
    mods = {
        'openai': types.ModuleType('openai'),
        'openai.resources': types.ModuleType('openai.resources'),
        'openai.resources.chat': types.ModuleType('openai.resources.chat'),
        'openai.resources.chat.completions': types.ModuleType('openai.resources.chat.completions'),
    }
    for name, mod in mods.items():
        sys.modules[name] = mod
    
    # Create completions class and instance
    completions = Completions()
    sys.modules['openai.resources.chat.completions'].Completions = Completions
    
    # Create chat module with completions instance
    chat = type('Chat', (), {'completions': completions})()
    
    # Create client class that returns our chat instance
    class Client:
        def __init__(self):
            self.chat = chat
    sys.modules['openai'].Client = Client
    
    # Call an LLM tool
    from ag3tools.tools.docs.rank_docs_llm import RankDocsLLMInput
    from ag3tools.core.types import SearchResult
    inp = RankDocsLLMInput(
        technology='x',
        candidates=[SearchResult(title='', url='https://a', snippet='')],
        model='gpt-4o-mini'
    )
    
    # Run tool and verify output
    out = invoke_tool('rank_docs_llm', **inp.model_dump())
    assert out.url == 'https://example.com'
    
    # Verify cost log
    data = log_file.read_text().strip().splitlines()
    assert len(data) >= 1
    rec = json.loads(data[-1])
    assert rec['tool'] == 'rank_docs_llm'
    assert rec['input_tokens'] == 100
    assert rec['output_tokens'] == 20
