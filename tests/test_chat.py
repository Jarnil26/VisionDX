import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
class TestChatAPI:
    """Tests for AI Chat Doctor endpoints."""

    async def test_chat_text_input(self, auth_client):
        """Test sending text message to AI chat."""
        payload = {
            "message": "I have been feeling very tired lately and have pale skin.",
            "session_id": "session-123",
            "lang": "en"
        }
        response = await auth_client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "session_id" in data
        assert isinstance(data["suggestions"], list)

    async def test_chat_voice_input(self, auth_client):
        """Test sending voice audio to AI chat."""
        # Mock transcription utility
        with patch("visiondx.api.routes.chat.transcribe_audio") as mock_transcribe:
            mock_transcribe.return_value = ("I have a fever and cough.", None)
            
            audio_content = b"fake audio content"
            files = {"audio": ("sample.wav", audio_content, "audio/wav")}
            data = {"session_id": "sid-456", "lang": "en"}
            
            response = await auth_client.post("/chat/voice", files=files, data=data)
            assert response.status_code == 200
            data = response.json()
            assert "reply" in data
            assert data["session_id"] == "sid-456"

    async def test_chat_emergency_detection(self, auth_client):
        """Test chat response when a medical emergency is simulated."""
        from visiondx.api.routes import chat
        
        # Override mock_chat_service specifically for this test
        with patch("visiondx.services.chat_service.process_chat_message") as mock_chat:
            mock_chat.return_value = (
                "Call an ambulance!", "sid-999", ["Emergency"], True, [{"name": "Hospital X"}]
            )
            
            payload = {"message": "Severe chest pain"}
            response = await auth_client.post("/chat", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["emergency_alert"] is True
            assert len(data["nearby_facilities"]) > 0
