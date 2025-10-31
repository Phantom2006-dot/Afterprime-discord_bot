from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime, timedelta
import config
from database import get_session, SocialAccount, User
from encryption import encrypt_token
from platforms import get_platform
import uvicorn
import asyncio

app = FastAPI()

oauth_states = {}

@app.get("/")
async def root():
    return {
        "message": "Social Army OAuth Server Running - Multi-Platform Support",
        "base_url": config.BASE_URL,
        "linkedin_redirect_uri": config.LINKEDIN_REDIRECT_URI
    }

@app.get("/oauth/{platform}/start")
async def oauth_start(platform: str, discord_id: str):
    try:
        platform_adapter = get_platform(platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    state = f"{platform}_{discord_id}_{datetime.utcnow().timestamp()}"
    oauth_states[state] = {'discord_id': discord_id, 'platform': platform}
    
    auth_url = platform_adapter.get_auth_url(state)
    return RedirectResponse(url=auth_url)

@app.get("/oauth/{platform}/callback")
async def oauth_callback(platform: str, code: str, state: str):
    if state not in oauth_states:
        return render_error("Invalid state parameter")
    
    state_data = oauth_states.pop(state)
    discord_id = state_data['discord_id']
    
    try:
        platform_adapter = get_platform(platform)
    except ValueError as e:
        return render_error(str(e))
    
    try:
        token_data = await platform_adapter.exchange_code_for_token(code)
        
        if 'access_token' not in token_data:
            return render_error(f"Failed to obtain access token: {token_data}")
        
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in', 5184000)
        scopes = token_data.get('scope', '').split(',') if token_data.get('scope') else config.PLATFORM_SCOPES.get(platform, [])
        
        profile_data = await platform_adapter.get_user_profile(access_token)
        platform_user_id = profile_data.get('id') or profile_data.get('data', {}).get('user', {}).get('open_id')
        
        platform_metadata = {}
        if platform in ['meta', 'instagram']:
            instagram_accounts = profile_data.get('instagram_accounts', [])
            if instagram_accounts:
                platform_metadata['instagram_accounts'] = instagram_accounts
        
        session = get_session()
        try:
            user = session.query(User).filter_by(discord_id=discord_id).first()
            if not user:
                user = User(discord_id=discord_id)
                session.add(user)
                session.commit()
            
            social_account = session.query(SocialAccount).filter_by(
                user_id=user.id,
                platform=platform
            ).first()
            
            if social_account:
                social_account.access_token = encrypt_token(access_token)
                social_account.refresh_token = encrypt_token(refresh_token) if refresh_token else None
                social_account.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                social_account.scopes = scopes
                social_account.profile_data = profile_data
                social_account.platform_metadata = platform_metadata
                social_account.is_active = True
            else:
                social_account = SocialAccount(
                    user_id=user.id,
                    platform=platform,
                    platform_user_id=platform_user_id,
                    access_token=encrypt_token(access_token),
                    refresh_token=encrypt_token(refresh_token) if refresh_token else None,
                    token_expiry=datetime.utcnow() + timedelta(seconds=expires_in),
                    scopes=scopes,
                    profile_data=profile_data,
                    platform_metadata=platform_metadata,
                    is_active=True
                )
                session.add(social_account)
            
            session.commit()
            
            return render_success(platform)
        finally:
            session.close()
    except Exception as e:
        return render_error(f"OAuth error: {str(e)}")

def render_success(platform: str):
    platform_colors = {
        'linkedin': '#0077b5',
        'meta': '#1877f2',
        'instagram': '#E4405F',
        'tiktok': '#000000'
    }
    platform_names = {
        'linkedin': 'LinkedIn',
        'meta': 'Facebook/Instagram',
        'instagram': 'Instagram',
        'tiktok': 'TikTok'
    }
    
    color = platform_colors.get(platform, '#667eea')
    name = platform_names.get(platform, platform.title())
    
    return HTMLResponse(content=f"""
        <html>
            <head>
                <title>{name} Connected!</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 500px;
                    }}
                    h1 {{
                        color: {color};
                        margin-bottom: 20px;
                    }}
                    p {{
                        color: #333;
                        line-height: 1.6;
                    }}
                    .success {{
                        color: #10b981;
                        font-size: 48px;
                        margin-bottom: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success">✅</div>
                    <h1>{name} Connected Successfully!</h1>
                    <p>Your {name} account has been connected to Social Army.</p>
                    <p>You can now close this window and return to Discord to start posting missions!</p>
                </div>
            </body>
        </html>
    """)

def render_error(error_message: str):
    return HTMLResponse(content=f"""
        <html>
            <head>
                <title>Connection Error</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 500px;
                    }}
                    h1 {{
                        color: #ef4444;
                        margin-bottom: 20px;
                    }}
                    p {{
                        color: #333;
                        line-height: 1.6;
                        word-break: break-word;
                    }}
                    .error {{
                        color: #ef4444;
                        font-size: 48px;
                        margin-bottom: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error">❌</div>
                    <h1>Connection Failed</h1>
                    <p>{error_message}</p>
                    <p>Please try again or contact support if the issue persists.</p>
                </div>
            </body>
        </html>
    """, status_code=400)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
