import os
import re

def rebrand():
    root_dir = 'c:\\Users\\johns\\Music\\ecom\\django_ecommerce_mod5-master'
    templates_dir = os.path.join(root_dir, 'store', 'templates', 'store')
    
    # 1. Update all template titles
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(templates_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace any "Perfumes — Perfumes" or others with "Ecom — Perfumes"
            content = re.sub(r'\{% block title %\}.*?\{% endblock %\}', r'{% block title %}Ecom — Perfumes{% endblock %}', content)
            
            # Also cleanup any residual "Saleel" or "Saleel Parfums"
            content = content.replace('Saleel Parfums', 'Perfumes')
            content = content.replace('Saleel', 'Ecom')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated titles/branding in {filename}")

    # 2. Update Admin naming in admin.py
    admin_path = os.path.join(root_dir, 'store', 'admin.py')
    with open(admin_path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('Django Administration', 'Admin')
    content = content.replace('Django admin', 'Admin')
    with open(admin_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated admin.py")

if __name__ == '__main__':
    rebrand()
