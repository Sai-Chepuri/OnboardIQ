# Payment Gateway API Integration Guide
Access-Roles: [engineering, ops, admin]

This document describes how to integrate the Core Payment Gateway into internal services.

## Base URL
The staging and production endpoints are:
* **Staging:** `https://api.staging.payments.company.com/v2`
* **Production:** `https://api.payments.company.com/v2`

## Authentication
All API requests must include the API key in the request headers:
```http
Authorization: Bearer sec_key_live_abcdef123456
```

> [!WARNING]
> Never commit live API keys to Git. Use Secret Manager to retrieve keys at runtime.

## Endpoints

### 1. Create a Payment Intent
Create a payment session to accept checkout transactions.

* **HTTP Method:** `POST`
* **Path:** `/payment-intents`
* **Request Body:**
| Field | Type | Description | Required |
|---|---|---|---|
| `amount` | integer | Amount in cents (e.g. 1000 for $10.00) | Yes |
| `currency` | string | ISO 4-letter currency code (e.g. `USD`) | Yes |
| `idempotency_key` | string | Unique UUID to prevent double-charging | Yes |
