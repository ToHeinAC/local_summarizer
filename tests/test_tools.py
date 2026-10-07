from src import tools


def test_make_llm_disables_reasoning_and_caps_context():
    llm = tools.make_llm("qwen3.8-27b:latest", "http://127.0.0.1:1")
    assert llm.reasoning is False
    assert llm.num_ctx == tools.NUM_CTX
