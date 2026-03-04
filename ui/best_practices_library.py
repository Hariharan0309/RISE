"""
RISE Best Practices Library UI Component
Streamlit component for browsing, submitting, and adopting farming best practices
"""

import streamlit as st
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import time


def render_best_practices_library(best_practice_tools, user_id: str, user_language: str = 'en'):
    """
    Render best practices library interface in Streamlit
    
    Args:
        best_practice_tools: BestPracticeTools instance
        user_id: Current user identifier
        user_language: User's preferred language
    """
    st.header("📚 Best Practices Library")
    st.markdown("Discover, share, and adopt proven farming practices from the community")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌟 Browse Practices",
        "✍️ Submit Practice",
        "📊 My Adoptions",
        "🔍 Search",
        "🏆 My Contributions"
    ])
    
    with tab1:
        render_browse_practices(best_practice_tools, user_id, user_language)
    
    with tab2:
        render_submit_practice(best_practice_tools, user_id, user_language)
    
    with tab3:
        render_my_adoptions(best_practice_tools, user_id, user_language)
    
    with tab4:
        render_search_practices(best_practice_tools, user_id, user_language)
    
    with tab5:
        render_my_contributions(best_practice_tools, user_id, user_language)


def render_browse_practices(best_practice_tools, user_id: str, user_language: str):
    """Render practices browsing interface"""
    
    st.subheader("Browse Best Practices")
    
    # Filters and sorting
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        crop_type = st.selectbox(
            "Crop Type",
            options=["All", "wheat", "rice", "cotton", "sugarcane", "vegetables", "fruits", "pulses"],
            index=0
        )
    
    with col2:
        practice_type = st.selectbox(
            "Practice Type",
            options=["All", "organic_farming", "pest_control", "irrigation", "soil_management", "harvesting"],
            index=0
        )
    
    with col3:
        region = st.selectbox(
            "Region",
            options=["All", "north_india", "south_india", "east_india", "west_india", "central_india"],
            index=0
        )
    
    with col4:
        sort_by = st.selectbox(
            "Sort By",
            options=["recent", "popular", "success_rate"],
            format_func=lambda x: {
                'recent': 'Most Recent',
                'popular': 'Most Popular',
                'success_rate': 'Highest Success Rate'
            }[x]
        )
    
    # Build category filter
    category = None
    if crop_type != "All" or practice_type != "All" or region != "All":
        category = {}
        if crop_type != "All":
            category['crop_type'] = crop_type
        if practice_type != "All":
            category['practice_type'] = practice_type
        if region != "All":
            category['region'] = region
    
    # Fetch practices
    with st.spinner("Loading practices..."):
        result = best_practice_tools.get_practices(
            category=category,
            sort_by=sort_by,
            limit=20
        )
    
    if result['success'] and result['practices']:
        st.markdown(f"### Found {result['count']} practices")
        
        for practice in result['practices']:
            render_practice_card(best_practice_tools, practice, user_id, user_language)
    elif result['success']:
        st.info("📭 No practices found. Be the first to share a practice!")
    else:
        st.error(f"❌ Failed to load practices: {result.get('error')}")


