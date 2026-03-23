#!/usr/bin/env python3
"""
API tests for BoTTube Telegram Bot
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bottube_bot import BoTTubeAPI, Video


class TestBoTTubeAPIIntegration:
    """Integration tests for BoTTube API"""

    @pytest.mark.asyncio
    async def test_api_client_creation(self):
        """Test that API client can be created"""
        api = BoTTubeAPI()
        assert api.client is not None

    @pytest.mark.asyncio
    async def test_get_latest_videos_with_mock(self):
        """Test get_latest_videos with mocked response"""
        api = BoTTubeAPI()
        mock_response = [
            {
                'id': '1',
                'title': 'Test Video 1',
                'description': 'Description 1',
                'thumbnail_url': 'https://example.com/thumb1.jpg',
                'video_url': 'https://example.com/video1.mp4',
                'views': 1000,
                'likes': 50,
                'agent_name': 'Agent1'
            },
            {
                'id': '2',
                'title': 'Test Video 2',
                'description': 'Description 2',
                'thumbnail_url': 'https://example.com/thumb2.jpg',
                'video_url': 'https://example.com/video2.mp4',
                'views': 2000,
                'likes': 100,
                'agent_name': 'Agent2'
            }
        ]
        
        with patch.object(api.client, 'list_videos', return_value=mock_response):
            videos = await api.get_latest_videos(2)
            assert len(videos) == 2
            assert videos[0].title == 'Test Video 1'
            assert videos[1].views == 2000

    @pytest.mark.asyncio
    async def test_get_trending_videos_with_mock(self):
        """Test get_trending_videos with mocked response"""
        api = BoTTubeAPI()
        mock_response = [
            {
                'id': 'trending1',
                'title': 'Viral Video',
                'description': 'Going viral!',
                'thumbnail_url': 'https://example.com/viral.jpg',
                'video_url': 'https://example.com/viral.mp4',
                'views': 100000,
                'likes': 5000,
                'agent_name': 'ViralCreator'
            }
        ]
        
        with patch.object(api.client, 'trending', return_value=mock_response):
            videos = await api.get_trending_videos(1)
            assert len(videos) == 1
            assert videos[0].views == 100000

    @pytest.mark.asyncio
    async def test_search_videos_with_mock(self):
        """Test search_videos with mocked response"""
        api = BoTTubeAPI()
        mock_response = [
            {
                'id': 'search1',
                'title': 'Python Tutorial',
                'description': 'Learn Python',
                'thumbnail_url': 'https://example.com/python.jpg',
                'video_url': 'https://example.com/python.mp4',
                'views': 5000,
                'likes': 200,
                'agent_name': 'CodeTeacher'
            }
        ]
        
        with patch.object(api.client, 'search', return_value=mock_response):
            videos = await api.search_videos('python', 1)
            assert len(videos) == 1
            assert 'Python' in videos[0].title

    @pytest.mark.asyncio
    async def test_get_video_with_mock(self):
        """Test get_video with mocked response"""
        api = BoTTubeAPI()
        mock_response = {
            'id': 'specific123',
            'title': 'Specific Video',
            'description': 'A specific video description',
            'thumbnail_url': 'https://example.com/specific.jpg',
            'video_url': 'https://example.com/specific.mp4',
            'views': 12345,
            'likes': 678,
            'agent_name': 'SpecificCreator',
            'duration': 180
        }
        
        with patch.object(api.client, 'get_video', return_value=mock_response):
            video = await api.get_video('specific123')
            assert video is not None
            assert video.id == 'specific123'
            assert video.duration == 180

    @pytest.mark.asyncio
    async def test_get_agent_with_mock(self):
        """Test get_agent with mocked response"""
        api = BoTTubeAPI()
        mock_response = {
            'name': 'TestAgent',
            'bio': 'I create awesome videos',
            'video_count': 50,
            'total_views': 100000,
            'total_likes': 5000,
            'subscriber_count': 1000,
            'avatar_url': 'https://example.com/avatar.jpg',
            'recent_videos': []
        }
        
        with patch.object(api.client, 'get_agent', return_value=mock_response):
            agent = await api.get_agent('TestAgent')
            assert agent is not None
            assert agent['name'] == 'TestAgent'
            assert agent['video_count'] == 50

    @pytest.mark.asyncio
    async def test_tip_video_success(self):
        """Test tip_video with success"""
        api = BoTTubeAPI()
        
        with patch.object(api.client, 'tip', return_value={'success': True}):
            result = await api.tip_video('video123', 5.0, 'wallet123')
            assert result == True

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test API error handling"""
        api = BoTTubeAPI()
        from bottube import BoTTubeError
        
        with patch.object(api.client, 'list_videos', side_effect=BoTTubeError("API Error")):
            videos = await api.get_latest_videos(5)
            assert videos == []

    @pytest.mark.asyncio
    async def test_empty_search_results(self):
        """Test empty search results"""
        api = BoTTubeAPI()
        
        with patch.object(api.client, 'search', return_value=[]):
            videos = await api.search_videos('nonexistent', 5)
            assert videos == []


class TestVideoDataClass:
    """Tests for Video dataclass with various data formats"""

    def test_video_with_minimal_data(self):
        """Test Video with minimal required data"""
        data = {'id': 'min'}
        video = Video.from_dict(data)
        assert video.id == 'min'
        assert video.title == 'Untitled'
        assert video.views == 0

    def test_video_with_nested_agent(self):
        """Test Video with nested agent object"""
        data = {
            'id': 'nested',
            'title': 'Nested Agent Video',
            'agent': {'name': 'NestedAgent', 'id': 'agent123'}
        }
        video = Video.from_dict(data)
        assert video.agent_name == 'NestedAgent'

    def test_video_description_truncation(self):
        """Test that long descriptions are truncated"""
        long_desc = "A" * 300
        data = {
            'id': 'long',
            'description': long_desc
        }
        video = Video.from_dict(data)
        assert len(video.description) == 203  # 200 + "..."
        assert video.description.endswith('...')

    def test_video_short_description_not_truncated(self):
        """Test that short descriptions are not truncated"""
        short_desc = "Short description"
        data = {
            'id': 'short',
            'description': short_desc
        }
        video = Video.from_dict(data)
        assert video.description == short_desc
        assert not video.description.endswith('...')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])