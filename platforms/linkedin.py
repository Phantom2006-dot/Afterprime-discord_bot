import aiohttp
from urllib.parse import urlencode
from typing import Dict, Any, Optional
from .base import BasePlatform
import config

class LinkedInPlatform(BasePlatform):
    def __init__(self):
        self.client_id = config.LINKEDIN_CLIENT_ID
        self.client_secret = config.LINKEDIN_CLIENT_SECRET
        self.redirect_uri = config.LINKEDIN_REDIRECT_URI
        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.api_base = "https://api.linkedin.com/v2"
        self.scopes = config.PLATFORM_SCOPES['linkedin']
    
    def get_auth_url(self, state: str) -> str:
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'scope': ' '.join(self.scopes)
        }
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            async with session.post(self.token_url, data=data) as resp:
                return await resp.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            async with session.post(self.token_url, data=data) as resp:
                return await resp.json()
    
    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        headers = {'Authorization': f'Bearer {access_token}'}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base}/me", headers=headers) as resp:
                return await resp.json()
    
    async def publish_post(
        self, 
        access_token: str, 
        content: str, 
        media_urls: Optional[list] = None,
        platform_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        user_id = platform_metadata.get('user_id') if platform_metadata else None
        if not user_id:
            profile = await self.get_user_profile(access_token)
            user_id = profile.get('id')
        
        post_data = {
            'author': f'urn:li:person:{user_id}',
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {
                        'text': content
                    },
                    'shareMediaCategory': 'ARTICLE' if media_urls else 'NONE'
                }
            },
            'visibility': {
                'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
            }
        }
        
        if media_urls and len(media_urls) > 0:
            post_data['specificContent']['com.linkedin.ugc.ShareContent']['media'] = [{
                'status': 'READY',
                'originalUrl': media_urls[0]
            }]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/ugcPosts",
                headers=headers,
                json=post_data
            ) as resp:
                result = await resp.json()
                return {
                    'post_id': result.get('id'),
                    'post_url': f"https://www.linkedin.com/feed/update/{result.get('id')}",
                    'status': 'published' if resp.status == 201 else 'failed'
                }
    
    async def get_post_metrics(self, access_token: str, post_id: str) -> Dict[str, Any]:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base}/socialActions/{post_id}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        'reactions': data.get('likeCount', 0) + data.get('praiseCount', 0),
                        'comments': data.get('commentCount', 0),
                        'shares': data.get('shareCount', 0),
                        'views': 0
                    }
                return {'reactions': 0, 'comments': 0, 'shares': 0, 'views': 0}
