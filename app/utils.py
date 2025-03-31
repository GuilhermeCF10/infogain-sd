import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union

class DentalDataAnalyzer:
    """Class for analyzing dental utilization data.
    
    This class provides methods for filtering, analyzing, and visualizing
    dental care utilization data across different dimensions such as
    delivery systems, age groups, and provider types.
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None):
        """Initialize the analyzer with optional data.
        
        Args:
            data: Optional DataFrame containing dental utilization data
        """
        self.data = data
        self.filtered_data = data.copy() if data is not None else None
    
    def set_data(self, data: pd.DataFrame) -> None:
        """Set or update the data used for analysis.
        
        Args:
            data: DataFrame containing dental utilization data
        """
        self.data = data
        self.filtered_data = data.copy()
    
    def filter_data(self, delivery_system: str = 'All', 
                   age_group: str = 'All', 
                   provider_type: str = 'All',
                   use_original: bool = True) -> pd.DataFrame:
        """Filter the dental dataframe based on selected filters.
        
        Args:
            delivery_system: Delivery system to filter by, or 'All'
            age_group: Age group to filter by, or 'All'
            provider_type: Provider type to filter by, or 'All'
            use_original: If True, filter the original data; if False, filter the current filtered data
            
        Returns:
            Filtered DataFrame
        """
        if self.data is None:
            return pd.DataFrame()
        
        # Choose which data to filter
        base_df = self.data if use_original else self.filtered_data
        filtered_df = base_df.copy()
        
        if delivery_system != 'All':
            filtered_df = filtered_df[filtered_df['delivery_system'] == delivery_system]
        
        if age_group != 'All':
            filtered_df = filtered_df[filtered_df['age_group'] == age_group]
        
        if provider_type != 'All':
            filtered_df = filtered_df[filtered_df['provider_type'] == provider_type]
        
        # Store the filtered result
        self.filtered_data = filtered_df
        return filtered_df
    
    def get_service_counts(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Calculate service counts by type for the filtered data.
        
        Args:
            df: Optional DataFrame to analyze, or use filtered_data if None
            
        Returns:
            DataFrame with service types and counts
        """
        df = df if df is not None else self.filtered_data
        if df is None:
            return pd.DataFrame()
            
        service_types = []
        counts = []
        
        # Convert string columns to numeric before operations
        total_prev = pd.to_numeric(df['prev_svc_cnt'], errors='coerce').sum()
        total_txmt = pd.to_numeric(df['txmt_svc_cnt'], errors='coerce').sum()
        total_exam = pd.to_numeric(df['exam_svc_cnt'], errors='coerce').sum()
        total_adv = pd.to_numeric(df['adv_svc_cnt'], errors='coerce').sum() - (total_prev + total_txmt + total_exam)  # Remove double-counting
        
        service_types.extend(['Preventive', 'Treatment', 'Examination', 'Other'])
        counts.extend([total_prev, total_txmt, total_exam, total_adv])
        
        return pd.DataFrame({
            'Service Type': service_types,
            'Count': counts
        })
    
    def get_service_ratios(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Calculate service ratios for the filtered data.
        
        Args:
            df: Optional DataFrame to analyze, or use filtered_data if None
            
        Returns:
            DataFrame with service types, counts, and percentages
        """
        df = df if df is not None else self.filtered_data
        if df is None:
            return pd.DataFrame()
            
        counts_df = self.get_service_counts(df)
        total = pd.to_numeric(counts_df['Count'], errors='coerce').sum()
        
        if total > 0:
            counts_df['Percentage'] = (counts_df['Count'] / total) * 100
        else:
            counts_df['Percentage'] = 0
        
        return counts_df
    
    def get_age_group_patients(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Get patient counts by age group.
        
        Args:
            df: Optional DataFrame to analyze, or use filtered_data if None
            
        Returns:
            DataFrame with age groups and patient counts
        """
        df = df if df is not None else self.filtered_data
        if df is None or df.empty:
            return pd.DataFrame()
            
        age_groups = []
        patients = []
        
        for age in df['age_group'].unique():
            age_df = df[df['age_group'] == age]
            total_patients = pd.to_numeric(age_df['adv_user_cnt'], errors='coerce').sum()
            
            age_groups.append(age)
            patients.append(total_patients)
        
        return pd.DataFrame({
            'Age Group': age_groups,
            'Patients': patients
        })
    
    def get_age_group_services(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Get average services per patient by age group.
        
        Args:
            df: Optional DataFrame to analyze, or use filtered_data if None
            
        Returns:
            DataFrame with age groups and services per patient
        """
        df = df if df is not None else self.filtered_data
        if df is None or df.empty:
            return pd.DataFrame()
            
        age_groups = []
        services_per_patient = []
        
        for age in df['age_group'].unique():
            age_df = df[df['age_group'] == age]
            total_patients = pd.to_numeric(age_df['adv_user_cnt'], errors='coerce').sum()
            total_services = pd.to_numeric(age_df['total_services'], errors='coerce').sum()
            
            avg = total_services / total_patients if total_patients > 0 else 0
            
            age_groups.append(age)
            services_per_patient.append(avg)
        
        return pd.DataFrame({
            'Age Group': age_groups,
            'Services per Patient': services_per_patient
        })
    
    def get_delivery_system_coverage(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Calculate coverage percentages by delivery system.
        
        Args:
            df: Optional DataFrame to analyze, or use filtered_data if None
            
        Returns:
            DataFrame with delivery systems and coverage percentages
        """
        df = df if df is not None else self.filtered_data
        if df is None or df.empty:
            return pd.DataFrame()
            
        systems = []
        prev_coverage = []
        exam_coverage = []
        txmt_coverage = []
        
        for system in df['delivery_system'].unique():
            system_df = df[df['delivery_system'] == system]
            
            # Calculate average coverage percentages
            prev_cov = pd.to_numeric(system_df['preventive_coverage_pct'], errors='coerce').mean()
            exam_cov = pd.to_numeric(system_df['exam_coverage_pct'], errors='coerce').mean()
            txmt_cov = pd.to_numeric(system_df['treatment_coverage_pct'], errors='coerce').mean()
            
            systems.append(system)
            prev_coverage.append(prev_cov)
            exam_coverage.append(exam_cov)
            txmt_coverage.append(txmt_cov)
        
        return pd.DataFrame({
            'Delivery System': systems,
            'Preventive Coverage (%)': prev_coverage,
            'Exam Coverage (%)': exam_coverage,
            'Treatment Coverage (%)': txmt_coverage
        })
    
    def get_delivery_system_efficiency(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Calculate efficiency metrics by delivery system.
        
        Args:
            df: Optional DataFrame to analyze, or use filtered_data if None
            
        Returns:
            DataFrame with delivery systems and efficiency metrics
        """
        df = df if df is not None else self.filtered_data
        if df is None or df.empty:
            return pd.DataFrame()
            
        systems = []
        services_per_patient = []
        preventive_ratios = []
        total_patients = []
        
        for system in df['delivery_system'].unique():
            system_df = df[df['delivery_system'] == system]
            
            total_system_patients = pd.to_numeric(system_df['adv_user_cnt'], errors='coerce').sum()
            avg_services = pd.to_numeric(system_df['services_per_user'], errors='coerce').mean()
            avg_prev_ratio = pd.to_numeric(system_df['preventive_ratio'], errors='coerce').mean()
            
            systems.append(system)
            services_per_patient.append(avg_services)
            preventive_ratios.append(avg_prev_ratio)
            total_patients.append(total_system_patients)
        
        return pd.DataFrame({
            'Delivery System': systems,
            'Services per Patient': services_per_patient,
            'Preventive Ratio': preventive_ratios,
            'Total Patients': total_patients
        })
    
    def get_top_providers_by_volume(self, provider_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """Get top providers by patient volume.
        
        Args:
            provider_df: DataFrame with provider summary data
            top_n: Number of top providers to return
            
        Returns:
            DataFrame with top providers by volume
        """
        if provider_df is None or provider_df.empty:
            return pd.DataFrame()
            
        return provider_df.sort_values(by='total_users', ascending=False).head(top_n)
    
    def get_top_providers_by_efficiency(self, provider_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """Get top providers by efficiency score.
        
        Args:
            provider_df: DataFrame with provider summary data
            top_n: Number of top providers to return
            
        Returns:
            DataFrame with top providers by efficiency
        """
        if provider_df is None or provider_df.empty:
            return pd.DataFrame()
            
        return provider_df.sort_values(by='provider_efficiency_score', ascending=False).head(top_n)
    
    def get_provider_service_heatmap(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Create a provider service intensity heatmap data.
        
        Args:
            df: Optional DataFrame to analyze, or use filtered_data if None
            
        Returns:
            Pivot table for heatmap visualization
        """
        df = df if df is not None else self.filtered_data
        if df is None or df.empty:
            return pd.DataFrame()
            
        # Limit to top providers for readability
        # Convert adv_user_cnt to numeric before aggregation and using nlargest
        grouped = df.groupby('provider_legal_name')
        summed = grouped.apply(lambda x: pd.to_numeric(x['adv_user_cnt'], errors='coerce').sum())
        top_providers = summed.nlargest(15).index.tolist()
        
        if len(top_providers) < 3 or len(df['age_group'].unique()) < 2:
            return pd.DataFrame()  # Not enough data for meaningful heatmap
        
        # Filter to top providers only
        provider_df = df[df['provider_legal_name'].isin(top_providers)]
        
        # Convert services_per_user to numeric before pivot_table
        provider_df['services_per_user_numeric'] = pd.to_numeric(provider_df['services_per_user'], errors='coerce')
        
        # Create pivot table for heatmap
        heatmap_data = provider_df.pivot_table(
            index='provider_legal_name',
            columns='age_group',
            values='services_per_user_numeric',  # Use the numeric version
            aggfunc='mean',
            fill_value=0
        )
        
        return heatmap_data

