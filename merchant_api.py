from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

def create_content_api_client(service_account_file):
    """Создает клиент для работы с Content API for Shopping."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/content']
        )
        
        return build('content', 'v2.1', credentials=credentials)
    except Exception as e:
        print(f"Ошибка при создании клиента Content API: {e}")
        return None

def get_account_info(client, merchant_id):
    """Получает информацию об аккаунте Merchant Center."""
    try:
        return client.accounts().get(merchantId=merchant_id, accountId=merchant_id).execute()
    except Exception as e:
        print(f"Ошибка при получении информации об аккаунте: {e}")
        return None

def get_datafeeds(client, merchant_id):
    """Получает список фидов в аккаунте."""
    try:
        request = client.datafeeds().list(merchantId=merchant_id)
        response = request.execute()
        return response.get('resources', [])
    except Exception as e:
        print(f"Ошибка при получении списка фидов: {e}")
        return []

def get_products(client, merchant_id, max_results=250):
    """Получает список товаров из аккаунта."""
    products = []
    try:
        request = client.products().list(merchantId=merchant_id, maxResults=max_results)
        
        while request is not None:
            response = request.execute()
            products.extend(response.get('resources', []))
            request = client.products().list_next(request, response)
            
            # Для тестового MVP ограничиваем количество товаров
            if len(products) >= max_results:
                break
                
        return products
    except Exception as e:
        print(f"Ошибка при получении списка товаров: {e}")
        return []

def get_product_issues(client, merchant_id, max_results=250):
    """Получает информацию о проблемах с товарами."""
    try:
        request = client.productstatuses().list(merchantId=merchant_id, maxResults=max_results)
        response = request.execute()
        return response.get('resources', [])
    except Exception as e:
        print(f"Ошибка при получении статусов товаров: {e}")
        return []

def create_supplemental_feed(client, merchant_id, feed_name, feed_file_url):
    """Создает дополнительный фид (supplemental feed)."""
    try:
        body = {
            'name': feed_name,
            'contentType': 'products',
            'fetchSchedule': {
                'weekday': 'monday',
                'hour': 6,
                'fetchUrl': feed_file_url,
                'timeZone': 'Europe/Moscow'  # Измените на нужную вам таймзону
            },
            'format': {
                'fileEncoding': 'utf-8',
                'columnDelimiter': 'tab',
                'headerLine': True
            }
        }
        
        return client.datafeeds().insert(merchantId=merchant_id, body=body).execute()
    except Exception as e:
        print(f"Ошибка при создании supplemental feed: {e}")
        return None
