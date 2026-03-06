"""
RISE Analytics Dashboard
Streamlit-based admin dashboard for monitoring platform metrics
"""

import streamlit as st
import boto3
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any
import json


class AnalyticsDashboard:
    """Admin analytics dashboard for RISE platform"""
    
    def __init__(self):
        """Initialize dashboard"""
        self.cloudwatch = boto3.client('cloudwatch')
        self.lambda_client = boto3.client('lambda')
    
    def render(self):
        """Render the analytics dashboard"""
        st.set_page_config(
            page_title="RISE Analytics Dashboard",
            page_icon="📊",
            layout="wide"
        )
        
        st.title("📊 RISE Analytics Dashboard")
        st.markdown("**Admin Dashboard for Platform Metrics and KPIs**")
        
        # Sidebar for date range selection
        with st.sidebar:
            st.header("⚙️ Settings")
            
            date_range = st.selectbox(
                "Time Period",
                ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Custom Range"]
            )
            
            if date_range == "Custom Range":
                start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
                end_date = st.date_input("End Date", datetime.now())
                start_time = datetime.combine(start_date, datetime.min.time())
                end_time = datetime.combine(end_date, datetime.max.time())
            else:
                end_time = datetime.now()
                if date_range == "Last 24 Hours":
                    start_time = end_time - timedelta(days=1)
                elif date_range == "Last 7 Days":
                    start_time = end_time - timedelta(days=7)
                else:  # Last 30 Days
                    start_time = end_time - timedelta(days=30)
            
            st.markdown("---")
            
            refresh_button = st.button("🔄 Refresh Data", use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 📋 Quick Links")
            st.markdown("- [CloudWatch Console](https://console.aws.amazon.com/cloudwatch)")
            st.markdown("- [Lambda Functions](https://console.aws.amazon.com/lambda)")
            st.markdown("- [DynamoDB Tables](https://console.aws.amazon.com/dynamodb)")
        
        # Fetch analytics data
        with st.spinner("Loading analytics data..."):
            analytics_data = self._fetch_analytics_data(start_time, end_time)
        
        if not analytics_data:
            st.error("Failed to load analytics data. Please check AWS credentials.")
            return
        
        # Display metrics
        self._render_overview_metrics(analytics_data)
        
        # Tabs for different metric categories
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "👥 User Adoption",
            "📈 Impact Metrics",
            "⚡ Performance",
            "🎯 Feature Adoption",
            "🤝 Resource Sharing"
        ])
        
        with tab1:
            self._render_user_adoption(analytics_data)
        
        with tab2:
            self._render_impact_metrics(analytics_data)
        
        with tab3:
            self._render_performance_metrics(analytics_data)
        
        with tab4:
            self._render_feature_adoption(analytics_data)
        
        with tab5:
            self._render_resource_sharing(analytics_data)
    
    def _fetch_analytics_data(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Fetch analytics data from Lambda function"""
        try:
            # Call analytics aggregator Lambda
            response = self.lambda_client.invoke(
                FunctionName='rise-analytics-aggregator',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'generate_report',
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                })
            )
            
            result = json.loads(response['Payload'].read())
            return json.loads(result['body'])
        
        except Exception as e:
            st.error(f"Error fetching analytics: {str(e)}")
            # Return mock data for development
            return self._get_mock_data(start_time, end_time)
    
    def _render_overview_metrics(self, data: Dict[str, Any]):
        """Render overview metrics cards"""
        st.header("📊 Overview Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        user_adoption = data.get('user_adoption', {})
        impact = data.get('impact_metrics', {})
        performance = data.get('technical_performance', {})
        
        with col1:
            active_users = user_adoption.get('active_users', 0)
            st.metric(
                label="Active Users",
                value=f"{active_users:,}",
                delta="Target: 10K+"
            )
        
        with col2:
            yield_imp = impact.get('yield_improvement', {}).get('average_percent', 0)
            target_met = impact.get('yield_improvement', {}).get('meets_target', False)
            st.metric(
                label="Avg Yield Improvement",
                value=f"{yield_imp}%",
                delta="✓ Target Met" if target_met else "Target: 15-25%"
            )
        
        with col3:
            cost_savings = impact.get('cost_reduction', {}).get('total_savings_inr', 0)
            st.metric(
                label="Total Cost Savings",
                value=f"₹{cost_savings:,.0f}",
                delta="Target: 20-30% reduction"
            )
        
        with col4:
            uptime = performance.get('uptime', {}).get('percent', 0)
            uptime_met = performance.get('uptime', {}).get('meets_target', False)
            st.metric(
                label="System Uptime",
                value=f"{uptime}%",
                delta="✓ Target Met" if uptime_met else "Target: 99.5%"
            )
    
    def _render_user_adoption(self, data: Dict[str, Any]):
        """Render user adoption metrics"""
        st.header("👥 User Adoption Metrics")
        
        user_adoption = data.get('user_adoption', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Session Metrics")
            
            active_users = user_adoption.get('active_users', 0)
            session_duration = user_adoption.get('avg_session_duration_minutes', 0)
            return_rate = user_adoption.get('return_rate_percent', 0)
            
            st.metric("Active Users", f"{active_users:,}")
            st.metric("Avg Session Duration", f"{session_duration} min")
            st.metric("Return Rate", f"{return_rate}%")
            
            # Progress bars
            st.markdown("#### Targets")
            st.progress(min(active_users / 10000, 1.0), text=f"Active Users: {active_users:,} / 10,000")
            st.progress(min(session_duration / 15, 1.0), text=f"Session Duration: {session_duration} / 15 min")
            st.progress(min(return_rate / 70, 1.0), text=f"Return Rate: {return_rate}% / 70%")
        
        with col2:
            st.subheader("Language Distribution")
            
            lang_dist = user_adoption.get('language_distribution', {})
            
            if lang_dist:
                # Create pie chart
                fig = px.pie(
                    values=list(lang_dist.values()),
                    names=list(lang_dist.keys()),
                    title="Users by Language"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No language distribution data available")
    
    def _render_impact_metrics(self, data: Dict[str, Any]):
        """Render impact metrics"""
        st.header("📈 Impact Metrics")
        
        impact = data.get('impact_metrics', {})
        
        # Yield Improvement
        st.subheader("🌾 Yield Improvement")
        col1, col2, col3 = st.columns(3)
        
        yield_data = impact.get('yield_improvement', {})
        
        with col1:
            avg_yield = yield_data.get('average_percent', 0)
            st.metric("Average", f"{avg_yield}%")
        
        with col2:
            max_yield = yield_data.get('maximum_percent', 0)
            st.metric("Maximum", f"{max_yield}%")
        
        with col3:
            min_yield = yield_data.get('minimum_percent', 0)
            st.metric("Minimum", f"{min_yield}%")
        
        target_met = yield_data.get('meets_target', False)
        if target_met:
            st.success(f"✓ Target Met: {yield_data.get('target_range', '15-25%')}")
        else:
            st.warning(f"Target: {yield_data.get('target_range', '15-25%')}")
        
        st.markdown("---")
        
        # Cost Reduction
        st.subheader("💰 Cost Reduction")
        cost_data = impact.get('cost_reduction', {})
        total_savings = cost_data.get('total_savings_inr', 0)
        
        st.metric("Total Savings", f"₹{total_savings:,.2f}")
        st.info(f"Target: {cost_data.get('target_range', '20-30%')} reduction in input costs")
        
        st.markdown("---")
        
        # Market Access & Scheme Adoption
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏪 Market Access")
            market_data = impact.get('market_access', {})
            market_percent = market_data.get('percent', 0)
            market_users = market_data.get('users_count', 0)
            
            st.metric("Users with Market Access", f"{market_users:,}")
            st.metric("Percentage", f"{market_percent}%")
            
            if market_data.get('meets_target', False):
                st.success(f"✓ Target Met: {market_data.get('target', '40%+')}")
            else:
                st.warning(f"Target: {market_data.get('target', '40%+')}")
        
        with col2:
            st.subheader("🏛️ Scheme Adoption")
            scheme_data = impact.get('scheme_adoption', {})
            scheme_percent = scheme_data.get('percent', 0)
            scheme_users = scheme_data.get('users_count', 0)
            
            st.metric("Users Applying for Schemes", f"{scheme_users:,}")
            st.metric("Percentage", f"{scheme_percent}%")
            
            if scheme_data.get('meets_target', False):
                st.success(f"✓ Target Met: {scheme_data.get('target', '60%+')}")
            else:
                st.warning(f"Target: {scheme_data.get('target', '60%+')}")
    
    def _render_performance_metrics(self, data: Dict[str, Any]):
        """Render technical performance metrics"""
        st.header("⚡ Technical Performance")
        
        performance = data.get('technical_performance', {})
        
        # Response Time
        st.subheader("⏱️ Response Time")
        col1, col2, col3 = st.columns(3)
        
        response_data = performance.get('response_time', {})
        
        with col1:
            avg_latency = response_data.get('average_ms', 0)
            st.metric("Average Latency", f"{avg_latency:.0f} ms")
        
        with col2:
            p99_latency = response_data.get('p99_ms', 0)
            st.metric("P99 Latency", f"{p99_latency:.0f} ms")
        
        with col3:
            target = response_data.get('target_ms', 3000)
            st.metric("Target", f"{target} ms")
        
        if response_data.get('meets_target', False):
            st.success("✓ Response time target met")
        else:
            st.warning("Response time exceeds target")
        
        st.markdown("---")
        
        # Accuracy Rates
        st.subheader("🎯 Accuracy Rates")
        col1, col2 = st.columns(2)
        
        accuracy_data = performance.get('accuracy_rates', {})
        
        with col1:
            diagnosis_acc = accuracy_data.get('diagnosis_percent', 0)
            diagnosis_target = accuracy_data.get('diagnosis_target', 90)
            
            st.metric("Crop Diagnosis Accuracy", f"{diagnosis_acc}%")
            st.progress(min(diagnosis_acc / 100, 1.0), text=f"{diagnosis_acc}% / {diagnosis_target}%")
            
            if accuracy_data.get('diagnosis_meets_target', False):
                st.success(f"✓ Target Met: {diagnosis_target}%")
            else:
                st.warning(f"Target: {diagnosis_target}%")
        
        with col2:
            pest_acc = accuracy_data.get('pest_identification_percent', 0)
            pest_target = accuracy_data.get('pest_target', 85)
            
            st.metric("Pest Identification Accuracy", f"{pest_acc}%")
            st.progress(min(pest_acc / 100, 1.0), text=f"{pest_acc}% / {pest_target}%")
            
            if accuracy_data.get('pest_meets_target', False):
                st.success(f"✓ Target Met: {pest_target}%")
            else:
                st.warning(f"Target: {pest_target}%")
        
        st.markdown("---")
        
        # Uptime
        st.subheader("🟢 System Uptime")
        uptime_data = performance.get('uptime', {})
        uptime = uptime_data.get('percent', 0)
        target = uptime_data.get('target', 99.5)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.metric("Current Uptime", f"{uptime}%")
            st.progress(min(uptime / 100, 1.0), text=f"{uptime}% / {target}%")
        
        with col2:
            if uptime_data.get('meets_target', False):
                st.success(f"✓ Target Met: {target}%")
            else:
                st.error(f"Below Target: {target}%")
    
    def _render_feature_adoption(self, data: Dict[str, Any]):
        """Render feature adoption metrics"""
        st.header("🎯 Feature Adoption")
        
        feature_data = data.get('feature_adoption', {})
        
        if not feature_data:
            st.info("No feature adoption data available")
            return
        
        # Create bar chart for feature usage
        features = list(feature_data.keys())
        usage_counts = [feature_data[f].get('usage_count', 0) for f in features]
        success_rates = [feature_data[f].get('success_rate_percent', 0) for f in features]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Feature Usage Count")
            fig = go.Figure(data=[
                go.Bar(x=features, y=usage_counts, marker_color='lightblue')
            ])
            fig.update_layout(
                xaxis_title="Feature",
                yaxis_title="Usage Count",
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Feature Success Rate")
            fig = go.Figure(data=[
                go.Bar(x=features, y=success_rates, marker_color='lightgreen')
            ])
            fig.update_layout(
                xaxis_title="Feature",
                yaxis_title="Success Rate (%)",
                xaxis_tickangle=-45,
                yaxis_range=[0, 100]
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.subheader("Detailed Feature Metrics")
        
        table_data = []
        for feature, metrics in feature_data.items():
            table_data.append({
                'Feature': feature.replace('_', ' ').title(),
                'Usage Count': metrics.get('usage_count', 0),
                'Success Rate': f"{metrics.get('success_rate_percent', 0)}%"
            })
        
        st.table(table_data)
    
    def _render_resource_sharing(self, data: Dict[str, Any]):
        """Render resource sharing metrics"""
        st.header("🤝 Resource Sharing & Cooperative Buying")
        
        resource_data = data.get('resource_sharing', {})
        
        # Equipment Utilization
        st.subheader("🚜 Equipment Utilization")
        equipment_data = resource_data.get('equipment_utilization', {})
        util_percent = equipment_data.get('average_percent', 0)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.metric("Average Equipment Utilization", f"{util_percent}%")
            st.progress(min(util_percent / 100, 1.0), text=f"{util_percent}% utilization")
            st.caption(equipment_data.get('description', ''))
        
        with col2:
            # Gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=util_percent,
                title={'text': "Utilization"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkblue"},
                       'steps': [
                           {'range': [0, 50], 'color': "lightgray"},
                           {'range': [50, 75], 'color': "gray"},
                           {'range': [75, 100], 'color': "lightblue"}
                       ]}
            ))
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Cooperative Buying
        st.subheader("🛒 Cooperative Buying Groups")
        coop_data = resource_data.get('cooperative_buying', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            savings_percent = coop_data.get('average_savings_percent', 0)
            st.metric("Average Savings", f"{savings_percent}%")
        
        with col2:
            total_savings = coop_data.get('total_savings_inr', 0)
            st.metric("Total Savings", f"₹{total_savings:,.2f}")
        
        with col3:
            target_range = coop_data.get('target_range', '15-30%')
            st.metric("Target Range", target_range)
        
        if coop_data.get('meets_target', False):
            st.success("✓ Cooperative buying savings target met")
        else:
            st.warning(f"Target: {target_range}")
    
    def _get_mock_data(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Generate mock data for development/testing"""
        return {
            'report_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_days': (end_time - start_time).days
            },
            'user_adoption': {
                'active_users': 8500,
                'avg_session_duration_seconds': 1020,
                'avg_session_duration_minutes': 17.0,
                'return_rate_percent': 72.5,
                'language_distribution': {
                    'Hindi': 3200,
                    'English': 1800,
                    'Tamil': 1200,
                    'Telugu': 900,
                    'Kannada': 700,
                    'Bengali': 400,
                    'Gujarati': 200,
                    'Marathi': 100
                }
            },
            'impact_metrics': {
                'yield_improvement': {
                    'average_percent': 18.5,
                    'maximum_percent': 32.0,
                    'minimum_percent': 8.0,
                    'target_range': '15-25%',
                    'meets_target': True
                },
                'cost_reduction': {
                    'total_savings_inr': 2450000.50,
                    'target_range': '20-30%'
                },
                'market_access': {
                    'users_count': 3800,
                    'percent': 44.7,
                    'target': '40%+',
                    'meets_target': True
                },
                'scheme_adoption': {
                    'users_count': 5200,
                    'percent': 61.2,
                    'target': '60%+',
                    'meets_target': True
                }
            },
            'technical_performance': {
                'response_time': {
                    'average_ms': 2450,
                    'p99_ms': 4200,
                    'target_ms': 3000,
                    'meets_target': True
                },
                'accuracy_rates': {
                    'diagnosis_percent': 92.3,
                    'pest_identification_percent': 88.7,
                    'diagnosis_target': 90,
                    'pest_target': 85,
                    'diagnosis_meets_target': True,
                    'pest_meets_target': True
                },
                'uptime': {
                    'percent': 99.7,
                    'target': 99.5,
                    'meets_target': True
                }
            },
            'feature_adoption': {
                'crop_diagnosis': {'usage_count': 4500, 'success_rate_percent': 94.2},
                'pest_identification': {'usage_count': 3200, 'success_rate_percent': 91.5},
                'soil_analysis': {'usage_count': 2800, 'success_rate_percent': 89.3},
                'weather_alerts': {'usage_count': 6500, 'success_rate_percent': 97.8},
                'market_prices': {'usage_count': 5200, 'success_rate_percent': 96.1},
                'buyer_connection': {'usage_count': 3800, 'success_rate_percent': 87.4},
                'government_scheme': {'usage_count': 5200, 'success_rate_percent': 82.6},
                'profitability_calculator': {'usage_count': 4100, 'success_rate_percent': 93.7},
                'equipment_sharing': {'usage_count': 2400, 'success_rate_percent': 88.9},
                'cooperative_buying': {'usage_count': 1900, 'success_rate_percent': 85.2}
            },
            'resource_sharing': {
                'equipment_utilization': {
                    'average_percent': 68.5,
                    'description': 'Average equipment usage rate'
                },
                'cooperative_buying': {
                    'average_savings_percent': 22.3,
                    'total_savings_inr': 850000.75,
                    'target_range': '15-30%',
                    'meets_target': True
                }
            },
            'generated_at': datetime.utcnow().isoformat()
        }


def render_analytics_dashboard():
    """Main function to render analytics dashboard"""
    dashboard = AnalyticsDashboard()
    dashboard.render()


if __name__ == "__main__":
    render_analytics_dashboard()
