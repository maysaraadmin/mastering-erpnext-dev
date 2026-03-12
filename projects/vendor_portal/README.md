# Vendor Portal

REST API-based vendor portal for external system integration.

## Features

- RESTful API for vendor access
- Token-based authentication
- Purchase order retrieval and acknowledgement
- Webhook notifications for PO events
- Secure API key management
- Rate limiting and access control

## Installation

```bash
cd ~/frappe-bench
bench get-app vendor_portal_app /path/to/projects/vendor_portal/vendor_portal_app
bench --site your-site.local install-app vendor_portal_app
bench --site your-site.local migrate
```

## API Endpoints

### Authentication

**POST** `/api/method/vendor_portal_app.vendor_portal.api.vendor.authenticate`

Request:
```json
{
  "api_key": "your-api-key",
  "api_secret": "your-api-secret"
}
```

Response:
```json
{
  "success": true,
  "token": "session-token",
  "vendor": {
    "name": "VENDOR-001",
    "vendor_name": "ABC Supplies",
    "email": "vendor@example.com"
  }
}
```

### Get Purchase Orders

**GET** `/api/method/vendor_portal_app.vendor_portal.api.vendor.get_purchase_orders`

Headers:
```
Authorization: Bearer {token}
```

Parameters:
- `vendor`: Vendor ID (required)
- `status`: Filter by status (optional)

Response:
```json
{
  "success": true,
  "data": [
    {
      "name": "PO-0001",
      "transaction_date": "2026-03-01",
      "schedule_date": "2026-03-15",
      "grand_total": 50000,
      "status": "To Receive"
    }
  ]
}
```

### Get Purchase Order Details

**GET** `/api/method/vendor_portal_app.vendor_portal.api.purchase_order.get_purchase_order_details`

Headers:
```
Authorization: Bearer {token}
```

Parameters:
- `purchase_order`: PO ID (required)

### Acknowledge Purchase Order

**POST** `/api/method/vendor_portal_app.vendor_portal.api.purchase_order.acknowledge_purchase_order`

Headers:
```
Authorization: Bearer {token}
```

Request:
```json
{
  "purchase_order": "PO-0001",
  "acknowledgement_date": "2026-03-12",
  "notes": "Order received and processing"
}
```

## Webhooks

Configure webhook URL in Vendor master to receive notifications.

### Purchase Order Submitted

Event: `purchase_order.submitted`

Payload:
```json
{
  "event": "purchase_order.submitted",
  "purchase_order": "PO-0001",
  "transaction_date": "2026-03-12",
  "schedule_date": "2026-03-20",
  "grand_total": 50000,
  "items": [
    {
      "item_code": "ITEM-001",
      "qty": 10,
      "rate": 5000
    }
  ]
}
```

## Security

- Token-based authentication with 24-hour expiry
- API key/secret stored securely
- Rate limiting on API endpoints
- Vendor-specific data access control
- HTTPS required for production

## Testing

```bash
# Test authentication
curl -X POST http://localhost:8000/api/method/vendor_portal_app.vendor_portal.api.vendor.authenticate \
  -H "Content-Type: application/json" \
  -d '{"api_key":"test-key","api_secret":"test-secret"}'

# Test get purchase orders
curl -X GET "http://localhost:8000/api/method/vendor_portal_app.vendor_portal.api.vendor.get_purchase_orders?vendor=VENDOR-001" \
  -H "Authorization: Bearer {token}"
```

## License

MIT License
