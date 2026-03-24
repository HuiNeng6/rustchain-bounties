#!/usr/bin/env python3
"""
Tests for BoTTube Telegram Bot.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bottube_bot import BoTTubeAPI, format_video_message


class TestBoTTubeAPI:
    """Tests for BoTTube API client."""

    @patch("bottube_bot.requests.Session")
    def test_get_latest_videos(self, mock_session_class):
        """Test getting latest videos."""
        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "videos": [
                {"id": "1", "title": "Video 1", "views": 100},
                {"id": "2", "title": "Video 2", "views": 200},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session

        api = BoTTubeAPI()
        videos = api.get_latest_videos()

        assert len(videos) == 2
        assert videos[0]["id"] == "1"

    @patch("bottube_bot.requests.Session")
    def test_search_videos(self, mock_session_class):
        """Test searching videos."""
        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "videos": [
                {"id": "1", "title": "Gaming Video", "views": 50},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session

        api = BoTTubeAPI()
        videos = api.search_videos("gaming")

        assert len(videos) == 1
        assert "Gaming" in videos[0]["title"]

    @patch("bottube_bot.requests.Session")
    def test_get_video(self, mock_session_class):
        """Test getting a specific video."""
        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "abc123",
            "title": "Test Video",
            "views": 1000
        }
        mock_response.raise_for_status = Mock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session

        api = BoTTubeAPI()
        video = api.get_video("abc123")

        assert video is not None
        assert video["id"] == "abc123"

    @patch("bottube_bot.requests.Session")
    def test_get_agent(self, mock_session_class):
        """Test getting agent profile."""
        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "name": "TestAgent",
            "bio": "A test agent",
            "video_count": 10
        }
        mock_response.raise_for_status = Mock()
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session

        api = BoTTubeAPI()
        agent = api.get_agent("TestAgent")

        assert agent is not None
        assert agent["name"] == "TestAgent"


class TestFormatVideoMessage:
    """Tests for video message formatting."""

    def test_basic_formatting(self):
        """Test basic video message formatting."""
        video = {
            "id": "abc123",
            "title": "Test Video",
            "agent_name": "TestAgent",
            "views": 1000,
            "duration": "5:30",
            "tags": ["gaming", "retro"]
        }

        message = format_video_message(video)

        assert "Test Video" in message
        assert "TestAgent" in message
        assert "1,000 views" in message
        assert "5:30" in message
        assert "abc123" in message
        assert "#gaming" in message

    def test_video_without_tags(self):
        """Test formatting a video without tags."""
        video = {
            "id": "xyz789",
            "title": "No Tags Video",
            "agent_name": "Agent",
            "views": 500
        }

        message = format_video_message(video)

        assert "No Tags Video" in message
        assert "#" not in message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])