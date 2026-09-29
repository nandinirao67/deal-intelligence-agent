import streamlit as st
from backend import (
    hindsight_service,
    setup_deal_bank,
    store_deal_note,
    recall_deal_memories,
    generate_sales_response
)

# --- 1. PAGE CONFIG & STATE INITIALIZATION ---
st.set_page_config(
    page_title="DealDNA | Sales Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "hindsight_service_started" not in st.session_state:
    hindsight_service.start()
    st.session_state.hindsight_service_started = True

BANK_ID = "sarah_techflow"

if "initialized" not in st.session_state:
    setup_deal_bank(BANK_ID, "Sarah Jenkins", "TechFlow")
    store_deal_note(BANK_ID, "Sarah is VP of Engineering at TechFlow.", "Discovery")
    store_deal_note(BANK_ID, "Main objection: budget is tight.", "Call 1")
    store_deal_note(BANK_ID, "She is comparing us to Competitor X.", "Call 2")
    store_deal_note(BANK_ID, "Her CTO must approve purchases. Needs a one-pager.", "Call 3")
    st.session_state.initialized = True

# --- 2. CUSTOM CSS FOR A PREMIUM UI ---
st.markdown("""
<style>
    /* Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1e293b;
    }

    /* Hide default Streamlit elements for a cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main Background */
    .stApp {
        background-color: #f8fafc;
    }

    /* Split Screen Layout */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Custom Memory Card */
    .memory-card {
        background-color: #ffffff;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .memory-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .memory-tag {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        color: #6366f1;
        margin-bottom: 4px;
        display: block;
    }
    .memory-text {
        font-size: 14px;
        color: #334155;
        line-height: 1.5;
    }

    /* Chat Bubbles */
    .stChatMessage {
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #eef2ff;
        border-color: #c7d2fe;
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #ffffff;
    }

    /* Headers */
    h1 {
        color: #0f172a;
        font-weight: 700;
        font-size: 2rem !important;
    }
    h3 {
        color: #475569;
        font-weight: 600;
        font-size: 1.1rem !important;
        margin-top: 1rem;
    }

    /* Buttons */
    .stButton>button {
        background-color: #6366f1;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
        font-weight: 600;
        transition: background-color 0.2s;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #4f46e5;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR: MEMORY DASHBOARD ---
with st.sidebar:
    st.markdown("### 🧬 DealDNA")
    st.caption("Persistent Memory Engine")
    st.divider()
    
    memories = recall_deal_memories(BANK_ID, "deal information")
    
    # Metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Memories", value=len(memories) if memories else 0)
    with col2:
        st.metric(label="Deal Stage", value="Discovery")
    
    st.divider()
    st.markdown("### 📌 Memory Bank")
    
    if memories:
        for i, mem in enumerate(memories, 1):
            st.markdown(
                f'<div class="memory-card">'
                f'<span class="memory-tag">Memory {i}</span>'
                f'<div class="memory-text">{mem.text}</div>'
                f'</div>', 
                unsafe_allow_html=True
            )
    else:
        st.info("No memories stored yet.")
    
    st.divider()
    st.markdown("### ➕ Add Context")
    new_note = st.text_area("Paste a call transcript or note:", height=100, placeholder="e.g., Call 4: Sarah mentioned budget review is next Tuesday...")
    if st.button("Store in Memory", use_container_width=True):
        if new_note.strip():
            store_deal_note(BANK_ID, new_note, "Manual entry")
            st.success("✅ Stored! Refreshing...")
            st.rerun()

# --- 4. MAIN LAYOUT ---
# Create a two-column layout: 65% Chat, 35% Live Memory Trace
col_chat, col_memory = st.columns([2, 1])

with col_chat:
    st.title("💼 Deal Intelligence Agent")
    st.markdown("##### Powered by Hindsight Memory + Groq LLM")
    st.markdown("---")

    # Welcome message
    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        st.info("👋 **Welcome!** I'm your Deal Intelligence Agent. Ask me: *'What should I email Sarah today?'* and I'll draft a personalized email using my memory of the deal.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🧬"):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask for a follow-up email, deal summary, or strategy..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant", avatar="🧬"):
            with st.spinner("🧠 Recalling deal memories..."):
                result = generate_sales_response(BANK_ID, prompt)
            st.markdown(result["response"])
            
            # Show the "Memory Trace" to prove Hindsight is working
            with st.expander(f"📚 View {result['memory_count']} Memories Used"):
                st.markdown(result['memories_used'])

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["response"]
        })
        
        # Refresh to show any new memories in the sidebar
        st.rerun()

with col_memory:
    st.markdown("### 🔍 Live Memory Trace")
    st.caption("Real-time view of what the agent remembers from this interaction.")
    
    # This is where we show the most recent memories retrieved
    recent_memories = recall_deal_memories(BANK_ID, "most recent deal information")
    
    if recent_memories:
        for i, mem in enumerate(recent_memories[:3], 1): # Show top 3 recent
            st.markdown(
                f'<div class="memory-card" style="border-left-color: #10b981;">'
                f'<span class="memory-tag" style="color: #10b981;">Active Memory</span>'
                f'<div class="memory-text">{mem.text}</div>'
                f'</div>', 
                unsafe_allow_html=True
            )
    else:
        st.info("Waiting for the first memory to be retrieved...")
        
    st.markdown("---")
    st.markdown("#### 🎯 How it works")
    st.markdown("""
    1. **Recall:** Agent queries Hindsight for past context.
    2. **Generate:** Groq LLM drafts an email using the recalled memories.
    3. **Retain:** The new interaction is saved back to Hindsight.
    4. **Learn:** Next time, the agent is smarter.
    """)