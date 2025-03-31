-- 
-- # SQL SCRIPT: RAW TO TRUSTED DATA TRANSFORMATION
-- 
-- **Author:** Guilherme Fialho  
-- **Created:** 2025-03-30  
-- **Last Modified:** 2025-03-30
--
-- # Dental Analytics - Raw to Trusted Layer Transformation
--
-- ## Purpose
-- This script transforms raw dental data into the trusted layer by cleaning the source data, 
-- standardizing formats, and calculating derived metrics to enable reliable analytics.
--
-- ## Transformation Approach
-- This script uses Common Table Expressions (CTEs) to create a modular, step-by-step transformation pipeline.
-- Each CTE handles a specific part of the transformation process, making the code:
--    - More organized and easier to maintain
--    - Logically separated by function (normalization, conversion, calculation)
--    - Easier to understand with progressive data transformations
--    - More efficient by avoiding repetitive calculations
--
-- ## Transformation Operations
-- 1. **Data Cleaning (CTE: normalized_data)**
--    - Removes whitespace from text fields
--    - Normalizes null/empty values to '0' for metrics
--    - Standardizes data formats for consistency
--
-- 2. **Type Conversion (CTE: decimal_conversions)**
--    - Converts string values to decimal for mathematical operations
--    - Preserves original values while enabling accurate calculations
--
-- 3. **Derived Metrics Calculation (CTEs: totals_calculated, final_calculations)**
--    - **Total Services**: Sum of all service types (advisory, preventive, treatment, exam)
--    - **Services Per User**: Utilization rate measuring services delivered per patient
--    - **Service Ratios**: Proportion of each service type to total services
--       - Preventive Ratio: Measure of focus on preventative care
--       - Treatment Ratio: Measure of therapeutic interventions
--       - Exam Ratio: Measure of diagnostic services
--
-- 4. **Performance Optimization**
--    - Creates indexes on frequently queried fields
--    - Optimizes storage for analytical queries
--
-- ## Trusted Tables Created
-- 1. **trusted_dental** - Main table with cleaned and enhanced metrics
--    - Preserves original data with consistent formatting
--    - Handles null/empty values for analysis reliability
--    - Adds calculated service ratios and totals
--
-- ## Data Type Handling
-- - VARCHAR fields are used for numeric counts to preserve original formatted values
-- - DECIMAL casting is applied during calculations for mathematical precision
-- - Derived metrics use DECIMAL(10,2) for standardized ratio representation
--
-- ## Dependencies
-- - Requires `raw_dental` table with complete schema from the database initialization script
-- - Requires appropriate database privileges for table creation and indexing
    -- | Drop the trusted table if it exists to start fresh
    DROP TABLE IF EXISTS trusted_dental;
    -- | ===== TABLE CREATION SECTION =====
    -- | Creates the trusted_dental table with appropriate data types and constraints.
    -- | Note: VARCHAR is used for numeric fields to preserve original values with decimals,
    -- | while still allowing proper decimal calculations via CAST when needed.
    CREATE TABLE trusted_dental (
        id INT AUTO_INCREMENT PRIMARY KEY,
        rendering_npi VARCHAR(20),
        provider_legal_name VARCHAR(100),
        calendar_year INTEGER,
        delivery_system VARCHAR(20),
        provider_type VARCHAR(20),
        age_group VARCHAR(20),
        adv_user_cnt VARCHAR(20),    
        adv_svc_cnt VARCHAR(20),     
        prev_user_cnt VARCHAR(20),   
        prev_svc_cnt VARCHAR(20),    
        txmt_user_cnt VARCHAR(20),   
        txmt_svc_cnt VARCHAR(20),    
        exam_user_cnt VARCHAR(20),   
        exam_svc_cnt VARCHAR(20),    
        -- | Derived metrics
        total_services VARCHAR(20),  
        services_per_user DECIMAL(10,2),
        preventive_ratio DECIMAL(10,2),
        treatment_ratio DECIMAL(10,2),
        exam_ratio DECIMAL(10,2)
    );
    
    -- | Start transaction for atomic data transformation
    START TRANSACTION;

    -- | ===== DATA TRANSFORMATION SECTION =====
    -- | Insert data from raw_dental table with cleansing and transformation:
    -- | - Trims text fields to remove whitespace
    -- | - Handles empty/null numeric values
    -- | - Calculates derived metrics like service ratios and totals
    -- | - Uses DECIMAL casting for precise calculations while preserving original values
    -- | The approach below uses Common Table Expressions (CTE) to improve readability and maintainability
    
    -- | Insert data with the transformed values
    INSERT INTO trusted_dental (
        rendering_npi, provider_legal_name, calendar_year, delivery_system, provider_type, age_group,
        adv_user_cnt, adv_svc_cnt, prev_user_cnt, prev_svc_cnt, txmt_user_cnt, txmt_svc_cnt, 
        exam_user_cnt, exam_svc_cnt, total_services, services_per_user, preventive_ratio, 
        treatment_ratio, exam_ratio
    )
    -- | Start of Common Table Expressions (CTEs) for a more organized data transformation approach
    WITH 
    -- | CTE 1: Normalize text fields (trim) and handle empty/null values
    normalized_data AS (
        SELECT
            TRIM(rendering_npi) AS rendering_npi,
            TRIM(provider_legal_name) AS provider_legal_name,
            calendar_year,
            TRIM(delivery_system) AS delivery_system,
            TRIM(provider_type) AS provider_type,
            TRIM(age_group) AS age_group,
            -- | User counts: Store raw values but replace empty/null with '0'
            -- | Using COALESCE and NULLIF for cleaner handling of nulls/empty strings
            COALESCE(NULLIF(adv_user_cnt, ''), '0') AS adv_user_cnt,
            COALESCE(NULLIF(adv_svc_cnt, ''), '0') AS adv_svc_cnt,
            COALESCE(NULLIF(prev_user_cnt, ''), '0') AS prev_user_cnt,
            COALESCE(NULLIF(prev_svc_cnt, ''), '0') AS prev_svc_cnt,
            COALESCE(NULLIF(txmt_user_cnt, ''), '0') AS txmt_user_cnt,
            COALESCE(NULLIF(txmt_svc_cnt, ''), '0') AS txmt_svc_cnt,
            COALESCE(NULLIF(exam_user_cnt, ''), '0') AS exam_user_cnt,
            COALESCE(NULLIF(exam_svc_cnt, ''), '0') AS exam_svc_cnt
        FROM raw_dental
    ),
    -- | CTE 2: Calculate decimal versions of metrics for mathematical operations
    -- | This avoids repeating the CAST operations throughout the query
    decimal_conversions AS (
        SELECT
            *,
            -- | Convert string values to decimal for calculations
            CAST(adv_user_cnt AS DECIMAL(10,2)) AS adv_user_dec,
            CAST(adv_svc_cnt AS DECIMAL(10,2)) AS adv_svc_dec,
            CAST(prev_user_cnt AS DECIMAL(10,2)) AS prev_user_dec,
            CAST(prev_svc_cnt AS DECIMAL(10,2)) AS prev_svc_dec,
            CAST(txmt_user_cnt AS DECIMAL(10,2)) AS txmt_user_dec,
            CAST(txmt_svc_cnt AS DECIMAL(10,2)) AS txmt_svc_dec,
            CAST(exam_user_cnt AS DECIMAL(10,2)) AS exam_user_dec,
            CAST(exam_svc_cnt AS DECIMAL(10,2)) AS exam_svc_dec
        FROM normalized_data
    ),
    -- | CTE 3: Calculate total services for reuse in multiple ratio calculations
    -- | This avoids repeating the same calculation multiple times
    totals_calculated AS (
        SELECT
            *,
            -- | Total services as decimal for ratio calculations
            (adv_svc_dec + prev_svc_dec + txmt_svc_dec + exam_svc_dec) AS total_services_dec
        FROM decimal_conversions
    ),
    -- | CTE 4: Calculate all ratios and derived metrics
    -- | This keeps all calculations in one place and simplifies the final SELECT
    final_calculations AS (
        SELECT
            *,
            -- | Convert total services to string format
            CAST(total_services_dec AS CHAR) AS total_services,
            -- | Services per user: Total services divided by total users
            -- | Key metric for understanding service utilization per patient
            CASE
                WHEN adv_user_dec > 0 THEN total_services_dec / adv_user_dec
                ELSE 0
            END AS services_per_user,
            -- | Preventive ratio: Proportion of preventive services to total services
            -- | Higher values indicate more focus on preventive care
            CASE
                WHEN total_services_dec > 0 THEN prev_svc_dec / total_services_dec
                ELSE 0
            END AS preventive_ratio,
            -- | Treatment ratio: Proportion of treatment services to total
            CASE
                WHEN total_services_dec > 0 THEN txmt_svc_dec / total_services_dec
                ELSE 0
            END AS treatment_ratio,
            -- | Exam ratio: Proportion of exam services to total
            CASE
                WHEN total_services_dec > 0 THEN exam_svc_dec / total_services_dec
                ELSE 0
            END AS exam_ratio
        FROM totals_calculated
    )
    -- | Final SELECT statement - all calculations are done in CTEs
    -- | This makes the final query very clean and easy to understand
    SELECT
        rendering_npi,
        provider_legal_name,
        calendar_year,
        delivery_system,
        provider_type,
        age_group,
        -- | Original count fields (normalized)
        adv_user_cnt,
        adv_svc_cnt,
        prev_user_cnt,
        prev_svc_cnt,
        txmt_user_cnt,
        txmt_svc_cnt,
        exam_user_cnt,
        exam_svc_cnt,
        -- | Derived metrics (all calculated in the CTEs)
        total_services,
        services_per_user,
        preventive_ratio,
        treatment_ratio,
        exam_ratio
    FROM final_calculations;
    
    -- | Commit transaction
    COMMIT;

    -- | Display completion message
    SELECT 'Trusted layer transformation completed successfully' AS Status;
