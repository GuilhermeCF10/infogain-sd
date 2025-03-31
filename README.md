# Dental Analytics Solution

A comprehensive analytics application that transforms dental care utilization data into actionable insights through an interactive dashboard with data visualizations, SQL documentation, and AI-generated reports.

## Architecture

```
+-------------+     +------------------+     +-------------------+     +-------------------+
|             |     |                  |     |                   |     |                   |
|   MySQL     +---->+  Python ETL      +---->+  Streamlit App    +---->+  User Interface   |
|  Database   |     |  (SQL Scripts)   |     |                   |     |                   |
|             |     |                  |     |                   |     |                   |
+-------------+     +------------------+     +-------------------+     +-------------------+
                            |                         |
                            v                         v
                    +----------------+        +---------------------+
                    |                |        |                     |
                    | Data Layers:   |        | Views:              |
                    | 0. Tables      |        | - Project Overview  |
                    | 1. Raw         |        | - Dashboard         |
                    | 2. Trusted     |        | - SQL Documentation |
                    | 3. Refined     |        |                     |
                    |                |        |                     |
                    +----------------+        +---------------------+
```

The application follows a structured data flow:

1. **Data Storage**: MySQL database stores all dental utilization data
2. **ETL Process**: Python executes SQL scripts in sequence:
   - `01_create_database.sql`: Creates database structure and raw tables
   - `02_raw_to_trusted.sql`: Transforms raw data to trusted layer with clean data
   - `03_trusted_to_refined.sql`: Creates refined analytical layer from trusted data
3. **Visualization**: Streamlit app provides interactive interface with two main views:
   - Dashboard tab with metrics, charts, and AI-generated insights
   - SQL Documentation tab with annotated SQL code and markdown documentation

## Project Overview

The Dental Analytics Solution analyzes dental care utilization data from the Denti-Cal program. It implements a three-layer data architecture with SQL transformations to clean, standardize, and enrich raw data, followed by a feature-rich Streamlit dashboard for visualization and insights generation.

### Data Source

The data comes from the California Department of Health Care Services (DHCS) Denti-Cal program via their open data portal. This dataset provides detailed information about dental services provided by rendering providers for calendar year 2018.

