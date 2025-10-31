import aiohttp
from urllib.parse import urlencode
from typing import Dict, Any, Optional
from .base import BasePlatform
import config

class TikTokPlatform(BasePlatform):
    def __init__(self):
        self.client_key = config.TIKTOK_CLIENT_KEY
        self.client_secret = config.TIKTOK_CLIENT_SECRET
        self.redirect_uri = config.TIKTOK_REDIRECT_URI
        self.auth_url = "https://www.tiktok.com/v2/auth/authorize/"
        self.token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        self.api_base = "https://open.tiktokapis.com/v2"
        self.scopes = config.PLATFORM_SCOPES['tiktok']
    
    def get_auth_url(self, state: str) -> str:
        params = {
            'client_key': self.client_key,
            'scope': ','.join(self.scopes),
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'state': state
        }
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'client_key': self.client_key,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }
            async with session.post(self.token_url, headers=headers, data=data) as resp:
                return await resp.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'client_key': self.client_key,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
            async with session.post(self.token_url, headers=headers, data=data) as resp:
                return await resp.json()
    
    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        headers = {'Authorization': f'Bearer {access_token}'}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base}/user/info/",
                headers=headers,
                params={'fields': 'open_id,union_id,avatar_url,display_name'}
            ) as resp:
                return await resp.json()
    
    async def publish_post(
        self, 
        access_token: str, 
        content: str, 
        media_urls: Optional[list] = None,
        platform_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        if not media_urls or len(media_urls) == 0:
            return {'status': 'failed', 'error': 'Video required for TikTok posts'}
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        post_data = {
            'post_info': {
                'title': content[:150],
                'privacy_level': 'PUBLIC_TO_EVERYONE',
                'disable_duet': False,
                'disable_comment': False,
                'disable_stitch': False,
                'video_cover_timestamp_ms': 1000
            },
            'source_info': {
                'source': 'PULL_FROM_URL',
                'video_url': media_urls[0]
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/post/publish/video/init/",
                headers=headers,
                json=post_data
            ) as resp:
                result = await resp.json()
                
                if result.get('data', {}).get('publish_id'):
                    return {
                        'post_id': result['data']['publish_id'],
                        'post_url': None,
                        'status': 'published'
                    }
                return {'status': 'failed', 'error': result}
    
    async def get_post_metrics(self, access_token: str, post_id: str) -> Dict[str, Any]:
        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with aiohttp.ClientSession() as session:
            params = {
                'fields': 'like_count,comment_count,share_count,view_count'
            }
            async with session.get(
                f"{self.api_base}/video/query/",
                headers=headers,
                params={'filters': f'{{"video_ids":["{post_id}"]}}', 'fields': params['fields']}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    video_data = data.get('data', {}).get('videos', [{}])[0]
                    
                    return {
                        'reactions': video_data.get('like_count', 0),
                        'comments': video_data.get('comment_count', 0),
                        'shares': video_data.get('share_count', 0),
                        'views': video_data.get('view_count', 0)
                    }
                return {'reactions': 0, 'comments': 0, 'shares': 0, 'views': 0}
