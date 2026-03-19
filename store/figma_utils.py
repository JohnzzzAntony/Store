import requests
import os
import datetime
from .models import Store

FIGMA_API_BASE = "https://api.figma.com/v1"

def extract_figma_file_key(url):
    """
    Extracts the file key from a Figma URL.
    """
    try:
        # Format: https://www.figma.com/file/FILE_KEY/name...
        if '/file/' in url:
            return url.split('/file/')[1].split('/')[0]
        # Format: https://www.figma.com/design/FILE_KEY/name...
        elif '/design/' in url:
            return url.split('/design/')[1].split('/')[0]
    except (IndexError, AttributeError):
        pass
    return None

def fetch_figma_design_data(store):
    """
    Fetches design tokens from Figma and updates the store instance.
    """
    if not store.figma_link or not store.figma_access_token:
        return {"error": "Missing Figma link or access token for this store."}

    file_key = extract_figma_file_key(store.figma_link)
    if not file_key:
        return {"error": "Invalid Figma URL."}

    headers = {"X-Figma-Token": store.figma_access_token}

    try:
        response = requests.get(f"{FIGMA_API_BASE}/files/{file_key}", headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {"error": f"Figma API error: {str(e)}"}

    found_primary = None
    found_secondary = None
    found_font = None

    def find_tokens_recursive(node):
        nonlocal found_primary, found_secondary, found_font
        
        name = node.get('name', '').lower()
        
        # Color Extraction Logic
        if any(keyword in name for keyword in ['primary', 'brand', 'main', 'accent']):
            fills = node.get('fills', [])
            if fills and fills[0].get('color'):
                c = fills[0]['color']
                r, g, b = int(c['r']*255), int(c['g']*255), int(c['b']*255)
                color_hex = f"#{r:02x}{g:02x}{b:02x}"
                if not found_primary or 'primary' in name:
                    found_primary = color_hex
                    
        elif 'secondary' in name:
            fills = node.get('fills', [])
            if fills and fills[0].get('color'):
                c = fills[0]['color']
                r, g, b = int(c['r']*255), int(c['g']*255), int(c['b']*255)
                found_secondary = f"#{r:02x}{g:02x}{b:02x}"

        # Font Extraction Logic (Heuristic from Text nodes)
        if node.get('type') == 'TEXT' and not found_font:
            style = node.get('style', {})
            font_family = style.get('fontFamily', '').lower()
            if 'garamond' in font_family or 'serif' in font_family:
                found_font = 'serif'
            elif 'inter' in font_family or 'sans' in font_family:
                found_font = 'sans'
            elif 'playfair' in font_family:
                found_font = 'playfair'

        for child in node.get('children', []):
            find_tokens_recursive(child)

    # Begin recursive search
    find_tokens_recursive(data.get('document', {}))

    if found_primary:
        store.primary_color = found_primary
    if found_secondary:
        store.secondary_color = found_secondary
    if found_font:
        store.font_family = found_font

    store.figma_design_data = data
    store.figma_last_sync = datetime.datetime.now()
    store.save()

    return {
        "status": "success", 
        "message": f"Design synced. Extracted: Primary({found_primary}), Font({found_font})"
    }

def create_store_from_figma(figma_url, access_token):
    """
    Creates a NEW store based on a Figma file.
    """
    from django.utils.text import slugify
    
    file_key = extract_figma_file_key(figma_url)
    if not file_key:
        return {"status": "error", "message": "Invalid Figma URL."}

    headers = {"X-Figma-Token": access_token}
    try:
        response = requests.get(f"{FIGMA_API_BASE}/files/{file_key}?depth=1", headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {"status": "error", "message": f"Figma API error: {str(e)}"}

    figma_name = data.get('name', 'New Figma Store')
    slug = slugify(figma_name)
    
    # Avoid collisions
    base_slug = slug
    counter = 1
    while Store.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    store = Store.objects.create(
        name=figma_name,
        slug=slug,
        figma_link=figma_url,
        figma_access_token=access_token,
        is_active=True
    )

    # Run full sync
    sync_result = fetch_figma_design_data(store)
    
    return {
        "status": "success", 
        "message": f"Store '{figma_name}' created.",
        "slug": slug,
        "sync_result": sync_result
    }

def sync_store_design_from_figma(store):
    """
    Trigger a fresh sync for an existing store.
    """
    return fetch_figma_design_data(store)