![Dental Analytics Dashboard](https://storage.googleapis.com/kaggle-datasets-images/3643269/6329740/9bde64ea42cac732ffe73c962a350760/dataset-cover.jpg?t=2023-08-19-16-02-42)


**Dataset Information:**
- **Original Source:** [Denti-Cal](https://www.denti-cal.ca.gov/)
- **Dataset Portal:** [California Health and Human Services Open Data Portal](https://data.chhs.ca.gov/dataset/dental-care-utilization-by-rendering-provider)
- **Kaggle Dataset:** [Dental Care Utilization](https://www.kaggle.com/datasets/mpwolke/cusersmarildownloadsdentalcsv)
- **Data World Mirror:** [CHHS Dental Care Utilization](https://data.world/chhs/4cc0cf04-4f24-4624-9480-23266f8c3f7e)
- **Last Updated:** 2020-06-01
- **License:** [CHHS Terms of Use](https://data.chhs.ca.gov/pages/terms)

**Data Description:**

"This dataset provides beneficiary and service counts for annual dental visits, dental preventive services, dental treatment, and dental exams by rendering providers (by NPI) for calendar year (CY) 2018. It includes fee-for-service (FFS), Geographic Managed Care, and Pre-Paid Health Plans delivery systems. Rendering providers are categorized as either rendering or rendering at a safety net clinic. Beneficiaries are grouped by Age 0-20 and Age 21+."

**Data Contents:**
- Provider information (NPI, legal name)
- Delivery systems (FFS, GMC, PHP)
- Patient age groups (0-20, 21+) 
- Service counts by type (preventive, treatment, examination)
- Patient counts by service type

## Project Structure

```
infogain-sd/
├── app/
│   ├── app.py                    # Main Streamlit dashboard
│   ├── ai_reporting.py           # AI-powered insights generation
│   ├── sql_documentation.py      # SQL documentation display module
│   └── utils.py                  # Utility functions for data processing and visualization
├── sql/
│   ├── 01_create_database.sql    # Database initialization script
│   ├── 02_raw_to_trusted.sql     # First transformation layer
│   └── 03_trusted_to_refined.sql # Second transformation layer
├── .env                          # Environment variables file
├── etl.py                        # ETL script for data processing
├── LATEST_REPORT.md              # Most recent AI-generated report
├── raw_dental.csv                # Original source data
├── README.md                     # Project documentation (this file)
├── requirements.txt              # Dependencies for the project
└── run.sh                        # Execution script
```

## Data Processing Pipeline

This project implements a three-layer data architecture:

### 1. Raw Layer
- Original source data in its unmodified form
- Contains potential data quality issues, inconsistencies, or missing values
- Implemented in `sql/01_create_database.sql`

### 2. Trusted Layer (ETL Process 1)
- Data cleaning and standardization
- Handling of null values and explicit data type conversion
- Addition of basic derived metrics
- Implementation: `sql/02_raw_to_trusted.sql`

### 3. Refined Layer (ETL Process 2)
- Advanced analytics-ready data
- Aggregations and summary tables
- Complex derived metrics and KPIs
- Provider efficiency scoring
- Implementation: `sql/03_trusted_to_refined.sql`

## Dashboard Features

The Streamlit dashboard (`app/app.py`) provides interactive visualization and analysis of the dental care utilization data through multiple tabs:

### Project Overview Tab
- Comprehensive documentation of the project
- Architecture diagram showing data flow
- Project structure and organization
- Details on data processing pipeline
- Instructions for setup and usage

### Dashboard Tab
- **Key Metrics Overview**: Total providers, patients, services, and average services per patient
- **Service Distribution Analysis**: Breakdown of service types (preventive, treatment, examination)
- **Age Group Comparison**: Patient volumes and service intensity by age group
- **Delivery System Performance**: Comparison of different delivery systems (FFS, GMC, PHP)
- **Provider Analysis**: Top providers by volume and efficiency
- **Service Intensity Heatmap**: Visual representation of service patterns
- **AI-Generated Insights**: Automated analysis report highlighting key findings with export functionality

### SQL Documentation Tab
- Interactive display of SQL scripts with accompanying documentation
- Documentation viewer with metadata extraction
- Side-by-side display of SQL code and markdown documentation
- Structured format with script metadata, purpose, and transformation details

## SQL Documentation Format

All SQL scripts include structured markdown documentation using SQL comments:

- Use standard SQL comments (`--`) for content that should appear in documentation
- Use special comment format (`-- |`) for technical/code-specific comments that should remain in the code but not appear in documentation

Example documentation structure:
```sql
-- # SQL SCRIPT: [Script Title]
-- 
-- **Author:** [Author Name]
-- **Created:** [Creation Date]
-- **Last Modified:** [Last Modification Date]
-- 
-- ## Purpose
-- [Description of what this script does]
-- 
-- ## Transformations
-- [Details about data transformations]
-- 
-- ## Dependencies
-- [Required tables, views, or procedures]
--
-- Technical comment that won't show in docs
-- | This is a technical comment that won't appear in the markdown documentation
```

## How to Use This Project

### Prerequisites
- Python 3.8+
- MySQL database
- OpenAI API key (for AI-generated insights)
- Required Python packages (see `requirements.txt`)

### Setup and Execution

1. **Configure the OpenAI API key**:
   ```bash
   # Set your OpenAI API key as environment variable
   export OPENAI_API_KEY="your-api-key"
   ```

2. **Database configuration**:
   
   The database configuration is managed through the `.env` file in the project root. The file already contains the default configuration:
   ```
   DATABASE_NAME=dental_analytics
   DATABASE_USER=root
   DATABASE_PASSWORD=root
   DATABASE_HOST=localhost
   DATABASE_PORT=3306
   ```
   
   You can modify these values if needed for your specific database setup.

3. **Run the initialization script**:
   ```bash
   # Execute the setup script
   ./run.sh
   ```

   This script will:
   - Configure other necessary environment variables
   - Activate the conda environment
   - Initialize the database if needed

4. **Alternatively, set up manually**:
   ```bash
   # Create and activate conda environment
   conda create --name infogain python=3.12
   conda activate infogain
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set OpenAI API key
   export OPENAI_API_KEY="your-api-key"
   ```

5. **Launch the Streamlit dashboard**:
   ```bash
   streamlit run app/app.py
   ```

6. **Explore the dashboard**:
   - Use the tab selector to navigate between Dashboard and SQL Documentation
   - Apply filters to focus on specific segments of data
   - Generate AI-powered insights for deeper understanding
   - Explore SQL transformation logic through the documentation viewer

## Data Type Handling

This application implements careful data type handling throughout:

- Numeric columns from the database are loaded as strings initially
- All numeric operations require explicit conversion using `pd.to_numeric()`
- Data type conversions are implemented before any mathematical operations

## Analysis Focus Areas

This project enables several key analytical areas:

1. **Provider Performance Analysis**:
   - Identify high-volume and high-efficiency providers
   - Compare service intensity across providers
   - Analyze preventive vs. treatment care patterns

2. **Age Group Utilization Patterns**:
   - Compare service utilization between children/youth and adults
   - Identify differences in preventive care coverage
   - Analyze service types by age group

3. **Delivery System Effectiveness**:
   - Compare efficiency across delivery systems (FFS, GMC, PHP)
   - Evaluate coverage percentages and service ratios
   - Identify system-specific performance patterns

4. **Service Type Distribution**:
   - Analyze preventive service coverage
   - Evaluate treatment intensity
   - Identify examination rates and patterns
   
## Future Enhancements

Potential enhancements to the project could include:

### Scaled Data Architecture
- **Expanded Data Sources**:
  - Integration with much larger datasets (millions of records across multiple years)
  - Ingestion of additional dental healthcare data sources with more detailed patient information
  - Combining clinical data with financial and demographic information for comprehensive analysis

### Cloud-native Analytics Platform
- **BigQuery Implementation**:
  - Migration from MySQL to Google BigQuery for high-performance analysis of massive datasets
  - Leveraging BigQuery's columnar storage for accelerated analytical queries
  - Utilizing BigQuery ML for in-database machine learning capabilities
  - Implementing partitioning and clustering strategies for optimal performance

### Enterprise-grade Orchestration
- **Pipeline Orchestration**:
  - Implementation of Apache Airflow or Google Cloud Composer for workflow management
  - Creation of directed acyclic graphs (DAGs) for complex ETL dependencies
  - Scheduled executions with robust error handling and notifications
  - Integration with data quality validation tools to ensure analytical integrity

### Advanced AI Integration
- **Enhanced AI Insights**:
  - Deep learning models for dental treatment outcome prediction
  - Natural language processing to generate more contextually relevant insights
  - Anomaly detection systems to identify unusual service utilization patterns
  - Patient segmentation using clustering algorithms to identify targeted intervention opportunities

### Additional Analytical Capabilities
- **Multi-dimensional Analysis**:
  - Time-series analysis for multi-year trend detection and seasonality patterns
  - Geographic mapping with regional performance metrics and access analysis
  - Provider performance prediction models with confidence intervals
  - Interactive documentation with automated SQL diagram generation

---

*This mini-project was developed as a practical exercise to apply SQL, ETL, and Python knowledge, demonstrating how to transform raw data into insights through a simple analytics pipeline.*