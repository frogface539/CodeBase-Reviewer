from ai_coding_agent.llm import GroqSettings, OpenAiChatLlm


def test_llm_formats_groq_1010_error() -> None:
    llm = OpenAiChatLlm(GroqSettings(api_key="test-key"))

    message = llm._format_error("error code: 1010")

    assert "Groq rejected the request with code 1010" in message
    assert "GROQ_BASE_URL" in message
