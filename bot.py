import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import config
from database import get_session, User, Mission, Post, SocialAccount
import aiohttp
from encryption import encrypt_token, decrypt_token
from publishing_service import publishing_service
import os
import traceback

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Multi-Platform Support: LinkedIn, Instagram/Meta, TikTok')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

class PlatformSelect(discord.ui.Select):
    def __init__(self, user_id: str):
        self.user_id = user_id
        options = [
            discord.SelectOption(label="LinkedIn", description="Connect your LinkedIn account", emoji="💼"),
            discord.SelectOption(label="Instagram/Meta", description="Connect Instagram Business account", emoji="📸"),
            discord.SelectOption(label="TikTok", description="Connect your TikTok account", emoji="🎵")
        ]
        super().__init__(placeholder="Choose a platform to connect...", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        platform = self.values[0].lower().replace("/", "").replace("instagram", "meta")
        base_url = os.getenv('BASE_URL', config.BASE_URL)
        oauth_url = f"{base_url}/oauth/{platform}/start?discord_id={self.user_id}"
        
        embed = discord.Embed(
            title=f"🔗 Connect {self.values[0]}",
            description=f"Click the button below to connect your {self.values[0]} account!",
            color=discord.Color.blue()
        )
        
        view = discord.ui.View()
        button = discord.ui.Button(label=f"Connect {self.values[0]}", style=discord.ButtonStyle.link, url=oauth_url)
        view.add_item(button)
        
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="connect", description="Connect your social media accounts (LinkedIn, Instagram, TikTok)")
async def connect(interaction: discord.Interaction):
    """Connect social media accounts - IMMEDIATE RESPONSE"""
    try:
        # Immediate response to prevent timeout
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        session = get_session()
        try:
            user = session.query(User).filter_by(discord_id=str(interaction.user.id)).first()
            if not user:
                user = User(
                    discord_id=str(interaction.user.id),
                    discord_username=str(interaction.user)
                )
                session.add(user)
                session.commit()
            
            connected_accounts = session.query(SocialAccount).filter_by(user_id=user.id, is_active=True).all()
            
            embed = discord.Embed(
                title="🌐 Connect Social Media Accounts",
                description="Choose a platform below to connect your account. You can connect multiple platforms!",
                color=discord.Color.blue()
            )
            
            if connected_accounts:
                connected_list = "\n".join([f"✅ {acc.platform.title()}" for acc in connected_accounts])
                embed.add_field(name="Connected Accounts", value=connected_list, inline=False)
            
            embed.add_field(
                name="Supported Platforms", 
                value="• LinkedIn (Personal/Company)\n• Instagram (Business accounts only)\n• TikTok", 
                inline=False
            )
            
            view = discord.ui.View()
            view.add_item(PlatformSelect(str(interaction.user.id)))
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            session.close()
            
    except Exception as e:
        # Fallback response if defer fails
        try:
            await interaction.response.send_message("❌ Command failed. Please try again.", ephemeral=True)
        except:
            pass

