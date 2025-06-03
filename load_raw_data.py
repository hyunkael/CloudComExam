import pandas as pd
from sqlalchemy import create_engine

print("connecting to dbs...")

# prod db
prod_engine = create_engine('postgresql://production_unmx_user:WDJB0GjyyQDXkPH7MATl2ITXK2z0EUuY@dpg-d0q2h9re5dus73eb7ftg-a.singapore-postgres.render.com/production_unmx')

# warehouse db
wh_engine = create_engine('postgresql://warehouse_0uj2_user:ZD55uP1cyY7p7BWx7KeMek1az3GzL3SI@dpg-d0qmhfidbo4c73c9d2e0-a.singapore-postgres.render.com/warehouse_0uj2')

print("reading from prod...")
# get all data
raw_df = pd.read_sql('SELECT * FROM hardware_sales', prod_engine)
print(f"got {len(raw_df)} rows")
print(f"cols: {raw_df.columns.tolist()}")

print("\nwriting to warehouse...")
# dump to warehouse
raw_df.to_sql('hardware_sales', wh_engine, if_exists='replace', index=False)
print("done!") 