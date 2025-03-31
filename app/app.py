import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
from plotly.subplots import make_subplots
import mysql.connector
import os
from ai_reporting import DentalInsightsGenerator
from utils import DentalDataAnalyzer
from sql_documentation import SqlDocumentationManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Dental Care Utilization Dashboard",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application title (appears once)
st.title("🦷 Dental Care Utilization Dashboard")

# --- Session State Initialization ---
if 'selected_view' not in st.session_state:
    st.session_state.selected_view = "Project Overview" # Default view

# --- Database Connection & Data Loading ---
def get_database_connection():
    return mysql.connector.connect(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=int(os.getenv('DATABASE_PORT', 3306)),
        user=os.getenv('DATABASE_USER', 'root'),
        password=os.getenv('DATABASE_PASSWORD', 'root'),
        database=os.getenv('DATABASE_NAME', 'dental_analytics')
    )

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    conn = get_database_connection()
    
    dental_query = "SELECT * FROM refined_dental"
    provider_summary_query = "SELECT * FROM refined_provider_summary"
    age_group_summary_query = "SELECT * FROM refined_age_group_summary"
    delivery_system_summary_query = "SELECT * FROM refined_delivery_system_summary"
    
    dental_df = pd.read_sql(dental_query, conn)
    provider_summary_df = pd.read_sql(provider_summary_query, conn)
    age_group_summary_df = pd.read_sql(age_group_summary_query, conn)
    delivery_system_summary_df = pd.read_sql(delivery_system_summary_query, conn)
    
    conn.close()
    
    return dental_df, provider_summary_df, age_group_summary_df, delivery_system_summary_df

try:
    dental_df, provider_summary_df, age_group_summary_df, delivery_system_summary_df = load_data()
    data_analyzer = DentalDataAnalyzer(dental_df)
    data_loaded = True
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.warning("Please ensure the MySQL database is running and contains the refined data tables.")
    data_loaded = False
    data_analyzer = None
    # Initialize placeholders if data loading fails to prevent errors later
    dental_df = pd.DataFrame()
    provider_summary_df = pd.DataFrame()
    age_group_summary_df = pd.DataFrame()
    delivery_system_summary_df = pd.DataFrame()

# --- Sidebar Navigation and Filters ---
st.sidebar.title("Navigation")
selected_view = st.sidebar.radio(
    "Select View",
    ["Project Overview", "Dashboard", "SQL Documentation"],
    key='selected_view' # Use session state key
)

# Initialize filter variables
selected_delivery_system = 'All'
selected_age_group = 'All'
selected_provider_type = 'All'

# Conditionally display filters in the sidebar ONLY if Dashboard is selected
if selected_view == "Dashboard" and data_loaded:
    st.sidebar.header("Filters")
    
    # Delivery System filter
    delivery_systems = ['All'] + sorted(dental_df['delivery_system'].unique().tolist())
    selected_delivery_system = st.sidebar.selectbox(
        "Delivery System", 
        delivery_systems, 
        key='filter_delivery_system' # Key for session state
    )
    
    # Age Group filter
    age_groups = ['All'] + sorted(dental_df['age_group'].unique().tolist())
    selected_age_group = st.sidebar.selectbox(
        "Age Group", 
        age_groups, 
        key='filter_age_group' # Key for session state
    )
    
    # Provider Type filter
    provider_types = ['All'] + sorted(dental_df['provider_type'].unique().tolist())
    selected_provider_type = st.sidebar.selectbox(
        "Provider Type", 
        provider_types, 
        key='filter_provider_type' # Key for session state
    )

# --- Main Area Content (Conditional Rendering) ---

if selected_view == "Project Overview":
    st.header("Dental Analytics Solution - Project Documentation")
    st.markdown("""
    This dashboard provides insights into dental care utilization data from the Denti-Cal program for calendar year 2018.
    Analyze provider performance, patient demographics, and service distribution across different delivery systems.
    """)
    # Read and display README.md content
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md'), 'r') as f:
            readme_content = f.read()
        st.markdown(readme_content)
    except FileNotFoundError:
        st.warning("README.md file not found.")

