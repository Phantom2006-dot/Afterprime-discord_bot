import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import config
from database import get_session, User, Mission, Post, SocialAccount
import aiohttp
from encryption import encrypt_token, decrypt_token

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@bot.tree.command(name="connect", description="Connect your social media accounts")
async def connect(interaction: discord.Interaction):
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
        
        oauth_url = f"http://localhost:8000/oauth/linkedin/start?discord_id={interaction.user.id}"
        
        embed = discord.Embed(
            title="🔗 Connect Your LinkedIn Account",
            description="Click the button below to connect your LinkedIn account to Social Army!",
            color=discord.Color.blue()
        )
        embed.add_field(name="Step 1", value="Click 'Connect LinkedIn' below", inline=False)
        embed.add_field(name="Step 2", value="Authorize the app on LinkedIn", inline=False)
        embed.add_field(name="Step 3", value="You'll be redirected back automatically", inline=False)
        
        view = discord.ui.View()
        button = discord.ui.Button(label="Connect LinkedIn", style=discord.ButtonStyle.link, url=oauth_url)
        view.add_item(button)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    finally:
        session.close()

@bot.tree.command(name="missions", description="View active missions")
async def missions(interaction: discord.Interaction):
    session = get_session()
    try:
        active_missions = session.query(Mission).filter_by(status='active').all()
        
        if not active_missions:
            await interaction.response.send_message("No active missions right now. Check back soon!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎯 Active Missions",
            description=f"Found {len(active_missions)} active mission(s)",
            color=discord.Color.green()
        )
        
        for mission in active_missions[:5]:
            end_info = f"Ends: {mission.end_date.strftime('%Y-%m-%d')}" if mission.end_date else "No end date"
            platforms = ", ".join(mission.platforms) if mission.platforms else "All platforms"
            embed.add_field(
                name=f"Mission #{mission.id}: {mission.title}",
                value=f"{mission.description[:100]}...\n**Platforms:** {platforms}\n**{end_info}**",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    finally:
        session.close()

@bot.tree.command(name="post", description="Post a mission to your social media")
@app_commands.describe(mission_id="The ID of the mission to post")
async def post_mission(interaction: discord.Interaction, mission_id: int):
    session = get_session()
    try:
        user = session.query(User).filter_by(discord_id=str(interaction.user.id)).first()
        if not user:
            await interaction.response.send_message("Please run `/connect` first to set up your account!", ephemeral=True)
            return
        
        linkedin_account = session.query(SocialAccount).filter_by(
            user_id=user.id, 
            platform='linkedin'
        ).first()
        
        if not linkedin_account:
            await interaction.response.send_message("Please connect your LinkedIn account first using `/connect`!", ephemeral=True)
            return
        
        mission = session.query(Mission).filter_by(id=mission_id).first()
        if not mission:
            await interaction.response.send_message(f"Mission #{mission_id} not found!", ephemeral=True)
            return
        
        if mission.status != 'active':
            await interaction.response.send_message("This mission is no longer active!", ephemeral=True)
            return
        
        existing_post = session.query(Post).filter_by(
            user_id=user.id,
            mission_id=mission.id,
            platform='linkedin'
        ).first()
        
        if existing_post:
            await interaction.response.send_message("You've already posted this mission!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📝 Mission Preview",
            description=mission.content,
            color=discord.Color.blue()
        )
        embed.add_field(name="Mission", value=mission.title, inline=False)
        embed.set_footer(text="Click 'Confirm & Post' to publish to LinkedIn")
        
        view = ConfirmPostView(mission, user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
    finally:
        session.close()

class ConfirmPostView(discord.ui.View):
    def __init__(self, mission, user):
        super().__init__(timeout=300)
        self.mission = mission
        self.user = user
    
    @discord.ui.button(label="Confirm & Post", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        db_session = get_session()
        try:
            linkedin_account = db_session.query(SocialAccount).filter_by(
                user_id=self.user.id,
                platform='linkedin'
            ).first()
            
            access_token = decrypt_token(linkedin_account.access_token)
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    'https://api.linkedin.com/v2/ugcPosts',
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json',
                        'X-Restli-Protocol-Version': '2.0.0'
                    },
                    json={
                        'author': f'urn:li:person:{linkedin_account.platform_user_id}',
                        'lifecycleState': 'PUBLISHED',
                        'specificContent': {
                            'com.linkedin.ugc.ShareContent': {
                                'shareCommentary': {
                                    'text': self.mission.content
                                },
                                'shareMediaCategory': 'NONE'
                            }
                        },
                        'visibility': {
                            'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
                        }
                    }
                ) as response:
                    if response.status == 201:
                        post_data = await response.json()
                        post_id = post_data.get('id', 'unknown')
                        
                        was_on_time = (datetime.utcnow() - self.mission.start_date) <= timedelta(hours=24)
                        points = config.SCORING['publish_success']
                        if was_on_time:
                            points += config.SCORING['on_time_bonus']
                        
                        new_post = Post(
                            user_id=self.user.id,
                            mission_id=self.mission.id,
                            platform='linkedin',
                            platform_post_id=post_id,
                            was_on_time=was_on_time,
                            points_earned=points
                        )
                        db_session.add(new_post)
                        
                        user = db_session.query(User).filter_by(id=self.user.id).first()
                        user.total_score += points
                        user.monthly_score += points
                        
                        await update_user_role(interaction.user, user.total_score)
                        
                        db_session.commit()
                        
                        success_embed = discord.Embed(
                            title="✅ Mission Posted Successfully!",
                            description=f"Your post has been published to LinkedIn!",
                            color=discord.Color.green()
                        )
                        success_embed.add_field(name="Points Earned", value=f"+{points} points", inline=True)
                        success_embed.add_field(name="Total Score", value=f"{user.total_score} points", inline=True)
                        
                        await interaction.followup.send(embed=success_embed, ephemeral=True)
                    else:
                        error_text = await response.text()
                        await interaction.followup.send(f"Failed to post to LinkedIn. Error: {error_text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"Error posting to LinkedIn: {str(e)}", ephemeral=True)
        finally:
            db_session.close()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Post cancelled.", ephemeral=True)

@bot.tree.command(name="score", description="Check your current score")
async def score(interaction: discord.Interaction):
    session = get_session()
    try:
        user = session.query(User).filter_by(discord_id=str(interaction.user.id)).first()
        
        if not user:
            await interaction.response.send_message("You haven't joined Social Army yet! Use `/connect` to get started.", ephemeral=True)
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
        
        await interaction.response.send_message(embed=embed)
    finally:
        session.close()

@bot.tree.command(name="leaderboard", description="View the top performers")
async def leaderboard(interaction: discord.Interaction):
    session = get_session()
    try:
        top_users = session.query(User).order_by(User.monthly_score.desc()).limit(10).all()
        
        if not top_users:
            await interaction.response.send_message("No one on the leaderboard yet!", ephemeral=True)
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
        
        await interaction.response.send_message(embed=embed)
    finally:
        session.close()

@bot.tree.command(name="rolesync", description="Sync your Discord role based on your score")
async def rolesync(interaction: discord.Interaction):
    session = get_session()
    try:
        user = session.query(User).filter_by(discord_id=str(interaction.user.id)).first()
        
        if not user:
            await interaction.response.send_message("You haven't joined Social Army yet!", ephemeral=True)
            return
        
        await update_user_role(interaction.user, user.total_score)
        await interaction.response.send_message(f"Your role has been synced! Current rank: **{user.current_role}**", ephemeral=True)
    finally:
        session.close()

@bot.tree.command(name="mission", description="[ADMIN] Manage missions")
@app_commands.describe(action="Action to perform (new/close)", mission_id="Mission ID (for close)")
async def mission_admin(interaction: discord.Interaction, action: str, mission_id: int = None):
    if not any(role.name == config.ADMIN_ROLE_NAME for role in interaction.user.roles):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    if action == "new":
        modal = MissionModal()
        await interaction.response.send_modal(modal)
    elif action == "close":
        if not mission_id:
            await interaction.response.send_message("Please provide a mission_id to close!", ephemeral=True)
            return
        
        session = get_session()
        try:
            mission = session.query(Mission).filter_by(id=mission_id).first()
            if mission:
                mission.status = 'closed'
                session.commit()
                await interaction.response.send_message(f"Mission #{mission_id} has been closed!", ephemeral=True)
            else:
                await interaction.response.send_message(f"Mission #{mission_id} not found!", ephemeral=True)
        finally:
            session.close()
    else:
        await interaction.response.send_message("Invalid action! Use 'new' or 'close'", ephemeral=True)

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
            
            await interaction.response.send_message(f"Mission #{mission.id} created successfully!", ephemeral=True)
        finally:
            session.close()

async def update_user_role(discord_user, total_score):
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
