import streamlit as st
from backend import (
    hindsight_service,
    setup_deal_bank,
    store_deal_note,
    recall_deal_memories,
    generate_sales_response
)

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Deal Intelligence Agent",
    page_icon="💼",
    layout="wide"
)

# --- INITIALIZE SERVICE & DATA ---
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

# --- SIDEBAR: MEMORY DASHBOARD ---
with st.sidebar:
    st.markdown("## 🧬 DealDNA")
    st.caption("Persistent Memory Engine")
    st.divider()
    
    memories = recall_deal_memories(BANK_ID, "deal information")
    
    # Dashboard Metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Memories", value=len(memories) if memories else 0)
    with col2:
        st.metric(label="Deal Stage", value="Discovery")
    
    st.divider()
    st.markdown("### 📌 Memory Bank")
    
    if memories:
        for i, mem in enumerate(memories[:5], 1): # Show top 5
            with st.container(border=True):
                st.caption(f"Memory #{i}")
                st.write(mem.text)
    else:
        st.info("No memories stored yet.")
    
    st.divider()
    st.markdown("### ➕ Add Context")
    new_note = st.text_area("Paste a call note:", height=80)
    if st.button("Store in Memory", use_container_width=True):
        if new_note.strip():
            store_deal_note(BANK_ID, new_note, "Manual entry")
            st.success("✅ Stored!")
            st.rerun()

# --- MAIN LAYOUT ---
col_chat, col_memory = st.columns([2, 1])

with col_chat:
    st.title("💼 Deal Intelligence Agent")
    st.caption("Powered by Hindsight Persistent Memory + Groq LLM")
    st.markdown("---")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if len(st.session_state.messages) == 0:
        st.info("👋 **Welcome!** Ask me: *'What should I email Sarah today?'*")

    for msg in st.session_state.messages:
        avatar = "👤" if msg["role"] == "user" else "🧬"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask for a follow-up email..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🧬"):
            with st.spinner("🧠 Recalling deal memories..."):
                result = generate_sales_response(BANK_ID, prompt)
            st.markdown(result["response"])
            with st.expander(f"📚 View {result['memory_count']} Memories Used"):
                st.markdown(result['memories_used'])

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["response"]
        })
        st.rerun()

with col_memory:
    st.markdown("### 🔍 Live Memory Trace")
    st.caption("Real-time view of what the agent recalls.")
    
    recent_memories = recall_deal_memories(BANK_ID, "most recent deal information")
    
    if recent_memories:
        for mem in recent_memories[:3]: # Show top 3 active memories
            with st.container(border=True):
                st.markdown("**Active Memory**")
                st.write(mem.text)
    else:
        st.info("Waiting for the first memory...")
    
    st.markdown("---")
    st.markdown("#### 🎯 How it works")
    st.markdown("""
    1. **Recall:** Agent queries Hindsight for past context.
    2. **Generate:** Groq LLM drafts an email using the memories.
    3. **Retain:** The new interaction is saved back to Hindsight.
    """)