elif selected_view == "Dashboard":
    if data_loaded:
        # Apply filters (using values potentially set in the sidebar)
        # Retrieve filter values from session state if they were set
        current_delivery_system = st.session_state.get('filter_delivery_system', 'All')
        current_age_group = st.session_state.get('filter_age_group', 'All')
        current_provider_type = st.session_state.get('filter_provider_type', 'All')
        
        filtered_df = data_analyzer.filter_data(
            delivery_system=current_delivery_system,
            age_group=current_age_group,
            provider_type=current_provider_type,
            use_original=True
        )

        # --- Dashboard Content (Only if data loaded and Dashboard selected) ---
        
        # Key metrics
        st.header("Key Metrics")
        st.markdown("*These core metrics provide a high-level overview of the dental care ecosystem...*")
        col1, col2, col3, col4 = st.columns(4)
        
        total_providers = filtered_df['rendering_npi'].nunique()
        total_patients = pd.to_numeric(filtered_df['adv_user_cnt'], errors='coerce').sum()
        total_services = pd.to_numeric(filtered_df['total_services'], errors='coerce').sum()
        avg_service_per_patient = total_services / total_patients if total_patients > 0 else 0
        
        col1.metric("Total Providers", f"{total_providers:,}")
        col2.metric("Total Patients", f"{total_patients:,}")
        col3.metric("Total Services", f"{total_services:,}")
        col4.metric("Avg Services per Patient", f"{avg_service_per_patient:.2f}")

        # Services breakdown
        st.header("Service Distribution")
        st.markdown("*Understanding the distribution of service types helps identify...*")
        
        # Use st.tabs for sub-navigation within the Dashboard view if desired
        tab1, tab2 = st.tabs(["Service Counts", "Service Ratios"])
    
        with tab1:
            service_counts = data_analyzer.get_service_counts(filtered_df)
            fig_sc = px.bar(service_counts, x='Service Type', y='Count', color='Service Type', title='Service Counts by Type', height=400)
            st.plotly_chart(fig_sc, use_container_width=True)
    
        with tab2:
            service_ratios = data_analyzer.get_service_ratios(filtered_df)
            fig_sr = px.pie(service_ratios, values='Percentage', names='Service Type', title='Service Distribution (%)', height=400)
            fig_sr.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_sr, use_container_width=True)

        # Age group comparison
        st.header("Age Group Comparison")
        st.markdown("*Analyzing service patterns across different age groups reveals...*")
        col_ag1, col_ag2 = st.columns(2)
        with col_ag1:
            age_users = data_analyzer.get_age_group_patients(filtered_df)
            fig_au = px.bar(age_users, x='Age Group', y='Patients', color='Age Group', title='Patients by Age Group', height=400)
            st.plotly_chart(fig_au, use_container_width=True)
        with col_ag2:
            age_services = data_analyzer.get_age_group_services(filtered_df)
            fig_as = px.bar(age_services, x='Age Group', y='Services per Patient', color='Age Group', title='Services per Patient by Age Group', height=400)
            st.plotly_chart(fig_as, use_container_width=True)

        # Delivery system performance
        st.header("Delivery System Performance")
        st.markdown("*Comparing different healthcare delivery systems helps identify...*")
        col_ds1, col_ds2 = st.columns(2)
        with col_ds1:
            system_coverage = data_analyzer.get_delivery_system_coverage(filtered_df)
            fig_dsc = px.bar(system_coverage, x='Delivery System', y=['Preventive Coverage (%)', 'Exam Coverage (%)', 'Treatment Coverage (%)'], title='Service Coverage by Delivery System', barmode='group', height=400)
            st.plotly_chart(fig_dsc, use_container_width=True)
        with col_ds2:
            system_efficiency = data_analyzer.get_delivery_system_efficiency(filtered_df)
            fig_dse = px.scatter(system_efficiency, x='Services per Patient', y='Preventive Ratio', size='Total Patients', color='Delivery System', title='Delivery System Efficiency', height=400)
            st.plotly_chart(fig_dse, use_container_width=True)

        # Top providers
        st.header("Top Providers")
        st.markdown("*Identifying high-performing providers offers valuable insights...*")
        top_n = st.slider("Number of top providers to show", 5, 20, 10, key='slider_top_n')
        tab_tp1, tab_tp2 = st.tabs(["By Patient Volume", "By Efficiency Score"])
        with tab_tp1:
            top_volume = data_analyzer.get_top_providers_by_volume(provider_summary_df, top_n)
            fig_tpv = px.bar(top_volume, x='provider_legal_name', y='total_users', title=f'Top {top_n} Providers by Patient Volume', color='total_users', height=500)
            fig_tpv.update_layout(xaxis_title='Provider', yaxis_title='Number of Patients')
            st.plotly_chart(fig_tpv, use_container_width=True)
        with tab_tp2:
            top_efficiency = data_analyzer.get_top_providers_by_efficiency(provider_summary_df, top_n)
            fig_tpe = px.bar(top_efficiency, x='provider_legal_name', y='provider_efficiency_score', title=f'Top {top_n} Providers by Efficiency Score', color='provider_efficiency_score', height=500)
            fig_tpe.update_layout(xaxis_title='Provider', yaxis_title='Efficiency Score')
            st.plotly_chart(fig_tpe, use_container_width=True)

        # Provider heatmap
        st.header("Provider Service Intensity")
        st.markdown("*This visualization highlights variations in service intensity...*")
        provider_heatmap = data_analyzer.get_provider_service_heatmap(filtered_df)
        if not provider_heatmap.empty:
            fig_hm = px.imshow(provider_heatmap, aspect="auto", title="Service Intensity by Provider and Age Group", height=600)
            fig_hm.update_layout(xaxis_title='Age Group', yaxis_title='Provider')
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("Not enough data to generate heatmap with current filters.")
        
        # AI-powered insights
        st.header("AI-Generated Insights Report")
        st.markdown("*This AI-generated report analyzes complex patterns in the data...*")
        report_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "LATEST_REPORT.md")
        report_exists = os.path.exists(report_path)
        generate_button_text = "Generate New Insights Report" if report_exists else "Generate Insights Report"

        # --- State for Toggling Report Level ---
        if 'next_report_level' not in st.session_state:
            st.session_state.next_report_level = 'detailed' # Start with detailed

        # Determine the text for the button based on the NEXT level
        if report_exists:
             generate_button_text = f"Generate {st.session_state.next_report_level.capitalize()} Report"
        else:
             generate_button_text = f"Generate Initial {st.session_state.next_report_level.capitalize()} Report"
        # ----------------------------------------

        # Row for Info message and Generate button
        col1, col2 = st.columns([3, 1]) # Adjust ratio if needed (3 parts for info, 1 for button)

        with col1:
            if report_exists:
                last_modified = datetime.fromtimestamp(os.path.getmtime(report_path))
                last_modified_str = last_modified.strftime("%Y-%m-%d %H:%M:%S")
                st.info(f"Last report generated on: {last_modified_str}", icon="ℹ️")
            else:
                st.empty() # Keep column structure consistent

        with col2:
            # Place button in the second column
            generate_clicked = st.button(generate_button_text, key='btn_generate_report', use_container_width=True)

        # Logic to generate and display the new report if button clicked
        if generate_clicked:
            with st.spinner("Analyzing data and generating insights..."):
                # --- Determine level to generate and call generator ---
                level_to_generate = st.session_state.next_report_level
                insights_generator = DentalInsightsGenerator(dental_df, provider_summary_df, age_group_summary_df, delivery_system_summary_df)
                insights = insights_generator.generate_insights(level=level_to_generate)
                # -----------------------------------------------------

                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                report_title = f"# Dental Analytics Insights Report\n\n*Generated on: {current_time}*\n\n"
                # --- Add level indicator to the report --- 
                level_indicator = f"**Report Level:** {level_to_generate.capitalize()}\n\n"
                full_report = report_title + level_indicator + insights
                # ------------------------------------------
                
                with open(report_path, 'w') as f:
                    f.write(full_report)
                st.success(f"Report saved to {report_path}")
                st.markdown("---")
                st.markdown(full_report)

                # --- Toggle the state for the NEXT click ---
                if st.session_state.next_report_level == 'detailed':
                    st.session_state.next_report_level = 'summary'
                else:
                    st.session_state.next_report_level = 'detailed'
                st.rerun() # Rerun to update button text immediately
                # ---------------------------------------------

        # Display the existing/latest report content if the button wasn't just clicked
        elif report_exists:
             try:
                 st.markdown("---") # Separator before showing existing report
                 with open(report_path, 'r') as f:
                     report_content = f.read()
                 st.markdown(report_content) # Display existing report content below the button row
             except FileNotFoundError:
                 st.warning("Could not read the existing report file.")
    else:
        # Message if Dashboard selected but data failed to load
        st.header("Data Loading Failed")
        st.info("Cannot display Dashboard content because the data could not be loaded from the database. Please check the connection details and ensure the ETL process has run successfully.")

elif selected_view == "SQL Documentation":
    st.header("SQL Transformation Documentation")
    st.markdown("""This section provides documentation for the SQL transformation scripts... Select a script to view its SQL code alongside structured documentation...""")
    
    # Get SQL directory path
    sql_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql")
    
    # Create SQL documentation manager and display documentation
    try:
        doc_manager = SqlDocumentationManager(sql_dir)
        doc_manager.display_documentation()
    except Exception as doc_error:
        st.error(f"Error displaying SQL documentation: {doc_error}")

# Footer or other common elements can go here, outside the conditional blocks
# st.markdown("--- ")
# st.text("Dental Analytics Solution - Footer")
