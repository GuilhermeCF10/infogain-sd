import pandas as pd
import numpy as np
import os
import json
from typing import Dict, List, Any, Tuple, Optional
from openai import OpenAI


class DentalInsightsGenerator:
    """Class responsible for generating AI-powered insights from dental data.
    
    This class encapsulates functionality for analyzing dental utilization data,
    extracting meaningful insights, and generating reports using both rule-based
    analysis and AI through the OpenAI API.
    """
    
    def __init__(self, dental_df=None, provider_summary_df=None, 
                 age_group_summary_df=None, delivery_system_summary_df=None):
        """Initialize the insights generator with dental data.
        
        Args:
            dental_df: DataFrame containing dental utilization data
            provider_summary_df: DataFrame with provider summary metrics
            age_group_summary_df: DataFrame with age group metrics
            delivery_system_summary_df: DataFrame with delivery system metrics
        """
        self.dental_df = dental_df
        self.provider_summary_df = provider_summary_df
        self.age_group_summary_df = age_group_summary_df
        self.delivery_system_summary_df = delivery_system_summary_df
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.openai_client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    def set_data(self, dental_df=None, provider_summary_df=None, 
                age_group_summary_df=None, delivery_system_summary_df=None) -> None:
        """Update the data used for analysis.
        
        Args:
            dental_df: DataFrame containing dental utilization data
            provider_summary_df: DataFrame with provider summary metrics
            age_group_summary_df: DataFrame with age group metrics
            delivery_system_summary_df: DataFrame with delivery system metrics
        """
        if dental_df is not None:
            self.dental_df = dental_df
        if provider_summary_df is not None:
            self.provider_summary_df = provider_summary_df
        if age_group_summary_df is not None:
            self.age_group_summary_df = age_group_summary_df
        if delivery_system_summary_df is not None:
            self.delivery_system_summary_df = delivery_system_summary_df
            
    def prepare_data_summary(self) -> Dict[str, Any]:
        """Prepare a summary of the data for the OpenAI API
        
        Returns:
            Dictionary containing structured summary of dental data
        """
        # Validate data availability
        if (self.dental_df is None or self.provider_summary_df is None or
            self.age_group_summary_df is None or self.delivery_system_summary_df is None):
            raise ValueError("All dataframes must be provided before generating insights")
        
        # Ensure necessary columns exist and are numeric
        required_provider_cols = {
            'rendering_npi': 'object', 
            'total_users': 'numeric', 
            'total_services': 'numeric', 
            'provider_efficiency_score': 'numeric'
        }
        required_dental_cols = {
            'prev_svc_cnt': 'numeric',
            'total_services': 'numeric',
            'txmt_svc_cnt': 'numeric'
        }
        required_age_cols = {
            'age_group': 'object',
            'preventive_services_pct': 'numeric',
            'treatment_services_pct': 'numeric',
            'avg_services_per_user': 'numeric'
        }
        required_delivery_cols = {
            'delivery_system': 'object',
            'system_effectiveness_score': 'numeric',
            'preventive_services_pct': 'numeric',
            'total_users': 'numeric',
            'avg_services_per_user': 'numeric'
        }

        def _validate_and_convert(df, col_dict, df_name):
            for col, dtype in col_dict.items():
                if col not in df.columns:
                    raise KeyError(f"Column '{col}' not found in {df_name}. Available: {df.columns.tolist()}")
                if dtype == 'numeric':
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            return df

        try:
            self.provider_summary_df = _validate_and_convert(self.provider_summary_df, required_provider_cols, "provider_summary_df")
            self.dental_df = _validate_and_convert(self.dental_df, required_dental_cols, "dental_df")
            self.age_group_summary_df = _validate_and_convert(self.age_group_summary_df, required_age_cols, "age_group_summary_df")
            self.delivery_system_summary_df = _validate_and_convert(self.delivery_system_summary_df, required_delivery_cols, "delivery_system_summary_df")
        except KeyError as e:
             raise ValueError(f"Data validation failed: {e}")
        
        # Overall metrics
        total_providers = self.provider_summary_df['rendering_npi'].nunique()
        total_patients = self.provider_summary_df['total_users'].sum()
        # Use dental_df for total services as it might be more accurate
        total_services = self.dental_df['total_services'].sum() 
        avg_services = total_services / total_patients if total_patients > 0 else 0
    
        # Age group metrics
        age_group_data = self.age_group_summary_df.to_dict(orient='records')
        
        # Delivery system metrics
        delivery_system_data = self.delivery_system_summary_df.to_dict(orient='records')
        
        # Top providers by volume
        top_volume_providers = self.provider_summary_df.nlargest(5, 'total_users')[['rendering_npi', 'total_users']].to_dict(orient='records')
        
        # Top providers by efficiency
        top_efficient_providers = self.provider_summary_df.nlargest(5, 'provider_efficiency_score')[['rendering_npi', 'provider_efficiency_score']].to_dict(orient='records')
    
        # Preventive vs treatment ratios
        prev_svc_sum = self.dental_df['prev_svc_cnt'].sum()
        txmt_svc_sum = self.dental_df['txmt_svc_cnt'].sum()
            
        overall_prev_pct = (prev_svc_sum / total_services * 100) if total_services > 0 else 0
        overall_txmt_pct = (txmt_svc_sum / total_services * 100) if total_services > 0 else 0
                
        # Create the summary object
        data_summary = {
            "overall_metrics": {
                "total_providers": int(total_providers),
                "total_patients": float(total_patients),
                "total_services": float(total_services),
                "avg_services_per_patient": float(avg_services),
                "preventive_pct": float(overall_prev_pct),
                "treatment_pct": float(overall_txmt_pct),
            },
            "age_groups": age_group_data,
            "delivery_systems": delivery_system_data,
            "top_providers_by_volume": top_volume_providers,
            "top_providers_by_efficiency": top_efficient_providers
        }
        
        return data_summary

    def generate_insights(self, level: str = 'detailed') -> str:
        """
        Generate insights from the dental data in the specified format.

        Args:
            level (str): The level of detail ('detailed' or 'summary').
                         'detailed' provides structured lists.
                         'summary' provides a narrative text.
                         Defaults to 'detailed'.
        
        Returns:
            str: Markdown formatted insights string
        """
        # --- 1. Data Validation and Preparation ---
        try:
            data_summary = self.prepare_data_summary()
            # Ensure dataframes used later are also validated/converted numeric
            # (prepare_data_summary already modifies them in place)
            age_df = self.age_group_summary_df
            delivery_df = self.delivery_system_summary_df
            provider_df = self.provider_summary_df
        except (ValueError, KeyError) as e:
             return f"Error preparing data for insights: {e}"
             
        # --- 2. Extract Key Metrics from Prepared Summary ---
        om = data_summary['overall_metrics']
        total_providers = om['total_providers']
        total_patients = om['total_patients']
        total_services = om['total_services']
        avg_services = om['avg_services_per_patient']
        overall_prev_pct = om['preventive_pct']
        overall_txmt_pct = om['treatment_pct']
        
        # Age Group Data Extraction
        younger_data = next((item for item in data_summary['age_groups'] if item['age_group'] == 'AGE 0-20'), None)
        older_data = next((item for item in data_summary['age_groups'] if item['age_group'] == 'AGE 21+'), None)
        
        # Delivery System Data Extraction
        delivery_systems = data_summary['delivery_systems']
        most_effective_system = max(delivery_systems, key=lambda x: x.get('system_effectiveness_score', 0)) if delivery_systems else None
        highest_avg_svc_system = max(delivery_systems, key=lambda x: x.get('avg_services_per_user', 0)) if delivery_systems else None
        
        # Provider Data Extraction
        top_volume_providers_list = data_summary['top_providers_by_volume'][:3] # Take top 3
        top_efficiency_providers_list = data_summary['top_providers_by_efficiency'][:3]
        # Find lowest efficiency (requires sorting the original validated df)
        lowest_efficiency_providers_list = provider_df.nsmallest(3, 'provider_efficiency_score')[['rendering_npi', 'provider_efficiency_score']].to_dict(orient='records') if not provider_df.empty else []
        
        # --- 3. Format Output Based on Level ---
        
        # Common Titles
        report_title = "## 📊 Dental Care Utilization Analysis Report"
        report_subtitle = "*Analysis of Denti-Cal program data for calendar year 2018*\n"
        
        insights_content = []

        if level == 'detailed':
            insights_content.append(report_title)
            insights_content.append(report_subtitle)
            
            # Overall Metrics (Detailed)
            insights_content.append("### 📈 Summary Metrics")
            insights_content.append(f"- **Total Providers Analyzed**: {total_providers:,}")
            insights_content.append(f"- **Total Patients Served**: {total_patients:,.0f}")
            insights_content.append(f"- **Total Services Provided**: {total_services:,.0f}")
            insights_content.append(f"- **Average Services per Patient**: {avg_services:.2f}\n")

            # Age Group Analysis (Detailed)
            insights_content.append("### 👥 Age Group Analysis")
            if younger_data and older_data:
                insights_content.append(f"- Younger patients (0-20) receive **{younger_data['preventive_services_pct']:.1f}%** of preventive services, compared to **{older_data['preventive_services_pct']:.1f}%** for adults (21+). This suggests a stronger focus on preventive care for younger patients.")
                insights_content.append(f"- Younger patients require fewer treatment services (**{younger_data['treatment_services_pct']:.1f}%**) compared to adults (**{older_data['treatment_services_pct']:.1f}%**), potentially reflecting better preventive care effectiveness.")
                insights_content.append(f"- Younger patients receive significantly more services per patient (**{younger_data['avg_services_per_user']:.2f}**) compared to adults (**{older_data['avg_services_per_user']:.2f}**).")
            else:
                insights_content.append("- *Age group comparison data not fully available.*")
            insights_content.append("\n")

            # Delivery System Performance (Detailed)
            insights_content.append("### 🏥 Delivery System Performance")
            if most_effective_system:
                 insights_content.append(f"- **{most_effective_system['delivery_system']}** is the most effective delivery system with an efficiency score of **{most_effective_system['system_effectiveness_score']:.2f}**.")
            else:
                 insights_content.append("- *Could not determine the most effective delivery system.*")
            
            insights_content.append("- Preventive service percentages by delivery system:")
            if delivery_systems:
                for system in delivery_systems:
                    insights_content.append(f"  - **{system['delivery_system']}**: {system['preventive_services_pct']:.1f}% preventive services, serving {system['total_users']:,.0f} patients")
            else:
                insights_content.append("  - *Data not available.*")

            if highest_avg_svc_system:
                 insights_content.append(f"- **{highest_avg_svc_system['delivery_system']}** provides the highest average number of services per patient at **{highest_avg_svc_system['avg_services_per_user']:.2f}** services.")
            else:
                 insights_content.append("- *Could not determine the system with the highest average services.*")
            insights_content.append("\n")

            # Provider Performance (Detailed)
            insights_content.append("### 👨‍⚕️ Provider Performance")
            insights_content.append("- **Top providers by patient volume**:")
            if top_volume_providers_list:
                for provider in top_volume_providers_list:
                    insights_content.append(f"  - Provider NPI {provider['rendering_npi']} ({provider['total_users']:,.0f} patients)")
            else:
                insights_content.append("  - *Data not available.*")

            insights_content.append("- **Top providers by efficiency score**:")
            if top_efficiency_providers_list:
                for provider in top_efficiency_providers_list:
                     insights_content.append(f"  - Provider NPI {provider['rendering_npi']} (Score: {provider['provider_efficiency_score']:.2f})")
            else:
                insights_content.append("  - *Data not available.*")

            insights_content.append("- **Providers with lowest efficiency scores** (potential review needed):")
            if lowest_efficiency_providers_list:
                for provider in lowest_efficiency_providers_list:
                    insights_content.append(f"  - Provider NPI {provider['rendering_npi']} (Score: {provider['provider_efficiency_score']:.2f})")
            else:
                 insights_content.append("  - *Data not available.*")

        elif level == 'summary':
            narrative = [report_title, report_subtitle]
            
            # Introduction & Overall Metrics Paragraph
            narrative.append(f"This analysis reviews dental care utilization data from {total_providers:,} providers serving approximately {total_patients:,.0f} patients within the Denti-Cal program for 2018. A total of {total_services:,.0f} services were rendered, averaging {avg_services:.2f} services per patient. Overall, preventive services comprised {overall_prev_pct:.1f}% of the total, while treatment services accounted for {overall_txmt_pct:.1f}%, indicating a relatively balanced approach between prevention and treatment.")
            narrative.append("\n") # Paragraph break

            # Age Group Paragraph
            age_narrative = "Regarding age demographics, "
            if younger_data and older_data:
                age_narrative += f"a stronger focus on preventive care was observed for younger patients (0-20), who received {younger_data['preventive_services_pct']:.1f}% of such services compared to {older_data['preventive_services_pct']:.1f}% for adults (21+). Correspondingly, younger patients required fewer treatment services ({younger_data['treatment_services_pct']:.1f}% vs. {older_data['treatment_services_pct']:.1f}% for adults). Notably, the average number of services per patient was significantly higher for the younger group ({younger_data['avg_services_per_user']:.2f}) compared to adults ({older_data['avg_services_per_user']:.2f})."
            else:
                age_narrative += "a detailed comparison between age groups was not fully possible due to data limitations."
            narrative.append(age_narrative)
            narrative.append("\n")

            # Delivery System Paragraph
            delivery_narrative = "Analysis of delivery systems showed that "
            if most_effective_system:
                delivery_narrative += f"the {most_effective_system['delivery_system']} model was the most effective, achieving an efficiency score of {most_effective_system['system_effectiveness_score']:.2f}. "
            else:
                delivery_narrative += "determining the most effective system was not possible. "
            
            if delivery_systems:
                delivery_narrative += "Preventive service percentages were similar across systems ("
                sys_prev_details = []
                for system in delivery_systems:
                     sys_prev_details.append(f"{system['delivery_system']}: {system['preventive_services_pct']:.1f}% for {system['total_users']:,.0f} patients")
                delivery_narrative += "; ".join(sys_prev_details) + "). "
            
            if highest_avg_svc_system:
                 delivery_narrative += f"The {highest_avg_svc_system['delivery_system']} system provided the highest average number of services per patient ({highest_avg_svc_system['avg_services_per_user']:.2f})."
            else:
                 delivery_narrative += "The system providing the highest average services per patient could not be determined."
            narrative.append(delivery_narrative)
            narrative.append("\n")
            
            # Provider Paragraph
            provider_narrative = "At the provider level, "
            if top_volume_providers_list:
                provider_narrative += f"NPI {top_volume_providers_list[0]['rendering_npi']} served the highest volume of patients ({top_volume_providers_list[0]['total_users']:,.0f}). "
            else:
                provider_narrative += "top providers by volume could not be identified. "
                
            if top_efficiency_providers_list:
                provider_narrative += f"NPI {top_efficiency_providers_list[0]['rendering_npi']} achieved the highest efficiency score ({top_efficiency_providers_list[0]['provider_efficiency_score']:.2f}). "
            else:
                provider_narrative += "Top providers by efficiency could not be identified. "
                
            if lowest_efficiency_providers_list:
                provider_narrative += f"Conversely, providers such as NPI {lowest_efficiency_providers_list[0]['rendering_npi']} exhibited the lowest efficiency scores ({lowest_efficiency_providers_list[0]['provider_efficiency_score']:.2f}), suggesting areas for potential review."
            else:
                 provider_narrative += "Providers with the lowest efficiency could not be identified."
            narrative.append(provider_narrative)
            
            insights_content = narrative # Use the narrative list for summary
            
        else:
             # Handle invalid level specification
             return f"Error: Invalid report level specified ('{level}'). Use 'detailed' or 'summary'."

        # --- 4. Return Final String --- 
        return "\n".join(insights_content)

    def _create_prompt(self, data_summary: Dict[str, Any]) -> str:
        """Create a detailed prompt for the OpenAI API based on the data summary.
        
        Args:
            data_summary: Dictionary containing the structured data summary
            
        Returns:
            String prompt for the OpenAI API
        """
        # Convert the data summary dictionary to a JSON string for the prompt
        summary_json = json.dumps(data_summary, indent=2)
        
        prompt = f"""
Analyze the following Denti-Cal utilization data summary for 2018 and provide key insights and potential recommendations in markdown format. Focus on:
1.  Overall program performance (patient volume, service volume, efficiency).
2.  Significant differences between age groups (0-20 vs 21+).
3.  Performance variations between delivery systems (FFS, GMC, PHP).
4.  Highlighting top-performing and potentially underperforming providers.

Data Summary:
```json
{summary_json}
```

Insights and Recommendations:
"""
        return prompt

    def _call_openai_api(self, prompt: str) -> str:
        """Call the OpenAI API to get insights based on the prompt.
        
        Args:
            prompt: The prompt string for the API
            
        Returns:
            The response text from the OpenAI API, or an error message.
        """
        if not self.openai_client:
            return "*OpenAI API key not configured. AI insights unavailable.*"
            
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo", 
                messages=[
                    {"role": "system", "content": "You are an expert healthcare data analyst specializing in dental program evaluation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.5
            )
            # Accessing the response content correctly
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip()
            else:
                return "*AI response received, but content is empty.*"
        except Exception as e:
            return f"*Error calling OpenAI API: {e}*"

    # Method to generate AI insights, potentially called separately or integrated
    def generate_ai_insights(self) -> str:
        """Generate insights using OpenAI's API based on prepared data.
        
        Returns:
            str: Markdown formatted insights string from AI or error message.
        """
        try:
            data_summary = self.prepare_data_summary()
            prompt = self._create_prompt(data_summary)
            ai_response = self._call_openai_api(prompt)
            
            # Format the AI response slightly
            ai_section = ["\n### 🤖 AI Generated Summary", ai_response]
            return "\n".join(ai_section)
        except (ValueError, KeyError) as e:
             return f"*Error preparing data for AI insights: {e}*"
        except Exception as e:
            return f"*Unexpected error during AI insight generation: {e}*"
