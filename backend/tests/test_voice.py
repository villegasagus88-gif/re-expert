"""TTS: el payload a OpenAI incluye instructions (acento/tono argentino) + speed
para gpt-4o-mini-tts, y omite instructions si el modelo es tts-1 (no lo soporta)."""
import pytest

import services.voice_service as vs


class _FakeResp:
    status_code = 200
    content = b"MP3DATA"
    text = ""


class _FakeClient:
    captured: dict = {}

    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, headers=None, json=None):
        _FakeClient.captured = json
        return _FakeResp()


@pytest.mark.asyncio
async def test_speak_incluye_instructions_y_speed_para_gpt4o(monkeypatch):
    monkeypatch.setattr(vs.settings, "OPENAI_TTS_MODEL", "gpt-4o-mini-tts", raising=False)
    monkeypatch.setattr(vs.settings, "OPENAI_TTS_VOICE", "coral", raising=False)
    monkeypatch.setattr(vs.settings, "OPENAI_TTS_INSTRUCTIONS", "hablá argentino cálido", raising=False)
    monkeypatch.setattr(vs.settings, "OPENAI_TTS_SPEED", 0.96, raising=False)
    monkeypatch.setattr(vs.httpx, "AsyncClient", _FakeClient)

    out = await vs.speak("Hola, ¿cómo va?")
    p = _FakeClient.captured
    assert out == b"MP3DATA"
    assert p["voice"] == "coral"
    assert p["speed"] == 0.96
    assert p["instructions"] == "hablá argentino cálido"  # el lever de acento/tono
    assert p["response_format"] == "mp3"


@pytest.mark.asyncio
async def test_speak_omite_instructions_en_tts1(monkeypatch):
    monkeypatch.setattr(vs.settings, "OPENAI_TTS_MODEL", "tts-1", raising=False)
    monkeypatch.setattr(vs.settings, "OPENAI_TTS_INSTRUCTIONS", "algo", raising=False)
    monkeypatch.setattr(vs.httpx, "AsyncClient", _FakeClient)

    await vs.speak("hola")
    assert "instructions" not in _FakeClient.captured  # tts-1 no lo soporta
    assert "speed" in _FakeClient.captured  # speed sí vale para todos
