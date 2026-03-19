import os

def replace_in_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.html', '.py', '.js', '.css')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = content.replace('Saleel Parfums', 'Perfumes')
                    new_content = new_content.replace('Saleel', 'Ecom')
                    new_content = new_content.replace('saleelparfums.com', 'perfumes.com')
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Updated {path}")
                except Exception as e:
                    print(f"Could not process {path}: {e}")

if __name__ == '__main__':
    replace_in_files('c:\\Users\\johns\\Music\\ecom\\django_ecommerce_mod5-master\\store')
    replace_in_files('c:\\Users\\johns\\Music\\ecom\\django_ecommerce_mod5-master\\ecommerce')
    replace_in_files('c:\\Users\\johns\\Music\\ecom\\django_ecommerce_mod5-master\\functions')
