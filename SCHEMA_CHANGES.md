# Database Schema Changes Summary

## OrderItem Table Added

Order items are now stored in a separate `order_items` table instead of as JSON in the orders table.

### New Table: order_items

```sql
CREATE TABLE order_items (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    product_name VARCHAR NOT NULL,
    quantity INTEGER NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    total NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Benefits

1. **Better Normalization**: Follows database best practices
2. **Easier Queries**: Can query order items directly
3. **Data Integrity**: Foreign key constraints ensure data consistency
4. **Flexibility**: Can add more fields to order items without affecting orders table
5. **Performance**: Better indexing and query optimization

### Relationships

```
Order (1) ----< (N) OrderItem (N) >---- (1) Product
```

- One order can have many order items
- Each order item references one product (nullable in case product is deleted)
- Product name is stored to preserve order history even if product is deleted

### Migration Required

After pulling these changes, you'll need to:

1. Create a new migration:
   ```bash
   make makemigrations
   ```

2. Apply the migration:
   ```bash
   make migrate
   ```

This will create the `order_items` table and remove the `items` JSON column from the `orders` table.

### API Changes

The API remains the same - order items are still sent as an array in the request body, but they're now stored in a separate table:

```json
{
  "organization_id": "uuid",
  "customer_name": "John Doe",
  "customer_phone": "+1234567890",
  "items": [
    {
      "product_id": "uuid",
      "product_name": "Product Name",
      "quantity": 2,
      "price": 10.00,
      "total": 20.00
    }
  ]
}
```

Response now includes full OrderItem objects with IDs:

```json
{
  "id": "order-uuid",
  "items": [
    {
      "id": "order-item-uuid",
      "order_id": "order-uuid",
      "product_id": "product-uuid",
      "product_name": "Product Name",
      "quantity": 2,
      "price": 10.00,
      "total": 20.00,
      "created_at": "2026-01-10T21:39:44Z"
    }
  ],
  // ... other order fields
}
```
