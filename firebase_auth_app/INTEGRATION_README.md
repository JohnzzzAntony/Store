# Django ↔ Firebase + Stripe Integration Guide

Complete setup instructions for integrating your Django backend with
Firebase Admin SDK, Firestore, Firebase Auth, and Stripe Payments.

---

## 1 · File Structure

Copy the following into your Django project root (same level as `manage.py`):

```
your_django_project/
├── manage.py
├── firebase_init.py            ← Firebase Admin singleton
├── frontend_api.ts             ← Drop into React src/api/djangoApi.ts
├── requirements.txt            ← pip dependencies
├── .env                        ← secrets (never commit)
│
├── firebase_auth_app/          ← User sync & auth helpers
│   ├── __init__.py
│   ├── authentication.py       ← DRF token authenticator
│   ├── middleware.py           ← Injects uid into every request
│   ├── permissions.py          ← IsFirebaseAdmin / IsFirebaseOwnerOrAdmin
│   ├── views.py                ← /api/auth/ endpoints
│   └── urls.py
│
├── products/                   ← Product CRUD
│   ├── __init__.py
│   ├── views.py
│   └── urls.py
│
├── categories/                 ← Category CRUD
│   ├── __init__.py
│   ├── views.py
│   └── urls.py
│
├── orders/                     ← Order management + stock decrement
│   ├── __init__.py
│   ├── views.py
│   └── urls.py
│
└── payments/                   ← Stripe PaymentIntents + Webhook
    ├── __init__.py
    ├── views.py
    └── urls.py
```

---

## 2 · Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3 · Firebase Service Account

1. Go to **Firebase Console → Project Settings → Service Accounts**
2. Click **"Generate new private key"** → download the JSON file
3. Save it somewhere safe (e.g. `secrets/serviceAccountKey.json`)
4. Add to `.env`:
   ```
   FIREBASE_SERVICE_ACCOUNT_PATH=secrets/serviceAccountKey.json
   FIREBASE_PROJECT_ID=gen-lang-client-0858875649
   FIREBASE_DATABASE_ID=ai-studio-c28338d1-3abd-4103-a4bb-d523f16d7d5e
   FIREBASE_STORAGE_BUCKET=gen-lang-client-0858875649.firebasestorage.app
   ```

---

## 4 · Stripe Setup

1. Get your keys from **Stripe Dashboard → Developers → API keys**
2. Add to `.env`:
   ```
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...   # from Stripe webhook settings
   ```
3. Register the webhook endpoint in **Stripe Dashboard → Developers → Webhooks**:
   - URL: `https://yourdomain.com/api/payments/webhook/`
   - Events to listen for:
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
     - `payment_intent.canceled`

---

## 5 · Merge into settings.py

Add/merge these into your **existing** `settings.py`:

```python
from decouple import config, Csv

INSTALLED_APPS += [
    'rest_framework',
    'corsheaders',
    'firebase_auth_app',
    'products',
    'orders',
    'categories',
    'payments',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # must be FIRST
    *MIDDLEWARE,
    'firebase_auth_app.middleware.FirebaseAuthMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'firebase_auth_app.authentication.FirebaseAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

CORS_ALLOWED_ORIGINS  = config('CORS_ALLOWED_ORIGINS', cast=Csv(), default='http://localhost:3000')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS    = ['accept', 'authorization', 'content-type', 'x-csrftoken']

STRIPE_SECRET_KEY      = config('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET  = config('STRIPE_WEBHOOK_SECRET', default='')
STRIPE_CURRENCY        = 'usd'   # change to your currency

STORE_ADMIN_EMAIL = config('STORE_ADMIN_EMAIL', default='johns@maylaainternational.com')
```

---

## 6 · Add URL routes

In your project's `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/',       include('firebase_auth_app.urls')),
    path('api/products/',   include('products.urls')),
    path('api/categories/', include('categories.urls')),
    path('api/orders/',     include('orders.urls')),
    path('api/payments/',   include('payments.urls')),
    # ... your existing routes
]
```

---

## 7 · React Frontend Setup

Copy `frontend_api.ts` to `src/api/djangoApi.ts` in your React project.

Add to your `.env` (React side):
```
VITE_DJANGO_API_URL=http://localhost:8000/api
```

### After Firebase sign-in — sync the user:
```typescript
import { signInWithEmailAndPassword, getAuth } from 'firebase/auth';
import api from '@/api/djangoApi';

