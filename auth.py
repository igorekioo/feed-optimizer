import os
import logging
from flask import Blueprint, redirect, url_for, session, request, current_app
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import google.auth.transport.requests

# Create logger
logger = logging.getLogger(__name__)

# Create Blueprint for authorization routes
auth_bp = Blueprint('auth', __name__)

# Minimal, specific scopes
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

def get_google_oauth_flow(redirect_uri):
    """Safely create OAuth flow without exposing credentials."""
    try:
        # Use environment variables securely
        client_config = {
            "web": {
                "client_id": os.environ.get("GCP_CLIENT_ID"),
                "client_secret": os.environ.get("GCP_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [
                    "https://feed-optimization-448714.uc.r.appspot.com/auth/callback",
                    "http://localhost:5000/auth/callback"
                ]
            }
        }
        
        return Flow.from_client_config(
            client_config=client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
    except Exception as e:
        logger.error(f"OAuth flow creation error: {e}")
        return None

@auth_bp.route('/login')
def login():
    """Initiate secure OAuth authentication."""
    try:
        # Use _external=True to get full URL
        redirect_uri = url_for('auth.callback', _external=True)
        
        flow = get_google_oauth_flow(redirect_uri)
        if not flow:
            logger.error("Failed to create OAuth flow")
            return "Authentication setup error", 500
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )
        
        # Securely store state in session
        session['oauth_state'] = state
        
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Login process error: {e}")
        return "Authentication error", 500

@auth_bp.route('/callback')
def callback():
    """Handle OAuth callback securely."""
    try:
        # Validate state to prevent CSRF
        if request.args.get('state') != session.get('oauth_state'):
            logger.warning("State mismatch - possible CSRF attempt")
            return "Authentication failed", 403
        
        # Prepare redirect URI
        redirect_uri = url_for('auth.callback', _external=True)
        
        # Create flow
        flow = get_google_oauth_flow(redirect_uri)
        if not flow:
            return "Authentication setup error", 500
        
        # Fetch and validate token
        flow.fetch_token(authorization_response=request.url)
        
        # Get credentials
        credentials = flow.credentials
        
        # Fetch minimal user info
        oauth2_client = build('oauth2', 'v2', credentials=credentials)
        user_info = oauth2_client.userinfo().get().execute()
        
        # Store user info in session
        session['user_info'] = {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture')
        }
        
        # Clear sensitive state
        session.pop('oauth_state', None)
        
        return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Callback processing error: {e}")
        return "Authentication failed", 401

@auth_bp.route('/logout')
def logout():
    """Secure logout."""
    session.clear()
    return redirect(url_for('index'))
