import os
import re

files_to_update = ['app/templates/base.html', 'app/templates/client_dashboard.html']
for filepath in files_to_update:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'notifications.js' not in content:
            content = content.replace('</head>', '    <script src="{{ url_for(\'static\', path=\'/js/notifications.js\') }}"></script>\n</head>')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Added notifications.js to {filepath}')

template_dir = 'app/templates'
for filename in os.listdir(template_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(template_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content

        # Remove local notification containers
        content = re.sub(r'<div id="notification-container"[^>]*>.*?</div>\s*', '', content, flags=re.DOTALL)
        content = re.sub(r'<div id="success-notification-container"[^>]*>.*?</div>\s*', '', content, flags=re.DOTALL)
        
        # Remove local function definitions for notifications
        content = re.sub(r'function\s+showSuccessNotification\s*\([^\)]*\)\s*\{(?:[^{}]*|\{[^{}]*\})*\}\s*', '', content)
        content = re.sub(r'function\s+showErrorNotification\s*\([^\)]*\)\s*\{(?:[^{}]*|\{[^{}]*\})*\}\s*', '', content)
        
        # Replace alert('Error...') with showNotification('Error...', 'error')
        content = re.sub(r'alert\(\s*([\'"`])(error)(.*?)\1\s*\)', r'showNotification(\1\2\3\1, "error")', content, flags=re.IGNORECASE)
        
        # Replace alert('Éxito...') with showNotification('Éxito...', 'success')
        content = re.sub(r'alert\(\s*([\'"`])(éxito|exito)(.*?)\1\s*\)', r'showNotification(\1\2\3\1, "success")', content, flags=re.IGNORECASE)
        
        # Replace general alert() with showNotification()
        content = re.sub(r'(?<!\.)alert\(', 'showNotification(', content)

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Updated {filename}')
