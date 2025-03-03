import os
import json
from flask import Blueprint, redirect, url_for, session, request, current_app
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import google.auth.transport.requests

# Create Blueprint for authorization routes
auth_bp = Blueprint('auth', __name__)

# Scopes we request from the user
SCOPES = [
    'https://www.googleapis.com/auth/content',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

def create_flow(redirect_uri):
    """Creates a Flow object for OAuth authentication."""
    client_config = {
        "web": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    return Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

@auth_bp.route('/login')
def login():
    """Initiates the OAuth authentication process."""
    # Define the callback URL
    redirect_uri = url_for('auth.callback', _external=True)
    
    # Create Flow object
    flow = create_flow(redirect_uri)
    
    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Save state in session for security
    session['state'] = state
    
    # Redirect the user to Google authorization page
    return redirect(authorization_url)

@auth_bp.route('/callback')
def callback():
    """Handles the response from the authorization server."""
    # Verify state for CSRF protection
    if request.args.get('state') != session.get('state'):
        return redirect(url_for('index'))
    
    # Get authorization code
    authorization_code = request.args.get('code')
    if not authorization_code:
        return redirect(url_for('index'))
    
    # Define the callback URL
    redirect_uri = url_for('auth.callback', _external=True)
    
    # Create Flow object
    flow = create_flow(redirect_uri)
    
    # Exchange code for access tokens
    flow.fetch_token(code=authorization_code)
    
    # Get credentials
    credentials = flow.credentials
    
    # Save credentials in session
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    # Get user information
    user_info = get_user_info(credentials)
    session['user_info'] = user_info
    
    # Redirect to Merchant Center account selection page
    return redirect(url_for('merchant.list_accounts'))

@auth_bp.route('/logout')
def logout():
    """Logs the user out."""
    # Clear session
    session.clear()
    
    # Redirect to home page
    return redirect(url_for('index'))

def get_user_info(credentials):
    """Gets information about the user."""
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    return user_info

def get_credentials():
    """Gets credentials from the session."""
    if 'credentials' not in session:
        return None
    
    credentials_dict = session['credentials']
    return Credentials(
        token=credentials_dict['token'],
        refresh_token=credentials_dict['refresh_token'],
        token_uri=credentials_dict['token_uri'],
        client_id=credentials_dict['client_id'],
        client_secret=credentials_dict['client_secret'],
        scopes=credentials_dict['scopes']
    )
