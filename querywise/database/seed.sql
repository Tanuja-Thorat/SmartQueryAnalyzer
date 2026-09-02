-- =============================================================================
-- QueryWise Demo Database — Sample Data
-- =============================================================================
-- Run this AFTER schema.sql, against the same database.
--
-- Safe to re-run: the TRUNCATE ... RESTART IDENTITY CASCADE below wipes all
-- rows (and resets auto-increment IDs) before re-inserting, so running this
-- script multiple times never creates duplicates.
--
-- Uses generate_series() so we get realistic volume (tens of thousands of
-- rows on the bigger tables) without writing thousands of INSERT statements
-- by hand - enough for PostgreSQL's planner to produce meaningful,
-- realistic EXPLAIN plans (sequential scans on unindexed filters, index
-- scans where indexes exist, real join costs, etc).
-- =============================================================================

TRUNCATE TABLE
    reviews, shipments, payments, order_items, orders,
    addresses, products, suppliers, categories,
    customers, employees, departments
    RESTART IDENTITY CASCADE;

-- -----------------------------------------------------------------------------
-- departments (10 rows)
-- -----------------------------------------------------------------------------
INSERT INTO departments (name, location)
VALUES
    ('Engineering', 'Bangalore'),
    ('Sales', 'Mumbai'),
    ('Marketing', 'Pune'),
    ('Human Resources', 'Delhi'),
    ('Finance', 'Hyderabad'),
    ('Customer Support', 'Chennai'),
    ('Product Management', 'Bangalore'),
    ('Legal', 'Delhi'),
    ('Operations', 'Pune'),
    ('IT Infrastructure', 'Hyderabad');

-- -----------------------------------------------------------------------------
-- employees (800 rows) — department_id 1..10
-- -----------------------------------------------------------------------------
INSERT INTO employees (first_name, last_name, email, department_id, salary, hire_date)
SELECT
    'Employee' || i,
    'Last' || i,
    'employee' || i || '@querywise.demo',
    (1 + floor(random() * 10))::int,
    (30000 + random() * 150000)::numeric(10,2),
    (CURRENT_DATE - (random() * 3650)::int)
FROM generate_series(1, 800) AS s(i);

-- -----------------------------------------------------------------------------
-- customers (1,500 rows)
-- -----------------------------------------------------------------------------
INSERT INTO customers (first_name, last_name, email, city, country, created_at)
SELECT
    'Customer' || i,
    'Surname' || i,
    'customer' || i || '@querywise.demo',
    (ARRAY['Pune','Mumbai','Delhi','Bangalore','Chennai','Hyderabad','Kolkata','Ahmedabad'])[1 + floor(random()*8)],
    (ARRAY['India','USA','UK','Germany','Canada','Australia'])[1 + floor(random()*6)],
    NOW() - (random() * interval '900 days')
FROM generate_series(1, 1500) AS s(i);

-- -----------------------------------------------------------------------------
-- addresses (1,800 rows) — customer_id 1..1500
-- -----------------------------------------------------------------------------
INSERT INTO addresses (customer_id, address_line, city, state, postal_code, country, is_default)
SELECT
    (1 + floor(random() * 1500))::int,
    (100 + i) || ' Demo Street',
    (ARRAY['Pune','Mumbai','Delhi','Bangalore','Chennai','Hyderabad'])[1 + floor(random()*6)],
    (ARRAY['Maharashtra','Delhi','Karnataka','Tamil Nadu','Telangana'])[1 + floor(random()*5)],
    (100000 + floor(random() * 899999))::text,
    'India',
    (random() < 0.5)
FROM generate_series(1, 1800) AS s(i);

-- -----------------------------------------------------------------------------
-- categories (25 rows)
-- -----------------------------------------------------------------------------
INSERT INTO categories (name, description)
SELECT
    'Category ' || i,
    'Demo product category number ' || i
FROM generate_series(1, 25) AS s(i);

