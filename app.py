from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import json
from dotenv import load_dotenv
import merchant_api
import analyzer

load_dotenv()  # Загружаем переменные окружения из .env файла

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Путь к файлу сервисного аккаунта
SERVICE_ACCOUNT_FILE = 'service-account-key.json'  # Замените на путь к вашему ключу

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['GET', 'POST'])
def connect():
    if request.method == 'POST':
        merchant_id = request.form.get('merchant_id')
        
        # Сохраняем ID в сессии
        session['merchant_id'] = merchant_id
        
        try:
            # Создаем клиент API
            client = merchant_api.create_content_api_client(SERVICE_ACCOUNT_FILE)
            
            # Проверяем подключение, получая информацию об аккаунте
            account_info = merchant_api.get_account_info(client, merchant_id)
            
            if account_info:
                return redirect(url_for('analyze'))
            else:
                error_message = "Не удалось подключиться к аккаунту. Проверьте ID и права доступа."
                return render_template('connect.html', error=error_message)
                
        except Exception as e:
            error_message = f"Ошибка при подключении: {str(e)}"
            return render_template('connect.html', error=error_message)
    
    return render_template('connect.html')

@app.route('/analyze')
def analyze():
    merchant_id = session.get('merchant_id')
    
    if not merchant_id:
        return redirect(url_for('connect'))
    
    try:
        # Создаем клиент API
        client = merchant_api.create_content_api_client(SERVICE_ACCOUNT_FILE)
        
        # Получаем данные аккаунта
        account_info = merchant_api.get_account_info(client, merchant_id)
        datafeeds = merchant_api.get_datafeeds(client, merchant_id)
        product_statuses = merchant_api.get_product_issues(client, merchant_id, max_results=100)
        
        # Анализируем аккаунт
        account_analysis = analyzer.analyze_account(account_info, datafeeds, product_statuses)
        
        # Получаем несколько товаров для примера
        products = merchant_api.get_products(client, merchant_id, max_results=10)
        
        # Анализируем товары
        product_analyses = []
        for product in products:
            # Находим статус для этого товара
            product_status = next((s for s in product_statuses if s.get('productId') == product.get('id')), None)
            product_analysis = analyzer.analyze_product(product, product_status)
            product_analyses.append(product_analysis)
        
        return render_template(
            'analyze.html',
            account=account_info,
            account_analysis=account_analysis,
            product_analyses=product_analyses
        )
        
    except Exception as e:
        error_message = f"Ошибка при анализе: {str(e)}"
        return render_template('analyze.html', error=error_message)

@app.route('/optimize')
def optimize():
    merchant_id = session.get('merchant_id')
    
    if not merchant_id:
        return redirect(url_for('connect'))
    
    return render_template('optimize.html')

if __name__ == '__main__':
    app.run(debug=True)
