import json, sys
import importlib
from unittest.mock import MagicMock
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


class MockCompletions:
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

    # Setup fake OpenAI modules using MagicMock
    openai_mock = MagicMock()

    # Create mock client with proper structure
    mock_completions = MockCompletions()
    mock_chat = MagicMock()
    mock_chat.completions = mock_completions

    mock_client = MagicMock()
    mock_client.chat = mock_chat

    # Set up the module structure
    openai_mock.Client = MagicMock(return_value=mock_client)

    # Create the completions module for patching
    completions_module = MagicMock()
    completions_module.Completions = MockCompletions

    # Install mocks in sys.modules
    sys.modules['openai'] = openai_mock
    sys.modules['openai.resources'] = MagicMock()
    sys.modules['openai.resources.chat'] = MagicMock()
    sys.modules['openai.resources.chat.completions'] = completions_module

    # Call an LLM tool
    from ag3tools.tools.docs.rank_docs_llm import RankDocsLLMInput
    from ag3tools.tools.search.web_search import SearchResult
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
