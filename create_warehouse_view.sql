-- Drop the view if it exists
DROP VIEW IF EXISTS dashboard_data;

-- Create a view that handles all transformations
CREATE OR REPLACE VIEW dashboard_data AS
WITH transformed_data AS (
    SELECT 
        -- Original columns
        sls_ord_num,
        prd_key,
        "CID",
        sls_quantity,
        prd_id,
        prd_nm,
        "BDATE",
        "GEN",
        cst_id,
        cst_create_date,
        "CNTRY",
        prd_line,
        "CAT",
        sls_order_dt,
        sls_ship_dt,
        sls_due_dt,
        prd_cost,
        sls_sales,
        sls_price,
        cst_firstname,
        cst_lastname,
        cst_marital_status,
        -- Date transformations
        CASE 
            WHEN sls_order_dt IS NOT NULL AND TRIM(CAST(sls_order_dt AS TEXT)) != '' AND CAST(sls_order_dt AS TEXT) != '0' THEN 
                TO_DATE(CAST(sls_order_dt AS TEXT), 'YYYYMMDD')
            ELSE NULL 
        END as order_date,
        CASE 
            WHEN sls_ship_dt IS NOT NULL THEN 
                TO_DATE(CAST(sls_ship_dt AS TEXT), 'YYYYMMDD')
            ELSE NULL 
        END as ship_date,
        CASE 
            WHEN sls_due_dt IS NOT NULL THEN 
                TO_DATE(CAST(sls_due_dt AS TEXT), 'YYYYMMDD')
            ELSE NULL 
        END as due_date,
        -- Clean date columns
        CASE WHEN "BDATE" IS NOT NULL AND TRIM(CAST("BDATE" AS TEXT)) != '' THEN TO_DATE("BDATE", 'YYYY-MM-DD') ELSE NULL END as birth_date,
        CASE WHEN cst_create_date IS NOT NULL AND TRIM(CAST(cst_create_date AS TEXT)) != '' THEN TO_DATE(cst_create_date, 'YYYY-MM-DD') ELSE NULL END as customer_creation_date,
        -- Gender standardization
        CASE 
            WHEN UPPER(TRIM("GEN")) IN ('M', 'MALE', 'MALES') THEN 'MALE'
            WHEN UPPER(TRIM("GEN")) IN ('F', 'FEMALE', 'FEMALES') THEN 'FEMALE'
            ELSE 'UNKNOWN'
        END as gender,
        -- Country standardization
        UPPER(TRIM("CNTRY")) as country,
        -- Calculate customer age
        CASE WHEN "BDATE" IS NOT NULL AND TRIM(CAST("BDATE" AS TEXT)) != '' THEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, TO_DATE("BDATE", 'YYYY-MM-DD'))) ELSE NULL END as customer_age,
        -- Calculate order to ship days
        CASE 
            WHEN sls_order_dt IS NOT NULL AND sls_ship_dt IS NOT NULL AND TRIM(CAST(sls_order_dt AS TEXT)) != '' AND CAST(sls_order_dt AS TEXT) != '0' AND TRIM(CAST(sls_ship_dt AS TEXT)) != '' AND CAST(sls_ship_dt AS TEXT) != '0' THEN
                TO_DATE(CAST(sls_ship_dt AS TEXT), 'YYYYMMDD') - TO_DATE(CAST(sls_order_dt AS TEXT), 'YYYYMMDD')
            ELSE NULL
        END as order_to_ship_days
    FROM hardware_sales
    WHERE 
        -- Remove outliers (z-score > 3)
        ABS((sls_quantity - (SELECT AVG(sls_quantity) FROM hardware_sales)) / 
            (SELECT STDDEV(sls_quantity) FROM hardware_sales)) <= 3
        AND
        ABS((sls_price - (SELECT AVG(sls_price) FROM hardware_sales)) / 
            (SELECT STDDEV(sls_price) FROM hardware_sales)) <= 3
)
SELECT 
    sls_ord_num,
    prd_key,
    "CID",
    sls_quantity,
    prd_id,
    prd_nm,
    "BDATE",
    "GEN",
    cst_id,
    cst_create_date,
    "CNTRY",
    prd_line,
    "CAT",
    sls_order_dt,
    sls_ship_dt,
    sls_due_dt,
    order_date,
    ship_date,
    due_date,
    birth_date,
    customer_creation_date,
    gender,
    country,
    customer_age,
    order_to_ship_days,
    -- Handle missing values
    COALESCE(sls_sales, (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY sls_sales) FROM hardware_sales)) as sls_sales,
    COALESCE(sls_price, (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY sls_price) FROM hardware_sales)) as sls_price,
    COALESCE(prd_cost, (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY prd_cost) FROM hardware_sales)) as prd_cost,
    COALESCE(cst_firstname, 'Not Specified') as cst_firstname,
    COALESCE(cst_lastname, 'Not Specified') as cst_lastname,
    COALESCE(cst_marital_status, 'Not Specified') as cst_marital_status
FROM transformed_data; 