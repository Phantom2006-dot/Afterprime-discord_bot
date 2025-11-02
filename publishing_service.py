from datetime import datetime
from database import get_session, Post, Mission, SocialAccount, User, EngagementSnapshot
from encryption import decrypt_token
from platforms import get_platform
from link_shortener import shortener
import config
from typing import Optional, Dict
import traceback

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
            print(f"📤 Starting publish process for user {discord_id}, mission {mission_id}, platform {platform}")
            
            user = session.query(User).filter_by(discord_id=discord_id).first()
            if not user:
                print(f"❌ User not found: {discord_id}")
                return {'status': 'error', 'message': 'User not found'}
            
            mission = session.query(Mission).filter_by(id=mission_id).first()
            if not mission:
                print(f"❌ Mission not found: {mission_id}")
                return {'status': 'error', 'message': 'Mission not found'}
            
            if mission.status != 'active':
                print(f"❌ Mission not active: {mission_id}")
                return {'status': 'error', 'message': 'Mission is not active'}
            
            # Check if mission has platform restrictions
            mission_platforms = mission.platforms or []
            if mission_platforms and platform not in mission_platforms:
                print(f"❌ Platform not allowed: {platform} not in {mission_platforms}")
                return {'status': 'error', 'message': f'Mission not available for {platform}'}
            
            social_account = session.query(SocialAccount).filter_by(
                user_id=user.id,
                platform=platform,
                is_active=True
            ).first()
            
            if not social_account:
                print(f"❌ No active social account for platform: {platform}")
                return {'status': 'error', 'message': f'{platform.title()} account not connected'}
            
            # Check for existing post
            existing_post = session.query(Post).filter_by(
                user_id=user.id,
                mission_id=mission_id,
                platform=platform
            ).first()
            
            if existing_post:
                if existing_post.status == 'published':
                    print(f"❌ Already posted this mission: user {user.id}, mission {mission_id}, platform {platform}")
                    return {'status': 'error', 'message': 'Already posted this mission to this platform'}
                else:
                    # Remove failed post to allow retry
                    session.delete(existing_post)
                    session.commit()
                    print(f"🗑️ Removed failed post for retry")
            
            print(f"🔐 Decrypting access token...")
            access_token = decrypt_token(social_account.access_token)
            
            # Prepare content with short link if needed
            short_link_data = None
            content_with_link = mission.content
            
            if mission.target_url:
                print(f"🔗 Generating short link for target URL: {mission.target_url}")
                try:
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
                        print(f"✅ Short link created: {short_link_data['short_url']}")
                except Exception as e:
                    print(f"⚠️ Short link creation failed: {e}")
                    # Continue without short link
            
            # Prepare platform metadata
            platform_metadata = social_account.platform_metadata or {}
            platform_metadata['user_id'] = social_account.platform_user_id
            
            if platform in ['meta', 'instagram'] and 'instagram_accounts' in platform_metadata:
                ig_accounts = platform_metadata['instagram_accounts']
                if ig_accounts:
                    platform_metadata['ig_account_id'] = ig_accounts[0]['ig_account_id']
            
            print(f"🚀 Publishing to {platform}...")
            try:
                platform_adapter = get_platform(platform)
                publish_result = await platform_adapter.publish_post(
                    access_token,
                    content_with_link,
                    mission.media_urls,
                    platform_metadata
                )
                
                print(f"📝 Publish result: {publish_result}")
                
                # Check if publishing was successful
                is_published = publish_result.get('status') == 'published'
                error_message = publish_result.get('error')
                note = publish_result.get('note', '')
                
                # Calculate points - award points for ALL successful posts
                was_on_time = True
                base_points = config.SCORING['publish_success'] if is_published else 0
                
                # Award on-time bonus for ALL successful posts (real or simulated)
                if was_on_time and is_published:
                    base_points += config.SCORING['on_time_bonus']
                    print(f"✅ Awarding on-time bonus")
                
                print(f"💰 Points calculated: {base_points} (published: {is_published}, note: {note})")
                
                # Create post record
                post = Post(
                    user_id=user.id,
                    mission_id=mission_id,
                    platform=platform,
                    platform_post_id=publish_result.get('post_id'),
                    post_url=publish_result.get('post_url'),
                    short_url=short_link_data.get('short_url') if short_link_data else None,
                    bitly_id=short_link_data.get('bitly_id') if short_link_data else None,
                    status='published' if is_published else 'failed',
                    was_on_time=was_on_time,
                    points_earned=base_points,
                    error_message=error_message
                )
                
                session.add(post)
                
                # Update user scores if published successfully
                if is_published:
                    user.total_score += base_points
                    user.monthly_score += base_points
                    print(f"✅ User scores updated: total={user.total_score}, monthly={user.monthly_score}")
                else:
                    print(f"❌ Post failed, no points awarded. Error: {error_message}")
                
                # Commit all changes
                session.commit()
                print(f"💾 Database committed successfully")
                
                # Verify the commit by refreshing the objects
                session.refresh(user)
                session.refresh(post)
                print(f"🔍 After commit - User total_score: {user.total_score}, Post status: {post.status}")
                
                if is_published:
                    response_data = {
                        'status': 'success',
                        'post': post,
                        'points_earned': base_points,
                        'post_url': publish_result.get('post_url'),
                        'message': 'Post published successfully!'
                    }
                    
                    # Add warning if it's a simulated post
                    if 'simulated' in note:
                        response_data['message'] = 'Post recorded successfully!'
                        response_data['warning'] = 'Note: This was a simulated post for development.'
                        response_data['post_url'] = None  # Remove URL for simulated posts
                    
                    return response_data
                else:
                    return {
                        'status': 'error', 
                        'message': f'Publishing failed: {error_message}'
                    }
                
            except Exception as e:
                print(f"❌ Publishing error: {e}")
                print(f"🔍 Traceback: {traceback.format_exc()}")
                
                # Create failed post record
                post = Post(
                    user_id=user.id,
                    mission_id=mission_id,
                    platform=platform,
                    status='failed',
                    points_earned=0,
                    error_message=str(e)
                )
                session.add(post)
                session.commit()
                
                return {'status': 'error', 'message': f'Publishing failed: {str(e)}'}
        
        except Exception as e:
            print(f"💥 Critical error in publish_mission: {e}")
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return {'status': 'error', 'message': f'System error: {str(e)}'}
        finally:
            session.close()

    @staticmethod
    async def get_user_posts(discord_id: str) -> list:
        """Get all posts for a user"""
        session = get_session()
        try:
            user = session.query(User).filter_by(discord_id=discord_id).first()
            if not user:
                return []
            
            posts = session.query(Post).filter_by(user_id=user.id).order_by(Post.posted_at.desc()).all()
            return posts
        finally:
            session.close()

    @staticmethod
    async def get_user_score(discord_id: str) -> Dict:
        """Get user score information"""
        session = get_session()
        try:
            user = session.query(User).filter_by(discord_id=discord_id).first()
            if not user:
                return {'total_score': 0, 'monthly_score': 0, 'posts_count': 0}
            
            posts_count = session.query(Post).filter_by(user_id=user.id, status='published').count()
            
            return {
                'total_score': user.total_score,
                'monthly_score': user.monthly_score,
                'posts_count': posts_count,
                'current_role': user.current_role
            }
        finally:
            session.close()

    @staticmethod
    async def update_post_metrics():
        """Update metrics for all published posts"""
        session = get_session()
        try:
            published_posts = session.query(Post).filter_by(status='published').all()
            
            for post in published_posts:
                try:
                    social_account = session.query(SocialAccount).filter_by(
                        user_id=post.user_id,
                        platform=post.platform,
                        is_active=True
                    ).first()
                    
                    if not social_account:
                        continue
                    
                    access_token = decrypt_token(social_account.access_token)
                    platform_adapter = get_platform(post.platform)
                    
                    metrics = await platform_adapter.get_post_metrics(
                        access_token, 
                        post.platform_post_id
                    )
                    
                    # Create engagement snapshot
                    snapshot = EngagementSnapshot(
                        post_id=post.id,
                        clicks=metrics.get('clicks', 0),
                        reactions=metrics.get('reactions', 0),
                        comments=metrics.get('comments', 0),
                        shares=metrics.get('shares', 0),
                        views=metrics.get('views', 0),
                        platform_metrics=metrics
                    )
                    
                    session.add(snapshot)
                    
                    # Update post metrics
                    post.metrics = metrics
                    post.last_metrics_update = datetime.utcnow()
                    
                    # Calculate additional points based on engagement
                    additional_points = 0
                    
                    # Click-based points
                    clicks = metrics.get('clicks', 0)
                    additional_points += (clicks // 10) * config.SCORING['clicks_per_10']
                    
                    # Engagement tier points
                    if post.platform == 'linkedin':
                        reactions = metrics.get('reactions', 0)
                        if reactions >= 100:
                            additional_points += config.SCORING['linkedin_reactions_100']
                        elif reactions >= 30:
                            additional_points += config.SCORING['linkedin_reactions_30']
                        elif reactions >= 10:
                            additional_points += config.SCORING['linkedin_reactions_10']
                    
                    elif post.platform in ['meta', 'instagram']:
                        views = metrics.get('views', 0)
                        if views >= 2000:
                            additional_points += config.SCORING['instagram_views_2000']
                        elif views >= 500:
                            additional_points += config.SCORING['instagram_views_500']
                        elif views >= 100:
                            additional_points += config.SCORING['instagram_views_100']
                    
                    elif post.platform == 'tiktok':
                        views = metrics.get('views', 0)
                        if views >= 2000:
                            additional_points += config.SCORING['tiktok_views_2000']
                        elif views >= 500:
                            additional_points += config.SCORING['tiktok_views_500']
                        elif views >= 100:
                            additional_points += config.SCORING['tiktok_views_100']
                    
                    # Update points if any additional points were earned
                    if additional_points > 0:
                        post.points_earned += additional_points
                        
                        user = session.query(User).filter_by(id=post.user_id).first()
                        if user:
                            user.total_score += additional_points
                            user.monthly_score += additional_points
                    
                    session.commit()
                    print(f"✅ Updated metrics for post {post.id}: +{additional_points} points")
                    
                except Exception as e:
                    print(f"❌ Error updating metrics for post {post.id}: {e}")
                    session.rollback()
                    continue
                    
        finally:
            session.close()

publishing_service = PublishingService()
