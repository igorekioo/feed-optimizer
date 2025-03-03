import os
import logging
from flask import Flask, render_template, redirect, url_for, session, flash, request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)

# Configure secret key
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Simple session configuration - use app engine default storage
app.config['SESSION_TYPE'] = 'cookie'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7  # 7 days in seconds

# Try to import modules, log errors if they occur
try:
    from auth import auth_bp
    from merchant import merchant_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(merchant_bp, url_prefix='/merchant')
    logger.info("Blueprints registered successfully")
except Exception as e:
    logger.error(f"Error registering blueprints: {e}")

@app.route('/')
def index():
    """Home page."""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return f"Error: {str(e)}", 500

@app.route('/analyze')
def analyze():
    """Analysis page."""
    try:
        # Check if Merchant Center account is selected
        if 'merchant_id' not in session:
            flash('Please select a Merchant Center account first.', 'warning')
            return redirect(url_for('merchant.list_accounts'))
        
        # Simplified version for now
        return render_template('analyze.html', 
                              account_analysis={'account_status': 'good', 'stats': {}, 'issues': {}},
                              product_analyses=[])
    except Exception as e:
        logger.error(f"Error in analyze route: {e}")
        return f"Error in analysis page: {str(e)}", 500

@app.route('/optimize')
def optimize():
    """Optimization page."""
    try:
        # Check if Merchant Center account is selected
        if 'merchant_id' not in session:
            flash('Please select a Merchant Center account first.', 'warning')
            return redirect(url_for('merchant.list_accounts'))
        
        return render_template('optimize.html')
    except Exception as e:
        logger.error(f"Error in optimize route: {e}")
        return f"Error in optimization page: {str(e)}", 500

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
