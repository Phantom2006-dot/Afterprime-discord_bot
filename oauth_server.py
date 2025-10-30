from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import requests
from datetime import datetime, timedelta
import config
from database import get_session, SocialAccount, User
from encryption import encrypt_token
import uvicorn

app = FastAPI()

oauth_states = {}

@app.get("/")
async def root():
    return {"message": "Social Army OAuth Server Running"}

@app.get("/oauth/linkedin/start")
async def linkedin_oauth_start(discord_id: str):
    state = f"{discord_id}_{datetime.utcnow().timestamp()}"
    oauth_states[state] = discord_id
    
    linkedin_auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&"
        f"client_id={config.LINKEDIN_CLIENT_ID}&"
        f"redirect_uri={config.OAUTH_REDIRECT_URI}&"
        f"state={state}&"
        f"scope=r_liteprofile%20w_member_social"
    )
    
    return RedirectResponse(url=linkedin_auth_url)

@app.get("/oauth/linkedin/callback")
async def linkedin_oauth_callback(code: str, state: str):
    if state not in oauth_states:
        return HTMLResponse(content="<h1>Error: Invalid state</h1>", status_code=400)
    
    discord_id = oauth_states.pop(state)
    
    token_response = requests.post(
        'https://www.linkedin.com/oauth/v2/accessToken',
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': config.OAUTH_REDIRECT_URI,
            'client_id': config.LINKEDIN_CLIENT_ID,
            'client_secret': config.LINKEDIN_CLIENT_SECRET
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    if token_response.status_code != 200:
        return HTMLResponse(
            content=f"<h1>Error: Failed to get access token</h1><p>{token_response.text}</p>",
            status_code=400
        )
    
    token_data = token_response.json()
    access_token = token_data.get('access_token')
    expires_in = token_data.get('expires_in', 5184000)
    
    profile_response = requests.get(
        'https://api.linkedin.com/v2/me',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    if profile_response.status_code != 200:
        return HTMLResponse(
            content=f"<h1>Error: Failed to get profile</h1><p>{profile_response.text}</p>",
            status_code=400
        )
    
    profile_data = profile_response.json()
    linkedin_user_id = profile_data.get('id')
    
    session = get_session()
    try:
        user = session.query(User).filter_by(discord_id=discord_id).first()
        if not user:
            user = User(discord_id=discord_id)
            session.add(user)
            session.commit()
        
        social_account = session.query(SocialAccount).filter_by(
            user_id=user.id,
            platform='linkedin'
        ).first()
        
        if social_account:
            social_account.access_token = encrypt_token(access_token)
            social_account.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            social_account.profile_data = profile_data
        else:
            social_account = SocialAccount(
                user_id=user.id,
                platform='linkedin',
                platform_user_id=linkedin_user_id,
                access_token=encrypt_token(access_token),
                token_expiry=datetime.utcnow() + timedelta(seconds=expires_in),
                profile_data=profile_data
            )
            session.add(social_account)
        
        session.commit()
        
        return HTMLResponse(content="""
            <html>
                <head>
                    <title>LinkedIn Connected!</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }
                        .container {
                            background: white;
                            padding: 40px;
                            border-radius: 10px;
                            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                            text-align: center;
                            max-width: 500px;
                        }
                        h1 {
                            color: #0077b5;
                            margin-bottom: 20px;
                        }
                        p {
                            color: #333;
                            line-height: 1.6;
                        }
                        .success {
                            color: #10b981;
                            font-size: 48px;
                            margin-bottom: 20px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="success">✅</div>
                        <h1>LinkedIn Connected Successfully!</h1>
                        <p>Your LinkedIn account has been connected to Social Army.</p>
                        <p>You can now close this window and return to Discord to start posting missions!</p>
                    </div>
                </body>
            </html>
        """)
    finally:
        session.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
