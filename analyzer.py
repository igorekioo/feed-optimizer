from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from auth import get_credentials
from flask import session

def get_merchant_service():
    """Creates and returns a Content API service."""
    credentials = get_credentials()
    if not credentials:
        return None
    
    return build('content', 'v2.1', credentials=credentials)

def get_account_info(merchant_id):
    """Gets basic information about the Merchant Center account."""
    service = get_merchant_service()
    if not service:
        return None
    
    try:
        account_info = service.accounts().get(
            merchantId=merchant_id, 
            accountId=merchant_id
        ).execute()
        return account_info
    except HttpError as e:
        print(f"Error fetching account info: {e}")
        return None

def get_data_feeds(merchant_id):
    """Gets list of data feeds in the account."""
    service = get_merchant_service()
    if not service:
        return []
    
    try:
        response = service.datafeeds().list(merchantId=merchant_id).execute()
        return response.get('resources', [])
    except HttpError as e:
        print(f"Error fetching data feeds: {e}")
        return []

def get_products(merchant_id, max_results=250):
    """Gets list of products from the account."""
    service = get_merchant_service()
    if not service:
        return []
    
    products = []
    try:
        request = service.products().list(merchantId=merchant_id, maxResults=max_results)
        
        while request is not None:
            response = request.execute()
            products.extend(response.get('resources', []))
            request = service.products().list_next(request, response)
            
            # Limit for testing
            if len(products) >= max_results:
                break
                
        return products
    except HttpError as e:
        print(f"Error fetching products: {e}")
        return []

def get_product_statuses(merchant_id, max_results=250):
    """Gets status information for products."""
    service = get_merchant_service()
    if not service:
        return []
    
    product_statuses = []
    try:
        request = service.productstatuses().list(merchantId=merchant_id, maxResults=max_results)
        
        while request is not None:
            response = request.execute()
            product_statuses.extend(response.get('resources', []))
            request = service.productstatuses().list_next(request, response)
            
            # Limit for testing
            if len(product_statuses) >= max_results:
                break
                
        return product_statuses
    except HttpError as e:
        print(f"Error fetching product statuses: {e}")
        return []

def analyze_account(merchant_id):
    """Analyzes the overall state of a Merchant Center account."""
    account_info = get_account_info(merchant_id)
    datafeeds = get_data_feeds(merchant_id)
    product_statuses = get_product_statuses(merchant_id, max_results=100)
    
    issues = {
        'critical': [],
        'warning': [],
        'info': []
    }
    
    # Check datafeeds
    if not datafeeds:
        issues['warning'].append({
            'code': 'no_datafeeds',
            'message': 'No data feeds found in account'
        })
    
    # Analyze product statuses
    product_issues_count = 0
    disapproved_count = 0
    
    for status in product_statuses:
        if 'itemLevelIssues' in status:
            product_issues_count += len(status['itemLevelIssues'])
            
        if status.get('destinationStatuses'):
            for dest_status in status['destinationStatuses']:
                if dest_status.get('status') == 'disapproved':
                    disapproved_count += 1
    
    if disapproved_count > 0:
        issues['critical'].append({
            'code': 'disapproved_products',
            'message': f'{disapproved_count} disapproved products',
            'count': disapproved_count
        })
    
    if product_issues_count > 0:
        issues['warning'].append({
            'code': 'product_issues',
            'message': f'{product_issues_count} product issues detected',
            'count': product_issues_count
        })
    
    # Overall account stats
    stats = {
        'name': account_info.get('name', 'Unknown') if account_info else 'Unknown',
        'website': account_info.get('websiteUrl', '') if account_info else '',
        'products_count': len(product_statuses),
        'feeds_count': len(datafeeds),
        'issues_count': product_issues_count,
        'disapproved_count': disapproved_count
    }
    
    return {
        'account_status': 'critical' if issues['critical'] else ('warning' if issues['warning'] else 'good'),
        'issues': issues,
        'stats': stats
    }

def analyze_product(product, product_status):
    """Analyzes a specific product and identifies issues."""
    issues = {
        'critical': [],
        'warning': [],
        'info': []
    }
    
    # Extract issues from product status
    if product_status and 'itemLevelIssues' in product_status:
        for issue in product_status['itemLevelIssues']:
            severity = map_severity(issue.get('severity', ''))
            issues[severity].append({
                'code': issue.get('code', 'unknown'),
                'message': issue.get('detail', 'Unknown issue'),
                'attribute': issue.get('attribute', None)
            })
    
    # Additional product checks
    title = product.get('title', '')
    description = product.get('description', '')
    
    # Check title
    if not title:
        issues['critical'].append({
            'code': 'missing_title',
            'message': 'Missing product title',
            'attribute': 'title'
        })
    elif len(title) < 20:
        issues['warning'].append({
            'code': 'short_title',
            'message': 'Title is too short (less than 20 characters)',
            'attribute': 'title'
        })
    
    # Check description
    if not description:
        issues['warning'].append({
            'code': 'missing_description',
            'message': 'Missing product description',
            'attribute': 'description'
        })
    elif len(description) < 100:
        issues['info'].append({
            'code': 'short_description',
            'message': 'Description should be expanded (less than 100 characters)',
            'attribute': 'description'
        })
    
    # Check GTIN
    if 'gtin' not in product and product.get('brand') != 'Custom':
        issues['warning'].append({
            'code': 'missing_gtin',
            'message': 'Missing GTIN/UPC/EAN',
            'attribute': 'gtin'
        })
    
    # Check image
    if not product.get('imageLink'):
        issues['critical'].append({
            'code': 'missing_image',
            'message': 'Missing product image',
            'attribute': 'imageLink'
        })
    
    return {
        'product_id': product.get('id', ''),
        'title': title,
        'status': 'critical' if issues['critical'] else ('warning' if issues['warning'] else 'good'),
        'issues': issues
    }

def map_severity(severity):
    """Maps API severity level to our categories."""
    if severity in ['error', 'critical']:
        return 'critical'
    elif severity in ['warning']:
        return 'warning'
    else:
        return 'info'
