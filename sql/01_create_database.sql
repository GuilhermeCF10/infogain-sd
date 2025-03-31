-- 
-- # SQL SCRIPT: DATABASE INITIALIZATION
-- 
-- **Author:** Guilherme Fialho  
-- **Created:** 2025-03-30  
-- **Last Modified:** 2025-03-30

--
-- # Dental Analytics Project - Database Initialization
--
-- ## Purpose
-- This script initializes the database structure for the Dental Analytics Solution.
-- It creates the necessary tables to store raw dental utilization data from the Denti-Cal program.
--
-- ## Table Structure
-- The `raw_dental` table stores the initial import of data with the following categories:
-- - Provider identification (NPI, name)
-- - Service categorization (year, delivery system, provider type)
-- - Patient demographics (age groups)
-- - Service counts by category (preventive, treatment, exam services)

-- | Create raw data table with original data types
CREATE TABLE IF NOT EXISTS raw_dental (
    -- | Provider identification
    rendering_npi VARCHAR(20),         -- | National Provider Identifier
    provider_legal_name VARCHAR(100),  -- | Legal name of the dental provider
    
    -- | Service categorization
    calendar_year INT,                 -- | Year of service delivery
    delivery_system VARCHAR(20),       -- | Method of service delivery (FFS, GMC, etc.)
    provider_type VARCHAR(20),         -- | Type of dental provider
    age_group VARCHAR(20),             -- | Patient age grouping
    -- | Advantage metrics (all dental services)
    adv_user_cnt VARCHAR(20),          -- | Count of unique patients receiving any dental service
    adv_user_annotation_code VARCHAR(20), -- | Data quality indicator for adv_user_cnt
    adv_svc_cnt VARCHAR(20),           -- | Count of all dental services provided
    adv_svc_annotation_code VARCHAR(20), -- | Data quality indicator for adv_svc_cnt
    -- | Preventive service metrics
    prev_user_cnt VARCHAR(20),         -- | Count of unique patients receiving preventive services
    prev_user_annotation_code VARCHAR(20), -- | Data quality indicator for prev_user_cnt
    prev_svc_cnt VARCHAR(20),          -- | Count of preventive services provided
    prev_svc_annotation_code VARCHAR(20), -- | Data quality indicator for prev_svc_cnt
    -- | Treatment service metrics
    txmt_user_cnt VARCHAR(20),         -- | Count of unique patients receiving treatment services
    txmt_user_annotation_code VARCHAR(20), -- | Data quality indicator for txmt_user_cnt
    txmt_svc_cnt VARCHAR(20),          -- | Count of treatment services provided
    txmt_svc_annotation_code VARCHAR(20), -- | Data quality indicator for txmt_svc_cnt
    -- | Examination service metrics
    exam_user_cnt VARCHAR(20),         -- | Count of unique patients receiving examination services
    exam_user_annotation_code VARCHAR(20), -- | Data quality indicator for exam_user_cnt
    exam_svc_cnt VARCHAR(20),          -- | Count of examination services provided
    exam_svc_annotation_code VARCHAR(20)  -- | Data quality indicator for exam_svc_cnt
);
