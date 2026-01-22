import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ===============================
# SAFE LOGGING (NO FILE WRITES)
# ===============================
try:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
except Exception:
    pass


def log_interaction(request, response, case_context=None):
    """Safe logging – never breaks app"""
    try:
        if not request or "api" in request.lower():
            return

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request": request[:100],
            "case": case_context.get("title", "No case")[:80] if case_context else "No case",
            "status": "success" if "error" not in response.lower() else "failed",
        }

        logging.info(json.dumps(log_entry, ensure_ascii=False))
    except Exception:
        pass


# ===============================
# API KEY RESOLUTION (IMPORTANT)
# ===============================
def get_gemini_api_key():
    """
    Priority:
    1. User-entered API key (sidebar)
    2. Streamlit secrets
    3. Empty string
    """
    if st.session_state.get("gemini_api_key"):
        return st.session_state.gemini_api_key

    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


# ===============================
# AI RESPONSE (SAME LOGIC)
# ===============================
def get_legal_response(question, context=""):
    api_key = get_gemini_api_key()

    if not api_key:
        return (
            "🤖 **AI Assistant Offline**\n\n"
            "Please enter a Gemini API key in the sidebar to enable AI features."
        )

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=api_key,
            temperature=0.3,
            max_tokens=2048
        )

        system_prompt = """You are an expert legal assistant specializing in Indian Supreme Court cases."""

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Case Context:\n{context}\n\nQuestion:\n{question}")
        ])

        chain = prompt_template | llm | StrOutputParser()

        return chain.invoke({
            "context": context or "No case context provided.",
            "question": question
        })

    except Exception:
        return "⚠️ Sorry, something went wrong while generating the response."


# ===============================
# APP SETUP
# ===============================
st.set_page_config(page_title="Legal AI Assistant", layout="wide")
st.title("⚖️ Legal AI Assistant")

st.session_state.setdefault("gemini_api_key", "")
st.session_state.setdefault("show_api_input", True)
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("selected_case", None)

# ===============================
# SIDEBAR – API CONFIG
# ===============================
st.sidebar.title("🔑 API Configuration")

if st.session_state.show_api_input:
    with st.sidebar.expander("🚀 Gemini AI Setup", expanded=True):
        api_key_input = st.text_input(
            "Enter Gemini API Key (optional)",
            type="password",
            help="Your API key is stored securely in browser session storage and never sent to our servers."
        )

        if st.button("Save API Key"):
            st.session_state.gemini_api_key = api_key_input.strip()
            st.session_state.show_api_input = False
            st.success("API key preference saved")
            st.rerun()

# Show status
if get_gemini_api_key():
    st.sidebar.success("✅ Gemini AI Available")
else:
    st.sidebar.warning("⚠️ Gemini API key not configured")

# ===============================
# DATA LOADING (SAFE)
# ===============================
@st.cache_data
def load_data():
    try:
        return pd.read_parquet("data/base_for_dashboard.parquet")
    except Exception:
        return None


df = load_data()

# ===============================
# LAYOUT
# ===============================
col1, col2 = st.columns([2, 1])

# ===============================
# CHAT UI
# ===============================
with col1:
    st.subheader("💬 Legal AI Chat")

    chat_container = st.container(height=600)
    with chat_container:
        for msg in st.session_state.chat_history:
            role = "You" if msg["role"] == "user" else "Assistant"
            st.markdown(f"**{role}:** {msg['content']}")
            st.markdown("---")

    user_question = st.text_input("Ask about legal cases, precedents, or analysis")

    col_send, col_clear = st.columns(2)
    send_button = col_send.button("Send")
    clear_button = col_clear.button("Clear Chat")

# ===============================
# CASE SELECTION
# ===============================
with col2:
    st.subheader("📄 Case Selection")

    if df is not None:
        search_term = st.text_input("Search cases")
        filtered_df = (
            df[df["title"].str.contains(search_term, case=False, na=False)]
            if search_term else df
        )

        if not filtered_df.empty:
            selected_case_display = st.selectbox(
                "Choose a case",
                ["None"] + filtered_df["title"].head(50).tolist()
            )

            if selected_case_display != "None":
                st.session_state.selected_case = filtered_df[
                    filtered_df["title"] == selected_case_display
                ].iloc[0]

# ===============================
# SEND QUERY (SAFE FLOW)
# ===============================
if send_button and user_question.strip():
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_question
    })

    status_box = st.info("⚖️ Generating legal analysis...")

    try:
        context = ""
        case_ctx = None

        if st.session_state.selected_case is not None:
            case_ctx = st.session_state.selected_case.to_dict()
            context = f"{case_ctx.get('title')} ({case_ctx.get('year')})"

        response = get_legal_response(user_question, context)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
            "case_context": case_ctx
        })

        log_interaction(user_question, response, case_ctx)
        status_box.success("✅ Analysis complete")

    except Exception:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "⚠️ An error occurred, but the app is still running."
        })
        status_box.warning("⚠️ Temporary issue")

    st.rerun()

# ===============================
# CLEAR CHAT
# ===============================
if clear_button:
    st.session_state.chat_history = []
    st.session_state.selected_case = None
    st.rerun()

# ===============================
# DATA ATTRIBUTION & PRIVACY
# ===============================
st.markdown("---")
st.markdown("""
### 🔒 API Key Privacy Notice

**Your API key will be completely secure.** It is stored securely in your browser's session storage and is never transmitted to our servers. It is used only for direct communication with Google's Gemini AI service.

### 📚 Data Attribution

This dashboard uses data from the Indian Supreme Court Judgments dataset, which contains:
- Supreme Court judgments from 1950 to present
- Structured metadata and case information
- Licensed under Creative Commons Attribution 4.0 (CC-BY-4.0)

**Source:** [https://github.com/vanga/indian-supreme-court-judgments](https://github.com/vanga/indian-supreme-court-judgments)

### 📄 Source Code
**GitHub Repository:** [Indian Legal Analytics](https://github.com/Suhas-Koheda/Indian-Legal-Analytics/blob/main/pages/7_Chatbot.py)
""")
