"""
Chat interface components for Streamlit UI
Handles chat message display, history, and conversation management
"""

import streamlit as st
from typing import List, Dict, Any
from datetime import datetime
import json


def render_chat_message(message: Dict[str, Any], index: int, language: str) -> None:
    """
    Render a single chat message with speaker identification and timestamp
    
    Args:
        message: Message dictionary with role, content, timestamp
        index: Message index for unique keys
        language: Current language for TTS
    """
    role = message.get('role', 'user')
    content = message.get('content', '')
    timestamp = message.get('timestamp', '')
    agent_name = message.get('agent', 'AI Assistant')
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(timestamp)
        formatted_time = dt.strftime('%I:%M %p')
    except:
        formatted_time = timestamp
    
    if role == 'user':
        # User message (right-aligned, blue background)
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="message-header">👤 You</div>
            <div class="message-content">{content}</div>
            <div class="message-timestamp">{formatted_time}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Agent message (left-aligned, gray background)
        st.markdown(f"""
        <div class="chat-message agent-message">
            <div class="message-header">🤖 {agent_name}</div>
            <div class="message-content">{content}</div>
            <div class="message-timestamp">{formatted_time}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Audio playback button for agent responses
        from ui.voice_components import render_audio_playback
        render_audio_playback(content, language, f"msg_{index}_{timestamp}")


def render_chat_history(messages: List[Dict[str, Any]], language: str) -> None:
    """
    Render complete chat history with auto-scroll
    
    Args:
        messages: List of message dictionaries
        language: Current language for TTS
    """
    if not messages:
        st.info("💬 No messages yet. Start a conversation by typing or speaking!")
        return
    
    # Create a container for messages
    chat_container = st.container()
    
    with chat_container:
        for idx, message in enumerate(messages):
            render_chat_message(message, idx, language)
    
    # Auto-scroll to bottom (using JavaScript)
    st.markdown("""
    <script>
        var chatContainer = window.parent.document.querySelector('[data-testid="stVerticalBlock"]');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    </script>
    """, unsafe_allow_html=True)


def add_message_to_history(role: str, content: str, agent: str = None) -> None:
    """
    Add a message to chat history in session state
    
    Args:
        role: 'user' or 'agent'
        content: Message content
        agent: Agent name (for agent messages)
    """
    message = {
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat(),
    }
    
    if agent:
        message['agent'] = agent
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    st.session_state.chat_history.append(message)


def clear_chat_history() -> None:
    """Clear all chat history"""
    st.session_state.chat_history = []


def export_chat_history() -> str:
    """
    Export chat history as JSON string
    
    Returns:
        JSON string of chat history
    """
    if 'chat_history' not in st.session_state:
        return "[]"
    
    return json.dumps(st.session_state.chat_history, indent=2)


def render_chat_controls() -> None:
    """Render chat control buttons (clear, export, etc.)"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Clear Chat"):
            clear_chat_history()
            st.rerun()
    
    with col2:
        if st.button("💾 Export Chat"):
            chat_json = export_chat_history()
            st.download_button(
                label="Download JSON",
                data=chat_json,
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col3:
        message_count = len(st.session_state.get('chat_history', []))
        st.metric("Messages", message_count)


def render_typing_indicator() -> None:
    """Render typing indicator animation"""
    st.markdown("""
    <div class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
    </div>
    <style>
        .typing-indicator {
            display: flex;
            gap: 0.25rem;
            padding: 1rem;
        }
        .typing-indicator span {
            width: 0.5rem;
            height: 0.5rem;
            background-color: #999;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.7;
            }
            30% {
                transform: translateY(-0.5rem);
                opacity: 1;
            }
        }
    </style>
    """, unsafe_allow_html=True)


def get_conversation_summary() -> str:
    """
    Generate a brief summary of the conversation
    
    Returns:
        Summary string
    """
    messages = st.session_state.get('chat_history', [])
    
    if not messages:
        return "No conversation yet"
    
    user_messages = [m for m in messages if m['role'] == 'user']
    agent_messages = [m for m in messages if m['role'] == 'agent']
    
    return f"{len(user_messages)} user messages, {len(agent_messages)} agent responses"


def render_conversation_stats() -> None:
    """Render conversation statistics"""
    messages = st.session_state.get('chat_history', [])
    
    if not messages:
        return
    
    user_count = len([m for m in messages if m['role'] == 'user'])
    agent_count = len([m for m in messages if m['role'] == 'agent'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Your Messages", user_count)
    with col2:
        st.metric("Agent Responses", agent_count)
    with col3:
        st.metric("Total", len(messages))
