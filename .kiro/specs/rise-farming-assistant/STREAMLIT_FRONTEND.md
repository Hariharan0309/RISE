# Streamlit Frontend for RISE

## Why Streamlit?

Streamlit is perfect for RISE because:
- **Fast Development**: Build UI in pure Python, no HTML/CSS/JavaScript needed
- **Simple for Hackathons**: Get a working demo quickly
- **Built-in Components**: Chat interface, file uploads, forms all included
- **Auto-Responsive**: Works on mobile and desktop automatically
- **Easy Deployment**: Deploy to Streamlit Community Cloud for free

## Basic RISE App Structure

```python
# app.py
import streamlit as st
from strands import Agent
from agents.orchestrator import create_orchestrator_agent

# Page config
st.set_page_config(
    page_title="RISE - Farming Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize agent (cached)
@st.cache_resource
def get_agent():
    return create_orchestrator_agent()

agent = get_agent()

# Sidebar
with st.sidebar:
    st.title("🌾 RISE")
    st.caption("Rural Innovation & Sustainable Ecosystem")
    
    # Language selector
    language = st.selectbox(
        "Language / भाषा",
        ["English", "हिंदी (Hindi)", "தமிழ் (Tamil)", "తెలుగు (Telugu)", 
         "ಕನ್ನಡ (Kannada)", "বাংলা (Bengali)", "ગુજરાતી (Gujarati)", 
         "मराठी (Marathi)", "ਪੰਜਾਬੀ (Punjabi)"]
    )
    
    # User profile
    st.divider()
    farmer_name = st.text_input("Your Name", "Ravi Kumar")
    location = st.text_input("Location", "Punjab")
    land_size = st.number_input("Land Size (acres)", 1, 100, 2)

# Main chat interface
st.title("💬 Chat with RISE")
st.caption("Ask me anything about farming, crops, weather, markets, and more!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask your farming question..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = agent(prompt)
            st.markdown(response)
    
    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})
```

## Key Streamlit Components for RISE

### 1. Chat Interface
```python
# Chat messages
with st.chat_message("user"):
    st.markdown("What crops should I plant?")

with st.chat_message("assistant"):
    st.markdown("Based on your soil type...")

# Chat input
prompt = st.chat_input("Type your message...")
```

### 2. Image Upload (Crop Diagnosis)
```python
# Image uploader
uploaded_file = st.file_uploader(
    "Upload crop image for diagnosis",
    type=["jpg", "jpeg", "png"],
    help="Take a clear photo of the affected crop"
)

if uploaded_file:
    # Display image
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    
    # Analyze with agent
    with st.spinner("Analyzing crop..."):
        # Save to temp file and send to agent
        diagnosis = crop_agent.analyze_image(uploaded_file)
        
        # Show results
        if diagnosis['severity'] == 'high':
            st.error(f"⚠️ {diagnosis['disease']} detected!")
        else:
            st.warning(f"⚠️ {diagnosis['disease']} detected")
        
        st.info(f"**Treatment:** {diagnosis['treatment']}")
```

### 3. Voice Input/Output
```python
# Voice input (Streamlit 1.28+)
audio_input = st.audio_input("Record your question")

if audio_input:
    # Send to transcription tool
    with st.spinner("Transcribing..."):
        text = transcribe_tool(audio_input)
        st.write(f"You said: {text}")
        
        # Get response
        response = agent(text)
        
        # Convert to speech
        audio_response = synthesize_tool(response, language="hi")
        st.audio(audio_response)
```

### 4. Forms (Equipment Booking, Scheme Application)
```python
with st.form("equipment_booking"):
    st.subheader("Book Equipment")
    
    equipment_type = st.selectbox("Equipment", ["Tractor", "Harvester", "Pump"])
    start_date = st.date_input("Start Date")
    duration = st.number_input("Duration (days)", 1, 30, 1)
    
    submitted = st.form_submit_button("Book Now")
    
    if submitted:
        with st.spinner("Booking..."):
            result = booking_tool(equipment_type, start_date, duration)
            st.success(f"✅ Booked! Total: ₹{result['cost']}")
```

### 5. Data Display (Market Prices, Schemes)
```python
# Dataframe with highlighting
import pandas as pd

prices_df = pd.DataFrame({
    'Crop': ['Wheat', 'Rice', 'Cotton'],
    'Price (₹/quintal)': [2500, 3200, 6800],
    'Change': ['+5%', '-2%', '+8%']
})

st.dataframe(
    prices_df,
    use_container_width=True,
    hide_index=True
)

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Wheat Price", "₹2,500", "+5%")
col2.metric("Rice Price", "₹3,200", "-2%")
col3.metric("Cotton Price", "₹6,800", "+8%")
```

### 6. Charts (Price Trends, Analytics)
```python
import pandas as pd

# Line chart for price trends
price_history = pd.DataFrame({
    'Date': pd.date_range('2024-01-01', periods=30),
    'Wheat': [2400, 2420, 2450, ...],
    'Rice': [3100, 3150, 3200, ...]
})

st.line_chart(price_history.set_index('Date'))

# Or use Plotly for interactive charts
import plotly.express as px

fig = px.line(price_history, x='Date', y=['Wheat', 'Rice'])
st.plotly_chart(fig, use_container_width=True)
```

