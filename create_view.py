import sqlalchemy
from sqlalchemy import create_engine, text

# Connect to warehouse database
engine = create_engine('postgresql://warehouse_0uj2_user:ZD55uP1cyY7p7BWx7KeMek1az3GzL3SI@dpg-d0qmhfidbo4c73c9d2e0-a.singapore-postgres.render.com/warehouse_0uj2')

# Read SQL file
with open('create_warehouse_view.sql', 'r') as file:
    sql = file.read()

# Execute SQL
with engine.connect() as conn:
    conn.execute(text(sql))
    conn.commit()

print("View created successfully!") 