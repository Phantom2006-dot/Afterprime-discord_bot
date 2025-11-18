import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime
from sqlalchemy import func
import config
from database import get_session, SocialScore, SocialMessageScore

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

def get_current_month_key():
    """Get current month in YYYY-MM format"""
    return datetime.utcnow().strftime('%Y-%m')

def is_judge(member: discord.Member) -> bool:
    """Check if user has Social Army Judge role"""
    return any(role.name == config.SOCIAL_ARMY_JUDGE_ROLE_NAME for role in member.roles)

def is_admin(member: discord.Member) -> bool:
    """Check if user has admin role"""
    return any(role.name == config.ADMIN_ROLE_NAME for role in member.roles)

def is_owner(user_id: int, guild: discord.Guild) -> bool:
    """Check if user is server owner"""
    return guild.owner_id == user_id

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Social Army - Reaction-Based Scoring System')
    print(f'Monitoring channel ID: {config.SOCIAL_ARMY_CHANNEL_ID}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    """Handle reactions added to messages in the social army channel"""
    if user.bot:
        return
    
    if reaction.message.channel.id != config.SOCIAL_ARMY_CHANNEL_ID:
        return
    
    if reaction.message.author.bot:
        return
    
    emoji_str = str(reaction.emoji)
    
    if emoji_str not in config.EMOJI_POINTS:
        return
    
    member = reaction.message.guild.get_member(user.id)
    if not member:
        return
    
    if not is_judge(member):
        await reaction.remove(user)
        return
    
    if emoji_str in config.OWNER_ONLY_EMOJIS and not is_owner(user.id, reaction.message.guild):
        await reaction.remove(user)
        return
    
    points = config.EMOJI_POINTS[emoji_str]
    month_key = get_current_month_key()
    author_id = str(reaction.message.author.id)
    judge_id = str(user.id)
    message_id = reaction.message.id
    
    session = get_session()
    try:
        existing_score = session.query(SocialMessageScore).filter_by(
            message_id=message_id,
            judge_id=judge_id,
            emoji=emoji_str
        ).first()
        
        if existing_score:
            return
        
        message_score = SocialMessageScore(
            message_id=message_id,
            author_id=author_id,
            judge_id=judge_id,
            emoji=emoji_str,
            points=points,
            month_key=month_key
        )
        session.add(message_score)
        
        user_score = session.query(SocialScore).filter_by(
            discord_id=author_id,
            month_key=month_key
        ).first()
        
        if not user_score:
            user_score = SocialScore(
                discord_id=author_id,
                discord_username=str(reaction.message.author),
                month_key=month_key,
                points=points
            )
            session.add(user_score)
        else:
            user_score.points += points
            user_score.discord_username = str(reaction.message.author)
        
        session.commit()
        print(f"✅ Added {points} points to {reaction.message.author} for {emoji_str} from {user.name}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error adding reaction score: {e}")
    finally:
        session.close()

@bot.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.User):
    """Handle reactions removed from messages in the social army channel"""
    if user.bot:
        return
    
    if reaction.message.channel.id != config.SOCIAL_ARMY_CHANNEL_ID:
        return
    
    if reaction.message.author.bot:
        return
    
    emoji_str = str(reaction.emoji)
    
    if emoji_str not in config.EMOJI_POINTS:
        return
    
    author_id = str(reaction.message.author.id)
    judge_id = str(user.id)
    message_id = reaction.message.id
    
    session = get_session()
    try:
        message_score = session.query(SocialMessageScore).filter_by(
            message_id=message_id,
            judge_id=judge_id,
            emoji=emoji_str
        ).first()
        
        if message_score:
            points = message_score.points
            score_month_key = message_score.month_key
            
            user_score = session.query(SocialScore).filter_by(
                discord_id=author_id,
                month_key=score_month_key
            ).first()
            
            if user_score:
                user_score.points -= points
            
            session.delete(message_score)
            session.commit()
            print(f"✅ Removed {points} points from {reaction.message.author} for {emoji_str} by {user.name}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error removing reaction score: {e}")
    finally:
        session.close()