@bot.tree.command(name="missions", description="View active missions")
async def missions(interaction: discord.Interaction):
    """View active missions - IMMEDIATE RESPONSE"""
    try:
        await interaction.response.defer(ephemeral=False, thinking=True)
        
        session = get_session()
        try:
            active_missions = session.query(Mission).filter_by(status='active').all()
            
            if not active_missions:
                await interaction.followup.send("No active missions right now. Check back soon!", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🎯 Active Missions",
                description=f"Found {len(active_missions)} active mission(s)",
                color=discord.Color.green()
            )
            
            for mission in active_missions[:5]:  # Limit to 5 missions
                end_info = f"Ends: {mission.end_date.strftime('%Y-%m-%d')}" if mission.end_date else "No end date"
                platforms = ", ".join(mission.platforms) if mission.platforms else "All platforms"
                embed.add_field(
                    name=f"Mission #{mission.id}: {mission.title}",
                    value=f"{mission.description[:100]}...\n**Platforms:** {platforms}\n**{end_info}**",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Error loading missions: {str(e)}", ephemeral=True)
        finally:
            session.close()
            
    except Exception as e:
        try:
            await interaction.response.send_message("❌ Command failed. Please try again.", ephemeral=True)
        except:
            pass

class PostPlatformSelect(discord.ui.Select):
    def __init__(self, mission, user, available_platforms):
        self.mission = mission
        self.user = user
        options = []
        
        platform_emojis = {'linkedin': '💼', 'meta': '📸', 'instagram': '📸', 'tiktok': '🎵'}
        platform_names = {'linkedin': 'LinkedIn', 'meta': 'Instagram/Meta', 'instagram': 'Instagram/Meta', 'tiktok': 'TikTok'}
        
        for platform in available_platforms:
            options.append(discord.SelectOption(
                label=platform_names.get(platform, platform.title()),
                description=f"Post to {platform_names.get(platform, platform.title())}",
                value=platform,
                emoji=platform_emojis.get(platform, '📱')
            ))
        
        super().__init__(placeholder="Choose platform to post...", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        platform = self.values[0]
        
        embed = discord.Embed(
            title="📝 Mission Preview",
            description=self.mission.content,
            color=discord.Color.blue()
        )
        embed.add_field(name="Mission", value=self.mission.title, inline=False)
        embed.add_field(name="Platform", value=platform.title(), inline=True)
        embed.set_footer(text=f"Click 'Confirm & Post' to publish to {platform.title()}")
        
        view = ConfirmPostView(self.mission, self.user, platform)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="post", description="Post a mission to your social media")
@app_commands.describe(mission_id="The ID of the mission to post")
async def post_mission(interaction: discord.Interaction, mission_id: int):
    """Post mission - IMMEDIATE RESPONSE"""
    try:
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        session = get_session()
        try:
            user = session.query(User).filter_by(discord_id=str(interaction.user.id)).first()
            if not user:
                await interaction.followup.send("Please run `/connect` first to set up your account!", ephemeral=True)
                return
            
            mission = session.query(Mission).filter_by(id=mission_id).first()
            if not mission:
                await interaction.followup.send(f"Mission #{mission_id} not found!", ephemeral=True)
                return
            
            if mission.status != 'active':
                await interaction.followup.send("This mission is no longer active!", ephemeral=True)
                return
            
            connected_accounts = session.query(SocialAccount).filter_by(
                user_id=user.id,
                is_active=True
            ).all()
            
            if not connected_accounts:
                await interaction.followup.send("Please connect at least one social account first using `/connect`!", ephemeral=True)
                return
            
            mission_platforms = mission.platforms if mission.platforms else []
            connected_platforms = [acc.platform for acc in connected_accounts]
            
            available_platforms = [p for p in connected_platforms if not mission_platforms or p in mission_platforms]
            
            if not available_platforms:
                await interaction.followup.send(
                    f"You don't have any connected accounts for this mission's platforms: {', '.join(mission_platforms)}", 
                    ephemeral=True
                )
                return
            
            if len(available_platforms) == 1:
                platform = available_platforms[0]
                existing_post = session.query(Post).filter_by(
                    user_id=user.id,
                    mission_id=mission.id,
                    platform=platform
                ).first()
                
                if existing_post and existing_post.status == 'published':
                    await interaction.followup.send(f"You've already posted this mission to {platform.title()}!", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="📝 Mission Preview",
                    description=mission.content,
                    color=discord.Color.blue()
                )
                embed.add_field(name="Mission", value=mission.title, inline=False)
                embed.add_field(name="Platform", value=platform.title(), inline=True)
                embed.set_footer(text=f"Click 'Confirm & Post' to publish to {platform.title()}")
                
                view = ConfirmPostView(mission, user, platform)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="🌐 Choose Platform",
                    description=f"Select which platform to post **{mission.title}** to:",
                    color=discord.Color.blue()
                )
                
                view = discord.ui.View()
                view.add_item(PostPlatformSelect(mission, user, available_platforms))
                
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            session.close()
    
    except Exception as e:
        try:
            await interaction.response.send_message("❌ Command failed. Please try again.", ephemeral=True)
        except:
            pass

