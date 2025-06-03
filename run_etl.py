import pandas as pd
import sqlalchemy
import numpy as np
from scipy import stats
from sqlalchemy import create_engine
from datetime import datetime

# db connections
PROD_DB_URL = "postgresql://production_unmx_user:WDJB0GjyyQDXkPH7MATl2ITXK2z0EUuY@dpg-d0q2h9re5dus73eb7ftg-a.singapore-postgres.render.com/production_unmx"
WAREHOUSE_DB_URL = "postgresql://warehouse_0uj2_user:ZD55uP1cyY7p7BWx7KeMek1az3GzL3SI@dpg-d0qmhfidbo4c73c9d2e0-a.singapore-postgres.render.com/warehouse_0uj2"

def fix_messy_date(val):
    try:
        val_str = str(int(val))
        if len(val_str) == 8:
            return pd.to_datetime(val_str, format='%Y%m%d', errors='coerce').date()
    except:
        return pd.NaT
    return pd.NaT

def main():
    print("starting etl...")
    
    # connect to prod db
    print("connecting to prod db...")
    prod_engine = create_engine(PROD_DB_URL)
    
    # get data
    print("getting data from prod...")
    data = pd.read_sql('SELECT * FROM hardware_sales', prod_engine)
    
    # transform data
    print("transforming data...")
    
    # fix dates
    messy_date_map = {
        'sls_order_dt': 'order_date',
        'sls_ship_dt': 'ship_date',
        'sls_due_dt': 'due_date'
    }
    
    for old_col, new_col in messy_date_map.items():
        if old_col in data.columns:
            data[new_col] = data[old_col].apply(fix_messy_date)
            data.drop(old_col, axis=1, inplace=True)
    
    clean_columns_map = {
        'BDATE': 'birth_date',
        'cst_create_date': 'customer_creation_date',
        'prd_start_dt': 'product_start_date',
        'prd_end_dt': 'product_end_date'
    }
    
    for old_col, new_col in clean_columns_map.items():
        if old_col in data.columns:
            data[new_col] = pd.to_datetime(data[old_col], errors='coerce').dt.date
            data.drop(old_col, axis=1, inplace=True)
    
    # fill missing values
    numeric_cols = ['sls_sales', 'sls_price', 'prd_cost']
    data[numeric_cols] = data[numeric_cols].fillna(data[numeric_cols].median())
    
    categorical_cols = ['cst_firstname', 'cst_lastname', 'cst_marital_status']
    data[categorical_cols] = data[categorical_cols].fillna('Not Specified')
    
    # clean up categories
    data['GEN'] = data['GEN'].str.upper().str.strip()
    data['CNTRY'] = data['CNTRY'].str.upper().str.strip()
    
    # fix gender values
    gender_map = {'Male': 'M', 'Female': 'F', 'm': 'M', 'f': 'F'}
    data['cst_gndr'] = data['cst_gndr'].replace(gender_map).fillna('Unknown')
    
    # remove dupes
    data = data.drop_duplicates(subset='sls_ord_num', keep='first')
    
    # add product flags
    data['is_active_product'] = data['product_end_date'].isna().astype(int)
    data['full_category'] = data['CAT'] + ' > ' + data['SUBCAT']
    
    # remove outliers
    data = data[(np.abs(stats.zscore(data[['sls_quantity', 'sls_price']])) < 3).all(axis=1)]
    
    # add age calc
    data['birth_date'] = pd.to_datetime(data['birth_date'], errors='coerce')
    data['customer_age'] = (pd.to_datetime('today') - data['birth_date']).dt.days // 365
    data['customer_age'] = data['customer_age'].astype('Int64')
    
    # convert all dates
    date_cols = [
        'order_date', 'ship_date', 'due_date',
        'birth_date', 'customer_creation_date',
        'product_start_date', 'product_end_date'
    ]
    
    for col in date_cols:
        data[col] = pd.to_datetime(data[col], errors='coerce')
    
    # load to warehouse
    print("loading to warehouse...")
    warehouse_engine = create_engine(WAREHOUSE_DB_URL)
    
    data.to_sql(
        name='dashboard_data',
        con=warehouse_engine,
        if_exists='replace',
        index=False,
        chunksize=1000
    )
    
    print("etl done!")

if __name__ == "__main__":
    main() 