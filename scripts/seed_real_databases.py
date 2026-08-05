"""Create and populate real databases (sales_db, hr_db) on the PostgreSQL container."""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text


# Base connection to default postgres database (for creating new databases)
BASE_URL = "postgresql+psycopg://postgres:postgres@postgres:5432/postgres"


def create_database(db_name: str) -> None:
    """Create database if it doesn't exist."""
    engine = create_engine(BASE_URL, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": db_name},
        ).fetchone()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
            print(f"Created database: {db_name}")
        else:
            print(f"Database already exists: {db_name}")
    engine.dispose()


def populate_sales_db() -> None:
    """Populate the sales_db with realistic e-commerce data."""
    engine = create_engine("postgresql+psycopg://postgres:postgres@postgres:5432/sales_db")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20),
                city VARCHAR(50),
                country VARCHAR(50),
                segment VARCHAR(20) DEFAULT 'Regular',
                registration_date DATE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(50) NOT NULL,
                brand VARCHAR(50),
                price DECIMAL(10,2) NOT NULL,
                cost DECIMAL(10,2),
                stock_quantity INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE
            );

            CREATE TABLE IF NOT EXISTS suppliers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                contact_email VARCHAR(100),
                country VARCHAR(50),
                phone VARCHAR(20),
                rating DECIMAL(2,1) DEFAULT 0.0
            );

            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER REFERENCES customers(id),
                order_date DATE NOT NULL,
                ship_date DATE,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                total_amount DECIMAL(12,2) NOT NULL,
                shipping_method VARCHAR(30),
                payment_method VARCHAR(30)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id),
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                discount_percent DECIMAL(5,2) DEFAULT 0.00
            );

            CREATE TABLE IF NOT EXISTS product_reviews (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id),
                customer_id INTEGER REFERENCES customers(id),
                rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                review_text TEXT,
                review_date DATE NOT NULL
            );
        """))
        conn.commit()

        # Check if data already exists
        count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        if count and count > 0:
            print(f"Sales DB already populated ({count} customers). Skipping.")
            engine.dispose()
            return

        # Insert customers
        conn.execute(text("""
            INSERT INTO customers (first_name, last_name, email, phone, city, country, segment, registration_date) VALUES
            ('Ahmed', 'Hassan', 'ahmed.hassan@email.com', '+20-1012345678', 'Cairo', 'Egypt', 'Premium', '2024-01-15'),
            ('Sara', 'Mohamed', 'sara.m@email.com', '+20-1098765432', 'Alexandria', 'Egypt', 'Regular', '2024-02-20'),
            ('John', 'Smith', 'john.smith@email.com', '+1-5551234567', 'New York', 'USA', 'VIP', '2023-11-10'),
            ('Emma', 'Wilson', 'emma.w@email.com', '+44-7700900123', 'London', 'UK', 'Premium', '2024-03-05'),
            ('Omar', 'Ali', 'omar.ali@email.com', '+971-501234567', 'Dubai', 'UAE', 'VIP', '2023-09-22'),
            ('Fatima', 'Khan', 'fatima.k@email.com', '+92-3001234567', 'Karachi', 'Pakistan', 'Regular', '2024-04-18'),
            ('Carlos', 'Rodriguez', 'carlos.r@email.com', '+34-612345678', 'Madrid', 'Spain', 'Premium', '2024-01-30'),
            ('Yuki', 'Tanaka', 'yuki.t@email.com', '+81-9012345678', 'Tokyo', 'Japan', 'VIP', '2023-12-08'),
            ('Maria', 'Garcia', 'maria.g@email.com', '+52-5512345678', 'Mexico City', 'Mexico', 'Regular', '2024-05-12'),
            ('David', 'Brown', 'david.b@email.com', '+1-5559876543', 'San Francisco', 'USA', 'Premium', '2024-02-14'),
            ('Nour', 'Ibrahim', 'nour.i@email.com', '+20-1156789012', 'Giza', 'Egypt', 'Regular', '2024-06-01'),
            ('Li', 'Wei', 'li.wei@email.com', '+86-13912345678', 'Shanghai', 'China', 'VIP', '2023-10-25'),
            ('Anna', 'Petrov', 'anna.p@email.com', '+7-9161234567', 'Moscow', 'Russia', 'Regular', '2024-03-20'),
            ('Mohammed', 'Al-Saud', 'mohammed.s@email.com', '+966-501234567', 'Riyadh', 'Saudi Arabia', 'VIP', '2024-01-08'),
            ('Sophie', 'Dupont', 'sophie.d@email.com', '+33-612345678', 'Paris', 'France', 'Premium', '2024-04-02'),
            ('James', 'Taylor', 'james.t@email.com', '+61-412345678', 'Sydney', 'Australia', 'Regular', '2024-07-15'),
            ('Amina', 'Diallo', 'amina.d@email.com', '+221-771234567', 'Dakar', 'Senegal', 'Regular', '2024-05-28'),
            ('Hans', 'Mueller', 'hans.m@email.com', '+49-15112345678', 'Berlin', 'Germany', 'Premium', '2024-02-09'),
            ('Priya', 'Sharma', 'priya.s@email.com', '+91-9876543210', 'Mumbai', 'India', 'VIP', '2023-08-17'),
            ('Lucas', 'Silva', 'lucas.s@email.com', '+55-11987654321', 'Sao Paulo', 'Brazil', 'Regular', '2024-06-20');
        """))

        # Insert products
        conn.execute(text("""
            INSERT INTO products (name, category, brand, price, cost, stock_quantity, is_active) VALUES
            ('MacBook Pro 16"', 'Laptops', 'Apple', 2499.99, 1800.00, 45, true),
            ('Galaxy S24 Ultra', 'Smartphones', 'Samsung', 1199.99, 750.00, 120, true),
            ('AirPods Pro 2', 'Audio', 'Apple', 249.99, 120.00, 300, true),
            ('Dell XPS 15', 'Laptops', 'Dell', 1799.99, 1200.00, 30, true),
            ('Sony WH-1000XM5', 'Audio', 'Sony', 349.99, 180.00, 85, true),
            ('iPad Air M2', 'Tablets', 'Apple', 599.99, 350.00, 60, true),
            ('ThinkPad X1 Carbon', 'Laptops', 'Lenovo', 1549.99, 1000.00, 25, true),
            ('Pixel 8 Pro', 'Smartphones', 'Google', 999.99, 600.00, 75, true),
            ('Samsung 55" OLED TV', 'TVs', 'Samsung', 1299.99, 800.00, 15, true),
            ('Bose QuietComfort', 'Audio', 'Bose', 279.99, 140.00, 110, true),
            ('Nintendo Switch OLED', 'Gaming', 'Nintendo', 349.99, 220.00, 200, true),
            ('PS5 Slim', 'Gaming', 'Sony', 449.99, 350.00, 40, true),
            ('Kindle Paperwhite', 'E-Readers', 'Amazon', 139.99, 70.00, 150, true),
            ('Apple Watch Ultra 2', 'Wearables', 'Apple', 799.99, 400.00, 55, true),
            ('Dyson V15 Detect', 'Home', 'Dyson', 749.99, 400.00, 35, true),
            ('Canon EOS R6 II', 'Cameras', 'Canon', 2499.99, 1600.00, 12, true),
            ('Mechanical Keyboard', 'Accessories', 'Keychron', 89.99, 35.00, 250, true),
            ('USB-C Hub 10-in-1', 'Accessories', 'Anker', 59.99, 20.00, 400, true),
            ('Gaming Mouse Pro', 'Accessories', 'Logitech', 129.99, 55.00, 180, true),
            ('27" 4K Monitor', 'Monitors', 'LG', 449.99, 280.00, 50, true),
            ('Wireless Charger Pad', 'Accessories', 'Belkin', 39.99, 12.00, 500, false),
            ('Old Laptop Model X', 'Laptops', 'Dell', 899.99, 600.00, 0, false);
        """))

        # Insert suppliers
        conn.execute(text("""
            INSERT INTO suppliers (name, contact_email, country, phone, rating) VALUES
            ('TechSource Global', 'orders@techsource.com', 'China', '+86-2112345678', 4.5),
            ('ElectroParts Ltd', 'supply@electroparts.co.uk', 'UK', '+44-2079460123', 4.2),
            ('Digital World Inc', 'sales@digitalworld.com', 'USA', '+1-4089876543', 4.8),
            ('Tokyo Electronics', 'info@tokyoelec.jp', 'Japan', '+81-3412345678', 4.6),
            ('Euro Components', 'contact@eurocomp.de', 'Germany', '+49-3012345678', 3.9),
            ('Nile Tech Supply', 'orders@niletech.eg', 'Egypt', '+20-223456789', 4.0);
        """))

        # Insert orders
        conn.execute(text("""
            INSERT INTO orders (customer_id, order_date, ship_date, status, total_amount, shipping_method, payment_method) VALUES
            (1, '2024-08-01', '2024-08-03', 'delivered', 2749.98, 'Express', 'Credit Card'),
            (2, '2024-08-02', '2024-08-05', 'delivered', 249.99, 'Standard', 'PayPal'),
            (3, '2024-08-03', '2024-08-04', 'delivered', 3499.98, 'Express', 'Credit Card'),
            (4, '2024-08-05', '2024-08-08', 'delivered', 1799.99, 'Standard', 'Credit Card'),
            (5, '2024-08-07', '2024-08-09', 'delivered', 2399.98, 'Express', 'Apple Pay'),
            (1, '2024-08-10', '2024-08-12', 'delivered', 599.99, 'Standard', 'Credit Card'),
            (6, '2024-08-12', '2024-08-15', 'delivered', 1199.99, 'Standard', 'PayPal'),
            (7, '2024-08-14', '2024-08-16', 'delivered', 349.99, 'Express', 'Credit Card'),
            (8, '2024-08-15', '2024-08-17', 'delivered', 4299.98, 'Express', 'Credit Card'),
            (9, '2024-08-18', '2024-08-22', 'delivered', 139.99, 'Economy', 'PayPal'),
            (10, '2024-08-20', '2024-08-22', 'delivered', 2499.99, 'Express', 'Credit Card'),
            (11, '2024-09-01', '2024-09-04', 'delivered', 449.99, 'Standard', 'Debit Card'),
            (12, '2024-09-03', '2024-09-05', 'delivered', 1999.98, 'Express', 'Apple Pay'),
            (3, '2024-09-05', '2024-09-07', 'delivered', 799.99, 'Express', 'Credit Card'),
            (14, '2024-09-08', '2024-09-12', 'delivered', 1549.99, 'Standard', 'Credit Card'),
            (15, '2024-09-10', NULL, 'shipped', 2529.98, 'Express', 'PayPal'),
            (5, '2024-09-12', NULL, 'shipped', 689.98, 'Standard', 'Apple Pay'),
            (16, '2024-09-14', NULL, 'processing', 1299.99, 'Express', 'Credit Card'),
            (17, '2024-09-15', NULL, 'processing', 349.99, 'Economy', 'PayPal'),
            (18, '2024-09-16', NULL, 'processing', 1549.99, 'Standard', 'Credit Card'),
            (19, '2024-09-17', NULL, 'pending', 3299.98, 'Express', 'Credit Card'),
            (20, '2024-09-18', NULL, 'pending', 449.99, 'Standard', 'Debit Card'),
            (2, '2024-09-19', NULL, 'pending', 129.99, 'Economy', 'PayPal'),
            (13, '2024-09-20', NULL, 'cancelled', 2499.99, 'Express', 'Credit Card'),
            (4, '2024-09-20', NULL, 'cancelled', 599.99, 'Standard', 'Credit Card');
        """))

        # Insert order items
        conn.execute(text("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_percent) VALUES
            (1, 1, 1, 2499.99, 0.00), (1, 3, 1, 249.99, 0.00),
            (2, 3, 1, 249.99, 0.00),
            (3, 1, 1, 2499.99, 0.00), (3, 8, 1, 999.99, 0.00),
            (4, 4, 1, 1799.99, 0.00),
            (5, 2, 2, 1199.99, 0.00),
            (6, 6, 1, 599.99, 0.00),
            (7, 2, 1, 1199.99, 0.00),
            (8, 5, 1, 349.99, 0.00),
            (9, 16, 1, 2499.99, 0.00), (9, 4, 1, 1799.99, 0.00),
            (10, 13, 1, 139.99, 0.00),
            (11, 16, 1, 2499.99, 0.00),
            (12, 12, 1, 449.99, 0.00),
            (13, 2, 1, 1199.99, 10.00), (13, 14, 1, 799.99, 0.00),
            (14, 14, 1, 799.99, 0.00),
            (15, 7, 1, 1549.99, 0.00),
            (16, 1, 1, 2499.99, 5.00), (16, 17, 1, 89.99, 0.00),
            (17, 6, 1, 599.99, 0.00), (17, 17, 1, 89.99, 0.00),
            (18, 9, 1, 1299.99, 0.00),
            (19, 11, 1, 349.99, 0.00),
            (20, 7, 1, 1549.99, 0.00),
            (21, 1, 1, 2499.99, 0.00), (21, 14, 1, 799.99, 0.00),
            (22, 12, 1, 449.99, 0.00),
            (23, 19, 1, 129.99, 0.00),
            (24, 1, 1, 2499.99, 0.00),
            (25, 6, 1, 599.99, 0.00);
        """))

        # Insert product reviews
        conn.execute(text("""
            INSERT INTO product_reviews (product_id, customer_id, rating, review_text, review_date) VALUES
            (1, 1, 5, 'Best laptop I have ever used. Blazing fast performance!', '2024-08-10'),
            (1, 3, 4, 'Great machine but a bit heavy for travel.', '2024-08-15'),
            (2, 5, 5, 'Amazing camera and battery life. Love it!', '2024-08-20'),
            (2, 7, 4, 'Good phone, but the price is a bit steep.', '2024-09-01'),
            (3, 2, 5, 'Perfect sound quality. Noise cancellation is incredible.', '2024-08-08'),
            (4, 4, 4, 'Solid laptop. Keyboard is excellent.', '2024-08-18'),
            (5, 8, 5, 'Best headphones on the market. Period.', '2024-08-22'),
            (6, 1, 4, 'Excellent tablet for productivity.', '2024-08-25'),
            (8, 8, 3, 'Good phone but camera could be better in low light.', '2024-08-28'),
            (11, 9, 5, 'So much fun! Great for family gaming.', '2024-09-05'),
            (12, 11, 4, 'Fast loading times. Game library growing.', '2024-09-10'),
            (14, 3, 5, 'The health tracking features are next level.', '2024-09-12'),
            (16, 10, 5, 'Professional quality photos. Worth every penny.', '2024-09-08'),
            (17, 18, 4, 'Nice keyboard for the price. Good tactile feedback.', '2024-09-15'),
            (20, 15, 5, 'Crystal clear display. Perfect for design work.', '2024-09-18');
        """))

        conn.commit()
        print(f"Populated sales_db: 20 customers, 22 products, 25 orders, 30 order_items, 15 reviews, 6 suppliers")
    engine.dispose()


