import aiohttp
import config
from typing import Dict, Any

class BitlyShortener:
    def __init__(self):
        self.access_token = config.BITLY_ACCESS_TOKEN
        self.api_base = "https://api-ssl.bitly.com/v4"
    
    async def create_short_link(self, long_url: str, title: str = "") -> Dict[str, Any]:
        if not self.access_token:
            return {
                'short_url': long_url,
                'bitly_id': None,
                'status': 'disabled'
            }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'long_url': long_url,
            'title': title[:50] if title else ''
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/shorten",
                headers=headers,
                json=data
            ) as resp:
                if resp.status == 200 or resp.status == 201:
                    result = await resp.json()
                    return {
                        'short_url': result.get('link'),
                        'bitly_id': result.get('id'),
                        'status': 'success'
                    }
                else:
                    error = await resp.text()
                    return {
                        'short_url': long_url,
                        'bitly_id': None,
                        'status': 'error',
                        'error': error
                    }
    
    async def get_click_metrics(self, bitly_id: str) -> Dict[str, Any]:
        if not self.access_token or not bitly_id:
            return {'clicks': 0}
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base}/bitlinks/{bitly_id}/clicks/summary",
                headers=headers,
                params={'unit': 'day', 'units': -1}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {'clicks': data.get('total_clicks', 0)}
                return {'clicks': 0}

shortener = BitlyShortener()
