from datetime import datetime
from database import get_session, Post, Mission, SocialAccount, User, EngagementSnapshot
from encryption import decrypt_token
from platforms import get_platform
from link_shortener import shortener
import config
from typing import Optional, Dict

class PublishingService:
    @staticmethod
    async def publish_mission(
        discord_id: str,
        mission_id: int,
        platform: str,
        platform_account_id: Optional[int] = None
    ) -> Dict:
        session = get_session()
        try:
            user = session.query(User).filter_by(discord_id=discord_id).first()
            if not user:
                return {'status': 'error', 'message': 'User not found'}
            
            mission = session.query(Mission).filter_by(id=mission_id).first()
            if not mission:
                return {'status': 'error', 'message': 'Mission not found'}
            
            if mission.status != 'active':
                return {'status': 'error', 'message': 'Mission is not active'}
            
            if platform not in mission.platforms:
                return {'status': 'error', 'message': f'Mission not available for {platform}'}
            
            social_account = session.query(SocialAccount).filter_by(
                user_id=user.id,
                platform=platform,
                is_active=True
            ).first()
            
            if not social_account:
                return {'status': 'error', 'message': f'{platform.title()} account not connected'}
            
            existing_post = session.query(Post).filter_by(
                user_id=user.id,
                mission_id=mission_id,
                platform=platform
            ).first()
            
            if existing_post and existing_post.status == 'published':
                return {'status': 'error', 'message': 'Already posted this mission to this platform'}
            
            access_token = decrypt_token(social_account.access_token)
            
            short_link_data = None
            content_with_link = mission.content
            
            if mission.target_url:
                utm_params = mission.utm_params or {}
                utm_params['utm_source'] = platform
                utm_params['utm_medium'] = 'social'
                utm_params['utm_campaign'] = f'mission_{mission_id}'
                utm_params['user_id'] = str(user.id)
                
                from urllib.parse import urlencode, urlparse, urlunparse
                url_parts = list(urlparse(mission.target_url))
                query = dict(utm_param.split('=') for utm_param in url_parts[4].split('&') if utm_param) if url_parts[4] else {}
                query.update(utm_params)
                url_parts[4] = urlencode(query)
                target_url_with_utm = urlunparse(url_parts)
                
                short_link_data = await shortener.create_short_link(
                    target_url_with_utm,
                    f"{mission.title} - {user.discord_username}"
                )
                
                if short_link_data.get('short_url'):
                    content_with_link = f"{mission.content}\n\n{short_link_data['short_url']}"
            
            platform_metadata = social_account.platform_metadata or {}
            if platform in ['meta', 'instagram'] and 'instagram_accounts' in platform_metadata:
                ig_accounts = platform_metadata['instagram_accounts']
                if ig_accounts:
                    platform_metadata['ig_account_id'] = ig_accounts[0]['ig_account_id']
            
            try:
                platform_adapter = get_platform(platform)
                publish_result = await platform_adapter.publish_post(
                    access_token,
                    content_with_link,
                    mission.media_urls,
                    platform_metadata
                )
                
                was_on_time = (datetime.utcnow() - mission.start_date).total_seconds() <= 86400
                
                base_points = config.SCORING['publish_success']
                if was_on_time:
                    base_points += config.SCORING['on_time_bonus']
                
                post = Post(
                    user_id=user.id,
                    mission_id=mission_id,
                    platform=platform,
                    platform_post_id=publish_result.get('post_id'),
                    post_url=publish_result.get('post_url'),
                    short_url=short_link_data.get('short_url') if short_link_data else None,
                    bitly_id=short_link_data.get('bitly_id') if short_link_data else None,
                    status='published' if publish_result.get('status') == 'published' else 'failed',
                    was_on_time=was_on_time,
                    points_earned=base_points if publish_result.get('status') == 'published' else 0,
                    error_message=publish_result.get('error') if publish_result.get('status') == 'failed' else None
                )
                
                session.add(post)
                
                if publish_result.get('status') == 'published':
                    user.total_score += base_points
                    user.monthly_score += base_points
                
                session.commit()
                
                return {
                    'status': 'success',
                    'post': post,
                    'points_earned': base_points,
                    'post_url': publish_result.get('post_url')
                }
                
            except Exception as e:
                post = Post(
                    user_id=user.id,
                    mission_id=mission_id,
                    platform=platform,
                    status='failed',
                    error_message=str(e)
                )
                session.add(post)
                session.commit()
                
                return {'status': 'error', 'message': f'Publishing failed: {str(e)}'}
        
        finally:
            session.close()

publishing_service = PublishingService()
