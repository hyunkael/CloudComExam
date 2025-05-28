import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Database connection
@st.cache_resource
def get_connection():
    return create_engine(
        "postgresql://warehouse_0uj2_user:ZD55uP1cyY7p7BWx7KeMek1az3GzL3SI@dpg-d0qmhfidbo4c73c9d2e0-a.singapore-postgres.render.com/warehouse_0uj2"
    )

@st.cache_data(ttl=3600)
def load_data(query):
    with get_connection().connect() as conn:
        return pd.read_sql(query, conn)

def main():
    st.title("📊 Sales Analytics Dashboard")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date range filter
    min_date = pd.to_datetime('2011-01-01')
    max_date = pd.to_datetime('2014-12-31')
    start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
    
    # Product category filter
    categories = load_data("SELECT DISTINCT \"CAT\" FROM dashboard_data ORDER BY \"CAT\"")
    selected_categories = st.sidebar.multiselect(
        "Product Categories",
        options=categories['CAT'].tolist(),
        default=categories['CAT'].tolist()
    )
    
    # Initialize parameters dictionary
    params = {"start_date": start_date, "end_date": end_date}
    
    # Build the base query
    sales_query = """
    SELECT s.*, p."CAT" as category, p."SUBCAT" as subcategory, 
           p."MAINTENANCE" as maintenance, c."cst_gndr" as gender
    FROM sales s
    JOIN products p ON s."prd_key" = p."prd_key"
    JOIN customers c ON s."CID" = c."CID"
    WHERE s."sls_order_dt" BETWEEN :start_date AND :end_date
    """
    
    # Add category filter if categories are selected
    if selected_categories:
        placeholders = ', '.join([f':cat_{i}' for i in range(len(selected_categories))])
        sales_query += f" AND p.\"CAT\" IN ({placeholders})"
        params.update({f'cat_{i}': cat for i, cat in enumerate(selected_categories)})
    
    # Execute the query with parameters
    sales_data = load_data(text(sales_query), params=params)
    
    # Convert date columns
    date_columns = ['sls_order_dt', 'sls_ship_dt', 'sls_due_dt']
    for col in date_columns:
        sales_data[col] = pd.to_datetime(sales_data[col], format='%Y%m%d')
    
    # KPI Cards
    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sales = sales_data['sls_sales'].sum()
        st.metric("Total Sales", f"${total_sales:,.2f}")
    
    with col2:
        avg_order_value = sales_data['sls_sales'].mean()
        st.metric("Average Order Value", f"${avg_order_value:,.2f}")
    
    with col3:
        total_orders = sales_data['sls_ord_num'].nunique()
        st.metric("Total Orders", f"{total_orders:,}")
    
    with col4:
        total_products = sales_data['prd_key'].nunique()
        st.metric("Unique Products Sold", f"{total_products:,}")
    
    # Sales Trend
    st.subheader("Sales Trend Over Time")
    sales_trend = sales_data.groupby(pd.Grouper(key='sls_order_dt', freq='M'))['sls_sales'].sum().reset_index()
    fig1 = px.line(sales_trend, x='sls_order_dt', y='sls_sales', 
                  title='Monthly Sales Trend',
                  labels={'sls_order_dt': 'Date', 'sls_sales': 'Total Sales ($)'})
    st.plotly_chart(fig1, use_container_width=True)
    
    # Sales by Category and Subcategory
    st.subheader("Sales by Category")
    col1, col2 = st.columns(2)
    
    with col1:
        category_sales = sales_data.groupby('category')['sls_sales'].sum().reset_index()
        fig2 = px.pie(category_sales, values='sls_sales', names='category', 
                     title='Sales Distribution by Category')
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        subcategory_sales = sales_data.groupby('subcategory')['sls_sales'].sum().reset_index().nlargest(10, 'sls_sales')
        fig3 = px.bar(subcategory_sales, x='subcategory', y='sls_sales',
                     title='Top 10 Subcategories by Sales',
                     labels={'subcategory': 'Subcategory', 'sls_sales': 'Total Sales ($)'})
        st.plotly_chart(fig3, use_container_width=True)
    
    # Customer Demographics
    st.subheader("Customer Demographics")
    col1, col2 = st.columns(2)
    
    with col1:
        gender_dist = sales_data.groupby('gender')['sls_ord_num'].nunique().reset_index()
        fig4 = px.pie(gender_dist, values='sls_ord_num', names='gender',
                     title='Orders by Gender')
        st.plotly_chart(fig4, use_container_width=True)
    
    with col2:
        maintenance_sales = sales_data.groupby('maintenance')['sls_sales'].sum().reset_index()
        fig5 = px.bar(maintenance_sales, x='maintenance', y='sls_sales',
                     title='Sales by Product Maintenance',
                     labels={'maintenance': 'Requires Maintenance', 'sls_sales': 'Total Sales ($)'})
        st.plotly_chart(fig5, use_container_width=True)
    
    # Top Products
    st.subheader("Top Selling Products")
    top_products = sales_data.groupby('prd_key')['sls_quantity'].sum().reset_index().nlargest(10, 'sls_quantity')
    fig6 = px.bar(top_products, x='prd_key', y='sls_quantity',
                 title='Top 10 Products by Quantity Sold',
                 labels={'prd_key': 'Product Key', 'sls_quantity': 'Quantity Sold'})
    st.plotly_chart(fig6, use_container_width=True)

if __name__ == "__main__":
    main()