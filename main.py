import os
from flask import Flask, render_template, redirect, url_for, session, flash
from werkzeug.middleware.proxy_fix import ProxyFix
import datetime

# Import custom session interface
from session_file import FileSystemSessionInterface

# Create Flask application
app = Flask(__name__)

# Fix for working behind proxy
app.wsgi_app = ProxyFix(app.wsgi_app)

# Configure secret key
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Configure sessions
app.session_interface = FileSystemSessionInterface(
    storage_path=os.path.join(os.getcwd(), 'flask_session')
)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)

# We'll register blueprints after creating them
# app.register_blueprint(auth_bp, url_prefix='/auth')
# app.register_blueprint(merchant_bp, url_prefix='/merchant')

@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')

@app.route('/analyze')
def analyze():
    """Analysis page."""
    # Check if Merchant Center account is selected
    if 'merchant_id' not in session:
        flash('Please select a Merchant Center account first.', 'warning')
        return redirect(url_for('merchant.list_accounts'))
    
    return render_template('analyze.html')

@app.route('/optimize')
def optimize():
    """Optimization page."""
    # Check if Merchant Center account is selected
    if 'merchant_id' not in session:
        flash('Please select a Merchant Center account first.', 'warning')
        return redirect(url_for('merchant.list_accounts'))
    
    return render_template('optimize.html')

if __name__ == '__main__':
    # This is for local development
    app.run(debug=True)
else:
    # This is for App Engine
    import os
    port = int(os.environ.get('PORT', 8080))
