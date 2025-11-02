import aiohttp
from urllib.parse import urlencode
from typing import Dict, Any, Optional
from .base import BasePlatform
import config
import re
import random
import traceback

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
            'scope': ' '.join(self.scopes'
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
        """Get LinkedIn user profile using the correct endpoint"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Use the userinfo endpoint which is more reliable
                print("👤 Getting user info from LinkedIn...")
                async with session.get(
                    "https://api.linkedin.com/v2/userinfo", 
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        userinfo_data = await resp.json()
                        print(f"✅ Userinfo data: {userinfo_data}")
                        
                        # Extract user ID from the 'sub' field
                        user_id = userinfo_data.get('sub')
                        if user_id:
                            # Clean the user ID - remove 'urn:li:person:' prefix if present
                            if 'urn:li:person:' in user_id:
                                user_id = user_id.replace('urn:li:person:', '')
                            
                            # Remove any non-numeric characters
                            user_id = re.sub(r'[^0-9]', '', user_id)
                            
                            if user_id:
                                print(f"✅ Extracted user ID: {user_id}")
                                return {
                                    'id': user_id,
                                    'firstName': userinfo_data.get('given_name', ''),
                                    'lastName': userinfo_data.get('family_name', ''),
                                    'email': userinfo_data.get('email', ''),
                                    'picture': userinfo_data.get('picture', '')
                                }
                    
                    error_text = await resp.text()
                    print(f"❌ Userinfo error: {resp.status} - {error_text}")
                    return {'id': None, 'error': f"HTTP {resp.status}: {error_text}"}
                
        except Exception as e:
            print(f"❌ Profile retrieval error: {e}")
            return {'id': None, 'error': str(e)}
    
    async def publish_post(
        self, 
        access_token: str, 
        content: str, 
        media_urls: Optional[list] = None,
        platform_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        print(f"🔗 Attempting REAL publish to LinkedIn...")
        print(f"📝 Content length: {len(content)}")
        
        # First, let's verify the access token is valid
        print("🔐 Verifying access token...")
        profile_data = await self.get_user_profile(access_token)
        if not profile_data.get('id'):
            print(f"❌ Access token invalid or insufficient permissions")
            return {
                'status': 'failed',
                'error': 'Invalid access token or insufficient LinkedIn permissions',
                'profile_data': profile_data
            }
        
        user_id = profile_data['id']
        print(f"✅ Access token valid. User ID: {user_id}")
        
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            # Use the correct author format for personal accounts
            author_urn = f"urn:li:person:{user_id}"
            print(f"👤 Using author URN: {author_urn}")
            
            # Prepare post data - SIMPLIFIED for testing
            post_data = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED", 
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content[:1300]  # LinkedIn has character limits
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            print(f"📦 Post data prepared")
            print(f"📤 Sending REAL request to LinkedIn API...")
            print(f"🔗 Endpoint: {self.api_base}/ugcPosts")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/ugcPosts",
                    headers=headers,
                    json=post_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    result_text = await resp.text()
                    print(f"🔗 LinkedIn API Response - Status: {resp.status}")
                    print(f"🔗 Response headers: {dict(resp.headers)}")
                    print(f"🔗 Response body: {result_text}")
                    
                    try:
                        result_json = await resp.json()
                        print(f"🔗 Parsed JSON: {result_json}")
                    except:
                        result_json = {"raw_text": result_text}
                    
                    if resp.status == 201:
                        # Success! Extract post ID from headers
                        post_id_header = resp.headers.get('X-RestLi-Id', '')
                        print(f"✅ Post ID Header: {post_id_header}")
                        
                        if post_id_header:
                            # The correct URL format for LinkedIn posts
                            post_url = f"https://www.linkedin.com/feed/update/{post_id_header}/"
                            
                            print(f"✅ REAL LinkedIn post SUCCESSFUL!")
                            print(f"✅ Post URL: {post_url}")
                            
                            # Double-check by trying to fetch the post
                            await self._verify_post_creation(access_token, post_id_header)
                            
                            return {
                                'post_id': post_id_header,
                                'post_url': post_url,
                                'status': 'published',
                                'response_status': resp.status,
                                'error': None,
                                'note': 'real_linkedin_post_created'
                            }
                        else:
                            print(f"❌ No post ID received from LinkedIn")
                            return {
                                'status': 'failed',
                                'error': 'LinkedIn API returned success but no post ID',
                                'response_status': resp.status,
                                'response_body': result_text
                            }
                    else:
                        error_msg = f"HTTP {resp.status}: {result_text}"
                        print(f"❌ REAL LinkedIn API FAILED: {error_msg}")
                        
                        # Provide detailed error information
                        detailed_error = self._parse_linkedin_error(result_text)
                        return {
                            'status': 'failed',
                            'error': detailed_error,
                            'response_status': resp.status,
                            'response_body': result_text
                        }
        
        except Exception as e:
            print(f"❌ REAL LinkedIn API error: {e}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
            
            return {
                'status': 'failed',
                'error': f'API call failed: {str(e)}',
                'exception': traceback.format_exc()
            }
    
    def _parse_linkedin_error(self, error_text: str) -> str:
        """Parse LinkedIn API error response for better error messages"""
        try:
            error_data = json.loads(error_text)
            message = error_data.get('message', 'Unknown error')
            
            # Common LinkedIn API errors
            if 'insufficient permissions' in message.lower():
                return f"LinkedIn permissions error: {message}. Please ensure your app has 'w_member_social' scope."
            elif 'author' in message.lower():
                return f"LinkedIn author error: {message}. User may not have posting permissions."
            elif 'validation' in message.lower():
                return f"LinkedIn validation error: {message}. Check post content format."
            else:
                return f"LinkedIn API error: {message}"
                
        except:
            return f"LinkedIn error: {error_text}"
    
    async def _verify_post_creation(self, access_token: str, post_urn: str):
        """Verify that the post was actually created by trying to fetch it"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            print(f"🔍 Verifying post creation: {post_urn}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base}/ugcPosts/{post_urn}",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        print(f"✅ Post verification SUCCESSFUL - post exists!")
                        post_data = await resp.json()
                        print(f"✅ Post details: {post_data}")
                    else:
                        print(f"⚠️ Post verification failed - status {resp.status}")
                        
        except Exception as e:
            print(f"⚠️ Post verification error: {e}")
    
    def _simulate_successful_post(self, content: str) -> Dict[str, Any]:
        """ONLY use simulation when explicitly needed"""
        print("🎯 EXPLICIT SIMULATION - No real LinkedIn post created")
        
        return {
            'post_id': f"simulated_{random.randint(1000000000, 9999999999)}",
            'post_url': None,  # No URL for simulated posts
            'status': 'published',
            'response_status': 201,
            'note': 'explicit_simulation_no_linkedin_post',
            'error': None
        }
    
    async def get_post_metrics(self, access_token: str, post_id: str) -> Dict[str, Any]:
        # For now, return basic metrics
        return {
            'reactions': 0,
            'comments': 0,
            'shares': 0,
            'views': 0
            }
