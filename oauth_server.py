from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime, timedelta
import config
from database import get_session, SocialAccount, User
from encryption import encrypt_token, decrypt_token, test_encryption
from platforms import get_platform
import uvicorn
import asyncio
import traceback

app = FastAPI(title="Social Army OAuth Server")

# Store OAuth states temporarily (in production, use Redis)
oauth_states = {}

@app.get("/")
async def root():
    return {
        "message": "Social Army OAuth Server Running - Multi-Platform Support",
        "status": "healthy",
        "base_url": config.BASE_URL,
        "supported_platforms": ["linkedin", "meta", "tiktok"]
    }

@app.get("/debug/encryption")
async def debug_encryption():
    """Debug endpoint to test encryption system"""
    try:
        test_result = test_encryption()
        return {
            "encryption_test": "passed" if test_result else "failed",
            "encryption_key_set": bool(getattr(config, "ENCRYPTION_KEY", None)),
            "encryption_key_length": len(config.ENCRYPTION_KEY) if config.ENCRYPTION_KEY else 0
        }
    except Exception as e:
        return {
            "encryption_test": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/oauth/{platform}/start")
async def oauth_start(platform: str, request: Request, discord_id: str = None):
    """Start OAuth flow for a platform"""
    if not discord_id:
        return render_error("Discord ID is required")
    
    try:
        platform_adapter = get_platform(platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create state with timestamp for expiration
    state = f"{platform}_{discord_id}_{datetime.utcnow().timestamp()}"
    oauth_states[state] = {
        'discord_id': discord_id, 
        'platform': platform,
        'created_at': datetime.utcnow()
    }
    
    # Clean up old states (older than 1 hour)
    cleanup_old_states()
    
    auth_url = platform_adapter.get_auth_url(state)
    print(f"🔗 Starting OAuth for {platform}, Discord ID: {discord_id}")
    print(f"📍 Redirecting to: {auth_url}")
    
    return RedirectResponse(url=auth_url)

@app.get("/oauth/{platform}/callback")
async def oauth_callback(
    platform: str, 
    request: Request,
    code: str = None, 
    state: str = None,
    error: str = None,
    error_description: str = None
):
    """Handle OAuth callback from platform"""
    print(f"🔄 OAuth callback received for {platform}")
    print(f"📋 Query params: code={code[:20] + '...' if code else 'None'}, state={state}, error={error}")
    
    # Handle OAuth errors from platform
    if error:
        error_msg = f"{platform.title()} OAuth error: {error}"
        if error_description:
            error_msg += f" - {error_description}"
        return render_error(error_msg)
    
    if not code or not state:
        return render_error("Missing code or state parameter")
    
    # Validate state
    if state not in oauth_states:
        print(f"❌ Invalid state: {state}")
        print(f"📝 Available states: {list(oauth_states.keys())}")
        return render_error("Invalid or expired state parameter. Please start the OAuth flow again.")
    
    state_data = oauth_states.pop(state)
    discord_id = state_data['discord_id']
    
    print(f"✅ Valid state found for Discord ID: {discord_id}")
    
    try:
        platform_adapter = get_platform(platform)
    except ValueError as e:
        return render_error(str(e))
    
    try:
        print(f"🔄 Exchanging code for access token...")
        token_data = await platform_adapter.exchange_code_for_token(code)
        
        print(f"📦 Token response: { {k: v for k, v in token_data.items() if 'token' in k.lower()} }")
        
        if 'access_token' not in token_data:
            error_detail = token_data.get('error_description') or token_data.get('error') or 'Unknown error'
            return render_error(f"Failed to obtain access token from {platform}: {error_detail}")
        
        # Extract token information
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in', 5184000)  # Default 60 days
        scopes = token_data.get('scope', '').split() if token_data.get('scope') else config.PLATFORM_SCOPES.get(platform, [])
        
        print(f"✅ Token exchange successful")
        print(f"📝 Scopes: {scopes}")
        
        # Get user profile
        print(f"👤 Getting user profile...")
        profile_data = await platform_adapter.get_user_profile(access_token)
        platform_user_id = (profile_data.get('id') or 
                          profile_data.get('data', {}).get('user', {}).get('open_id') or
                          str(hash(access_token)))  # Fallback
        
        print(f"✅ Profile retrieved, platform user ID: {platform_user_id}")
        
        # Test encryption before proceeding
        try:
            print(f"🔐 Testing encryption with access token...")
            encrypted_test = encrypt_token(access_token)
            decrypted_test = decrypt_token(encrypted_test)
            if decrypted_test == access_token:
                print("✅ Encryption test passed")
            else:
                raise ValueError("Encryption/decryption test failed")
        except Exception as crypto_error:
            print(f"❌ Encryption test failed: {crypto_error}")
            return render_error(f"Encryption system error: {crypto_error}")
        
        # Store in database
        session = get_session()
        try:
            user = session.query(User).filter_by(discord_id=discord_id).first()
            if not user:
                user = User(discord_id=discord_id)
                session.add(user)
                session.commit()
                session.refresh(user)
                print(f"👤 Created new user with ID: {user.id}")
            
            # Prepare platform metadata
            platform_metadata = {}
            if platform == 'meta':
                instagram_accounts = profile_data.get('instagram_accounts', [])
                if instagram_accounts:
                    platform_metadata['instagram_accounts'] = instagram_accounts
                    print(f"📸 Found {len(instagram_accounts)} Instagram accounts")
            
            # Encrypt tokens for storage
            encrypted_access_token = encrypt_token(access_token)
            encrypted_refresh_token = encrypt_token(refresh_token) if refresh_token else None
            
            # Find existing social account or create new
            social_account = session.query(SocialAccount).filter_by(
                user_id=user.id,
                platform=platform
            ).first()
            
            if social_account:
                print(f"📝 Updating existing social account")
                social_account.access_token = encrypted_access_token
                social_account.refresh_token = encrypted_refresh_token
                social_account.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                social_account.scopes = scopes
                social_account.profile_data = profile_data
                social_account.platform_metadata = platform_metadata
                social_account.is_active = True
                social_account.updated_at = datetime.utcnow()
            else:
                print(f"🆕 Creating new social account")
                social_account = SocialAccount(
                    user_id=user.id,
                    platform=platform,
                    platform_user_id=platform_user_id,
                    access_token=encrypted_access_token,
                    refresh_token=encrypted_refresh_token,
                    token_expiry=datetime.utcnow() + timedelta(seconds=expires_in),
                    scopes=scopes,
                    profile_data=profile_data,
                    platform_metadata=platform_metadata,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(social_account)
            
            session.commit()
            print(f"💾 Successfully saved {platform} account for user {discord_id}")
            
            return render_success(platform)
            
        except Exception as db_error:
            session.rollback()
            print(f"❌ Database error: {db_error}")
            return render_error(f"Database error: {str(db_error)}")
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ OAuth processing error: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return render_error(f"OAuth processing error: {str(e)}")

def cleanup_old_states():
    """Clean up OAuth states older than 1 hour"""
    now = datetime.utcnow()
    expired_states = [
        state for state, data in oauth_states.items()
        if now - data['created_at'] > timedelta(hours=1)
    ]
    for state in expired_states:
        del oauth_states[state]
    if expired_states:
        print(f"🧹 Cleaned up {len(expired_states)} expired OAuth states")

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
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>{name} Connected!</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, {color}20 0%, {color}40 100%);
                }}
                .container {{
                    background: white;
                    padding: 50px;
                    border-radius: 15px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                    border-left: 5px solid {color};
                }}
                h1 {{
                    color: {color};
                    margin-bottom: 20px;
                    font-weight: 600;
                }}
                p {{
                    color: #555;
                    line-height: 1.6;
                    margin-bottom: 15px;
                }}
                .success {{
                    color: {color};
                    font-size: 64px;
                    margin-bottom: 25px;
                }}
                .instructions {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-top: 20px;
                    border-left: 3px solid {color};
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✅</div>
                <h1>{name} Connected Successfully!</h1>
                <p>Your {name} account has been successfully connected to Social Army.</p>
                <div class="instructions">
                    <p><strong>You can now close this window and return to Discord.</strong></p>
                    <p>Use the <code>/missions</code> command to see available posting missions!</p>
                </div>
            </div>
            <script>
                // Close window automatically after 5 seconds
                setTimeout(() => {{
                    window.close();
                }}, 5000);
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

def render_error(error_message: str):
    print(f"🎯 Rendering error page: {error_message}")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Connection Error</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                }}
                .container {{
                    background: white;
                    padding: 50px;
                    border-radius: 15px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                    border-left: 5px solid #ef4444;
                }}
                h1 {{
                    color: #ef4444;
                    margin-bottom: 20px;
                    font-weight: 600;
                }}
                p {{
                    color: #555;
                    line-height: 1.6;
                    margin-bottom: 15px;
                    word-break: break-word;
                }}
                .error {{
                    color: #ef4444;
                    font-size: 64px;
                    margin-bottom: 25px;
                }}
                .retry-btn {{
                    background: #ef4444;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-size: 16px;
                    cursor: pointer;
                    margin-top: 20px;
                }}
                .retry-btn:hover {{
                    background: #dc2626;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">❌</div>
                <h1>Connection Failed</h1>
                <p>{error_message}</p>
                <p>Please try again or contact support if the issue persists.</p>
                <button class="retry-btn" onclick="window.close()">Close & Retry</button>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=400)

@app.on_event("startup")
async def startup_event():
    print("🚀 Social Army OAuth Server Starting...")
    print(f"📍 Base URL: {config.BASE_URL}")
    print(f"🔗 LinkedIn Redirect: {config.LINKEDIN_REDIRECT_URI}")
    print("🔐 Testing encryption system...")
    test_encryption()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
