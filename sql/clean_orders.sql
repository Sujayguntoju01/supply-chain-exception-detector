-- Clean the raw DataCo export into an `orders` table with order-time columns only.
-- - renames columns to snake_case
-- - parses order timestamps
-- - drops cancelled orders and rows with invalid quantities
-- - de-duplicates order items
CREATE OR REPLACE TABLE orders AS
SELECT
    "Order Id"                                             AS order_id,
    "Order Item Id"                                        AS order_item_id,
    strptime("order date (DateOrders)", '%m/%d/%Y %H:%M')  AS order_ts,
    "Type"                                                 AS payment_type,
    "Shipping Mode"                                        AS shipping_mode,
    CAST("Days for shipment (scheduled)" AS INTEGER)       AS days_scheduled,
    CAST("Days for shipping (real)" AS INTEGER)            AS days_real,
    "Market"                                               AS market,
    "Order Region"                                         AS order_region,
    "Customer Segment"                                     AS customer_segment,
    "Category Name"                                        AS category_name,
    CAST("Order Item Quantity" AS INTEGER)                 AS quantity,
    CAST("Order Item Product Price" AS DOUBLE)             AS unit_price,
    CAST("Order Item Discount Rate" AS DOUBLE)             AS discount_rate,
    CAST("Order Item Profit Ratio" AS DOUBLE)              AS profit_ratio,
    CAST("Sales" AS DOUBLE)                                AS sales,
    CAST("Order Profit Per Order" AS DOUBLE)               AS profit,
    "Order Status"                                         AS order_status,
    CAST("Late_delivery_risk" AS INTEGER)                  AS is_late
FROM raw_orders
WHERE "Order Id" IS NOT NULL
  AND "Order Item Quantity" > 0
  AND "Order Status" <> 'CANCELED'
QUALIFY row_number() OVER (PARTITION BY "Order Item Id" ORDER BY "Order Id") = 1;
