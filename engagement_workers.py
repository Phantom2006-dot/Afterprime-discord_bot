import asyncio
from datetime import datetime, timedelta
from database import get_session, Post, User, EngagementSnapshot, SocialAccount
from encryption import decrypt_token
from platforms import get_platform
from link_shortener import shortener
import config

class EngagementWorker:
    def __init__(self):
        self.running = False
    
    async def start(self):
        self.running = True
        asyncio.create_task(self.poll_engagement_metrics())
        asyncio.create_task(self.poll_click_metrics())
    
    async def stop(self):
        self.running = False
    
    async def poll_engagement_metrics(self):
        while self.running:
            try:
                await self._update_engagement_metrics()
            except Exception as e:
                print(f"Error polling engagement metrics: {e}")
            
            await asyncio.sleep(config.METRICS_POLL_INTERVAL)
    
    async def poll_click_metrics(self):
        while self.running:
            try:
                await self._update_click_metrics()
            except Exception as e:
                print(f"Error polling click metrics: {e}")
            
            await asyncio.sleep(config.CLICKS_POLL_INTERVAL)
    
    async def _update_engagement_metrics(self):
        session = get_session()
        try:
            posts = session.query(Post).filter(
                Post.status == 'published',
                Post.platform_post_id.isnot(None)
            ).all()
            
            for post in posts:
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
                    
                    snapshot = EngagementSnapshot(
                        post_id=post.id,
                        clicks=post.metrics.get('clicks', 0) if post.metrics else 0,
                        reactions=metrics.get('reactions', 0),
                        comments=metrics.get('comments', 0),
                        shares=metrics.get('shares', 0),
                        views=metrics.get('views', 0),
                        platform_metrics=metrics
                    )
                    
                    previous_metrics = post.metrics or {}
                    previous_reactions = previous_metrics.get('reactions', 0)
                    previous_views = previous_metrics.get('views', 0)
                    
                    new_points = 0
                    
                    if post.platform == 'linkedin':
                        reactions = metrics.get('reactions', 0)
                        if reactions >= 100 and previous_reactions < 100:
                            new_points += config.SCORING.get('linkedin_reactions_100', 0)
                        elif reactions >= 30 and previous_reactions < 30:
                            new_points += config.SCORING.get('linkedin_reactions_30', 0)
                        elif reactions >= 10 and previous_reactions < 10:
                            new_points += config.SCORING.get('linkedin_reactions_10', 0)
                    
                    elif post.platform in ['instagram', 'meta']:
                        views = metrics.get('views', 0)
                        if views >= 2000 and previous_views < 2000:
                            new_points += config.SCORING.get('instagram_views_2000', 0)
                        elif views >= 500 and previous_views < 500:
                            new_points += config.SCORING.get('instagram_views_500', 0)
                        elif views >= 100 and previous_views < 100:
                            new_points += config.SCORING.get('instagram_views_100', 0)
                    
                    elif post.platform == 'tiktok':
                        views = metrics.get('views', 0)
                        if views >= 2000 and previous_views < 2000:
                            new_points += config.SCORING.get('tiktok_views_2000', 0)
                        elif views >= 500 and previous_views < 500:
                            new_points += config.SCORING.get('tiktok_views_500', 0)
                        elif views >= 100 and previous_views < 100:
                            new_points += config.SCORING.get('tiktok_views_100', 0)
                    
                    if new_points > 0:
                        snapshot.points_awarded = new_points
                        post.points_earned += new_points
                        
                        user = session.query(User).filter_by(id=post.user_id).first()
                        if user:
                            user.total_score += new_points
                            user.monthly_score += new_points
                    
                    post.metrics = metrics
                    post.last_metrics_update = datetime.utcnow()
                    
                    session.add(snapshot)
                    session.commit()
                    
                except Exception as e:
                    print(f"Error updating metrics for post {post.id}: {e}")
                    continue
        
        finally:
            session.close()
    
    async def _update_click_metrics(self):
        session = get_session()
        try:
            posts = session.query(Post).filter(
                Post.status == 'published',
                Post.bitly_id.isnot(None)
            ).all()
            
            for post in posts:
                try:
                    click_data = await shortener.get_click_metrics(post.bitly_id)
                    clicks = click_data.get('clicks', 0)
                    
                    previous_clicks = post.metrics.get('clicks', 0) if post.metrics else 0
                    
                    if clicks > previous_clicks:
                        click_diff = clicks - previous_clicks
                        new_points = (click_diff // 10) * config.SCORING.get('clicks_per_10', 0)
                        
                        if new_points > 0:
                            post.points_earned += new_points
                            
                            user = session.query(User).filter_by(id=post.user_id).first()
                            if user:
                                user.total_score += new_points
                                user.monthly_score += new_points
                        
                        metrics = post.metrics or {}
                        metrics['clicks'] = clicks
                        post.metrics = metrics
                        post.last_metrics_update = datetime.utcnow()
                        
                        session.commit()
                
                except Exception as e:
                    print(f"Error updating clicks for post {post.id}: {e}")
                    continue
        
        finally:
            session.close()

engagement_worker = EngagementWorker()
