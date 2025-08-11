import types, sys
from ag3tools.core import llm_instrumentation as inst
from ag3tools.core.llm_instrumentation import ensure_openai_patched, start_capture, stop_capture


class DummyUsage:
    def __init__(self, p, c):
        self.prompt_tokens = p
        self.completion_tokens = c


class DummyResp:
    def __init__(self, usage):
        self.usage = usage
        self.choices = [type('X', (object,), {'message': type('M', (object,), {'content': 'ok'})()})()]


class Completions:
    def create(self, *args, **kwargs):
        return DummyResp(DummyUsage(123, 45))


def test_llm_instrumentation_aggregates_tokens(monkeypatch):
    # Reset patch state
    inst._patched = False
    
    # Setup fake OpenAI modules
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
    
    # Run test
    ensure_openai_patched()
    start_capture()
    
    # Make two calls that should each return 123 prompt + 45 completion tokens
    client = Client()
    client.chat.completions.create(model='gpt-4o-mini')
    client.chat.completions.create(model='gpt-4o-mini')
    
    # Check aggregated tokens
    agg = stop_capture()
    assert agg.get('gpt-4o-mini') == (246, 90)  # 2 * (123, 45)
