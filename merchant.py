import os
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from auth import get_credentials

# Create Blueprint for Merchant Center routes
merchant_bp = Blueprint('merchant', __name__)

@merchant_bp.route('/accounts')
def list_accounts():
    """Display list of available Merchant Center accounts."""
    # Get credentials
    credentials = get_credentials()
    if not credentials:
        return redirect(url_for('auth.login'))
    
    try:
        # Create Content API client
        service = build('content', 'v2.1', credentials=credentials)
        
        # Get list of accounts
        accounts_response = service.accounts().authinfo().execute()
        
        # Check if accounts exist
        if 'accountIdentifiers' not in accounts_response:
            flash('No Merchant Center accounts found for this Google account.', 'warning')
            return redirect(url_for('index'))
        
        # Get information about each account
        accounts = []
        for account_id in accounts_response['accountIdentifiers']:
            merchant_id = account_id.get('merchantId')
            if merchant_id:
                try:
                    # Get account details
                    account_info = service.accounts().get(
                        merchantId=merchant_id,
                        accountId=merchant_id
                    ).execute()
                    
                    accounts.append({
                        'id': merchant_id,
                        'name': account_info.get('name', f'Account {merchant_id}'),
                        'websiteUrl': account_info.get('websiteUrl', '')
                    })
                except HttpError as e:
                    # If no access to account, add just the ID
                    accounts.append({
                        'id': merchant_id,
                        'name': f'Account {merchant_id}',
                        'websiteUrl': '',
                        'error': str(e)
                    })
        
        # Display list of accounts
        return render_template('merchant/accounts.html', accounts=accounts)
    
    except HttpError as e:
        flash(f'Error accessing Merchant Center accounts: {str(e)}', 'error')
        return redirect(url_for('index'))

@merchant_bp.route('/select/<merchant_id>')
def select_account(merchant_id):
    """Select Merchant Center account to work with."""
    # Get credentials
    credentials = get_credentials()
    if not credentials:
        return redirect(url_for('auth.login'))
    
    try:
        # Create Content API client
        service = build('content', 'v2.1', credentials=credentials)
        
        # Check access to account
        account_info = service.accounts().get(
            merchantId=merchant_id,
            accountId=merchant_id
        ).execute()
        
        # Save selected account info in session
        session['merchant_id'] = merchant_id
        session['merchant_name'] = account_info.get('name', f'Account {merchant_id}')
        
        # Redirect to analysis page
        return redirect(url_for('analyze'))
    
    except HttpError as e:
        flash(f'Error accessing Merchant Center account: {str(e)}', 'error')
        return redirect(url_for('merchant.list_accounts'))