const auth = getAuth();
await signInWithEmailAndPassword(auth, email, password);
await api.auth.syncUser(displayName);   // ← creates/updates Firestore profile
```

### Add a product (admin):
```typescript
await api.products.create({
  name: 'Premium T-Shirt',
  description: 'Soft cotton tee',
  price: 29.99,
  category: 'apparel',
  images: ['https://...'],
  stock: 100,
  featured: true,
});
```

### Purchase flow:
```typescript
// 1 — Create order (validates stock, decrements it)
const order = await api.orders.create({
  items: [{ productId: 'abc123', quantity: 2 }],
  shippingAddress: { line1: '123 Main St', city: 'Dubai', country: 'AE' },
});

// 2 — Get Stripe publishable key (do this once on app load)
const { publishableKey } = await api.payments.getConfig();
const stripe = await loadStripe(publishableKey);

// 3 — Create PaymentIntent
const { clientSecret } = await api.payments.createIntent(order.id);

// 4 — Confirm payment using Stripe.js Elements
const { error } = await stripe.confirmPayment({
  elements,                    // your <PaymentElement />
  clientSecret,
  confirmParams: { return_url: 'https://yoursite.com/order-success' },
});
```

### Stripe webhook flow (automatic):
```
Stripe → POST /api/payments/webhook/
         └─ payment_intent.succeeded → order.status = 'paid'
         └─ payment_intent.canceled  → order.status = 'cancelled'
```

---

## 8 · API Reference

### Auth  `/api/auth/`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/sync-user/` | User | Create/update Firestore profile after login |
| GET  | `/me/` | User | Get current user's profile |
| GET  | `/users/` | Admin | List all users |
| PATCH | `/users/<uid>/role/` | Admin | Change user role |

### Products  `/api/products/`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Public | List products (filter by category/featured/search) |
| GET | `/<id>/` | Public | Get single product |
| POST | `/create/` | Admin | Add new product |
| PUT | `/<id>/update/` | Admin | Full update |
| PATCH | `/<id>/patch/` | Admin | Partial update (e.g. stock only) |
| DELETE | `/<id>/delete/` | Admin | Remove product |

### Categories  `/api/categories/`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Public | List categories |
| POST | `/create/` | Admin | Add category |
| PUT | `/<id>/update/` | Admin | Update category |
| DELETE | `/<id>/delete/` | Admin | Delete category |

### Orders  `/api/orders/`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/create/` | User | Create order + decrement stock |
| GET | `/` | User/Admin | Own orders (user) or all orders (admin) |
| GET | `/<id>/` | Owner/Admin | Order detail |
| PATCH | `/<id>/status/` | Admin | Update status |

### Payments  `/api/payments/`
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/config/` | Public | Get Stripe publishable key |
| POST | `/create-intent/` | User | Create PaymentIntent for an order |
| POST | `/webhook/` | Stripe | Webhook — mark order paid/cancelled |

---

## 9 · Running Locally

```bash
# Install deps
pip install -r requirements.txt

# Copy and fill in secrets
cp .env.example .env

# Migrate (only needed if you keep Django models alongside Firestore)
python manage.py migrate

# Start
python manage.py runserver
```

React frontend:
```bash
npm install
npm run dev       # starts on http://localhost:3000
```

---

## 10 · Security Notes

- **Never** commit `serviceAccountKey.json` or `.env` to git.
- The `STRIPE_WEBHOOK_SECRET` must be set in production — it prevents spoofed webhook calls.
- The Firestore rules in `firestore.rules` enforce the same permissions as the Django views — both layers protect your data.
- Admin status is determined by the user's `role` field in Firestore **or** a matching `STORE_ADMIN_EMAIL`. Promote your first admin directly in Firestore console.
