from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из .env файла

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Базовые маршруты
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect')
def connect():
    # Здесь будет код для подключения к Merchant Center
    return render_template('connect.html')

@app.route('/analyze')
def analyze():
    # Здесь будет код для анализа данных
    return render_template('analyze.html')

@app.route('/optimize')
def optimize():
    # Здесь будет код для оптимизации
    return render_template('optimize.html')

if __name__ == '__main__':
    app.run(debug=True)
