"""
Job Market Dashboard - Streamlit App
Interactive dashboard for Queensland job market analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime


# Page config
st.set_page_config(
    page_title="Queensland Job Market Dashboard",
    page_icon="📊",
    layout="wide"
)


@st.cache_data
def load_data(file_path):
    """Load data with caching"""
    try:
        df = pd.read_excel(file_path)
        if 'created' in df.columns:
            df['created'] = pd.to_datetime(df['created'])
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


def calculate_metrics(df):
    """Calculate key metrics"""
    total_jobs = len(df)
    unique_companies = df['company'].nunique()

    # Jobs with salary
    if 'has_salary' in df.columns:
        jobs_with_salary = df['has_salary'].sum()
    else:
        jobs_with_salary = df['salary_min'].notna().sum()

    # Average salary
    if 'salary_avg' in df.columns:
        avg_salary = df['salary_avg'].mean()
    else:
        avg_salary = ((df['salary_min'] + df['salary_max']) / 2).mean()

    return total_jobs, unique_companies, jobs_with_salary, avg_salary


def main():
    st.title("📊 Queensland Job Market Dashboard")
    st.markdown("---")

    # Sidebar - File upload
    st.sidebar.header("📁 Data Source")

    upload_option = st.sidebar.radio(
        "Choose data source:",
        ["Upload File", "Use Sample Data"]
    )

    df = None

    if upload_option == "Upload File":
        uploaded_file = st.sidebar.file_uploader(
            "Upload Excel file",
            type=['xlsx', 'xls']
        )
        if uploaded_file:
            df = load_data(uploaded_file)
    else:
        sample_path = Path('cleaned_datasets/queensland_all_jobs.xlsx')
        if sample_path.exists():
            df = load_data(sample_path)
        else:
            st.warning("No sample data found. Please upload a file or run the pipeline first.")

    if df is None or df.empty:
        st.info("👆 Please upload a job dataset to begin analysis")
        return

    # Sidebar - Filters
    st.sidebar.header("🔍 Filters")

    # Category filter
    categories = ['All'] + sorted([str(x) for x in df['category'].unique() if pd.notna(x)])
    selected_category = st.sidebar.selectbox("Category", categories)

    # Location filter
    if 'city' in df.columns:
        cities = ['All'] + sorted([str(x) for x in df['city'].unique() if pd.notna(x)])
        selected_city = st.sidebar.selectbox("City", cities)
    else:
        selected_city = 'All'

    # Contract time filter  ✅ CHANGED
    contract_times = ['All'] + sorted(
        [str(x) for x in df['contract_time'].unique() if pd.notna(x)]
    )
    selected_contract_time = st.sidebar.selectbox("Contract Time", contract_times)

    # Apply filters
    df_filtered = df.copy()

    if selected_category != 'All':
        df_filtered = df_filtered[df_filtered['category'] == selected_category]

    if selected_city != 'All' and 'city' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['city'] == selected_city]

    if selected_contract_time != 'All':
        df_filtered = df_filtered[
            df_filtered['contract_time'] == selected_contract_time
        ]

    # Key Metrics
    st.header("📈 Key Metrics")
    total_jobs, unique_companies, jobs_with_salary, avg_salary = calculate_metrics(df_filtered)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Jobs", f"{total_jobs:,}")
    with col2:
        st.metric("Unique Companies", f"{unique_companies:,}")
    with col3:
        st.metric("Jobs with Salary Info", f"{jobs_with_salary:,}")
    with col4:
        st.metric("Avg. Salary", f"${avg_salary:,.0f}" if pd.notna(avg_salary) else "N/A")

    st.markdown("---")

    # Charts Row 1
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Total Jobs")
        st.markdown(
        f"""
        <div style="
            font-size:120px;
            font-weight:800;
            text-align:center;
            padding-top:60px;
        ">
            {len(df_filtered):,}
        </div>
        """,
        unsafe_allow_html=True
    )


    with col2:
        st.subheader("🏢 Top 10 Hiring Companies")
        company_counts = df_filtered['company'].value_counts().head(10)
        fig2 = px.bar(
            x=company_counts.values,
            y=company_counts.index,
            orientation='h',
            labels={'x': 'Number of Jobs', 'y': 'Company'}
        )
        fig2.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig2, use_container_width=True)

    # Charts Row 2
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Jobs by Location")
        location_counts = df_filtered['location'].value_counts().head(10)
        fig3 = px.pie(
            values=location_counts.values,
            names=location_counts.index
        )
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)

    # Pie chart — Contract Time ✅ CHANGED
    with col2:
        st.subheader("📝 Contract Time")
        contract_time_counts = df_filtered['contract_time'].value_counts()
        fig4 = px.pie(
            values=contract_time_counts.values,
            names=contract_time_counts.index
        )
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

    # Salary Analysis
    st.markdown("---")
    st.header("💰 Salary Analysis")

    df_with_salary = df_filtered[
        df_filtered['salary_min'].notna() | df_filtered['salary_max'].notna()
    ].copy()

    if not df_with_salary.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Salary Distribution")
            salary_data = (
                df_with_salary['salary_avg']
                if 'salary_avg' in df_with_salary.columns
                else (df_with_salary['salary_min'] + df_with_salary['salary_max']) / 2
            ).dropna()

            fig5 = px.histogram(
                salary_data,
                nbins=30,
                labels={'value': 'Salary (AUD)', 'count': 'Number of Jobs'}
            )
            fig5.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig5, use_container_width=True)

        with col2:
            st.subheader("Average Salary by Category")
            if 'salary_avg' in df_with_salary.columns:
                salary_by_cat = (
                    df_with_salary.groupby('category')['salary_avg']
                    .mean()
                    .sort_values(ascending=False)
                    .head(10)
                )
            else:
                df_with_salary['temp_avg'] = (
                    df_with_salary['salary_min'] + df_with_salary['salary_max']
                ) / 2
                salary_by_cat = (
                    df_with_salary.groupby('category')['temp_avg']
                    .mean()
                    .sort_values(ascending=False)
                    .head(10)
                )

            fig6 = px.bar(
                x=salary_by_cat.values,
                y=salary_by_cat.index,
                orientation='h',
                labels={'x': 'Average Salary (AUD)', 'y': 'Category'}
            )
            fig6.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig6, use_container_width=True)

    # Time Series
    if 'created' in df_filtered.columns:
        st.markdown("---")
        st.header("📅 Jobs Posted Over Time")

        df_time = df_filtered.copy()
        df_time['date'] = pd.to_datetime(df_time['created'])
        jobs_by_date = df_time.groupby(df_time['date'].dt.date).size().reset_index()
        jobs_by_date.columns = ['Date', 'Jobs Posted']

        fig7 = px.line(
            jobs_by_date,
            x='Date',
            y='Jobs Posted',
            markers=True
        )
        fig7.update_layout(height=400)
        st.plotly_chart(fig7, use_container_width=True)

    # Raw Data Table
    st.markdown("---")
    st.header("📋 Raw Data")

    show_columns = st.multiselect(
        "Select columns to display",
        df_filtered.columns.tolist(),
        default=['title', 'company', 'location', 'category', 'salary_min', 'salary_max']
    )

    if show_columns:
        st.dataframe(df_filtered[show_columns], use_container_width=True)

    # Download button
    st.download_button(
        label="📥 Download Filtered Data",
        data=df_filtered.to_csv(index=False).encode('utf-8'),
        file_name=f"filtered_jobs_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


if __name__ == "__main__":
    main()



