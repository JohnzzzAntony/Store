# Multi-Site Development Guide (Single Backend)

This backend is designed as a **Headless E-commerce Service**. You can connect multiple frontends (Web, Mobile, Different Themes) to this single Django instance.

## 1. How it Works (Store Identification)

The backend uses a `StoreMiddleware` to identify which store is being requested based on the URL slug.

-   **Primary Store:** `yourdomain.com/s/saleel-luxury/`
-   **Secondary Store:** `yourdomain.com/s/arctic-mint/`

Each `Store` in the database has its own:
-   `primary_color` & `secondary_color`
-   `font_family` (Sans, Serif, Playfair, etc.)
-   `theme_style` (Minimal, Luxury, Modern)
-   `Figma Link` (for design token synchronization)

## 2. Connecting a New Frontend

### Option A: Django Templates (Integrated)
If you want to build a new design using the built-in Django templates:
1.  **Create a New Template Folder:** `store/templates/store/themes/alternate_design/`
2.  **Update View Mapping:** Update `store/views/pages.py` to check `request.current_store.theme_style` and return a different template string.
    ```python
    if request.current_store.theme_style == 'MODERN':
        return render(request, 'store/themes/modern/store.html', context)
    ```

### Option B: External Frontend (React/Next.js/Vue)
If you want a completely separate codebase:
1.  **Use the APIs:**
    -   `GET /api/v1/products/`
    -   `POST /api/v1/orders/create/`
    -   `GET /api/v1/stats/` (Admin Dashboard)
2.  **Authentication:** Use **Firebase Auth**. Once the user logs in on your React app, send the `idToken` to `/firebase-login-sync/` on this backend to create/sync the customer record.

## 3. Customizing UI per Store

In the base templates (`main.html`), we dynamically inject CSS variables based on the active store:

```html
<style>
  :root {
    --primary-color: {{ request.current_store.primary_color|default:"#1a1a1a" }};
    --secondary-color: {{ request.current_store.secondary_color|default:"#c4a17e" }};
    --font-family: {{ request.current_store.font_family|default:"'Inter', sans-serif" }};
  }
</style>
```

## 4. Key Refactor Highlights
-   **`store/views/`**: All logic is separated by concern (Admin, Auth, Cart, Pages, Payments).
-   **`store/core/`**: Shared business logic (Notifications, Firebase, Figma, Payment Registry).
-   **`store/signals.py`**: Automated triggers for Order Shipped/Delivered notifications.

## 5. Adding a New Store
1.  Go to Django Admin (`/admin/store/store/`).
2.  Add a new Store entry with a unique slug.
3.  Upload unique Banners and Products targeted to this store.
4.  Optionally, paste a **Figma Design Link** and **Access Token**, then click "Sync from Figma" in the admin to automatically import the brand colors and typography.
