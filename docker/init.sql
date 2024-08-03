-- Create Currencies table
CREATE TABLE currencies (
    currency_id SERIAL PRIMARY KEY,
    currency_code VARCHAR(3) NOT NULL UNIQUE,
    currency_name VARCHAR(50) NOT NULL
);

-- Create Units table
CREATE TABLE units (
    unit_id SERIAL PRIMARY KEY,
    unit_name VARCHAR(25) NOT NULL UNIQUE
);

-- Create Suppliers table
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL,
    postal_code VARCHAR(10) NOT NULL
);

-- Create Brands table
CREATE TABLE brands (
    brand_id SERIAL PRIMARY KEY,
    brand_name VARCHAR(255) NOT NULL UNIQUE
);

-- Create Materials table
CREATE TABLE materials (
    material_id SERIAL PRIMARY KEY,
    material_name VARCHAR(50) NOT NULL UNIQUE
);

-- Create Deposit_Types table
CREATE TABLE deposit_types (
    deposit_type_id SERIAL PRIMARY KEY,
    deposit_type_name VARCHAR(50) NOT NULL UNIQUE
);

-- Create Beers table
CREATE TABLE beers (
    beer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand_id INTEGER REFERENCES brands(brand_id),
    description TEXT,
    alcohol_content NUMERIC(4, 2)
);

-- Create main Beer_Data table
CREATE TABLE beer_data (
    id SERIAL PRIMARY KEY,
    beer_id INTEGER REFERENCES beers(beer_id),
    price NUMERIC(10, 2) NOT NULL,
    currency_id INTEGER REFERENCES currencies(currency_id),
    quantity NUMERIC(10, 2) NOT NULL,
    unit_id INTEGER REFERENCES units(unit_id),
    supplier_id INTEGER REFERENCES suppliers(supplier_id),
    material_id INTEGER REFERENCES materials(material_id),
    deposit_type_id INTEGER REFERENCES deposit_types(deposit_type_id),
    article_number VARCHAR(50),
    delivery_time VARCHAR(50),
    scrape_date TIMESTAMP NOT NULL
);

-- Create views for the dashboard
CREATE VIEW beer_price_overview AS
SELECT
    b.name AS beer_name,
    br.brand_name,
    bd.price,
    c.currency_code,
    bd.quantity,
    u.unit_name,
    s.supplier_name,
    s.postal_code,
    m.material_name,
    dt.deposit_type_name,
    b.alcohol_content,
    bd.scrape_date
FROM
    beer_data bd
JOIN beers b ON bd.beer_id = b.beer_id
JOIN brands br ON b.brand_id = br.brand_id
JOIN currencies c ON bd.currency_id = c.currency_id
JOIN units u ON bd.unit_id = u.unit_id
JOIN suppliers s ON bd.supplier_id = s.supplier_id
JOIN materials m ON bd.material_id = m.material_id
JOIN deposit_types dt ON bd.deposit_type_id = dt.deposit_type_id;

CREATE VIEW price_trends AS
SELECT
    b.name AS beer_name,
    bd.price,
    c.currency_code,
    bd.quantity,
    u.unit_name,
    bd.scrape_date
FROM
    beer_data bd
JOIN beers b ON bd.beer_id = b.beer_id
JOIN currencies c ON bd.currency_id = c.currency_id
JOIN units u ON bd.unit_id = u.unit_id
ORDER BY
    b.name, bd.scrape_date;

CREATE VIEW supplier_statistics AS
SELECT
    s.supplier_name,
    COUNT(DISTINCT bd.beer_id) AS unique_beers,
    AVG(bd.price) AS avg_price,
    MIN(bd.price) AS min_price,
    MAX(bd.price) AS max_price
FROM
    beer_data bd
JOIN suppliers s ON bd.supplier_id = s.supplier_id
GROUP BY
    s.supplier_name;