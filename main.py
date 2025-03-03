from auth import auth_bp
from merchant import merchant_bp

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
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(merchant_bp, url_prefix='/merchant')

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
    
    # Get merchant ID from session
    merchant_id = session['merchant_id']
    
    # Import analyzer here to avoid circular imports
    from analyzer import analyze_account, get_products, get_product_statuses, analyze_product
    
    # Analyze account
    account_analysis = analyze_account(merchant_id)
    
    # Get sample products for demonstration
    products = get_products(merchant_id, max_results=10)
    product_statuses = get_product_statuses(merchant_id, max_results=10)
    
    # Map products to their statuses
    product_status_map = {status.get('productId'): status for status in product_statuses}
    
    # Analyze products
    product_analyses = []
    for product in products:
        product_id = product.get('id')
        product_status = product_status_map.get(product_id)
        product_analysis = analyze_product(product, product_status)
        product_analyses.append(product_analysis)
    
    return render_template(
        'analyze.html',
        account_analysis=account_analysis,
        product_analyses=product_analyses
    )

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
