
conf_path = '/etc/nginx/sites-available/mr.pkld.online'
with open(conf_path, 'r', encoding='utf-8') as f:
    text = f.read()

rule = '''    location ~* ^/(?:etabs_hub\\.js|static/etabs_hub\\.js|etabs_beam_data\\.json|api/.*)$ {
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate, max-age=0";
        try_files $uri =404;
    }
'''

if 'etabs_hub' not in text:
    text = text.replace('location / {', rule + '\n    location / {')
    with open(conf_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Updated Nginx config successfully.')
else:
    print('Already present.')
