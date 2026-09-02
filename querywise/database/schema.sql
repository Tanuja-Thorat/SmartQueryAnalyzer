-- =============================================================================
-- QueryWise Demo Database Schema — "TARGET" database (the DB being analyzed)
-- =============================================================================
-- A realistic 12-table e-commerce / company-management schema, purpose-built
-- to demonstrate QueryWise's Query Analyzer and Index Advisor:
--   - WHERE filtering, multi-condition WHERE, ORDER BY, GROUP BY, aggregates
--   - single JOIN, multi-table JOIN, foreign-key relationships
--   - some foreign keys ARE indexed (so those queries show fast Index Scans)
--   - some commonly-filtered columns are INTENTIONALLY left unindexed, so
--     QueryWise has real Sequential Scans to detect and recommend fixes for
--
-- Safe to re-run: every table is dropped first, so running this script
-- always leaves you with a clean, correctly-structured schema.
-- Run seed.sql AFTER this file.
-- =============================================================================

DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS shipments CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS addresses CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

-- -----------------------------------------------------------------------------
-- 1. departments
-- -----------------------------------------------------------------------------
CREATE TABLE departments (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    location    VARCHAR(100)
);

-- -----------------------------------------------------------------------------
-- 2. employees  -> departments
--    department_id and salary are INTENTIONALLY left unindexed.
-- -----------------------------------------------------------------------------
CREATE TABLE employees (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(50) NOT NULL,
    last_name       VARCHAR(50) NOT NULL,
    email           VARCHAR(150) UNIQUE,
    department_id   INTEGER NOT NULL REFERENCES departments(id),
    salary          NUMERIC(10, 2) NOT NULL,
    hire_date       DATE NOT NULL
);

-- -----------------------------------------------------------------------------
-- 3. customers
--    city and created_at are INTENTIONALLY left unindexed.
-- -----------------------------------------------------------------------------
CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    first_name  VARCHAR(50) NOT NULL,
    last_name   VARCHAR(50) NOT NULL,
    email       VARCHAR(150) UNIQUE,
    city        VARCHAR(100),
    country     VARCHAR(100),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 4. addresses -> customers (indexed FK)
-- -----------------------------------------------------------------------------
CREATE TABLE addresses (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    address_line    VARCHAR(200) NOT NULL,
    city            VARCHAR(100),
    state           VARCHAR(100),
    postal_code     VARCHAR(20),
    country         VARCHAR(100),
    is_default      BOOLEAN DEFAULT FALSE
);

-- -----------------------------------------------------------------------------
-- 5. categories
-- -----------------------------------------------------------------------------
CREATE TABLE categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- -----------------------------------------------------------------------------
-- 6. suppliers
-- -----------------------------------------------------------------------------
CREATE TABLE suppliers (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    contact_email   VARCHAR(150),
    country         VARCHAR(100)
);

-- -----------------------------------------------------------------------------
-- 7. products -> categories, suppliers (both FKs indexed)
--    price is INTENTIONALLY left unindexed.
-- -----------------------------------------------------------------------------
CREATE TABLE products (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    category_id     INTEGER NOT NULL REFERENCES categories(id),
    supplier_id     INTEGER NOT NULL REFERENCES suppliers(id),
    price           NUMERIC(10, 2) NOT NULL,
    stock_qty       INTEGER DEFAULT 0
);

-- -----------------------------------------------------------------------------
-- 8. orders -> customers (indexed FK)
--    status and order_date are INTENTIONALLY left unindexed.
-- -----------------------------------------------------------------------------
CREATE TABLE orders (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    order_date      TIMESTAMP NOT NULL DEFAULT NOW(),
    status          VARCHAR(30) NOT NULL DEFAULT 'pending',
    total_amount    NUMERIC(12, 2) NOT NULL DEFAULT 0
);

-- -----------------------------------------------------------------------------
-- 9. order_items -> orders, products (both FKs indexed)
-- -----------------------------------------------------------------------------
CREATE TABLE order_items (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER NOT NULL REFERENCES orders(id),
    product_id  INTEGER NOT NULL REFERENCES products(id),
    quantity    INTEGER NOT NULL DEFAULT 1,
    unit_price  NUMERIC(10, 2) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 10. payments -> orders (indexed FK)
-- -----------------------------------------------------------------------------
CREATE TABLE payments (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    payment_date    TIMESTAMP NOT NULL DEFAULT NOW(),
    amount          NUMERIC(12, 2) NOT NULL,
    payment_method  VARCHAR(30) NOT NULL DEFAULT 'card',
    status          VARCHAR(30) NOT NULL DEFAULT 'completed'
);

-- -----------------------------------------------------------------------------
-- 11. shipments -> orders (indexed FK)
-- -----------------------------------------------------------------------------
CREATE TABLE shipments (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    shipped_date    TIMESTAMP,
    delivery_date   TIMESTAMP,
    carrier         VARCHAR(50),
    status          VARCHAR(30) NOT NULL DEFAULT 'processing'
);

-- -----------------------------------------------------------------------------
-- 12. reviews -> customers, products (both FKs indexed)
-- -----------------------------------------------------------------------------
CREATE TABLE reviews (
    id          SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    product_id  INTEGER NOT NULL REFERENCES products(id),
    rating      SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Indexes — some foreign keys ARE indexed (realistic baseline), while several
-- commonly-filtered columns are deliberately left WITHOUT an index so the
-- Index Advisor has real recommendations to make. See README for the full
-- "indexed vs. intentionally unindexed" list.
-- =============================================================================

CREATE INDEX idx_addresses_customer_id  ON addresses(customer_id);
CREATE INDEX idx_products_category_id   ON products(category_id);
CREATE INDEX idx_products_supplier_id   ON products(supplier_id);
CREATE INDEX idx_orders_customer_id     ON orders(customer_id);
CREATE INDEX idx_order_items_order_id   ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_payments_order_id      ON payments(order_id);
CREATE INDEX idx_shipments_order_id     ON shipments(order_id);
CREATE INDEX idx_reviews_customer_id    ON reviews(customer_id);
CREATE INDEX idx_reviews_product_id     ON reviews(product_id);

-- Intentionally NOT indexed (left for the Index Advisor to detect):
--   employees.department_id
--   employees.salary
--   customers.city
--   customers.created_at
--   products.price
--   orders.status
--   orders.order_date

-- Optional: install hypopg for more accurate What-If index simulations.
-- Requires the hypopg extension package to be installed on your PostgreSQL
-- server first (e.g. `apt install postgresql-16-hypopg` or via your package
-- manager). If it's not available, QueryWise automatically falls back to a
-- heuristic estimate instead - everything still works either way.
-- CREATE EXTENSION IF NOT EXISTS hypopg;
