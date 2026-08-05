from sqlalchemy import create_engine, text
import os

e = create_engine(os.environ.get('PLATFORM_DATABASE_URL', ''))
c = e.connect()

# List all public tables
r = c.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
print("=== TABLES ===")
for row in r:
    print(row[0])

# Count columns per table
print("\n=== COLUMNS PER TABLE ===")
r2 = c.execute(text("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public' ORDER BY table_name, ordinal_position"))
current_table = None
for row in r2:
    if row[0] != current_table:
        current_table = row[0]
        print(f"\n-- {current_table} --")
    print(f"  {row[1]}")

# Show some sample data from seed tables
for tbl in ['sales_orders', 'customer_profiles', 'inventory_items', 'analytics_events', 'marketing_campaigns']:
    try:
        r3 = c.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
        cnt = r3.scalar()
        print(f"\n{tbl}: {cnt} rows")
    except:
        pass

c.close()