### 7. Tabs (Different Features)
```python
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "🌾 Diagnosis", "📊 Market", "🤝 Community"])

with tab1:
    # Chat interface
    st.chat_input("Ask anything...")

with tab2:
    # Crop diagnosis
    st.file_uploader("Upload crop image")

with tab3:
    # Market prices
    st.dataframe(prices_df)

with tab4:
    # Forum
    st.text_area("Share your farming tip...")
```

### 8. Sidebar Navigation
```python
with st.sidebar:
    st.title("🌾 RISE")
    
    page = st.radio(
        "Navigate",
        ["🏠 Home", "🌾 Crop Diagnosis", "📊 Market Prices", 
         "🤝 Community", "💰 Financial Planning"]
    )
    
    st.divider()
    
    # User info
    st.caption("Logged in as:")
    st.write(f"👤 {farmer_name}")
    st.write(f"📍 {location}")
```

### 9. Loading States
```python
# Spinner
with st.spinner("Analyzing your query..."):
    response = agent(query)

# Progress bar
progress_bar = st.progress(0)
for i in range(100):
    progress_bar.progress(i + 1)
    time.sleep(0.01)

# Status
with st.status("Processing...", expanded=True) as status:
    st.write("Fetching weather data...")
    time.sleep(1)
    st.write("Analyzing soil conditions...")
    time.sleep(1)
    status.update(label="Complete!", state="complete")
```

### 10. Notifications
```python
# Success
st.success("✅ Booking confirmed!")

# Info
st.info("ℹ️ Weather alert: Rain expected tomorrow")

# Warning
st.warning("⚠️ Moderate pest infestation detected")

# Error
st.error("❌ Failed to connect to server")

# Toast (temporary notification)
st.toast("Message sent!", icon="✅")
```

## Multi-Page App Structure

For a more organized app, use Streamlit's multi-page feature:

```
rise-app/
├── app.py                    # Main page (Chat)
├── pages/
│   ├── 1_🌾_Crop_Diagnosis.py
│   ├── 2_📊_Market_Prices.py
│   ├── 3_🤝_Community.py
│   ├── 4_💰_Financial_Planning.py
│   └── 5_📈_Analytics.py
├── agents/
│   ├── orchestrator.py
│   ├── crop_diagnosis.py
│   ├── market_agent.py
│   └── ...
└── tools/
    ├── voice_tools.py
    ├── translation_tools.py
    └── ...
```

Each page is a separate Python file that runs independently.

## Caching for Performance

```python
# Cache data that doesn't change often
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_market_prices():
    return market_agent.get_prices()

# Cache resources (agents, models)
@st.cache_resource
def load_agent():
    return Agent(...)

# Clear cache button
if st.button("Refresh Data"):
    st.cache_data.clear()
```

## Session State Management

```python
# Initialize session state
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "name": "",
        "location": "",
        "land_size": 0
    }

# Update session state
st.session_state.user_profile["name"] = st.text_input("Name")

# Access session state
st.write(f"Welcome, {st.session_state.user_profile['name']}!")
```

## Deployment

### Option 1: Streamlit Community Cloud (Free)
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Deploy!

### Option 2: AWS EC2
```bash
# Install Streamlit on EC2
pip install streamlit

# Run app
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Or use systemd for production
```

### Option 3: Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Styling

```python
# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f0f8f0;
    }
    .stChatMessage {
        background-color: white;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Theme (config.toml)
[theme]
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F8F0"
textColor = "#262730"
font = "sans serif"
```

## Best Practices for RISE

1. **Use st.cache_resource for agents** - Load once, reuse
2. **Use st.cache_data for API calls** - Reduce latency
3. **Session state for user data** - Maintain context
4. **Tabs for organization** - Keep UI clean
5. **Spinners for long operations** - Show progress
6. **Forms for complex inputs** - Better UX
7. **Metrics for key numbers** - Visual impact
8. **Expanders for details** - Reduce clutter

## Example: Complete Crop Diagnosis Page

```python
# pages/1_🌾_Crop_Diagnosis.py
import streamlit as st
from agents.crop_diagnosis import crop_diagnosis_agent

st.title("🌾 Crop Disease Diagnosis")
st.caption("Upload a photo of your crop for instant diagnosis")

# Image upload
uploaded_file = st.file_uploader(
    "Choose an image",
    type=["jpg", "jpeg", "png"],
    help="Take a clear, well-lit photo of the affected area"
)

if uploaded_file:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Uploaded Image")
        st.image(uploaded_file, use_column_width=True)
    
    with col2:
        st.subheader("Diagnosis")
        
        with st.spinner("Analyzing..."):
            # Get diagnosis from agent
            result = crop_diagnosis_agent(uploaded_file)
            
            # Display results
            if result['severity'] == 'high':
                st.error(f"⚠️ **{result['disease']}** (Severe)")
            elif result['severity'] == 'medium':
                st.warning(f"⚠️ **{result['disease']}** (Moderate)")
            else:
                st.info(f"ℹ️ **{result['disease']}** (Mild)")
            
            st.metric("Confidence", f"{result['confidence']}%")
            
            st.divider()
            
            st.subheader("💊 Treatment")
            st.write(result['treatment'])
            
            st.subheader("🛡️ Prevention")
            st.write(result['prevention'])
            
            # Save to history
            if st.button("Save to History"):
                # Save to DynamoDB
                st.success("✅ Saved to your diagnosis history!")
```

This Streamlit approach will get your RISE demo up and running much faster than React.js!