@bot.event
async def on_message_delete(message: discord.Message):
    """Handle message deletion - remove all associated points"""
    if message.channel.id != config.SOCIAL_ARMY_CHANNEL_ID:
        return
    
    if message.author.bot:
        return
    
    session = get_session()
    try:
        message_scores = session.query(SocialMessageScore).filter_by(
            message_id=message.id
        ).all()
        
        if not message_scores:
            return
        
        author_id = str(message.author.id)
        
        points_by_month = {}
        for score in message_scores:
            points_by_month[score.month_key] = points_by_month.get(score.month_key, 0) + score.points
        
        for month_key, total_points in points_by_month.items():
            user_score = session.query(SocialScore).filter_by(
                discord_id=author_id,
                month_key=month_key
            ).first()
            
            if user_score:
                user_score.points -= total_points
        
        for score in message_scores:
            session.delete(score)
        
        session.commit()
        print(f"✅ Removed points from {message.author} across {len(points_by_month)} month(s) due to message deletion")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error handling message deletion: {e}")
    finally:
        session.close()

@bot.tree.command(name="social-leaderboard", description="View the monthly Social Army leaderboard")
async def social_leaderboard(interaction: discord.Interaction):
    """Display monthly leaderboard"""
    await interaction.response.defer()
    
    month_key = get_current_month_key()
    session = get_session()
    
    try:
        top_users = session.query(SocialScore).filter_by(
            month_key=month_key
        ).order_by(SocialScore.points.desc()).limit(config.LEADERBOARD_SIZE).all()
        
        if not top_users:
            await interaction.followup.send("No scores yet this month! Start posting in the Social Army channel!")
            return
        
        month_name = datetime.utcnow().strftime('%B %Y')
        embed = discord.Embed(
            title=f"🏆 Social Army Leaderboard - {month_name}",
            description="Top contributors this month:",
            color=discord.Color.gold()
        )
        
        medals = ['🥇', '🥈', '🥉']
        for idx, user in enumerate(top_users, 1):
            medal = medals[idx-1] if idx <= 3 else f"#{idx}"
            try:
                member = await interaction.guild.fetch_member(int(user.discord_id))
                username = member.display_name
            except:
                username = user.discord_username or f"User {user.discord_id}"
            
            embed.add_field(
                name=f"{medal} {username}",
                value=f"**{user.points}** points",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")
    finally:
        session.close()

@bot.tree.command(name="social-stats", description="View statistics for a user")
@app_commands.describe(user="The user to check stats for (leave empty for yourself)")
async def social_stats(interaction: discord.Interaction, user: discord.Member = None):
    """Display user statistics"""
    await interaction.response.defer()
    
    target_user = user or interaction.user
    month_key = get_current_month_key()
    session = get_session()
    
    try:
        user_score = session.query(SocialScore).filter_by(
            discord_id=str(target_user.id),
            month_key=month_key
        ).first()
        
        if not user_score or user_score.points == 0:
            await interaction.followup.send(f"{target_user.display_name} has no points this month yet!")
            return
        
        rank = session.query(SocialScore).filter(
            SocialScore.month_key == month_key,
            SocialScore.points > user_score.points
        ).count() + 1
        
        message_scores = session.query(SocialMessageScore).filter_by(
            author_id=str(target_user.id),
            month_key=month_key
        ).all()
        
        emoji_breakdown = {}
        for score in message_scores:
            emoji_breakdown[score.emoji] = emoji_breakdown.get(score.emoji, 0) + score.points
        
        month_name = datetime.utcnow().strftime('%B %Y')
        embed = discord.Embed(
            title=f"📊 Stats for {target_user.display_name}",
            description=f"Month: {month_name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Total Points", value=f"**{user_score.points}**", inline=True)
        embed.add_field(name="Rank", value=f"**#{rank}**", inline=True)
        embed.add_field(name="Reactions Received", value=f"**{len(message_scores)}**", inline=True)
        
        if emoji_breakdown:
            breakdown_text = "\n".join([f"{emoji}: {pts} pts" for emoji, pts in sorted(emoji_breakdown.items(), key=lambda x: x[1], reverse=True)])
            embed.add_field(name="Points by Category", value=breakdown_text, inline=False)
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")
    finally:
        session.close()

@bot.tree.command(name="social-config", description="View Social Army configuration")
async def social_config(interaction: discord.Interaction):
    """Display current configuration"""
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(
        title="⚙️ Social Army Configuration",
        color=discord.Color.blue()
    )
    
    channel = bot.get_channel(config.SOCIAL_ARMY_CHANNEL_ID)
    channel_name = f"#{channel.name}" if channel else f"ID: {config.SOCIAL_ARMY_CHANNEL_ID}"
    
    embed.add_field(name="Social Army Channel", value=channel_name, inline=False)
    embed.add_field(name="Judge Role", value=config.SOCIAL_ARMY_JUDGE_ROLE_NAME, inline=True)
    embed.add_field(name="Elite Role", value=config.SOCIAL_ARMY_ELITE_ROLE_NAME, inline=True)
    embed.add_field(name="Leaderboard Size", value=str(config.LEADERBOARD_SIZE), inline=True)
    
    effort_emojis = "✍️ (1pt), 🎨 (3pt), 🎬 (5pt), 🎞️ (8pt)"
    creativity_emojis = "💡 (2pt), 🤯 (4pt)"
    reach_emojis = "📊 (2pt), 🔥 (4pt), 🚀 (8pt)"
    consistency_emojis = "🧡 (2pt), 💪 (3pt)"
    bonus_emojis = "🏅 (5pt), 👑 (10pt - Owner only)"
    
    embed.add_field(name="Effort", value=effort_emojis, inline=False)
    embed.add_field(name="Creativity", value=creativity_emojis, inline=False)
    embed.add_field(name="Reach", value=reach_emojis, inline=False)
    embed.add_field(name="Consistency", value=consistency_emojis, inline=False)
    embed.add_field(name="Bonus", value=bonus_emojis, inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="social-reset", description="[ADMIN] Reset monthly scores and announce winners")
async def social_reset(interaction: discord.Interaction):
    """Reset monthly scores (admin only)"""
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    month_key = get_current_month_key()
    month_name = datetime.utcnow().strftime('%B %Y')
    session = get_session()
    
    try:
        top_users = session.query(SocialScore).filter_by(
            month_key=month_key
        ).order_by(SocialScore.points.desc()).limit(3).all()
        
        winners_announced = False
        if top_users:
            embed = discord.Embed(
                title=f"🎉 {month_name} Winners!",
                description="Congratulations to our top Social Army contributors!",
                color=discord.Color.gold()
            )
            
            medals = ['🥇', '🥈', '🥉']
            for idx, user in enumerate(top_users):
                try:
                    member = await interaction.guild.fetch_member(int(user.discord_id))
                    username = member.display_name
                except:
                    username = user.discord_username or f"User {user.discord_id}"
                
                embed.add_field(
                    name=f"{medals[idx]} {username}",
                    value=f"**{user.points}** points",
                    inline=False
                )
            
            channel = bot.get_channel(config.SOCIAL_ARMY_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)
                winners_announced = True
        
        score_count = session.query(SocialScore).filter_by(month_key=month_key).delete()
        message_score_count = session.query(SocialMessageScore).filter_by(month_key=month_key).delete()
        session.commit()
        
        message = f"✅ Monthly reset complete! "
        if winners_announced:
            message += f"Winners announced in <#{config.SOCIAL_ARMY_CHANNEL_ID}>. "
        message += f"Deleted {score_count} user scores and {message_score_count} message scores."
        
        await interaction.followup.send(message)
        
    except Exception as e:
        session.rollback()
        await interaction.followup.send(f"❌ Error: {str(e)}")
    finally:
        session.close()

@bot.tree.command(name="social-export", description="[ADMIN] Export top users")
@app_commands.describe(limit="Number of top users to export (default: 10)")
async def social_export(interaction: discord.Interaction, limit: int = 10):
    """Export top users (admin only)"""
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    month_key = get_current_month_key()
    session = get_session()
    
    try:
        top_users = session.query(SocialScore).filter_by(
            month_key=month_key
        ).order_by(SocialScore.points.desc()).limit(limit).all()
        
        if not top_users:
            await interaction.followup.send("No scores to export!", ephemeral=True)
            return
        
        export_text = f"Social Army Leaderboard Export - {datetime.utcnow().strftime('%B %Y')}\n"
        export_text += "=" * 50 + "\n\n"
        
        for idx, user in enumerate(top_users, 1):
            try:
                member = await interaction.guild.fetch_member(int(user.discord_id))
                username = member.display_name
            except:
                username = user.discord_username or f"User {user.discord_id}"
            
            export_text += f"{idx}. {username} - {user.points} points\n"
        
        with open('social_army_export.txt', 'w') as f:
            f.write(export_text)
        
        await interaction.followup.send(
            "✅ Export complete!",
            file=discord.File('social_army_export.txt'),
            ephemeral=True
        )
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    finally:
        session.close()

if __name__ == "__main__":
    bot.run(config.DISCORD_BOT_TOKEN)
