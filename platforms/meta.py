import aiohttp
from urllib.parse import urlencode
from typing import Dict, Any, Optional
from .base import BasePlatform
import config

class MetaPlatform(BasePlatform):
    def __init__(self):
        self.app_id = config.META_APP_ID
        self.app_secret = config.META_APP_SECRET
        self.redirect_uri = config.META_REDIRECT_URI
        self.auth_url = "https://www.facebook.com/v18.0/dialog/oauth"
        self.token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        self.graph_base = "https://graph.facebook.com/v18.0"
        self.scopes = config.PLATFORM_SCOPES['meta']
    
    def get_auth_url(self, state: str) -> str:
        params = {
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'scope': ','.join(self.scopes)
        }
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            params = {
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'redirect_uri': self.redirect_uri,
                'code': code
            }
            async with session.get(self.token_url, params=params) as resp:
                token_data = await resp.json()
                
                long_lived_params = {
                    'grant_type': 'fb_exchange_token',
                    'client_id': self.app_id,
                    'client_secret': self.app_secret,
                    'fb_exchange_token': token_data['access_token']
                }
                async with session.get(self.token_url, params=long_lived_params) as long_resp:
                    return await long_resp.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'fb_exchange_token': refresh_token
            }
            async with session.get(self.token_url, params=params) as resp:
                return await resp.json()
    
    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            params = {'access_token': access_token, 'fields': 'id,name,accounts'}
            async with session.get(f"{self.graph_base}/me", params=params) as resp:
                user_data = await resp.json()
                
                accounts = user_data.get('accounts', {}).get('data', [])
                instagram_accounts = []
                
                for page in accounts:
                    page_id = page['id']
                    page_token_params = {'access_token': access_token}
                    async with session.get(
                        f"{self.graph_base}/{page_id}",
                        params={'fields': 'instagram_business_account', 'access_token': access_token}
                    ) as ig_resp:
                        ig_data = await ig_resp.json()
                        if 'instagram_business_account' in ig_data:
                            instagram_accounts.append({
                                'page_id': page_id,
                                'page_name': page['name'],
                                'ig_account_id': ig_data['instagram_business_account']['id']
                            })
                
                user_data['instagram_accounts'] = instagram_accounts
                return user_data
    
    async def publish_post(
        self, 
        access_token: str, 
        content: str, 
        media_urls: Optional[list] = None,
        platform_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        if not platform_metadata or 'ig_account_id' not in platform_metadata:
            raise ValueError("Instagram account ID required in platform_metadata")
        
        ig_account_id = platform_metadata['ig_account_id']
        
        async with aiohttp.ClientSession() as session:
            if media_urls and len(media_urls) > 0:
                container_data = {
                    'image_url': media_urls[0],
                    'caption': content,
                    'access_token': access_token
                }
                
                async with session.post(
                    f"{self.graph_base}/{ig_account_id}/media",
                    data=container_data
                ) as container_resp:
                    container_result = await container_resp.json()
                    creation_id = container_result.get('id')
                    
                    if not creation_id:
                        return {'status': 'failed', 'error': container_result}
                    
                    publish_data = {
                        'creation_id': creation_id,
                        'access_token': access_token
                    }
                    
                    async with session.post(
                        f"{self.graph_base}/{ig_account_id}/media_publish",
                        data=publish_data
                    ) as publish_resp:
                        publish_result = await publish_resp.json()
                        post_id = publish_result.get('id')
                        
                        return {
                            'post_id': post_id,
                            'post_url': f"https://www.instagram.com/p/{post_id}/",
                            'status': 'published' if post_id else 'failed'
                        }
            else:
                return {'status': 'failed', 'error': 'Media required for Instagram posts'}
    
    async def get_post_metrics(self, access_token: str, post_id: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            params = {
                'fields': 'like_count,comments_count,insights.metric(impressions,reach,engagement)',
                'access_token': access_token
            }
            
            async with session.get(f"{self.graph_base}/{post_id}", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    insights = data.get('insights', {}).get('data', [])
                    impressions = next((i['values'][0]['value'] for i in insights if i['name'] == 'impressions'), 0)
                    
                    return {
                        'reactions': data.get('like_count', 0),
                        'comments': data.get('comments_count', 0),
                        'shares': 0,
                        'views': impressions
                    }
                return {'reactions': 0, 'comments': 0, 'shares': 0, 'views': 0}
