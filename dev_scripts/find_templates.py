import os

def find_files(filename, search_path):
    result = []
    for root, dirs, files in os.walk(search_path):
        if filename in files:
            result.append(os.path.join(root, filename))
    return result

if __name__ == "__main__":
    search_path = r'c:\Users\johns\Music\ecom\django_ecommerce_mod5-master'
    print("Searching for store.html...")
    for f in find_files('store.html', search_path):
        print(f)
    print("\nSearching for main.html...")
    for f in find_files('main.html', search_path):
        print(f)