def render_practice_card(best_practice_tools, practice: Dict[str, Any], user_id: str, user_language: str):
    """Render a single practice card"""
    
    # Translate if needed
    display_practice = practice
    if practice['original_language'] != user_language:
        with st.spinner("Translating..."):
            translate_result = best_practice_tools.translate_practice(
                practice['practice_id'],
                user_language
            )
            if translate_result['success'] and translate_result.get('translated'):
                display_practice = translate_result['practice']
    
    # Practice container
    with st.container():
        st.markdown("---")
        
        # Header
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {display_practice['title']}")
            
            # Translation indicator
            if display_practice.get('translated_to'):
                st.caption(f"🌐 Translated from {practice['original_language'].upper()}")
        
        with col2:
            # Validation score badge
            validation_score = practice.get('validation_score', 0)
            if validation_score >= 80:
                st.success(f"✓ Validated: {validation_score}%")
            elif validation_score >= 60:
                st.info(f"✓ Validated: {validation_score}%")
            else:
                st.warning(f"⚠ Score: {validation_score}%")
        
        # Description
        st.markdown(display_practice['description'])
        
        # Category tags
        category = practice.get('category', {})
        tag_cols = st.columns(len(category))
        
        for idx, (key, value) in enumerate(category.items()):
            with tag_cols[idx]:
                st.markdown(f"`{value}`")
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Adoptions", practice.get('adoption_count', 0))
        
        with col2:
            success_rate = practice.get('avg_success_rate', 0)
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col3:
            st.metric("Successful", practice.get('success_count', 0))
        
        with col4:
            st.metric("Feedback", practice.get('total_feedback', 0))
        
        # Expandable details
        with st.expander("📋 View Implementation Steps"):
            steps = display_practice.get('steps', [])
            for idx, step in enumerate(steps, 1):
                st.markdown(f"**Step {idx}:** {step}")
        
        with st.expander("💡 Expected Benefits"):
            benefits = practice.get('expected_benefits', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'yield_increase' in benefits:
                    st.metric("Yield Increase", f"+{benefits['yield_increase']}%")
                if 'cost_reduction' in benefits:
                    st.metric("Cost Reduction", f"-{benefits['cost_reduction']}%")
            
            with col2:
                if 'soil_health_improvement' in benefits:
                    st.info(f"Soil Health: {benefits['soil_health_improvement'].title()}")
                if 'sustainability_score' in benefits:
                    st.success(f"Sustainability: {benefits['sustainability_score']}/10")
        
        with st.expander("📦 Resources Needed"):
            resources = practice.get('resources_needed', [])
            if resources:
                for resource in resources:
                    st.markdown(f"• {resource}")
            else:
                st.info("No special resources required")
        
        with st.expander("📚 Scientific References"):
            references = practice.get('scientific_references', [])
            if references:
                for ref in references:
                    st.markdown(f"• {ref}")
            else:
                st.info("No references available")
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ Adopt This Practice", key=f"adopt_{practice['practice_id']}"):
                st.session_state[f'adopting_{practice["practice_id"]}'] = True
                st.rerun()
        
        with col2:
            if st.button("📊 View Analytics", key=f"analytics_{practice['practice_id']}"):
                st.session_state[f'viewing_analytics_{practice["practice_id"]}'] = True
                st.rerun()
        
        # Adoption form
        if st.session_state.get(f'adopting_{practice["practice_id"]}', False):
            render_adoption_form(best_practice_tools, practice, user_id)
        
        # Analytics view
        if st.session_state.get(f'viewing_analytics_{practice["practice_id"]}', False):
            render_practice_analytics(best_practice_tools, practice['practice_id'])


def render_adoption_form(best_practice_tools, practice: Dict[str, Any], user_id: str):
    """Render practice adoption form"""
    
    with st.form(key=f"adoption_form_{practice['practice_id']}"):
        st.markdown("### Adopt This Practice")
        
        implementation_date = st.date_input(
            "Implementation Date",
            value=date.today(),
            help="When will you start implementing this practice?"
        )
        
        notes = st.text_area(
            "Implementation Notes (Optional)",
            placeholder="Any specific adaptations or notes about your implementation...",
            height=100
        )
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            submit = st.form_submit_button("Confirm Adoption", type="primary")
        
        with col2:
            cancel = st.form_submit_button("Cancel")
        
        if submit:
            result = best_practice_tools.adopt_practice(
                practice_id=practice['practice_id'],
                user_id=user_id,
                implementation_date=implementation_date.isoformat(),
                notes=notes
            )
            
            if result['success']:
                st.success("✅ Practice adopted! Track your progress in 'My Adoptions' tab.")
                st.session_state[f'adopting_{practice["practice_id"]}'] = False
                time.sleep(2)
                st.rerun()
            else:
                st.error(f"❌ {result.get('error')}")
        
        if cancel:
            st.session_state[f'adopting_{practice["practice_id"]}'] = False
            st.rerun()


def render_practice_analytics(best_practice_tools, practice_id: str):
    """Render detailed practice analytics"""
    
    with st.spinner("Loading analytics..."):
        result = best_practice_tools.get_adoption_analytics(practice_id)
    
    if not result['success']:
        st.error(f"❌ Failed to load analytics: {result.get('error')}")
        return
    
    analytics = result['analytics']
    
    st.markdown("### 📊 Practice Analytics")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Adoptions", analytics['total_adoptions'])
    
    with col2:
        st.metric("Completed", analytics['completed_adoptions'])
    
    with col3:
        st.metric("Successful", analytics['successful_adoptions'])
    
    with col4:
        st.metric("Success Rate", f"{analytics['success_rate']:.1f}%")
    
    # Impact metrics
    st.markdown("### 📈 Average Impact")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        yield_change = analytics.get('avg_yield_change', 0)
        st.metric("Yield Change", f"{yield_change:+.1f}%")
    
    with col2:
        cost_change = analytics.get('avg_cost_change', 0)
        st.metric("Cost Change", f"{cost_change:+.1f}%")
    
    with col3:
        trend = analytics.get('adoption_trend', 'stable')
        trend_emoji = {'increasing': '📈', 'stable': '➡️', 'decreasing': '📉'}.get(trend, '➡️')
        st.metric("Trend", f"{trend_emoji} {trend.title()}")
    
    if st.button("Close Analytics"):
        st.session_state[f'viewing_analytics_{practice_id}'] = False
        st.rerun()


def render_submit_practice(best_practice_tools, user_id: str, user_language: str):
    """Render practice submission form"""
    
    st.subheader("Share Your Best Practice")
    st.markdown("Help other farmers by sharing your successful farming practices")
    
    with st.form("submit_practice_form"):
        # Basic information
        st.markdown("### Basic Information")
        
        title = st.text_input(
            "Practice Title *",
            placeholder="e.g., Organic Pest Control for Cotton",
            max_chars=200
        )
        
        description = st.text_area(
            "Description *",
            placeholder="Describe your practice in detail...",
            height=150,
            max_chars=2000
        )
        
        # Category
        st.markdown("### Categorize Your Practice")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            crop_type = st.selectbox(
                "Crop Type *",
                options=["wheat", "rice", "cotton", "sugarcane", "vegetables", "fruits", "pulses", "oilseeds"]
            )
        
        with col2:
            practice_type = st.selectbox(
                "Practice Type *",
                options=["organic_farming", "pest_control", "irrigation", "soil_management", "harvesting", "storage"]
            )
        
        with col3:
            region = st.selectbox(
                "Region *",
                options=["north_india", "south_india", "east_india", "west_india", "central_india"]
            )
        
        # Implementation steps
        st.markdown("### Implementation Steps")
        st.caption("Provide clear, step-by-step instructions")
        
        num_steps = st.number_input("Number of Steps", min_value=1, max_value=10, value=4)
        
        steps = []
        for i in range(num_steps):
            step = st.text_input(
                f"Step {i+1} *",
                placeholder=f"Describe step {i+1}...",
                key=f"step_{i}"
            )
            if step:
                steps.append(step)
        
        # Expected benefits
        st.markdown("### Expected Benefits")
        
        col1, col2 = st.columns(2)
        
        with col1:
            yield_increase = st.number_input(
                "Expected Yield Increase (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.5
            )
            
            cost_reduction = st.number_input(
                "Expected Cost Reduction (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.5
            )
        
        with col2:
            soil_health = st.selectbox(
                "Soil Health Impact",
                options=["none", "low", "medium", "high"]
            )
            
            sustainability = st.slider(
                "Sustainability Score",
                min_value=1,
                max_value=10,
                value=5
            )
        
        # Resources needed
        st.markdown("### Resources Needed")
        
        resources_input = st.text_area(
            "List Required Resources (one per line)",
            placeholder="e.g.,\nOrganic compost\nNeem oil\nSpraying equipment",
            height=100
        )
        
        # Submit button
        st.markdown("---")
        submit = st.form_submit_button("🚀 Submit Practice for Validation", type="primary")
        
        if submit:
            # Validate
            if not title or not description or len(steps) < num_steps:
                st.error("❌ Please fill in all required fields (marked with *)")
            else:
                # Parse resources
                resources = [r.strip() for r in resources_input.split('\n') if r.strip()]
                
                # Create category
                category = {
                    'crop_type': crop_type,
                    'practice_type': practice_type,
                    'region': region
                }
                
                # Create expected benefits
                expected_benefits = {
                    'yield_increase': yield_increase,
                    'cost_reduction': cost_reduction,
                    'soil_health_improvement': soil_health,
                    'sustainability_score': sustainability
                }
                
                # Submit practice
                with st.spinner("Validating practice with AI... This may take a moment."):
                    result = best_practice_tools.submit_practice(
                        user_id=user_id,
                        title=title,
                        description=description,
                        language=user_language,
                        category=category,
                        steps=steps,
                        expected_benefits=expected_benefits,
                        resources_needed=resources
                    )
                
                if result['success']:
                    st.success("✅ Your practice has been validated and published!")
                    st.info(f"Validation Score: {result['validation_score']}/100")
                    
                    # Show scientific references
                    if result.get('scientific_references'):
                        st.markdown("**Scientific References Found:**")
                        for ref in result['scientific_references']:
                            st.markdown(f"• {ref}")
                    
                    st.balloons()
                    time.sleep(3)
                    st.rerun()
                else:
                    error_msg = result.get('error', 'Unknown error')
                    reason = result.get('reason', '')
                    st.error(f"❌ Validation failed: {error_msg}")
                    
                    if reason:
                        st.warning(f"**Reason:** {reason}")
                    
                    # Show suggestions
                    suggestions = result.get('suggestions', [])
                    if suggestions:
                        st.markdown("**Suggestions for Improvement:**")
                        for suggestion in suggestions:
                            st.markdown(f"• {suggestion}")


def render_my_adoptions(best_practice_tools, user_id: str, user_language: str):
    """Render user's adopted practices"""
    
    st.subheader("My Adopted Practices")
    st.markdown("Track your progress and provide feedback on practices you've adopted")
    
    # In a real implementation, we'd fetch user's adoptions from the database
    st.info("🚧 This feature tracks your adopted practices. Adopt a practice to see it here!")
    
    # Placeholder for demonstration
    st.markdown("### How to Use")
    st.markdown("""
    1. **Browse** practices in the Browse tab
    2. **Adopt** a practice by clicking 'Adopt This Practice'
    3. **Implement** the practice on your farm
    4. **Track** your progress here
    5. **Provide feedback** to help other farmers
    """)


def render_search_practices(best_practice_tools, user_id: str, user_language: str):
    """Render practice search interface"""
    
    st.subheader("Search Best Practices")
    
    # Search input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Search",
            placeholder="Enter keywords to search practices...",
            label_visibility="collapsed"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    if search_button and search_query:
        with st.spinner("Searching..."):
            result = best_practice_tools.search_practices(query=search_query, limit=20)
        
        if result['success']:
            st.markdown(f"### Found {result['count']} results for '{search_query}'")
            
            if result['practices']:
                for practice in result['practices']:
                    render_practice_card(best_practice_tools, practice, user_id, user_language)
            else:
                st.info("📭 No practices found matching your search.")
        else:
            st.error(f"❌ Search failed: {result.get('error')}")
    else:
        st.info("👆 Enter a search query to find relevant practices")
        
        # Show popular topics
        st.markdown("### 🔥 Popular Topics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🌾 Organic Farming"):
                st.session_state['search_query'] = 'organic'
                st.rerun()
        
        with col2:
            if st.button("🐛 Pest Control"):
                st.session_state['search_query'] = 'pest'
                st.rerun()
        
        with col3:
            if st.button("💧 Water Management"):
                st.session_state['search_query'] = 'water'
                st.rerun()


def render_my_contributions(best_practice_tools, user_id: str, user_language: str):
    """Render user's contributed practices"""
    
    st.subheader("My Contributions")
    
    # Get user contributions
    with st.spinner("Loading your contributions..."):
        result = best_practice_tools.get_user_contributions(user_id)
    
    if not result['success']:
        st.error(f"❌ Failed to load contributions: {result.get('error')}")
        return
    
    contributions = result['contributions']
    practices = result.get('practices', [])
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Practices Shared", contributions['total_practices'])
    
    with col2:
        st.metric("Total Adoptions", contributions['total_adoptions'])
    
    with col3:
        st.metric("Successful Uses", contributions['total_successful'])
    
    with col4:
        st.metric("Avg Success Rate", f"{contributions['avg_success_rate']:.1f}%")
    
    # Most popular practice
    if contributions.get('most_popular_practice'):
        st.markdown("---")
        st.markdown("### 🌟 Your Most Popular Practice")
        
        most_popular = contributions['most_popular_practice']
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{most_popular['title']}**")
        
        with col2:
            st.metric("Adoptions", most_popular['adoptions'])
    
    # List of practices
    if practices:
        st.markdown("---")
        st.markdown("### Your Shared Practices")
        
        for practice in practices:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{practice['title']}**")
                    st.caption(f"Category: {practice['category'].get('crop_type', 'N/A')}")
                
                with col2:
                    st.metric("Adoptions", practice.get('adoption_count', 0))
                
                with col3:
                    success_rate = practice.get('avg_success_rate', 0)
                    st.metric("Success", f"{success_rate:.0f}%")
                
                st.markdown("---")
    else:
        st.info("You haven't shared any practices yet. Share your knowledge in the 'Submit Practice' tab!")


def render_best_practices_widget(best_practice_tools, user_language: str = 'en'):
    """
    Render compact best practices widget for sidebar or dashboard
    
    Args:
        best_practice_tools: BestPracticeTools instance
        user_language: User's preferred language
    """
    st.markdown("### 📚 Best Practices")
    
    # Get top practices
    result = best_practice_tools.get_practices(sort_by='success_rate', limit=3)
    
    if result['success'] and result['practices']:
        for practice in result['practices']:
            with st.container():
                st.markdown(f"**{practice['title'][:50]}...**")
                success_rate = practice.get('avg_success_rate', 0)
                st.caption(f"✅ {success_rate:.0f}% success • {practice.get('adoption_count', 0)} adoptions")
                st.markdown("---")
        
        if st.button("View All Practices", use_container_width=True):
            st.session_state['active_page'] = 'best_practices'
            st.rerun()
    else:
        st.info("No practices available yet")
