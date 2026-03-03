"""
RISE Farmer Forum UI Component
Streamlit component for multilingual farmer forums with real-time translation
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional
import time


def render_farmer_forum(forum_tools, user_id: str, user_language: str = 'en'):
    """
    Render farmer forum interface in Streamlit
    
    Args:
        forum_tools: ForumTools instance
        user_id: Current user identifier
        user_language: User's preferred language
    """
    st.header("👥 Farmer Community Forum")
    st.markdown("Connect with farmers across India. Share experiences, ask questions, and learn together.")
    
    # Language selector for translation
    col1, col2 = st.columns([3, 1])
    
    with col2:
        translation_enabled = st.toggle(
            "🌐 Auto-translate",
            value=True,
            help="Automatically translate posts to your language"
        )
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📰 All Posts", 
        "✍️ Create Post", 
        "🔍 Search", 
        "🏆 Expert Directory",
        "📊 My Profile"
    ])
    
    with tab1:
        render_posts_feed(forum_tools, user_id, user_language, translation_enabled)
    
    with tab2:
        render_create_post(forum_tools, user_id, user_language)
    
    with tab3:
        render_search_posts(forum_tools, user_id, user_language, translation_enabled)
    
    with tab4:
        render_expert_directory(forum_tools, user_language)
    
    with tab5:
        render_user_profile(forum_tools, user_id)


def render_posts_feed(forum_tools, user_id: str, user_language: str, translation_enabled: bool):
    """Render posts feed with filtering"""
    
    st.subheader("Recent Discussions")
    
    # Category filters
    with st.expander("🔽 Filter by Category"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            crop_type = st.selectbox(
                "Crop Type",
                options=["All", "wheat", "rice", "cotton", "sugarcane", "vegetables", "fruits"],
                index=0
            )
        
        with col2:
            region = st.selectbox(
                "Region",
                options=["All", "north_india", "south_india", "east_india", "west_india", "central_india"],
                index=0
            )
        
        with col3:
            method = st.selectbox(
                "Farming Method",
                options=["All", "traditional", "organic", "modern", "mixed"],
                index=0
            )
    
    # Build category filter
    category = None
    if crop_type != "All" or region != "All" or method != "All":
        category = {}
        if crop_type != "All":
            category['crop_type'] = crop_type
        if region != "All":
            category['region'] = region
        if method != "All":
            category['method'] = method
    
    # Fetch posts
    with st.spinner("Loading posts..."):
        result = forum_tools.get_posts(category=category, limit=20)
    
    if result['success'] and result['posts']:
        for post in result['posts']:
            render_post_card(forum_tools, post, user_id, user_language, translation_enabled)
    elif result['success']:
        st.info("📭 No posts found. Be the first to start a discussion!")
    else:
        st.error(f"❌ Failed to load posts: {result.get('error')}")


def render_post_card(forum_tools, post: Dict[str, Any], user_id: str, user_language: str, translation_enabled: bool):
    """Render a single post card"""
    
    # Translate if needed
    display_post = post
    if translation_enabled and post['original_language'] != user_language:
        with st.spinner("Translating..."):
            translate_result = forum_tools.translate_post(post['post_id'], user_language)
            if translate_result['success'] and translate_result.get('translated'):
                display_post = translate_result['post']
    
    # Post container
    with st.container():
        st.markdown("---")
        
        # Header with title and metadata
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"### {display_post['title']}")
            
            # Show translation indicator
            if display_post.get('translated_to'):
                st.caption(f"🌐 Translated from {post['original_language'].upper()} to {user_language.upper()}")
        
        with col2:
            # User reputation badge with enhanced display
            rep_result = forum_tools.get_user_reputation(post['user_id'])
            if rep_result['success']:
                badge_emoji = rep_result['badge_emoji']
                badge = rep_result['badge']
                is_verified = rep_result['is_verified_expert']
                
                # Show verified expert badge prominently
                if is_verified:
                    st.markdown(f"### {badge_emoji} VERIFIED EXPERT")
                    st.caption(rep_result['badge_description'])
                else:
                    st.markdown(f"## {badge_emoji}")
                    st.caption(badge.replace('_', ' ').title())
        
        # Post content
        st.markdown(display_post['content'])
        
        # Category tags
        category = post.get('category', {})
        tags = post.get('tags', [])
        
        tag_cols = st.columns(len(tags) + len(category))
        idx = 0
        
        for key, value in category.items():
            with tag_cols[idx]:
                st.markdown(f"`{value}`")
                idx += 1
        
        for tag in tags:
            with tag_cols[idx]:
                st.markdown(f"`#{tag}`")
                idx += 1
        
        # Post metadata and actions
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.caption(f"👁️ {post.get('views_count', 0)} views")
        
        with col2:
            st.caption(f"💬 {post.get('replies_count', 0)} replies")
        
        with col3:
            if st.button(f"👍 {post.get('likes_count', 0)}", key=f"like_{post['post_id']}"):
                like_result = forum_tools.like_post(post['post_id'], user_id)
                if like_result['success']:
                    st.success("Liked!")
                    st.rerun()
        
        with col4:
            # Mark as solution button
            if not post.get('is_solution', False):
                if st.button("✓ Solution", key=f"solution_{post['post_id']}"):
                    solution_result = forum_tools.mark_post_as_solution(post['post_id'], user_id)
                    if solution_result['success']:
                        st.success("Marked as solution!")
                        st.rerun()
            else:
                st.success("✓ Verified Solution")
        
        with col5:
            # Time ago
            timestamp = post.get('timestamp', 0)
            time_ago = get_time_ago(timestamp)
            st.caption(f"🕒 {time_ago}")
        
        with col6:
            if st.button("💬 Reply", key=f"reply_{post['post_id']}"):
                st.session_state[f'replying_to_{post["post_id"]}'] = True
        
        # Reply form
        if st.session_state.get(f'replying_to_{post["post_id"]}', False):
            with st.form(key=f"reply_form_{post['post_id']}"):
                reply_content = st.text_area(
                    "Your Reply",
                    placeholder="Share your thoughts...",
                    height=100
                )
                
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    submit_reply = st.form_submit_button("Send Reply", type="primary")
                
                with col2:
                    cancel_reply = st.form_submit_button("Cancel")
                
                if submit_reply and reply_content:
                    reply_result = forum_tools.add_reply(
                        post_id=post['post_id'],
                        user_id=user_id,
                        content=reply_content,
                        language=user_language
                    )
                    
                    if reply_result['success']:
                        st.success("✅ Reply posted!")
                        st.session_state[f'replying_to_{post["post_id"]}'] = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {reply_result.get('error')}")
                
                if cancel_reply:
                    st.session_state[f'replying_to_{post["post_id"]}'] = False
                    st.rerun()


def render_create_post(forum_tools, user_id: str, user_language: str):
    """Render create post form"""
    
    st.subheader("Create New Discussion")
    
    with st.form("create_post_form"):
        # Title
        title = st.text_input(
            "Title *",
            placeholder="What's your question or topic?",
            max_chars=200
        )
        
        # Content
        content = st.text_area(
            "Description *",
            placeholder="Provide details about your question or share your experience...",
            height=200,
            max_chars=5000
        )
        
        # Category selection
        st.markdown("### Categorize Your Post")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            crop_type = st.selectbox(
                "Crop Type *",
                options=["wheat", "rice", "cotton", "sugarcane", "vegetables", "fruits", "pulses", "oilseeds", "other"]
            )
        
        with col2:
            region = st.selectbox(
                "Region *",
                options=["north_india", "south_india", "east_india", "west_india", "central_india"]
            )
        
        with col3:
            method = st.selectbox(
                "Farming Method *",
                options=["traditional", "organic", "modern", "mixed"]
            )
        
        # Tags
        tags_input = st.text_input(
            "Tags (comma-separated)",
            placeholder="e.g., pest_control, irrigation, fertilizer",
            help="Add relevant tags to help others find your post"
        )
        
        # Submit button
        submit = st.form_submit_button("📤 Post to Forum", type="primary")
        
        if submit:
            # Validate
            if not title or not content:
                st.error("❌ Please fill in all required fields (marked with *)")
            else:
                # Parse tags
                tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                
                # Create category
                category = {
                    'crop_type': crop_type,
                    'region': region,
                    'method': method
                }
                
                # Create post
                with st.spinner("Posting... (checking for spam)"):
                    result = forum_tools.create_post(
                        user_id=user_id,
                        title=title,
                        content=content,
                        language=user_language,
                        category=category,
                        tags=tags
                    )
                
                if result['success']:
                    st.success("✅ Your post has been published!")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    error_msg = result.get('error', 'Unknown error')
                    reason = result.get('reason', '')
                    st.error(f"❌ Failed to create post: {error_msg}")
                    if reason:
                        st.warning(f"Reason: {reason}")


def render_search_posts(forum_tools, user_id: str, user_language: str, translation_enabled: bool):
    """Render search interface"""
    
    st.subheader("Search Discussions")
    
    # Search input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Search",
            placeholder="Enter keywords to search...",
            label_visibility="collapsed"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    if search_button and search_query:
        with st.spinner("Searching..."):
            result = forum_tools.search_posts(query=search_query, limit=20)
        
        if result['success']:
            st.markdown(f"### Found {result['count']} results for '{search_query}'")
            
            if result['posts']:
                for post in result['posts']:
                    render_post_card(forum_tools, post, user_id, user_language, translation_enabled)
            else:
                st.info("📭 No posts found matching your search.")
        else:
            st.error(f"❌ Search failed: {result.get('error')}")
    else:
        st.info("👆 Enter a search query to find relevant discussions")
        
        # Show popular topics
        st.markdown("### 🔥 Popular Topics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🌾 Wheat Cultivation"):
                st.session_state['search_query'] = 'wheat'
                st.rerun()
        
        with col2:
            if st.button("🐛 Pest Control"):
                st.session_state['search_query'] = 'pest'
                st.rerun()
        
        with col3:
            if st.button("💧 Irrigation"):
                st.session_state['search_query'] = 'irrigation'
                st.rerun()


def render_expert_directory(forum_tools, user_language: str = 'en'):
    """Render comprehensive expert directory"""
    
    st.subheader("🏆 Expert Directory")
    st.markdown("Discover verified agricultural experts and top contributors in our community")
    
    # Get expert directory
    with st.spinner("Loading expert directory..."):
        result = forum_tools.get_expert_directory()
    
    if not result['success']:
        st.error(f"❌ Failed to load expert directory: {result.get('error')}")
        return
    
    directory = result['directory']
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Experts", directory['total_experts'])
    
    with col2:
        st.metric("Verified Experts", directory['total_verified'])
    
    with col3:
        st.metric("Expertise Areas", len(directory['by_expertise']))
    
    st.markdown("---")
    
    # Filter options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        view_mode = st.radio(
            "View Mode",
            options=["All Experts", "Verified Only", "By Expertise Area"],
            horizontal=True
        )
    
    with col2:
        if view_mode == "By Expertise Area":
            expertise_areas = list(directory['by_expertise'].keys())
            selected_area = st.selectbox(
                "Select Area",
                options=expertise_areas if expertise_areas else ["No areas available"]
            )
    
    st.markdown("---")
    
    # Display experts based on view mode
    if view_mode == "Verified Only":
        st.subheader("🌟 Verified Experts")
        
        if directory['verified_experts']:
            for expert in directory['verified_experts']:
                render_expert_card(forum_tools, expert)
        else:
            st.info("No verified experts yet. Keep contributing to earn verified status!")
    
    elif view_mode == "By Expertise Area":
        if expertise_areas and selected_area in directory['by_expertise']:
            st.subheader(f"Experts in {selected_area.replace('_', ' ').title()}")
            
            area_experts = directory['by_expertise'][selected_area]
            
            for expert_summary in area_experts:
                # Get full expert details
                rep_result = forum_tools.get_user_reputation(expert_summary['user_id'])
                if rep_result['success']:
                    render_expert_card(forum_tools, rep_result)
        else:
            st.info("No experts found in this area yet.")
    
    else:  # All Experts
        st.subheader("All Community Experts")
        
        # Get top experts
        experts_result = forum_tools.get_top_experts(limit=50)
        
        if experts_result['success'] and experts_result['experts']:
            for expert in experts_result['experts']:
                render_expert_card(forum_tools, expert)
        else:
            st.info("No experts found yet.")


def render_expert_card(forum_tools, expert: Dict[str, Any]):
    """Render an expert profile card"""
    
    with st.container():
        st.markdown("---")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Expert badge and name
            badge_emoji = expert.get('badge_emoji', '👤')
            user_id = expert.get('user_id', 'Unknown')
            
            if expert.get('is_verified_expert', False):
                st.markdown(f"### {badge_emoji} {user_id}")
                st.markdown("**✓ VERIFIED EXPERT**")
            else:
                st.markdown(f"### {badge_emoji} {user_id}")
            
            # Badge description
            badge_desc = expert.get('badge_description', '')
            if badge_desc:
                st.caption(badge_desc)
        
        with col2:
            # Reputation metrics
            st.metric("Reputation Score", expert.get('reputation_score', 0))
            st.metric("Expertise Level", f"{expert.get('expertise_level', 0)}%")
        
        with col3:
            # View profile button
            if st.button("View Profile", key=f"view_expert_{user_id}"):
                st.session_state['view_user_profile'] = user_id
                st.rerun()
        
        # Expertise areas
        expertise_areas = expert.get('expertise_areas', [])
        if expertise_areas:
            st.markdown("**Expertise Areas:**")
            
            cols = st.columns(min(len(expertise_areas), 5))
            for idx, area in enumerate(expertise_areas[:5]):
                with cols[idx]:
                    area_name = area['area'].replace('_', ' ').title()
                    st.markdown(f"`{area_name}`")
                    st.caption(f"{area['posts_count']} posts")
        
        # Key metrics
        metrics = expert.get('metrics', {})
        if metrics:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.caption(f"📝 {metrics.get('total_posts', 0)} posts")
            
            with col2:
                st.caption(f"💡 {metrics.get('helpful_answers', 0)} helpful")
            
            with col3:
                st.caption(f"✓ {metrics.get('verified_solutions', 0)} solutions")
            
            with col4:
                st.caption(f"👍 {metrics.get('total_likes', 0)} likes")


def render_user_profile(forum_tools, user_id: str):
    """Render detailed user profile with reputation and achievements"""
    
    st.subheader("📊 My Profile")
    
    # Get user reputation
    with st.spinner("Loading your profile..."):
        result = forum_tools.get_user_reputation(user_id)
    
    if not result['success']:
        st.error(f"❌ Failed to load profile: {result.get('error')}")
        return
    
    # Profile header
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Badge display
        badge_emoji = result['badge_emoji']
        badge = result['badge']
        
        st.markdown(f"# {badge_emoji}")
        st.markdown(f"### {badge.replace('_', ' ').title()}")
        
        if result['is_verified_expert']:
            st.success("✓ VERIFIED EXPERT")
        
        st.caption(result['badge_description'])
    
    with col2:
        # Key metrics
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.metric("Reputation", result['reputation_score'])
        
        with col_b:
            st.metric("Expertise Level", f"{result['expertise_level']}%")
        
        with col_c:
            posts_count = result['metrics']['total_posts']
            st.metric("Total Posts", posts_count)
    
    st.markdown("---")
    
    # Detailed metrics
    st.subheader("📈 Contribution Metrics")
    
    metrics = result['metrics']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Helpful Answers", metrics['helpful_answers'])
        st.caption("High-quality responses")
    
    with col2:
        st.metric("Verified Solutions", metrics['verified_solutions'])
        st.caption("Confirmed solutions")
    
    with col3:
        st.metric("Community Endorsements", metrics['community_endorsements'])
        st.caption("Highly engaged posts")
    
    with col4:
        st.metric("Engagement Rate", f"{metrics['engagement_rate']:.1f}")
        st.caption("Avg replies + likes per post")
    
    st.markdown("---")
    
    # Expertise areas
    st.subheader("🌾 Your Expertise Areas")
    
    expertise_areas = result.get('expertise_areas', [])
    
    if expertise_areas:
        for area in expertise_areas:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    area_name = area['area'].replace('_', ' ').title()
                    st.markdown(f"**{area_name}**")
                
                with col2:
                    st.caption(f"📝 {area['posts_count']} posts")
                
                with col3:
                    st.caption(f"💬 {area['engagement']} engagement")
                
                # Progress bar for expertise score
                max_score = expertise_areas[0]['score'] if expertise_areas else 100
                progress = min(1.0, area['score'] / max_score)
                st.progress(progress)
    else:
        st.info("Start posting to build your expertise profile!")
    
    st.markdown("---")
    
    # Achievements
    st.subheader("🏅 Achievements")
    
    achievements = result.get('achievements', [])
    
    if achievements:
        cols = st.columns(min(len(achievements), 3))
        
        for idx, achievement in enumerate(achievements):
            col_idx = idx % 3
            with cols[col_idx]:
                st.markdown(f"**🏅 {achievement['title']}**")
                st.caption(achievement['description'])
    else:
        st.info("Keep contributing to unlock achievements!")
    
    st.markdown("---")
    
    # Progress to next level
    st.subheader("🎯 Progress to Next Level")
    
    current_score = result['reputation_score']
    badge = result['badge']
    
    # Define level thresholds
    levels = {
        'beginner': {'next': 'contributor', 'threshold': 200},
        'contributor': {'next': 'experienced', 'threshold': 500},
        'experienced': {'next': 'expert', 'threshold': 1000},
        'expert': {'next': 'master_farmer', 'threshold': 2000},
        'master_farmer': {'next': 'max', 'threshold': current_score}
    }
    
    if badge in levels and levels[badge]['next'] != 'max':
        next_level = levels[badge]['next'].replace('_', ' ').title()
        threshold = levels[badge]['threshold']
        progress = min(1.0, current_score / threshold)
        points_needed = max(0, threshold - current_score)
        
        st.markdown(f"**Next Level: {next_level}**")
        st.progress(progress)
        st.caption(f"{points_needed} points needed to reach {next_level}")
    else:
        st.success("🏆 You've reached the highest level! Keep being awesome!")


def render_top_contributors(forum_tools):
    """Legacy function - redirects to expert directory"""
    render_expert_directory(forum_tools)


def get_time_ago(timestamp_ms: int) -> str:
    """Convert timestamp to human-readable time ago"""
    try:
        now = time.time() * 1000
        diff_ms = now - timestamp_ms
        diff_seconds = diff_ms / 1000
        
        if diff_seconds < 60:
            return "just now"
        elif diff_seconds < 3600:
            minutes = int(diff_seconds / 60)
            return f"{minutes}m ago"
        elif diff_seconds < 86400:
            hours = int(diff_seconds / 3600)
            return f"{hours}h ago"
        elif diff_seconds < 604800:
            days = int(diff_seconds / 86400)
            return f"{days}d ago"
        else:
            weeks = int(diff_seconds / 604800)
            return f"{weeks}w ago"
    except:
        return "recently"


def render_forum_widget(forum_tools, user_language: str = 'en'):
    """
    Render compact forum widget for sidebar or dashboard
    
    Args:
        forum_tools: ForumTools instance
        user_language: User's preferred language
    """
    st.markdown("### 👥 Community Forum")
    
    # Get recent posts
    result = forum_tools.get_posts(limit=3)
    
    if result['success'] and result['posts']:
        for post in result['posts']:
            with st.container():
                st.markdown(f"**{post['title'][:50]}...**")
                st.caption(f"💬 {post.get('replies_count', 0)} replies • 👍 {post.get('likes_count', 0)} likes")
                st.markdown("---")
        
        if st.button("View All Discussions", use_container_width=True):
            st.session_state['active_page'] = 'forum'
            st.rerun()
    else:
        st.info("No recent discussions")
