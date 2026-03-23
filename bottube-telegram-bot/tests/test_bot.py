#!/usr/bin/env python3
"""
Unit tests for BoTTube Telegram Bot
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bottube_bot import (
    Video,
    BoTTubeAPI,
    format_video_caption,
    create_video_keyboard,
    user_wallets,
    WALLET_ADDRESS
)


class TestVideo:
    """Tests for Video dataclass"""

    def test_video_creation(self):
        """Test creating a Video instance"""
        video = Video(
            id="test123",
            title="Test Video",
            description="A test description",
            thumbnail_url="https://example.com/thumb.jpg",
            video_url="https://example.com/video.mp4",
            views=1000,
            likes=50,
            agent_name="TestAgent"
        )
        assert video.id == "test123"
        assert video.title == "Test Video"
        assert video.views == 1000

    def test_video_from_dict(self):
        """Test creating Video from dictionary"""
        data = {
            'id': 'abc123',
            'title': 'My Video',
            'description': 'A long description that should be truncated if it exceeds 200 characters ' * 5,
            'thumbnail_url': 'https://example.com/thumb.jpg',
            'video_url': 'https://example.com/video.mp4',
            'views': 5000,
            'likes': 200,
            'agent_name': 'Creator'
        }
        video = Video.from_dict(data)
        assert video.id == 'abc123'
        assert video.title == 'My Video'
        assert video.views == 5000
        assert video.description.endswith('...')

    def test_video_from_dict_alternative_keys(self):
        """Test Video creation with alternative key names"""
        data = {
            'id': 'xyz789',
            'title': 'Alternative Video',
            'thumbnail': 'https://example.com/alt.jpg',
            'url': 'https://example.com/alt.mp4',
            'view_count': 3000,
            'like_count': 150,
            'agent': {'name': 'AltAgent'}
        }
        video = Video.from_dict(data)
        assert video.thumbnail_url == 'https://example.com/alt.jpg'
        assert video.views == 3000
        assert video.agent_name == 'AltAgent'


class TestFormatVideoCaption:
    """Tests for format_video_caption function"""

    def test_basic_caption(self):
        """Test basic caption formatting"""
        video = Video(
            id="test1",
            title="Test Video",
            description="Description here",
            thumbnail_url="",
            video_url="",
            views=1000,
            likes=50,
            agent_name="Agent1"
        )
        caption = format_video_caption(video)
        assert "🎬 *Test Video*" in caption
        assert "👤 Agent: Agent1" in caption
        assert "👁 Views: 1,000" in caption
        assert "❤️ Likes: 50" in caption

    def test_caption_with_duration(self):
        """Test caption with duration"""
        video = Video(
            id="test2",
            title="Long Video",
            description="Desc",
            thumbnail_url="",
            video_url="",
            views=500,
            likes=25,
            agent_name="Agent2",
            duration=300
        )
        caption = format_video_caption(video)
        assert "Duration: 300s" in caption

    def test_caption_large_numbers(self):
        """Test caption with large view counts"""
        video = Video(
            id="test3",
            title="Viral Video",
            description="Desc",
            thumbnail_url="",
            video_url="",
            views=1234567,
            likes=98765,
            agent_name="Star"
        )
        caption = format_video_caption(video)
        assert "1,234,567" in caption
        assert "98,765" in caption


class TestCreateVideoKeyboard:
    """Tests for create_video_keyboard function"""

    def test_keyboard_creation(self):
        """Test that keyboard is created correctly"""
        keyboard = create_video_keyboard("video123")
        assert keyboard is not None
        # Check that it's an InlineKeyboardMarkup
        assert hasattr(keyboard, 'inline_keyboard')

    def test_keyboard_buttons(self):
        """Test that keyboard has correct buttons"""
        keyboard = create_video_keyboard("video456")
        buttons = keyboard.inline_keyboard
        # Should have 2 rows
        assert len(buttons) == 2
        # First row should have Watch and Tip
        assert len(buttons[0]) == 2
        # Second row should have Agent
        assert len(buttons[1]) == 1


class TestBoTTubeAPI:
    """Tests for BoTTubeAPI class"""

    def test_api_initialization(self):
        """Test API client initialization"""
        api = BoTTubeAPI()
        assert api.client is not None

    @pytest.mark.asyncio
    async def test_get_latest_videos_empty(self):
        """Test get_latest_videos with empty response"""
        api = BoTTubeAPI()
        with patch.object(api.client, 'list_videos', return_value=[]):
            videos = await api.get_latest_videos(5)
            assert videos == []

    @pytest.mark.asyncio
    async def test_get_trending_videos_empty(self):
        """Test get_trending_videos with empty response"""
        api = BoTTubeAPI()
        with patch.object(api.client, 'trending', return_value=[]):
            videos = await api.get_trending_videos(5)
            assert videos == []

    @pytest.mark.asyncio
    async def test_search_videos_empty(self):
        """Test search_videos with empty response"""
        api = BoTTubeAPI()
        with patch.object(api.client, 'search', return_value=[]):
            videos = await api.search_videos("test", 5)
            assert videos == []

    @pytest.mark.asyncio
    async def test_get_video_not_found(self):
        """Test get_video with non-existent video"""
        api = BoTTubeAPI()
        from bottube import BoTTubeError
        with patch.object(api.client, 'get_video', side_effect=BoTTubeError("Not found")):
            video = await api.get_video("nonexistent")
            assert video is None


class TestUserWallets:
    """Tests for user wallet management"""

    def test_wallet_storage(self):
        """Test storing user wallet"""
        user_wallets[12345] = "test_wallet_address"
        assert user_wallets[12345] == "test_wallet_address"
        # Cleanup
        del user_wallets[12345]

    def test_wallet_retrieval(self):
        """Test retrieving user wallet"""
        user_wallets[99999] = "another_wallet"
        assert 99999 in user_wallets
        # Cleanup
        del user_wallets[99999]


class TestWalletAddress:
    """Tests for developer wallet address"""

    def test_wallet_address_format(self):
        """Test that wallet address is valid format"""
        assert len(WALLET_ADDRESS) > 30
        assert WALLET_ADDRESS.startswith('9d') or len(WALLET_ADDRESS) >= 32

    def test_wallet_address_not_empty(self):
        """Test that wallet address is not empty"""
        assert WALLET_ADDRESS != ""
        assert WALLET_ADDRESS is not None


class TestVideoListProcessing:
    """Tests for video list processing"""

    @pytest.mark.asyncio
    async def test_latest_videos_limit(self):
        """Test that latest videos respects limit"""
        api = BoTTubeAPI()
        mock_videos = [{'id': str(i), 'title': f'Video {i}', 'description': '', 
                       'thumbnail_url': '', 'video_url': '', 'views': 0, 
                       'likes': 0, 'agent_name': 'Test'} for i in range(10)]
        
        with patch.object(api.client, 'list_videos', return_value=mock_videos):
            videos = await api.get_latest_videos(5)
            assert len(videos) == 5

    @pytest.mark.asyncio
    async def test_search_results_limit(self):
        """Test that search results respect limit"""
        api = BoTTubeAPI()
        mock_videos = [{'id': str(i), 'title': f'Search {i}', 'description': '',
                       'thumbnail_url': '', 'video_url': '', 'views': 0,
                       'likes': 0, 'agent_name': 'Test'} for i in range(20)]
        
        with patch.object(api.client, 'search', return_value=mock_videos):
            videos = await api.search_videos("test", 5)
            assert len(videos) == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])