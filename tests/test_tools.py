from src import models, tools


def test_make_llm_disables_reasoning_and_uses_the_model_window():
    llm = tools.make_llm("qwen3.8-27b:latest", "http://127.0.0.1:1")
    assert llm.reasoning is False
    assert llm.num_ctx == models.num_ctx("qwen3.8-27b:latest")
    assert llm.num_predict == tools.NUM_PREDICT
