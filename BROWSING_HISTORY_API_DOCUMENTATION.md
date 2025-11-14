# Browsing History API Documentation

## Overview
The Browsing History API allows tracking and retrieving user browsing history, displaying recently viewed products and categories based on user activity.

## Authentication
All endpoints require authentication using Token authentication. Include the token in the Authorization header:
```
Authorization: Token <your_token>
```

## Endpoints

### 1. Track Browsing History
**POST** `/api/browsing-history/track/`

Track when a user views a product.

**Request Body:**
```json
{
  "product_id": 1
}
```

**Response (201 Created):**
```json
{
  "message": "Browsing history tracked successfully",
  "data": {
    "id": 1,
    "product": {
      "id": 1,
      "title": "Product Name",
      "slug": "product-name",
      "main_image": "https://example.com/image.jpg",
      "price": "1000.00",
      "old_price": "1200.00",
      "average_rating": 4.5,
      "review_count": 10,
      "category": {
        "name": "Category Name",
        "slug": "category-name"
      }
    },
    "category": {
      "id": 1,
      "name": "Category Name",
      "slug": "category-name"
    },
    "subcategory": null,
    "viewed_at": "2025-01-10T10:30:00Z",
    "view_count": 1,
    "last_viewed": "2025-01-10T10:30:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request`: product_id is required
- `404 Not Found`: Product not found
- `401 Unauthorized`: Authentication required

---

### 2. Get Browsing History
**GET** `/api/browsing-history/`

Get user's browsing history with recently viewed products.

**Query Parameters:**
- `limit` (optional): Number of items to return (default: 20)

**Example Request:**
```
GET /api/browsing-history/?limit=10
```

**Response (200 OK):**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "title": "Product Name",
        "slug": "product-name",
        "main_image": "https://example.com/image.jpg",
        "price": "1000.00",
        "old_price": "1200.00",
        "average_rating": 4.5,
        "review_count": 10,
        "category": {
          "name": "Category Name",
          "slug": "category-name"
        }
      },
      "category": {
        "id": 1,
        "name": "Category Name",
        "slug": "category-name"
      },
      "subcategory": null,
      "viewed_at": "2025-01-10T10:30:00Z",
      "view_count": 3,
      "last_viewed": "2025-01-10T15:45:00Z"
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized`: Authentication required

---

### 3. Get Browsed Categories
**GET** `/api/browsing-history/categories/`

Get categories based on user's browsing history, ordered by view count.

**Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "Office Furniture",
      "slug": "office-furniture",
      "image": "https://example.com/category.jpg",
      "description": "Category description",
      "product_count": 245,
      "view_count": 15,
      "browsed_product_count": 12
    }
  ]
}
```

**Error Responses:**
- `401 Unauthorized`: Authentication required

---

### 4. Clear Browsing History
**DELETE** `/api/browsing-history/clear/`

Clear user's browsing history.

**Query Parameters:**
- `product_id` (optional): Clear specific product from history. If not provided, clears all history.

**Example Requests:**
```
DELETE /api/browsing-history/clear/                    # Clear all
DELETE /api/browsing-history/clear/?product_id=1       # Clear specific product
```

**Response (200 OK):**
```json
{
  "message": "Cleared 5 item(s) from browsing history"
}
```

**Error Responses:**
- `401 Unauthorized`: Authentication required

---

## Integration Guide

### Frontend Integration

1. **Track Product Views**: Call `trackBrowsingHistory(productId)` when a user views a product page:
```typescript
import { productAPI } from './services/api';

// In product detail page
useEffect(() => {
  if (productId && isAuthenticated) {
    productAPI.trackBrowsingHistory(productId);
  }
}, [productId]);
```

2. **Display Browsing History**: Use `getBrowsingHistory()` to fetch and display recently viewed products:
```typescript
const response = await productAPI.getBrowsingHistory(20);
const historyItems = response.data.results;
```

3. **Display Browsed Categories**: Use `getBrowsedCategories()` to show categories based on browsing:
```typescript
const response = await productAPI.getBrowsedCategories();
const categories = response.data.results;
```

### Backend Integration

1. **Automatic Tracking**: Consider adding middleware or signal handlers to automatically track product views when users access product detail pages.

2. **Data Privacy**: Ensure compliance with data privacy regulations. Consider adding:
   - Option to disable tracking
   - Data retention policies
   - User consent mechanisms

## Testing

### Test API Endpoints

1. **Track browsing history:**
```bash
curl -X POST http://localhost:8000/api/browsing-history/track/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1}'
```

2. **Get browsing history:**
```bash
curl -X GET http://localhost:8000/api/browsing-history/?limit=10 \
  -H "Authorization: Token YOUR_TOKEN"
```

3. **Get browsed categories:**
```bash
curl -X GET http://localhost:8000/api/browsing-history/categories/ \
  -H "Authorization: Token YOUR_TOKEN"
```

4. **Clear browsing history:**
```bash
curl -X DELETE http://localhost:8000/api/browsing-history/clear/ \
  -H "Authorization: Token YOUR_TOKEN"
```

## Notes
- Browsing history is user-specific and requires authentication
- View counts are automatically incremented when the same product is viewed again
- Categories are aggregated and sorted by total view count
- History is ordered by `last_viewed` timestamp (most recent first)