def populate_hr_db() -> None:
    """Populate the hr_db with realistic HR data."""
    engine = create_engine("postgresql+psycopg://postgres:postgres@postgres:5432/hr_db")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS departments (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                location VARCHAR(50),
                manager_name VARCHAR(100),
                budget DECIMAL(12,2),
                headcount_target INTEGER
            );

            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                department_id INTEGER REFERENCES departments(id),
                position VARCHAR(80) NOT NULL,
                hire_date DATE NOT NULL,
                salary DECIMAL(10,2) NOT NULL,
                employment_type VARCHAR(20) DEFAULT 'Full-time',
                status VARCHAR(20) DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                department_id INTEGER REFERENCES departments(id),
                start_date DATE NOT NULL,
                end_date DATE,
                budget DECIMAL(12,2),
                status VARCHAR(20) DEFAULT 'active',
                priority VARCHAR(10) DEFAULT 'medium'
            );

            CREATE TABLE IF NOT EXISTS leave_requests (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER REFERENCES employees(id),
                leave_type VARCHAR(30) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                days_count INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                reason TEXT
            );

            CREATE TABLE IF NOT EXISTS salary_history (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER REFERENCES employees(id),
                old_salary DECIMAL(10,2),
                new_salary DECIMAL(10,2) NOT NULL,
                change_date DATE NOT NULL,
                change_reason VARCHAR(50)
            );
        """))
        conn.commit()

        count = conn.execute(text("SELECT COUNT(*) FROM departments")).scalar()
        if count and count > 0:
            print(f"HR DB already populated ({count} departments). Skipping.")
            engine.dispose()
            return

        # Insert departments
        conn.execute(text("""
            INSERT INTO departments (name, location, manager_name, budget, headcount_target) VALUES
            ('Engineering', 'San Francisco', 'Sarah Chen', 2500000.00, 40),
            ('Product Management', 'San Francisco', 'Alex Rivera', 800000.00, 12),
            ('Data Science', 'London', 'Dr. James Okafor', 1200000.00, 15),
            ('Marketing', 'New York', 'Lisa Thompson', 600000.00, 10),
            ('Human Resources', 'San Francisco', 'Maya Patel', 400000.00, 8),
            ('Sales', 'Dubai', 'Ahmed Mansour', 900000.00, 20),
            ('Customer Support', 'Singapore', 'Wei Lin', 500000.00, 18),
            ('Finance', 'London', 'Robert Hughes', 450000.00, 7);
        """))

        # Insert employees
        conn.execute(text("""
            INSERT INTO employees (first_name, last_name, email, department_id, position, hire_date, salary, employment_type, status) VALUES
            ('Sarah', 'Chen', 'sarah.chen@technova.com', 1, 'VP of Engineering', '2019-03-15', 220000.00, 'Full-time', 'active'),
            ('Mike', 'Johnson', 'mike.j@technova.com', 1, 'Senior Backend Engineer', '2020-06-01', 165000.00, 'Full-time', 'active'),
            ('Aisha', 'Rahman', 'aisha.r@technova.com', 1, 'Frontend Lead', '2020-09-14', 155000.00, 'Full-time', 'active'),
            ('Tom', 'Baker', 'tom.b@technova.com', 1, 'DevOps Engineer', '2021-01-10', 145000.00, 'Full-time', 'active'),
            ('Yuki', 'Sato', 'yuki.s@technova.com', 1, 'ML Engineer', '2021-07-20', 170000.00, 'Full-time', 'active'),
            ('Carlos', 'Mendez', 'carlos.m@technova.com', 1, 'Junior Developer', '2024-01-15', 95000.00, 'Full-time', 'active'),
            ('Emily', 'Watson', 'emily.w@technova.com', 1, 'QA Engineer', '2022-03-01', 120000.00, 'Full-time', 'active'),
            ('Alex', 'Rivera', 'alex.r@technova.com', 2, 'Director of Product', '2019-06-10', 195000.00, 'Full-time', 'active'),
            ('Nina', 'Kowalski', 'nina.k@technova.com', 2, 'Senior PM', '2021-02-15', 150000.00, 'Full-time', 'active'),
            ('Ryan', 'O''Brien', 'ryan.o@technova.com', 2, 'Product Analyst', '2023-04-01', 110000.00, 'Full-time', 'active'),
            ('James', 'Okafor', 'james.o@technova.com', 3, 'Head of Data Science', '2020-01-20', 200000.00, 'Full-time', 'active'),
            ('Mei', 'Zhang', 'mei.z@technova.com', 3, 'Senior Data Scientist', '2020-08-15', 160000.00, 'Full-time', 'active'),
            ('David', 'Kim', 'david.k@technova.com', 3, 'Data Engineer', '2021-11-01', 140000.00, 'Full-time', 'active'),
            ('Priya', 'Patel', 'priya.p@technova.com', 3, 'ML Researcher', '2022-06-15', 155000.00, 'Full-time', 'active'),
            ('Lisa', 'Thompson', 'lisa.t@technova.com', 4, 'Marketing Director', '2020-03-01', 175000.00, 'Full-time', 'active'),
            ('Jake', 'Anderson', 'jake.a@technova.com', 4, 'Content Strategist', '2022-01-10', 95000.00, 'Full-time', 'active'),
            ('Sofia', 'Martinez', 'sofia.m@technova.com', 4, 'Digital Marketing Specialist', '2023-05-20', 85000.00, 'Full-time', 'active'),
            ('Maya', 'Patel', 'maya.p@technova.com', 5, 'HR Director', '2019-09-01', 165000.00, 'Full-time', 'active'),
            ('Chris', 'Lee', 'chris.l@technova.com', 5, 'Recruiter', '2022-08-15', 80000.00, 'Full-time', 'active'),
            ('Ahmed', 'Mansour', 'ahmed.m@technova.com', 6, 'Sales Director', '2020-04-15', 180000.00, 'Full-time', 'active'),
            ('Rachel', 'Green', 'rachel.g@technova.com', 6, 'Account Executive', '2021-06-01', 120000.00, 'Full-time', 'active'),
            ('Omar', 'Farooq', 'omar.f@technova.com', 6, 'Sales Development Rep', '2023-02-01', 75000.00, 'Full-time', 'active'),
            ('Wei', 'Lin', 'wei.l@technova.com', 7, 'Support Manager', '2020-10-01', 130000.00, 'Full-time', 'active'),
            ('Anna', 'Novak', 'anna.n@technova.com', 7, 'Support Specialist', '2022-04-15', 65000.00, 'Full-time', 'active'),
            ('Robert', 'Hughes', 'robert.h@technova.com', 8, 'Finance Director', '2019-12-01', 185000.00, 'Full-time', 'active'),
            ('Helen', 'Park', 'helen.p@technova.com', 8, 'Financial Analyst', '2023-01-15', 100000.00, 'Full-time', 'active'),
            ('Mark', 'Taylor', 'mark.t@technova.com', 1, 'Senior Engineer', '2020-11-01', 160000.00, 'Full-time', 'on_leave'),
            ('Laura', 'Jones', 'laura.j@technova.com', 4, 'Marketing Coordinator', '2023-09-01', 70000.00, 'Part-time', 'active'),
            ('Kevin', 'Brown', 'kevin.b@technova.com', 6, 'Account Manager', '2021-08-15', 110000.00, 'Full-time', 'terminated'),
            ('Diana', 'White', 'diana.w@technova.com', 1, 'Intern Developer', '2024-06-01', 45000.00, 'Intern', 'active');
        """))

        # Insert projects
        conn.execute(text("""
            INSERT INTO projects (name, department_id, start_date, end_date, budget, status, priority) VALUES
            ('Platform v3.0 Migration', 1, '2024-01-15', '2024-09-30', 500000.00, 'active', 'high'),
            ('AI-Powered Analytics Dashboard', 3, '2024-03-01', '2024-12-31', 350000.00, 'active', 'high'),
            ('Mobile App Redesign', 1, '2024-04-01', '2024-08-31', 200000.00, 'completed', 'medium'),
            ('Brand Refresh Campaign', 4, '2024-06-01', '2024-10-31', 150000.00, 'active', 'medium'),
            ('Customer 360 Data Lake', 3, '2024-02-15', NULL, 400000.00, 'active', 'high'),
            ('Sales CRM Integration', 6, '2024-05-01', '2024-11-30', 180000.00, 'active', 'medium'),
            ('SOC 2 Compliance Program', 1, '2024-01-01', '2024-06-30', 100000.00, 'completed', 'critical'),
            ('Employee Wellness Portal', 5, '2024-07-01', NULL, 75000.00, 'active', 'low'),
            ('Global Expansion - APAC', 6, '2024-03-15', '2025-03-15', 600000.00, 'active', 'critical'),
            ('API Gateway Modernization', 1, '2024-08-01', NULL, 250000.00, 'active', 'high'),
            ('Customer Chatbot v2', 7, '2024-04-15', '2024-09-15', 120000.00, 'completed', 'medium'),
            ('Annual Budget Planning Tool', 8, '2024-09-01', NULL, 80000.00, 'active', 'medium');
        """))

        # Insert leave requests
        conn.execute(text("""
            INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, days_count, status, reason) VALUES
            (2, 'Vacation', '2024-08-12', '2024-08-16', 5, 'approved', 'Family vacation'),
            (5, 'Sick Leave', '2024-07-22', '2024-07-23', 2, 'approved', 'Flu'),
            (8, 'Vacation', '2024-09-02', '2024-09-13', 10, 'approved', 'International travel'),
            (12, 'Conference', '2024-08-05', '2024-08-07', 3, 'approved', 'NeurIPS conference'),
            (15, 'Vacation', '2024-09-16', '2024-09-20', 5, 'approved', 'Personal time'),
            (3, 'Sick Leave', '2024-09-10', '2024-09-10', 1, 'approved', 'Medical appointment'),
            (27, 'Medical Leave', '2024-09-01', '2024-10-01', 22, 'approved', 'Surgery recovery'),
            (20, 'Vacation', '2024-10-01', '2024-10-10', 8, 'pending', 'Holiday trip'),
            (6, 'Training', '2024-10-14', '2024-10-18', 5, 'pending', 'AWS certification bootcamp'),
            (23, 'Vacation', '2024-11-01', '2024-11-05', 5, 'pending', 'Family visit'),
            (10, 'Sick Leave', '2024-09-18', '2024-09-18', 1, 'approved', 'Migraine'),
            (16, 'Vacation', '2024-12-20', '2024-12-31', 8, 'denied', 'Holiday season - team needs coverage');
        """))

        # Insert salary history
        conn.execute(text("""
            INSERT INTO salary_history (employee_id, old_salary, new_salary, change_date, change_reason) VALUES
            (1, 180000.00, 200000.00, '2021-01-01', 'Annual raise'),
            (1, 200000.00, 220000.00, '2023-01-01', 'Promotion to VP'),
            (2, 130000.00, 145000.00, '2022-01-01', 'Annual raise'),
            (2, 145000.00, 165000.00, '2024-01-01', 'Market adjustment'),
            (3, 120000.00, 140000.00, '2022-01-01', 'Promotion'),
            (3, 140000.00, 155000.00, '2024-01-01', 'Annual raise'),
            (5, 150000.00, 170000.00, '2023-07-01', 'Promotion + raise'),
            (8, 160000.00, 180000.00, '2022-01-01', 'Annual raise'),
            (8, 180000.00, 195000.00, '2024-01-01', 'Promotion to Director'),
            (11, 170000.00, 185000.00, '2022-01-01', 'Annual raise'),
            (11, 185000.00, 200000.00, '2024-01-01', 'Annual raise'),
            (15, 140000.00, 160000.00, '2022-01-01', 'Promotion'),
            (15, 160000.00, 175000.00, '2024-01-01', 'Annual raise'),
            (20, 150000.00, 165000.00, '2022-04-01', 'Market adjustment'),
            (20, 165000.00, 180000.00, '2024-01-01', 'Annual raise'),
            (21, 90000.00, 105000.00, '2023-01-01', 'Annual raise'),
            (21, 105000.00, 120000.00, '2024-06-01', 'Promotion');
        """))

        conn.commit()
        print(f"Populated hr_db: 8 departments, 30 employees, 12 projects, 12 leave_requests, 17 salary_history")
    engine.dispose()


def main() -> None:
    print("=== Creating Real Databases ===")
    create_database("sales_db")
    create_database("hr_db")

    print("\n=== Populating Sales DB ===")
    populate_sales_db()

    print("\n=== Populating HR DB ===")
    populate_hr_db()

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
