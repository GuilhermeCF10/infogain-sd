-- 
-- # SQL SCRIPT: TRUSTED TO REFINED DATA TRANSFORMATION
-- 
-- **Author:** Guilherme Fialho  
-- **Created:** 2025-03-30  
-- **Last Modified:** 2025-03-30
--
-- # Dental Analytics - Trusted to Refined Layer Transformation
--
-- ## Purpose
-- This script transforms trusted layer data into the refined analytical layer, creating a series of purpose-specific tables
-- optimized for dashboard visualization and insight generation.
--
-- ## Transformation Approach
-- This script uses Common Table Expressions (CTEs) for complex metric calculations and aggregations:
--    - Each analytics table is created using a modular approach
--    - CTEs are used to break down complex calculations into logical steps
--    - This improves readability and maintainability of complex scoring formulas
--    - Provides clear documentation for each calculation component
-- 
-- ## Refined Tables Created
-- 1. **refined_dental** - Enhanced main table with additional derived metrics
--    - Maintains all original fields from trusted layer
--    - Adds coverage percentages to measure care effectiveness
--    - Includes service intensity categorization for pattern analysis
--
-- 2. **refined_provider_summary** - Provider-level aggregated metrics
--    - Uses CTEs to build component metrics for efficiency scoring
--    - Calculates a composite efficiency score using multiple factors
--    - Enables provider benchmarking and best practice identification
--
-- 3. **refined_age_group_summary** - Demographic analysis by patient age
--    - Groups and aggregates data by patient age demographics
--    - Calculates service distribution patterns by age group
--    - Supports targeted intervention planning
--
-- 4. **refined_delivery_system_summary** - Healthcare system comparison
--    - Uses CTEs to organize calculation of system effectiveness metrics
--    - Creates a composite effectiveness score using weighted factors
--    - Enables systematic comparison between delivery models
--
-- ## Dependencies
-- - Requires `trusted_dental` table with complete schema
-- - Requires appropriate database privileges for table creation
    -- | ===== CLEANUP SECTION =====
    -- | Drop all refined tables if they exist to ensure a fresh transformation
    -- | This guarantees we're starting with clean data structures
    DROP TABLE IF EXISTS refined_dental;
    DROP TABLE IF EXISTS refined_provider_summary;
    DROP TABLE IF EXISTS refined_age_group_summary;
    DROP TABLE IF EXISTS refined_delivery_system_summary;
    
    -- | Start transaction for atomic table creation
    START TRANSACTION;

    -- | ===== MAIN REFINED TABLE CREATION =====
    -- | Creates the main refined_dental table using CTEs to organize the enhancement logic
    -- | Breaking calculations into logical steps improves readability and maintainability
    CREATE TABLE refined_dental AS
    WITH 
    -- | CTE 1: Prepare original data with converted numeric values for calculations
    -- | This avoids casting operations multiple times in subsequent calculations
    base_data AS (
        SELECT
            *,
            -- | Convert string counts to numeric for safe calculations
            CAST(prev_user_cnt AS DECIMAL(10,2)) AS prev_user_num,
            CAST(exam_user_cnt AS DECIMAL(10,2)) AS exam_user_num,
            CAST(txmt_user_cnt AS DECIMAL(10,2)) AS txmt_user_num,
            CAST(adv_user_cnt AS DECIMAL(10,2)) AS adv_user_num
        FROM trusted_dental
    ),
    
    -- | CTE 2: Calculate coverage percentages 
    -- | Measures what percentage of patients receive each type of service
    -- | Protected against division by zero with CASE statements
    coverage_metrics AS (
        SELECT
            *,
            -- | Preventive coverage: % of patients receiving preventive services
            -- | Higher values indicate better preventive care delivery models
            CASE 
                WHEN prev_user_num > 0 AND adv_user_num > 0 
                THEN ROUND((prev_user_num / adv_user_num) * 100, 2)
                ELSE 0
            END AS preventive_coverage_pct,
            
            -- | Examination coverage: % of patients receiving diagnostic services
            -- | Indicates thoroughness of assessment and care planning
            CASE 
                WHEN exam_user_num > 0 AND adv_user_num > 0 
                THEN ROUND((exam_user_num / adv_user_num) * 100, 2)
                ELSE 0
            END AS exam_coverage_pct,
            
            -- | Treatment coverage: % of patients receiving treatment services
            -- | Indicates actual intervention delivery effectiveness
            CASE 
                WHEN txmt_user_num > 0 AND adv_user_num > 0 
                THEN ROUND((txmt_user_num / adv_user_num) * 100, 2)
                ELSE 0
            END AS treatment_coverage_pct
        FROM base_data
    )
    
    -- | Final SELECT: Add service intensity classification and return all fields
    SELECT
        rendering_npi,
        provider_legal_name,
        calendar_year,
        delivery_system,
        provider_type,
        age_group,
        adv_user_cnt,
        adv_svc_cnt,
        prev_user_cnt,
        prev_svc_cnt,
        txmt_user_cnt,
        txmt_svc_cnt,
        exam_user_cnt,
        exam_svc_cnt,
        total_services,
        services_per_user,
        preventive_ratio,
        treatment_ratio,
        exam_ratio,
        preventive_coverage_pct,
        exam_coverage_pct,
        treatment_coverage_pct,
        -- | SERVICE INTENSITY CLASSIFICATION
        -- | Categorizes service utilization level for quick pattern identification:
        -- | - High: 8+ services per user (potential overutilization or complex cases)
        -- | - Medium: 4-7 services per user (expected utilization pattern)
        -- | - Low: <4 services per user (potential underutilization or healthy patients)
        CASE
            WHEN services_per_user >= 8 THEN 'High'
            WHEN services_per_user >= 4 THEN 'Medium'
            ELSE 'Low'
        END AS service_intensity
    FROM coverage_metrics;
    
    -- | ===== PROVIDER SUMMARY TABLE =====
    -- | Creates a provider-level analytical view using CTEs to organize the calculation steps
    -- | Each CTE focuses on a specific component of the analysis for better readability
    CREATE TABLE refined_provider_summary AS
    WITH 
    -- | CTE 1: Base provider aggregations - Calculate core metrics for each provider
    provider_base_metrics AS (
        SELECT
            rendering_npi,
            provider_legal_name,
            SUM(adv_user_cnt) AS total_users,
            SUM(total_services) AS total_services,
            ROUND(AVG(services_per_user), 2) AS avg_services_per_user,
            ROUND(AVG(preventive_ratio) * 100, 2) AS avg_preventive_ratio_pct,
            ROUND(AVG(treatment_ratio) * 100, 2) AS avg_treatment_ratio_pct,
            ROUND(AVG(exam_ratio) * 100, 2) AS avg_exam_ratio_pct,
            COUNT(DISTINCT delivery_system) AS delivery_systems_count,
            -- | Store raw values for score calculation
            AVG(services_per_user) AS raw_avg_services,
            AVG(preventive_ratio) AS raw_preventive_ratio,
            SUM(adv_user_cnt) AS raw_total_users
        FROM trusted_dental
        GROUP BY rendering_npi, provider_legal_name
    ),
    
    -- | CTE 2: Score components - Break down the efficiency score calculation
    -- | This makes each component of the scoring formula clear and maintainable
    score_components AS (
        SELECT
            *,
            -- | Component 1: Service Efficiency (30%)
            -- | Balances between adequate care and preventing overutilization
            (raw_avg_services * 0.3) AS service_efficiency_component,
            
            -- | Component 2: Preventive Focus (40%) 
            -- | Major component that rewards prevention-oriented providers
            (raw_preventive_ratio * 0.4 * 10) AS preventive_focus_component,
            
            -- | Component 3: Patient Volume Score (5-15%)
            -- | Rewards providers with higher patient volumes - indicator of experience
            CASE 
                WHEN raw_total_users > 500 THEN 5
                WHEN raw_total_users > 100 THEN 3
                ELSE 1 
            END AS volume_component,
            
            -- | Component 4: Delivery System Reach (0-10%)
            -- | Rewards versatility across different healthcare delivery systems
            CASE 
                WHEN delivery_systems_count > 1 THEN 2 
                ELSE 0 
            END AS system_reach_component
        FROM provider_base_metrics
    )
    
    -- | Final SELECT: Combine all metrics and calculate the composite efficiency score
    SELECT
        rendering_npi,
        provider_legal_name,
        total_users,
        total_services,
        avg_services_per_user,
        avg_preventive_ratio_pct,
        avg_treatment_ratio_pct,
        avg_exam_ratio_pct,
        delivery_systems_count,
        -- | Provider Efficiency Score: Combination of all component scores
        -- | Higher scores indicate providers with optimal practice patterns
        ROUND(
            service_efficiency_component + 
            preventive_focus_component + 
            volume_component + 
            system_reach_component
        , 2) AS provider_efficiency_score
    FROM score_components
    ORDER BY total_users DESC;
    
    -- | ===== AGE GROUP SUMMARY TABLE =====
    -- | Creates a demographic analytical view using CTEs for clearer organization
    -- | Allows for better understanding of service patterns across age demographics
    CREATE TABLE refined_age_group_summary AS
    WITH 
    -- | CTE 1: Group data by age and calculate base metrics
    -- | Primary aggregation by age group with basic counts and sums
    age_group_base_metrics AS (
        SELECT
            age_group,
            COUNT(DISTINCT rendering_npi) AS provider_count,
            SUM(adv_user_cnt) AS total_users,
            SUM(total_services) AS total_services,
            ROUND(AVG(services_per_user), 2) AS avg_services_per_user,
            SUM(prev_svc_cnt) AS total_preventive_services,
            SUM(txmt_svc_cnt) AS total_treatment_services,
            SUM(exam_svc_cnt) AS total_exam_services
        FROM trusted_dental
        GROUP BY age_group
    )
    
    -- | Final SELECT: Calculate service distribution percentages by age group
    -- | Safe division using IF to handle potential divide-by-zero scenarios
    SELECT
        age_group,
        provider_count,
        total_users,
        total_services,
        avg_services_per_user,
        -- | Calculate percentage distribution of each service type
        -- | These metrics reveal care patterns specific to each age demographic
        ROUND(total_preventive_services / IF(total_services = 0, 1, total_services) * 100, 2) AS preventive_services_pct,
        ROUND(total_treatment_services / IF(total_services = 0, 1, total_services) * 100, 2) AS treatment_services_pct,
        ROUND(total_exam_services / IF(total_services = 0, 1, total_services) * 100, 2) AS exam_services_pct
    FROM age_group_base_metrics
    ORDER BY age_group;
    
    -- | ===== DELIVERY SYSTEM SUMMARY TABLE =====
    -- | Creates a delivery system analytical view using CTEs to organize calculation steps
    -- | Each CTE handles a specific part of the analysis for improved readability and maintenance
    CREATE TABLE refined_delivery_system_summary AS
    WITH 
    -- | CTE 1: Base system metrics - Aggregate core metrics by delivery system
    -- | Handles the basic grouping and aggregation of raw metrics
    system_base_metrics AS (
        SELECT
            delivery_system,
            COUNT(DISTINCT rendering_npi) AS provider_count,
            SUM(adv_user_cnt) AS total_users,
            SUM(total_services) AS total_services,
            ROUND(AVG(services_per_user), 2) AS avg_services_per_user,
            SUM(prev_svc_cnt) AS total_preventive_services,
            SUM(txmt_svc_cnt) AS total_treatment_services,
            SUM(exam_svc_cnt) AS total_exam_services
        FROM trusted_dental
        GROUP BY delivery_system
    ),
    
    -- | CTE 2: Service distribution - Calculate service type percentages
    -- | Safe division with IF to prevent divide-by-zero errors
    service_distribution AS (
        SELECT
            *,
            -- | Calculate percentage of each service type with NULL protection
            ROUND(total_preventive_services / IF(total_services = 0, 1, total_services) * 100, 2) AS preventive_services_pct,
            ROUND(total_treatment_services / IF(total_services = 0, 1, total_services) * 100, 2) AS treatment_services_pct,
            ROUND(total_exam_services / IF(total_services = 0, 1, total_services) * 100, 2) AS exam_services_pct,
            
            -- | Pre-calculate components for the effectiveness score
            (total_preventive_services / IF(total_services = 0, 1, total_services) * 5) AS preventive_focus_component,
            (total_users / 1000) AS scale_efficiency_component,
            (avg_services_per_user * 0.5) AS service_efficiency_component
        FROM system_base_metrics
    )
    
    -- | Final SELECT: Combine all metrics and calculate the system effectiveness score
    SELECT
        delivery_system,
        provider_count,
        total_users,
        total_services,
        avg_services_per_user,
        preventive_services_pct,
        treatment_services_pct,
        exam_services_pct,
        -- | System Effectiveness Score: Combined weighted components
        -- | Component 1: Preventive Focus (50-70%) - Most heavily weighted
        -- | Component 2: Scale Efficiency (10-30%) - Rewards population reach
        -- | Component 3: Service Efficiency (10-20%) - Balances utilization
        ROUND(
            preventive_focus_component + 
            scale_efficiency_component + 
            service_efficiency_component
        , 2) AS system_effectiveness_score
    FROM service_distribution
    ORDER BY total_users DESC;
    
    -- | Commit transaction before creating indexes
    COMMIT;

    -- | ===== INDEX CREATION SECTION =====
    -- | Creates indexes on refined tables for optimized query performance
    -- | These indexes support common filtering and sorting patterns in dashboards/reports
    
    -- | Indexes for refined_dental (detailed table)
    CREATE INDEX idx_refined_dental_npi ON refined_dental(rendering_npi);
    CREATE INDEX idx_refined_dental_system ON refined_dental(delivery_system);
    CREATE INDEX idx_refined_dental_age ON refined_dental(age_group);
    CREATE INDEX idx_refined_dental_year ON refined_dental(calendar_year);
    
    -- | Indexes for refined_provider_summary (provider aggregates)
    -- | rendering_npi is likely unique, but index helps joins/lookups
    CREATE INDEX idx_refined_provider_summary_npi ON refined_provider_summary(rendering_npi);
    CREATE INDEX idx_refined_provider_efficiency ON refined_provider_summary(provider_efficiency_score);
    CREATE INDEX idx_refined_provider_total_users ON refined_provider_summary(total_users);

    -- | Indexes for refined_age_group_summary (age aggregates)
    CREATE INDEX idx_refined_age_summary_age ON refined_age_group_summary(age_group);

    -- | Indexes for refined_delivery_system_summary (system aggregates)
    CREATE INDEX idx_refined_del_sys_summary_system ON refined_delivery_system_summary(delivery_system);
    CREATE INDEX idx_refined_del_sys_effectiveness ON refined_delivery_system_summary(system_effectiveness_score);
    CREATE INDEX idx_refined_del_sys_total_users ON refined_delivery_system_summary(total_users);

    -- | ===== COMPLETION CONFIRMATION =====
    -- | Success message to indicate all transformations executed correctly
    SELECT 'Refined layer transformation completed successfully' AS Status;