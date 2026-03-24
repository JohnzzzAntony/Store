/**
 * frontend_api.ts
 * ─────────────────────────────────────────────────────────────────────────────
 * Drop this file into your React project (e.g. src/api/djangoApi.ts).
 * It replaces direct Firestore calls in your React components with
 * calls to the Django REST backend.
 *
 * Usage:
 *   import api from '@/api/djangoApi';
 *   const products = await api.products.list();
 *   const order    = await api.orders.create({ items, shippingAddress });
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { getAuth } from 'firebase/auth';

const BASE_URL = import.meta.env.VITE_DJANGO_API_URL ?? 'http://localhost:8000/api';

// ── Token helper ─────────────────────────────────────────────────────────────
async function getIdToken(): Promise<string | null> {
  const user = getAuth().currentUser;
  if (!user) return null;
  return user.getIdToken();
}

// ── Core fetch wrapper ───────────────────────────────────────────────────────
async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  requireAuth = false,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (requireAuth) {
    const token = await getIdToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err?.error ?? `Request failed: ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// AUTH
// ─────────────────────────────────────────────────────────────────────────────
export const authApi = {
  /** Call after every Firebase sign-in to sync the user in Django/Firestore. */
  syncUser(displayName?: string, photoURL?: string) {
    return apiFetch('/auth/sync-user/', {
      method: 'POST',
      body: JSON.stringify({ displayName, photoURL }),
    }, true);
  },

  /** Returns the current user's Firestore profile. */
  getMe() {
    return apiFetch<Record<string, unknown>>('/auth/me/', {}, true);
  },

  /** Admin: list all users. */
  listUsers() {
    return apiFetch<unknown[]>('/auth/users/', {}, true);
  },

  /** Admin: change a user's role. */
  setUserRole(uid: string, role: 'admin' | 'customer') {
    return apiFetch(`/auth/users/${uid}/role/`, {
      method: 'PATCH',
      body: JSON.stringify({ role }),
    }, true);
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// PRODUCTS
// ─────────────────────────────────────────────────────────────────────────────
export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  images: string[];
  stock: number;
  featured: boolean;
  createdAt: string;
}

export const productsApi = {
  list(params?: { category?: string; featured?: boolean; search?: string }) {
    const qs = new URLSearchParams();
    if (params?.category) qs.set('category', params.category);
    if (params?.featured) qs.set('featured', 'true');
    if (params?.search)   qs.set('search',   params.search);
    return apiFetch<Product[]>(`/products/?${qs}`);
  },

  get(id: string) {
    return apiFetch<Product>(`/products/${id}/`);
  },

  /** Admin only */
  create(data: Omit<Product, 'id' | 'createdAt'>) {
    return apiFetch<Product>('/products/create/', {
      method: 'POST',
      body: JSON.stringify(data),
    }, true);
  },

  /** Admin only */
  update(id: string, data: Omit<Product, 'id' | 'createdAt'>) {
    return apiFetch<Product>(`/products/${id}/update/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, true);
  },

  /** Admin only — partial update */
  patch(id: string, data: Partial<Omit<Product, 'id' | 'createdAt'>>) {
    return apiFetch(`/products/${id}/patch/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }, true);
  },

  /** Admin only */
  delete(id: string) {
    return apiFetch(`/products/${id}/delete/`, { method: 'DELETE' }, true);
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// CATEGORIES
// ─────────────────────────────────────────────────────────────────────────────
export interface Category {
  id: string;
  name: string;
  slug: string;
  image: string;
}

export const categoriesApi = {
  list() {
    return apiFetch<Category[]>('/categories/');
  },
  create(data: Omit<Category, 'id'>) {
    return apiFetch<Category>('/categories/create/', {
      method: 'POST',
      body: JSON.stringify(data),
    }, true);
  },
  update(id: string, data: Omit<Category, 'id'>) {
    return apiFetch<Category>(`/categories/${id}/update/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, true);
  },
  delete(id: string) {
    return apiFetch(`/categories/${id}/delete/`, { method: 'DELETE' }, true);
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// ORDERS
// ─────────────────────────────────────────────────────────────────────────────
export interface OrderItem {
  productId: string;
  quantity: number;
}

export interface ShippingAddress {
  line1: string;
  city: string;
  country: string;
  postalCode?: string;
}

export interface Order {
  id: string;
  userId: string;
  items: Array<OrderItem & { name: string; price: number; subtotal: number }>;
  totalAmount: number;
  status: 'pending' | 'paid' | 'shipped' | 'delivered' | 'cancelled';
  paymentIntentId: string;
  shippingAddress: ShippingAddress;
  createdAt: string;
}

export const ordersApi = {
  /** Creates an order + decrements stock. Returns the new order with its id. */
  create(data: { items: OrderItem[]; shippingAddress: ShippingAddress }) {
    return apiFetch<Order>('/orders/create/', {
      method: 'POST',
      body: JSON.stringify(data),
    }, true);
  },

  list() {
    return apiFetch<Order[]>('/orders/', {}, true);
  },

  get(id: string) {
    return apiFetch<Order>(`/orders/${id}/`, {}, true);
  },

  /** Admin only */
  updateStatus(id: string, status: Order['status']) {
    return apiFetch(`/orders/${id}/status/`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }, true);
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// PAYMENTS
// ─────────────────────────────────────────────────────────────────────────────
export const paymentsApi = {
  /** Fetch Stripe publishable key (used to initialise loadStripe()). */
  getConfig() {
    return apiFetch<{ publishableKey: string }>('/payments/config/');
  },

  /**
   * Creates a Stripe PaymentIntent for the given orderId.
   * Returns { clientSecret, paymentIntentId, amount, currency }.
   */
  createIntent(orderId: string) {
    return apiFetch<{
      clientSecret: string;
      paymentIntentId: string;
      amount: number;
      currency: string;
    }>('/payments/create-intent/', {
      method: 'POST',
      body: JSON.stringify({ orderId }),
    }, true);
  },
};

// ── Default export (convenience) ─────────────────────────────────────────────
const api = {
  auth:       authApi,
  products:   productsApi,
  categories: categoriesApi,
  orders:     ordersApi,
  payments:   paymentsApi,
};

export default api;
