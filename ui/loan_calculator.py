"""
RISE Loan Calculator UI
Streamlit interface for loan and credit planning
"""

import streamlit as st
import sys
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.loan_credit_tools import LoanCreditTools

@st.cache_resource
def get_loan_tools():
    return LoanCreditTools()


def render_loan_calculator():
    """Render the loan and credit planning UI (embeddable in main app)."""
    loan_tools = get_loan_tools()
    st.title("💰 RISE Loan and Credit Planning")
    st.markdown("**Comprehensive loan planning with financing needs assessment and repayment scheduling**")
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Financing Needs",
        "🏦 Loan Products",
        "📅 Repayment Schedule",
        "📋 Document Checklist"
    ])
    # Tab 1: Financing Needs Assessment
    with tab1:
        st.header("Financing Needs Assessment")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Farmer Profile")
            farmer_name = st.text_input("Name", value="Ravi Kumar")
            farmer_age = st.number_input("Age", min_value=21, max_value=65, value=35)
            annual_farm_income = st.number_input("Annual Farm Income (₹)", min_value=0, value=250000, step=10000)
            other_income = st.number_input("Other Income (₹)", min_value=0, value=50000, step=5000)
            annual_expenses = st.number_input("Annual Expenses (₹)", min_value=0, value=180000, step=10000)
            credit_score = st.number_input("Credit Score", min_value=300, max_value=900, value=680)
            land_ownership = st.checkbox("Land Ownership", value=True)
        with col2:
            st.subheader("Farm Details")
            farm_size = st.number_input("Farm Size (acres)", min_value=0.5, value=5.0, step=0.5)
            soil_type = st.selectbox("Soil Type",
                                     ["loamy", "clay", "sandy", "black", "red", "alluvial", "laterite"])
            st.subheader("Loan Purpose")
            purpose = st.selectbox("Purpose", [
                "crop_cultivation",
                "equipment_purchase",
                "land_improvement",
                "irrigation_setup",
                "livestock",
                "storage_facility",
                "working_capital"
            ])
        if st.button("Assess Financing Needs", type="primary"):
            with st.spinner("Assessing financing needs..."):
                farmer_profile = {
                    'name': farmer_name,
                    'age': farmer_age,
                    'annual_farm_income': annual_farm_income,
                    'other_income': other_income,
                    'annual_expenses': annual_expenses,
                    'credit_score': credit_score,
                    'land_ownership': land_ownership
                }
                farm_details = {'farm_size_acres': farm_size, 'soil_type': soil_type}
                result = loan_tools.assess_financing_needs(
                    farmer_profile=farmer_profile,
                    farm_details=farm_details,
                    purpose=purpose
                )
                if result['success']:
                    if 'loan_ai_summary' in st.session_state:
                        del st.session_state['loan_ai_summary']  # clear so new assessment gets fresh summary
                    st.success("✅ Financing needs assessed successfully!")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Required Amount", f"₹{result['required_amount']:,.0f}")
                    with col2:
                        st.metric("Monthly Surplus", f"₹{result['repayment_capacity']['monthly_surplus']:,.0f}")
                    with col3:
                        st.metric("Repayment Capacity", result['repayment_capacity']['capacity_level'].upper())
                    st.subheader("Eligibility Status")
                    if result['eligibility']['eligible']:
                        st.success("✅ ELIGIBLE for loan")
                    else:
                        st.error("❌ NOT ELIGIBLE - See factors below")
                    for factor in result['eligibility']['eligibility_factors']:
                        status = factor['status']
                        if status == 'eligible':
                            st.success(f"✅ {factor['factor']}: {factor['detail']}")
                        elif status == 'warning':
                            st.warning(f"⚠️ {factor['factor']}: {factor['detail']}")
                        else:
                            st.error(f"❌ {factor['factor']}: {factor['detail']}")
                    st.subheader("Recommendation")
                    rec = result['recommendation']
                    st.info(f"**{rec['message']}**")
                    if rec['recommendation_type'] == 'recommended':
                        st.write(f"**Loan Type:** {rec['loan_type']}")
                        st.write(f"**Recommended Tenure:** {rec['recommended_tenure_months']} months")
                        st.write(f"**Estimated EMI:** ₹{rec['estimated_emi']:,.2f}")
                        st.write("**Next Steps:**")
                        for step in rec['next_steps']:
                            st.write(f"- {step}")
                    else:
                        st.write("**Alternatives:**")
                        for alt in rec['alternatives']:
                            st.write(f"- {alt}")
                    # AI summary and tips (store in session state so it persists after rerun)
                    with st.expander("🤖 AI Summary & Tips"):
                        if st.button("Get AI summary", key="loan_ai_btn"):
                            with st.spinner("Generating AI summary..."):
                                from tools.ai_insights import get_ai_insight
                                el = result.get('eligibility', {})
                                cap = result.get('repayment_capacity', {})
                                prompt = f"""You are a loan advisor for Indian farmers. In 2-3 short paragraphs, explain in simple language:

Farmer: {farmer_name}, age {farmer_age}. Income ₹{annual_farm_income}, expenses ₹{annual_expenses}. Credit score {credit_score}. Loan purpose: {purpose}. Required amount: ₹{result.get('required_amount', 0):,.0f}. Eligible: {el.get('eligible', False)}. Repayment capacity: {cap.get('capacity_level', '')}. Recommendation: {rec.get('message', '')}.

Provide: (1) Plain-language summary of what this means. (2) Concrete next steps. (3) One or two tips to improve eligibility or get better terms if relevant. Be supportive and clear."""
                                ai = get_ai_insight(prompt)
                            st.session_state['loan_ai_summary'] = ai
                        if 'loan_ai_summary' in st.session_state:
                            ai = st.session_state['loan_ai_summary']
                            if ai.get('success'):
                                st.markdown(ai.get('text', ''))
                            else:
                                st.error(ai.get('error', 'Failed to generate summary'))
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")

    # Tab 2: Loan Product Recommendations
    with tab2:
        st.header("Loan Product Recommendations")
        col1, col2 = st.columns(2)
        with col1:
            req_amount = st.number_input("Required Loan Amount (₹)", min_value=10000, value=200000, step=10000)
            loan_purpose = st.selectbox("Loan Purpose", [
                "crop_cultivation",
                "equipment_purchase",
                "land_improvement",
                "irrigation_setup",
                "working_capital",
                "general"
            ], key="loan_purpose_tab2")
        with col2:
            state = st.text_input("State", value="Punjab")
            repayment_period = st.number_input("Desired Repayment Period (months)",
                                               min_value=6, max_value=120, value=60, step=6)
        if st.button("Find Loan Products", type="primary"):
            with st.spinner("Finding suitable loan products..."):
                location = {'state': state}
                farmer_profile = {'credit_score': 680}
                result = loan_tools.recommend_loan_products(
                    required_amount=req_amount,
                    purpose=loan_purpose,
                    farmer_profile=farmer_profile,
                    location=location,
                    repayment_period_months=repayment_period
                )
                if result['success']:
                    st.success(f"✅ Found {result['total_products_found']} loan products")
                    for idx, product in enumerate(result['recommendations'], 1):
                        with st.expander(f"#{idx} {product['lender_name']} - {product['product_name']} (Score: {product['suitability_score']:.0f}/100)"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Interest Rate", f"{product['interest_rate']}% p.a.")
                                st.metric("Processing Fee", f"{product['processing_fee_percent']}%")
                            with col2:
                                st.metric("Monthly EMI", f"₹{product['calculated_emi']:,.0f}")
                                st.metric("Total Interest", f"₹{product['total_interest']:,.0f}")
                            with col3:
                                st.metric("Total Repayment", f"₹{product['total_repayment']:,.0f}")
                                st.metric("Lender Type", product['lender_type'].upper())
                            st.write("**Features:**")
                            for feature in product['features']:
                                st.write(f"- {feature}")
                            st.write(f"**Eligibility:** {product['eligibility']}")
                            st.write(f"**Loan Range:** ₹{product['min_amount']:,} - ₹{product['max_amount']:,}")
                    if len(result['recommendations']) > 1:
                        st.subheader("Interest Rate Comparison")
                        df = pd.DataFrame([
                            {
                                'Lender': p['lender_name'],
                                'Interest Rate': p['interest_rate'],
                                'EMI': p['calculated_emi'],
                                'Total Interest': p['total_interest']
                            }
                            for p in result['recommendations']
                        ])
                        fig = px.bar(df, x='Lender', y='Interest Rate',
                                     title='Interest Rate Comparison',
                                     color='Interest Rate',
                                     color_continuous_scale='RdYlGn_r')
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")

    # Tab 3: Repayment Schedule
    with tab3:
        st.header("Crop-Cycle Aligned Repayment Schedule")
        col1, col2 = st.columns(2)
        with col1:
            loan_amt = st.number_input("Loan Amount (₹)", min_value=10000, value=200000, step=10000, key="loan_amt_tab3")
            interest = st.number_input("Interest Rate (% p.a.)", min_value=0.0, max_value=30.0, value=9.5, step=0.5)
            tenure = st.number_input("Tenure (months)", min_value=6, max_value=120, value=60, step=6, key="tenure_tab3")
        with col2:
            st.subheader("Crop Cycle (Optional)")
            has_crop_cycle = st.checkbox("Align with crop cycle")
            if has_crop_cycle:
                harvest_months_input = st.text_input("Harvest Months (comma-separated)", value="6,12,18,24")
                harvest_income = st.number_input("Harvest Income (₹)", min_value=0, value=100000, step=10000)
                try:
                    harvest_months = [int(m.strip()) for m in harvest_months_input.split(',')]
                    crop_cycle = {'harvest_months': harvest_months, 'harvest_income': harvest_income}
                except Exception:
                    crop_cycle = None
                    st.warning("Invalid harvest months format")
            else:
                crop_cycle = None
        if st.button("Generate Repayment Schedule", type="primary"):
            with st.spinner("Generating repayment schedule..."):
                result = loan_tools.generate_repayment_schedule(
                    loan_amount=loan_amt,
                    interest_rate=interest,
                    tenure_months=tenure,
                    crop_cycle=crop_cycle
                )
                if result['success']:
                    st.success("✅ Repayment schedule generated!")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Monthly EMI", f"₹{result['monthly_emi']:,.0f}")
                    with col2:
                        st.metric("Total Interest", f"₹{result['total_interest']:,.0f}")
                    with col3:
                        st.metric("Total Repayment", f"₹{result['total_repayment']:,.0f}")
                    with col4:
                        st.metric("Challenging Months", result['challenging_months'])
                    st.subheader("Detailed Repayment Schedule")
                    df = pd.DataFrame(result['schedule'])

                    def highlight_feasibility(row):
                        if row['payment_feasibility'] == 'low':
                            return ['background-color: #ffcccc'] * len(row)
                        if row['payment_feasibility'] == 'medium':
                            return ['background-color: #ffffcc'] * len(row)
                        return ['background-color: #ccffcc'] * len(row)

                    styled_df = df.style.apply(highlight_feasibility, axis=1)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    st.subheader("Payment Breakdown Over Time")
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=df['month'], y=df['principal'], name='Principal', marker_color='lightblue'))
                    fig.add_trace(go.Bar(x=df['month'], y=df['interest'], name='Interest', marker_color='lightcoral'))
                    if crop_cycle:
                        harvest_df = df[df['is_harvest_month']]
                        fig.add_trace(go.Scatter(
                            x=harvest_df['month'],
                            y=harvest_df['expected_income'],
                            name='Harvest Income',
                            mode='markers',
                            marker=dict(size=12, color='green', symbol='star')
                        ))
                    fig.update_layout(
                        barmode='stack',
                        title='EMI Breakdown by Month',
                        xaxis_title='Month',
                        yaxis_title='Amount (₹)',
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.subheader("Repayment Recommendations")
                    for rec in result['recommendations']:
                        st.info(f"💡 {rec}")
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")

    # Tab 4: Document Checklist
    with tab4:
        st.header("Financial Document Compilation Helper")
        col1, col2 = st.columns(2)
        with col1:
            doc_loan_purpose = st.selectbox("Loan Purpose", [
                "crop_cultivation",
                "equipment_purchase",
                "land_improvement",
                "irrigation_setup",
                "working_capital"
            ], key="doc_purpose")
            doc_loan_amount = st.number_input("Loan Amount (₹)", min_value=10000, value=200000, step=10000, key="doc_amount")
        with col2:
            doc_farmer_name = st.text_input("Farmer Name", value="Ravi Kumar", key="doc_name")
            doc_farm_size = st.number_input("Farm Size (acres)", min_value=0.5, value=5.0, step=0.5, key="doc_farm_size")
        if st.button("Generate Document Checklist", type="primary"):
            with st.spinner("Generating document checklist..."):
                farmer_profile = {'name': doc_farmer_name, 'annual_farm_income': 250000}
                farm_details = {'farm_size_acres': doc_farm_size}
                result = loan_tools.compile_financial_documents(
                    farmer_profile=farmer_profile,
                    farm_details=farm_details,
                    loan_purpose=doc_loan_purpose,
                    loan_amount=doc_loan_amount
                )
                if result['success']:
                    st.success("✅ Document checklist generated!")
                    st.info(f"⏱️ **Estimated Processing Time:** {result['estimated_processing_time']}")
                    st.subheader("Required Documents Checklist")
                    for doc in result['required_documents']:
                        with st.expander(f"{'🔴' if doc['mandatory'] else '🟡'} {doc['document']} {'(Mandatory)' if doc['mandatory'] else '(Optional)'}"):
                            st.write(f"**Format:** {doc['format']}")
                            st.write("**Examples:**")
                            for example in doc['examples']:
                                st.write(f"- {example}")
                            st.checkbox(f"I have {doc['document']}", key=f"check_{doc['document']}")
                    st.subheader("Financial Summary")
                    summary = result['financial_summary']
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Applicant Details:**")
                        st.write(f"- Name: {summary['applicant_details']['name']}")
                        st.write(f"- Age: {summary['applicant_details']['age']}")
                        st.write(f"- Experience: {summary['applicant_details']['farming_experience']}")
                        st.write("**Farm Details:**")
                        st.write(f"- Total Land: {summary['farm_details']['total_land']} acres")
                        st.write(f"- Soil Type: {summary['farm_details']['soil_type']}")
                    with col2:
                        st.write("**Financial Position:**")
                        st.write(f"- Annual Income: ₹{summary['financial_position']['annual_income']:,}")
                        st.write(f"- Assets Value: ₹{summary['financial_position']['assets_value']:,}")
                        st.write(f"- Net Worth: ₹{summary['financial_position']['net_worth']:,}")
                        st.write("**Loan Request:**")
                        st.write(f"- Amount: ₹{summary['loan_request']['amount']:,}")
                        st.write(f"- Purpose: {summary['loan_request']['purpose']}")
                    st.subheader("Application Process Guide")
                    for step in result['application_guidance']:
                        st.write(step)
                    st.download_button(
                        label="📥 Download Checklist",
                        data=str(result),
                        file_name=f"loan_checklist_{result['compilation_id']}.txt",
                        mime="text/plain"
                    )
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
    st.markdown("---")
    st.markdown("**RISE - Rural Innovation and Sustainable Ecosystem** | Loan and Credit Planning System")


if __name__ == "__main__":
    st.set_page_config(page_title="RISE Loan Calculator", page_icon="💰", layout="wide")
    render_loan_calculator()