class ConfirmPostView(discord.ui.View):
    def __init__(self, mission, user, platform):
        super().__init__(timeout=300)
        self.mission = mission
        self.user = user
        self.platform = platform
    
    @discord.ui.button(label="Confirm & Post", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            result = await publishing_service.publish_mission(
                discord_id=str(interaction.user.id),
                mission_id=self.mission.id,
                platform=self.platform
            )
            
            if result['status'] == 'success':
                db_session = get_session()
                try:
                    user = db_session.query(User).filter_by(id=self.user.id).first()
                    await update_user_role(interaction.user, user.total_score)
                finally:
                    db_session.close()
                
                success_embed = discord.Embed(
                    title="✅ Mission Posted Successfully!",
                    description=f"Your post has been published to {self.platform.title()}!",
                    color=discord.Color.green()
                )
                success_embed.add_field(name="Points Earned", value=f"+{result['points_earned']} points", inline=True)
                
                if result.get('post_url'):
                    success_embed.add_field(name="View Post", value=f"[Click here]({result['post_url']})", inline=True)
                
                await interaction.followup.send(embed=success_embed, ephemeral=True)
            else:
                error_embed = discord.Embed(
                    title="❌ Posting Failed",
                    description=result.get('message', 'Unknown error occurred'),
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
        
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Posting Failed",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Post cancelled.", ephemeral=True)

@bot.tree.command(name="score", description="Check your current score")
async def score(interaction: discord.Interaction):
    """Check score - IMMEDIATE RESPONSE"""
    try:
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        session = get_session()
        try:
            user = session.query(User).filter_by(discord_id=str(interaction.user.id)).first()
            
            if not user:
                await interaction.followup.send("You haven't joined Social Army yet! Use `/connect` to get started.", ephemeral=True)
                return
            
            posts_count = session.query(Post).filter_by(user_id=user.id).count()
            
            embed = discord.Embed(
                title=f"📊 Score for {interaction.user.display_name}",
                color=discord.Color.gold()
            )
            embed.add_field(name="Total Score", value=f"{user.total_score} points", inline=True)
            embed.add_field(name="Monthly Score", value=f"{user.monthly_score} points", inline=True)
            embed.add_field(name="Current Rank", value=user.current_role, inline=True)
            embed.add_field(name="Missions Completed", value=str(posts_count), inline=True)
            
            next_role, points_needed = get_next_role(user.total_score)
            if next_role:
                embed.add_field(name="Next Rank", value=f"{next_role} ({points_needed} points needed)", inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error loading score: {str(e)}", ephemeral=True)
        finally:
            session.close()
            
    except Exception as e:
        try:
            await interaction.response.send_message("❌ Command failed. Please try again.", ephemeral=True)
        except:
            pass

@bot.tree.command(name="leaderboard", description="View the top performers")
async def leaderboard(interaction: discord.Interaction):
    """Leaderboard - IMMEDIATE RESPONSE"""
    try:
        await interaction.response.defer(ephemeral=False, thinking=True)
        
        session = get_session()
        try:
            top_users = session.query(User).order_by(User.monthly_score.desc()).limit(10).all()
            
            if not top_users:
                await interaction.followup.send("No one on the leaderboard yet!", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🏆 Social Army Leaderboard",
                description="Top 10 performers this month",
                color=discord.Color.gold()
            )
            
            medals = ["🥇", "🥈", "🥉"]
            for idx, user in enumerate(top_users, 1):
                medal = medals[idx-1] if idx <= 3 else f"**{idx}.**"
                embed.add_field(
                    name=f"{medal} {user.discord_username}",
                    value=f"{user.monthly_score} points | {user.current_role}",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Error loading leaderboard: {str(e)}", ephemeral=True)
        finally:
            session.close()
            
    except Exception as e:
        try:
            await interaction.response.send_message("❌ Command failed. Please try again.", ephemeral=True)
        except:
            pass

@bot.tree.command(name="rolesync", description="Sync your Discord role based on your score")
async def rolesync(interaction: discord.Interaction):
    """Role sync - IMMEDIATE RESPONSE"""
    try:
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        session = get_session()
        try:
            user = session.query(User).filter_by(discord_id=str(interaction.user.id)).first()
            
            if not user:
                await interaction.followup.send("You haven't joined Social Army yet!", ephemeral=True)
                return
            
            await update_user_role(interaction.user, user.total_score)
            await interaction.followup.send(f"Your role has been synced! Current rank: **{user.current_role}**", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error syncing role: {str(e)}", ephemeral=True)
        finally:
            session.close()
            
    except Exception as e:
        try:
            await interaction.response.send_message("❌ Command failed. Please try again.", ephemeral=True)
        except:
            pass

@bot.tree.command(name="reconnect", description="Reconnect your social media accounts if posting fails")
@app_commands.describe(platform="The platform to reconnect (linkedin, meta, tiktok)")
async def reconnect(interaction: discord.Interaction, platform: str):
    """Reconnect social media account if token is revoked"""
    try:
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        session = get_session()
        try:
            user = session.query(User).filter_by(discord_id=str(interaction.user.id)).first()
            if not user:
                await interaction.followup.send("Please run `/connect` first to set up your account!", ephemeral=True)
                return
            
            # Mark the social account as inactive to force reconnection
            social_account = session.query(SocialAccount).filter_by(
                user_id=user.id,
                platform=platform.lower()
            ).first()
            
            if social_account:
                social_account.is_active = False
                session.commit()
                await interaction.followup.send(f"✅ {platform.title()} account marked for reconnection. Please use `/connect` to reconnect.", ephemeral=True)
            else:
                await interaction.followup.send(f"No {platform.title()} account found. Please use `/connect` to connect.", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        finally:
            session.close()
    except Exception as e:
        try:
            await interaction.response.send_message("❌ Command failed. Please try again.", ephemeral=True)
        except:
            pass

# FIXED MISSION COMMAND
@bot.tree.command(name="mission", description="[ADMIN] Manage missions")
@app_commands.choices(action=[
    app_commands.Choice(name="new", value="new"),
    app_commands.Choice(name="close", value="close")
])
@app_commands.describe(
    action="Action to perform",
    mission_id="Mission ID (required for close)"
)
async def mission_admin(interaction: discord.Interaction, action: str, mission_id: int = None):
    """Admin mission management - IMMEDIATE RESPONSE"""
    try:
        # Check admin permissions
        if not any(role.name == config.ADMIN_ROLE_NAME for role in interaction.user.roles):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        if action == "new":
            # Create new mission using modal
            modal = MissionModal()
            await interaction.response.send_modal(modal)
            
        elif action == "close":
            # Close existing mission
            if mission_id is None:
                await interaction.response.send_message("❌ Please provide a mission_id to close! Example: `/mission close mission_id:123`", ephemeral=True)
                return
            
            await interaction.response.defer(ephemeral=True, thinking=True)
            
            session = get_session()
            try:
                mission = session.query(Mission).filter_by(id=mission_id).first()
                if mission:
                    # Store mission title for confirmation message
                    mission_title = mission.title
                    mission.status = 'closed'
                    session.commit()
                    
                    embed = discord.Embed(
                        title="✅ Mission Closed",
                        description=f"**Mission #{mission_id}: {mission_title}** has been closed!",
                        color=discord.Color.orange()
                    )
                    embed.add_field(name="Status", value="🔒 Closed", inline=True)
                    embed.add_field(name="Closed by", value=interaction.user.display_name, inline=True)
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    
                    # Optional: Notify in mission channel
                    if config.MISSION_CHANNEL_ID:
                        try:
                            channel = bot.get_channel(config.MISSION_CHANNEL_ID)
                            if channel:
                                notify_embed = discord.Embed(
                                    title="🔒 Mission Closed",
                                    description=f"**{mission_title}** (Mission #{mission_id}) has been closed.",
                                    color=discord.Color.orange()
                                )
                                notify_embed.set_footer(text=f"Closed by {interaction.user.display_name}")
                                await channel.send(embed=notify_embed)
                        except Exception as e:
                            print(f"Failed to send close notification: {e}")
                    
                else:
                    await interaction.followup.send(f"❌ Mission #{mission_id} not found!", ephemeral=True)
                    
            except Exception as e:
                error_msg = f"❌ Error closing mission: {str(e)}"
                print(f"Mission close error: {traceback.format_exc()}")
                await interaction.followup.send(error_msg, ephemeral=True)
            finally:
                session.close()
        else:
            await interaction.response.send_message("❌ Invalid action! Use 'new' or 'close'", ephemeral=True)
            
    except Exception as e:
        print(f"Mission command error: {traceback.format_exc()}")
        try:
            await interaction.response.send_message("❌ Command failed. Please try again.", ephemeral=True)
        except:
            pass

class MissionModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='Create New Mission')
        self.mission_title = discord.ui.TextInput(label='Mission Title', max_length=200)
        self.description = discord.ui.TextInput(label='Description', style=discord.TextStyle.paragraph)
        self.content = discord.ui.TextInput(label='Post Content', style=discord.TextStyle.paragraph, max_length=1000)
        self.platforms = discord.ui.TextInput(label='Platforms (comma-separated)', placeholder='linkedin,instagram,tiktok')
        
        self.add_item(self.mission_title)
        self.add_item(self.description)
        self.add_item(self.content)
        self.add_item(self.platforms)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        session = get_session()
        try:
            platforms_list = [p.strip() for p in self.platforms.value.split(',')]
            
            mission = Mission(
                title=self.mission_title.value,
                description=self.description.value,
                content=self.content.value,
                platforms=platforms_list,
                created_by=str(interaction.user.id),
                status='active'
            )
            session.add(mission)
            session.commit()
            
            embed = discord.Embed(
                title=f"🎯 New Mission: {mission.title}",
                description=mission.description,
                color=discord.Color.green()
            )
            embed.add_field(name="Content Preview", value=mission.content[:200] + "...", inline=False)
            embed.add_field(name="Platforms", value=", ".join(platforms_list), inline=False)
            embed.add_field(name="Mission ID", value=str(mission.id), inline=False)
            embed.set_footer(text=f"Use /post {mission.id} to participate!")
            
            if config.MISSION_CHANNEL_ID:
                channel = bot.get_channel(config.MISSION_CHANNEL_ID)
                if channel:
                    await channel.send(embed=embed)
            
            await interaction.followup.send(f"Mission #{mission.id} created successfully!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error creating mission: {str(e)}", ephemeral=True)
        finally:
            session.close()

async def update_user_role(discord_user, total_score):
    try:
        guild = bot.get_guild(config.DISCORD_GUILD_ID)
        if not guild:
            return
        
        member = guild.get_member(discord_user.id)
        if not member:
            return
        
        role_mapping = {
            'Warlord': (config.WARLORD_ROLE_ID, config.ROLE_THRESHOLDS['Warlord']),
            'General': (config.GENERAL_ROLE_ID, config.ROLE_THRESHOLDS['General']),
            'Soldier': (config.SOLDIER_ROLE_ID, config.ROLE_THRESHOLDS['Soldier']),
            'Recruit': (config.RECRUIT_ROLE_ID, config.ROLE_THRESHOLDS['Recruit'])
        }
        
        target_role_name = 'Recruit'
        for role_name, (role_id, threshold) in role_mapping.items():
            if total_score >= threshold:
                target_role_name = role_name
                break
        
        session = get_session()
        try:
            user = session.query(User).filter_by(discord_id=str(discord_user.id)).first()
            if user:
                user.current_role = target_role_name
                session.commit()
        finally:
            session.close()
        
        for role_name, (role_id, _) in role_mapping.items():
            if role_id:
                role = guild.get_role(role_id)
                if role:
                    if role_name == target_role_name:
                        if role not in member.roles:
                            await member.add_roles(role)
                    else:
                        if role in member.roles:
                            await member.remove_roles(role)
    except Exception as e:
        print(f"Error updating user role: {e}")

def get_next_role(current_score):
    for role_name in ['Warlord', 'General', 'Soldier']:
        threshold = config.ROLE_THRESHOLDS[role_name]
        if current_score < threshold:
            return role_name, threshold - current_score
    return None, 0

if __name__ == '__main__':
    from database import init_db
    init_db()
    bot.run(config.DISCORD_BOT_TOKEN)                                 
