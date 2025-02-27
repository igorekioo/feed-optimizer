def analyze_account(account_info, datafeeds, product_statuses):
    """Анализирует общее состояние аккаунта."""
    issues = {
        'critical': [],
        'warning': [],
        'info': []
    }
    
    # Проверка наличия фидов
    if not datafeeds:
        issues['critical'].append({
            'code': 'no_datafeeds',
            'message': 'В аккаунте отсутствуют фиды данных'
        })
    
    # Анализ статусов товаров
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
            'message': f'В аккаунте {disapproved_count} отклоненных товаров',
            'count': disapproved_count
        })
    
    if product_issues_count > 0:
        issues['warning'].append({
            'code': 'product_issues',
            'message': f'Обнаружено {product_issues_count} проблем с товарами',
            'count': product_issues_count
        })
    
    return {
        'account_status': 'critical' if issues['critical'] else ('warning' if issues['warning'] else 'good'),
        'issues': issues
    }

def analyze_product(product, product_status):
    """Анализирует отдельный товар и выявляет проблемы."""
    issues = {
        'critical': [],
        'warning': [],
        'info': []
    }
    
    # Извлечение проблем из статуса товара
    if product_status and 'itemLevelIssues' in product_status:
        for issue in product_status['itemLevelIssues']:
            severity = map_severity(issue.get('severity', ''))
            issues[severity].append({
                'code': issue.get('code', 'unknown'),
                'message': issue.get('detail', 'Неизвестная проблема'),
                'attribute': issue.get('attribute', None)
            })
    
    # Дополнительные проверки товара
    title = product.get('title', '')
    description = product.get('description', '')
    
    # Проверка заголовка
    if not title:
        issues['critical'].append({
            'code': 'missing_title',
            'message': 'Отсутствует заголовок товара',
            'attribute': 'title'
        })
    elif len(title) < 20:
        issues['warning'].append({
            'code': 'short_title',
            'message': 'Слишком короткий заголовок товара',
            'attribute': 'title'
        })
    
    # Проверка описания
    if not description:
        issues['warning'].append({
            'code': 'missing_description',
            'message': 'Отсутствует описание товара',
            'attribute': 'description'
        })
    elif len(description) < 100:
        issues['info'].append({
            'code': 'short_description',
            'message': 'Рекомендуется расширить описание товара',
            'attribute': 'description'
        })
    
    # Проверка GTIN
    if 'gtin' not in product and product.get('brand') != 'Custom':
        issues['warning'].append({
            'code': 'missing_gtin',
            'message': 'Отсутствует GTIN/UPC/EAN',
            'attribute': 'gtin'
        })
    
    # Проверка наличия изображений
    if not product.get('imageLink'):
        issues['critical'].append({
            'code': 'missing_image',
            'message': 'Отсутствует основное изображение товара',
            'attribute': 'imageLink'
        })
    
    return {
        'product_id': product.get('id', ''),
        'title': title,
        'status': 'critical' if issues['critical'] else ('warning' if issues['warning'] else 'good'),
        'issues': issues
    }

def map_severity(severity):
    """Преобразует уровень серьезности проблемы в категорию."""
    if severity in ['error', 'critical']:
        return 'critical'
    elif severity in ['warning']:
        return 'warning'
    else:
        return 'info'