-- -----------------------------------------------------------------------------
-- suppliers (80 rows)
-- -----------------------------------------------------------------------------
INSERT INTO suppliers (name, contact_email, country)
SELECT
    'Supplier ' || i,
    'supplier' || i || '@querywise.demo',
    (ARRAY['India','China','USA','Germany','Vietnam'])[1 + floor(random()*5)]
FROM generate_series(1, 80) AS s(i);

-- -----------------------------------------------------------------------------
-- products (800 rows) — category_id 1..25, supplier_id 1..80
-- -----------------------------------------------------------------------------
INSERT INTO products (name, category_id, supplier_id, price, stock_qty)
SELECT
    'Product ' || i,
    (1 + floor(random() * 25))::int,
    (1 + floor(random() * 80))::int,
    (5 + random() * 2995)::numeric(10,2),
    (random() * 1000)::int
FROM generate_series(1, 800) AS s(i);

-- -----------------------------------------------------------------------------
-- orders (8,000 rows) — customer_id 1..1500
-- -----------------------------------------------------------------------------
INSERT INTO orders (customer_id, order_date, status, total_amount)
SELECT
    (1 + floor(random() * 1500))::int,
    NOW() - (random() * interval '730 days'),
    (ARRAY['pending','processing','shipped','delivered','cancelled','completed'])[1 + floor(random()*6)],
    (10 + random() * 4990)::numeric(12,2)
FROM generate_series(1, 8000) AS s(i);

-- -----------------------------------------------------------------------------
-- order_items (24,000 rows) — order_id 1..8000, product_id 1..800
-- -----------------------------------------------------------------------------
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    (1 + floor(random() * 8000))::int,
    (1 + floor(random() * 800))::int,
    (1 + floor(random() * 5))::int,
    (5 + random() * 995)::numeric(10,2)
FROM generate_series(1, 24000) AS s(i);

-- -----------------------------------------------------------------------------
-- payments (8,000 rows) — one payment per order, order_id 1..8000
-- -----------------------------------------------------------------------------
INSERT INTO payments (order_id, payment_date, amount, payment_method, status)
SELECT
    i,
    NOW() - (random() * interval '730 days'),
    (10 + random() * 4990)::numeric(12,2),
    (ARRAY['card','upi','netbanking','wallet','cod'])[1 + floor(random()*5)],
    (ARRAY['completed','pending','failed','refunded'])[1 + floor(random()*4)]
FROM generate_series(1, 8000) AS s(i);

-- -----------------------------------------------------------------------------
-- shipments (6,000 rows) — a subset of orders (order_id 1..6000)
-- -----------------------------------------------------------------------------
INSERT INTO shipments (order_id, shipped_date, delivery_date, carrier, status)
SELECT
    i,
    NOW() - (random() * interval '700 days'),
    NOW() - (random() * interval '690 days'),
    (ARRAY['BlueDart','Delhivery','DTDC','FedEx','IndiaPost'])[1 + floor(random()*5)],
    (ARRAY['processing','shipped','in_transit','delivered','returned'])[1 + floor(random()*5)]
FROM generate_series(1, 6000) AS s(i);

-- -----------------------------------------------------------------------------
-- reviews (5,000 rows) — customer_id 1..1500, product_id 1..800
-- -----------------------------------------------------------------------------
INSERT INTO reviews (customer_id, product_id, rating, comment, created_at)
SELECT
    (1 + floor(random() * 1500))::int,
    (1 + floor(random() * 800))::int,
    (1 + floor(random() * 5))::int,
    'Demo review comment #' || i,
    NOW() - (random() * interval '600 days')
FROM generate_series(1, 5000) AS s(i);

-- =============================================================================
-- Refresh planner statistics so EXPLAIN reflects realistic row estimates and
-- actually chooses sequential scans / index scans the way it would in
-- production.
-- =============================================================================
ANALYZE departments;
ANALYZE employees;
ANALYZE customers;
ANALYZE addresses;
ANALYZE categories;
ANALYZE suppliers;
ANALYZE products;
ANALYZE orders;
ANALYZE order_items;
ANALYZE payments;
ANALYZE shipments;
ANALYZE reviews;
