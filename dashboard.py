import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Bike Sales Analytics Dashboard",
    layout="wide",
    page_icon="💰",
    initial_sidebar_state="expanded"
)

# Custom color palette
COLORS = ['#2c1c0c', '#a85d04', '#e0aa01', '#ecd401']
BAR_COLORS = ['#ecd401', '#dbac08']  # Deep blue and coral for alternating bars
TEXT_COLOR = '#2c1c0c'
KPI_BOX_COLOR = '#dcd4b1'

# Custom CSS for text color and KPI box
st.markdown(f"""
    <style>
        .stTitle, .stSubheader, .stMarkdown, .stMetric, .stSidebar, .stButton button {{
            color: {TEXT_COLOR} !important;
        }}
        .kpi-box {{
            border-radius: 5px;
            padding: 20px;
            margin: 10px;
            background-color: {KPI_BOX_COLOR};
            text-align: center;
            height: 100%;
        }}
        .metric-value {{
            font-weight: bold;
            font-size: 1.5em;
            margin-top: 10px;
        }}
        .metric-label {{
            font-size: 1.1em;
            margin-bottom: 10px;
        }}
        .toc-link {{
            color: {TEXT_COLOR};
            text-decoration: none;
            display: block;
            padding: 5px 0;
        }}
        .toc-link:hover {{
            color: #a85d04;
        }}
    </style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_connection():
    return create_engine(
        "postgresql://warehouse_0uj2_user:ZD55uP1cyY7p7BWx7KeMek1az3GzL3SI@dpg-d0qmhfidbo4c73c9d2e0-a.singapore-postgres.render.com/warehouse_0uj2"
    )

@st.cache_data(ttl=3600)
def load_data(_query, params=None):
    with get_connection().connect() as conn:
        return pd.read_sql(_query, conn, params=params)

def main():
    st.title("💰 Bike Sales Analytics Dashboard")

    # Sidebar
    st.sidebar.header("Navigation")
    
    # Table of Contents
    st.sidebar.markdown("### Table of Contents")
    toc_html = """
    <div style="margin-bottom: 20px;">
        <a href="#key-performance-indicators" style="color: #2c1c0c; text-decoration: none; display: block; padding: 8px 12px; margin: 5px 0; background-color: #dcd4b1; border-radius: 20px;">📊 Key Performance Indicators</a>
        <a href="#sales-analysis" style="color: #2c1c0c; text-decoration: none; display: block; padding: 8px 12px; margin: 5px 0; background-color: #dcd4b1; border-radius: 20px;">📈 Sales Analysis</a>
        <a href="#top-selling-bike-models" style="color: #2c1c0c; text-decoration: none; display: block; padding: 8px 12px; margin: 5px 0; background-color: #dcd4b1; border-radius: 20px;">🚲 Top Selling Bike Models</a>
        <a href="#bike-categories-analysis" style="color: #2c1c0c; text-decoration: none; display: block; padding: 8px 12px; margin: 5px 0; background-color: #dcd4b1; border-radius: 20px;">📊 Bike Categories Analysis</a>
        <a href="#bike-customer-demographics" style="color: #2c1c0c; text-decoration: none; display: block; padding: 8px 12px; margin: 5px 0; background-color: #dcd4b1; border-radius: 20px;">👥 Bike Customer Demographics</a>
    </div>
    """
    st.sidebar.markdown(toc_html, unsafe_allow_html=True)
    
    # Date filters
    st.sidebar.header("Filters")
    min_date = pd.to_datetime('2011-01-01')
    max_date = pd.to_datetime('2014-12-31')
    start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

    # Build query for bike data
    base_query = """
    SELECT s.*, s."CAT" as category, s."SUBCAT" as subcategory,
           s."MAINTENANCE" as maintenance, s."GEN" as gender
    FROM dashboard_data s
    WHERE s."order_date" BETWEEN :start_date AND :end_date
    AND s."CAT" = 'Bikes'
    """
    params = {"start_date": start_date, "end_date": end_date}

    bike_data = load_data(text(base_query), params=params)

    # Convert date columns
    for col in ['order_date', 'ship_date', 'due_date']:
        bike_data[col] = pd.to_datetime(bike_data[col])

    # Standardize gender values
    bike_data['gender'] = bike_data['gender'].replace({'M': 'MALE', 'F': 'FEMALE', 'MALES': 'MALE', 'FEMALES': 'FEMALE'})

    # KPIs
    st.markdown('<a id="key-performance-indicators"></a>', unsafe_allow_html=True)
    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="kpi-box">
                <div class="metric-label">Total Bike Sales</div>
                <div class="metric-value">${bike_data['sls_sales'].sum():,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="kpi-box">
                <div class="metric-label">Average Bike Price</div>
                <div class="metric-value">${bike_data['sls_sales'].mean():,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="kpi-box">
                <div class="metric-label">Total Bike Orders</div>
                <div class="metric-value">{bike_data['sls_ord_num'].nunique():,}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="kpi-box">
                <div class="metric-label">Unique Bike Models</div>
                <div class="metric-value">{bike_data['prd_key'].nunique():,}</div>
            </div>
        """, unsafe_allow_html=True)

    # Bike Sales Trend Over Time and Gender-Bike Type Distribution
    st.markdown('<a id="sales-analysis"></a>', unsafe_allow_html=True)
    st.subheader("Sales Analysis")
    col1, col2 = st.columns([1.5, 1])  # Make second column narrower

    with col1:
        # Create combined gender-bike type categories
        gender_bike_sales = bike_data.groupby(['gender', 'subcategory'])['sls_sales'].sum().reset_index()
        gender_bike_sales['category'] = gender_bike_sales['gender'] + ' - ' + gender_bike_sales['subcategory']
        
        fig_pie = px.pie(gender_bike_sales, 
                        values='sls_sales', 
                        names='category',
                        title='Sales Distribution by Gender and Bike Type',
                        color_discrete_sequence=COLORS)
        fig_pie.update_layout(
            title_font_color=TEXT_COLOR,
            font_color=TEXT_COLOR,
            height=500  # Made the pie chart bigger
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Extract year and month, then group by year and month
        sales_trend = bike_data.copy()
        sales_trend['year'] = sales_trend['order_date'].dt.year
        sales_trend['month'] = sales_trend['order_date'].dt.month
        sales_trend = sales_trend.groupby(['year', 'month'])['sls_sales'].sum().reset_index()
        
        fig1 = px.line(sales_trend, 
                      x='month', 
                      y='sls_sales',
                      color='year',
                      title='Monthly Bike Sales Trend by Year',
                      labels={'month': 'Month', 'sls_sales': 'Total Sales ($)', 'year': 'Year'},
                      color_discrete_sequence=['#2c1c0c', '#a85d04', '#e0aa01', '#ecd401'])
        
        fig1.update_traces(mode='lines+markers', marker=dict(size=6), line=dict(width=3))
        fig1.update_layout(
            title_font_color=TEXT_COLOR,
            font_color=TEXT_COLOR,
            xaxis_title_font_color=TEXT_COLOR,
            yaxis_title_font_color=TEXT_COLOR,
            height=400,
            legend_title_text='Year',
            xaxis=dict(
                tickmode='array',
                ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                tickvals=list(range(1, 13))
            )
        )
        st.plotly_chart(fig1, use_container_width=True)

    # Top Selling Bike Models
    st.markdown('<a id="top-selling-bike-models"></a>', unsafe_allow_html=True)
    st.subheader("Top Selling Bike Models")
    top_models = bike_data.groupby('prd_key')['sls_quantity'].sum().reset_index().nlargest(10, 'sls_quantity')
    fig6 = px.bar(top_models, x='prd_key', y='sls_quantity',
                  title='Top 10 Bike Models by Quantity Sold',
                  labels={'prd_key': 'Bike Model', 'sls_quantity': 'Quantity Sold'},
                  color='prd_key',
                  color_discrete_sequence=['#2c1c0c', '#a85d04', '#e0aa01', '#ecd401'] * 3)  # Repeat colors for all 10 bars
    fig6.update_layout(
        title_font_color=TEXT_COLOR,
        font_color=TEXT_COLOR,
        xaxis_title_font_color=TEXT_COLOR,
        yaxis_title_font_color=TEXT_COLOR
    )
    st.plotly_chart(fig6, use_container_width=True)

    # Bike Categories Analysis
    st.markdown('<a id="bike-categories-analysis"></a>', unsafe_allow_html=True)
    st.subheader("Bike Categories Analysis")
    col1, col2 = st.columns(2)

    with col1:
        subcat_sales = bike_data.groupby('subcategory')['sls_sales'].sum().reset_index().nlargest(2, 'sls_sales')
        fig2 = px.bar(subcat_sales, x='subcategory', y='sls_sales',
                      title='Top 2 Bike Types by Sales',
                      labels={'subcategory': 'Bike Type', 'sls_sales': 'Total Sales ($)'},
                      color='subcategory',
                      color_discrete_sequence=BAR_COLORS)
        fig2.update_layout(
            title_font_color=TEXT_COLOR,
            font_color=TEXT_COLOR,
            xaxis_title_font_color=TEXT_COLOR,
            yaxis_title_font_color=TEXT_COLOR
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        # Create a stacked bar chart for maintenance by gender
        maintenance_gender = bike_data.groupby(['maintenance', 'gender'])['sls_sales'].sum().reset_index()
        fig3 = px.bar(maintenance_gender, 
                      y='maintenance', 
                      x='sls_sales',
                      color='gender',
                      orientation='h',
                      title='Sales by Maintenance Requirement and Gender',
                      labels={'maintenance': 'Requires Maintenance', 
                             'sls_sales': 'Total Sales ($)',
                             'gender': 'Gender'},
                      color_discrete_sequence=['#2c1c0c', '#a85d04', '#e0aa01', '#ecd401'])
        fig3.update_layout(
            title_font_color=TEXT_COLOR,
            font_color=TEXT_COLOR,
            xaxis_title_font_color=TEXT_COLOR,
            yaxis_title_font_color=TEXT_COLOR
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Customer Demographics for Bike Sales
    st.markdown('<a id="bike-customer-demographics"></a>', unsafe_allow_html=True)
    st.subheader("Bike Customer Demographics")
    col1, col2 = st.columns(2)

    with col1:
        gender_dist = bike_data.groupby('gender')['sls_ord_num'].nunique().reset_index()
        fig4 = px.pie(gender_dist, values='sls_ord_num', names='gender',
                      title='Bike Orders by Gender',
                      color_discrete_sequence=['#2c1c0c', '#a85d04', '#e0aa01', '#ecd401'])
        fig4.update_layout(
            title_font_color=TEXT_COLOR,
            font_color=TEXT_COLOR
        )
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        # Monthly sales by gender
        monthly_gender = bike_data.groupby([pd.Grouper(key='order_date', freq='M'), 'gender'])['sls_sales'].sum().reset_index()
        fig5 = px.line(monthly_gender, x='order_date', y='sls_sales', color='gender',
                      title='Monthly Bike Sales by Gender',
                      labels={'order_date': 'Date', 'sls_sales': 'Total Sales ($)', 'gender': 'Gender'},
                      color_discrete_sequence=['#2c1c0c', '#a85d04', '#e0aa01', '#ecd401'])
        fig5.update_traces(mode='lines+markers', marker=dict(size=6), line=dict(width=3))
        fig5.update_layout(
            title_font_color=TEXT_COLOR,
            font_color=TEXT_COLOR,
            xaxis_title_font_color=TEXT_COLOR,
            yaxis_title_font_color=TEXT_COLOR
        )
        st.plotly_chart(fig5, use_container_width=True)

if __name__ == "__main__":
    main()
