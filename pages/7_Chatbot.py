import streamlit as st
import pandas as pd
from datetime import datetime
import cache_utils
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

st.set_page_config(page_title="Legal AI Assistant", layout="wide")
st.title("⚖️ Legal AI Assistant")

st.session_state.setdefault("gemini_api_key", "")
st.session_state.setdefault("show_api_input", True)
st.session_state.setdefault("chat_history", [])

def get_gemini_api_key():
    """
    Priority:
    1. User-entered API key (sidebar)
    2. Streamlit secrets
    3. Hugging Face secrets
    4. Environment variable
    5. Empty string
    """
    if st.session_state.get("gemini_api_key"):
        return st.session_state.gemini_api_key

    try:
        if st.secrets.get("GEMINI_API_KEY"):
            return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    
    try:
        import os
        hf_gemini_key = os.environ.get("HF_GEMINI_API_KEY")
        if hf_gemini_key:
            return hf_gemini_key
    except Exception:
        pass
    
    import os
    return os.environ.get("GEMINI_API_KEY", "")

def get_legal_response(question, context=""):
    api_key = get_gemini_api_key()

    if not api_key:
        return (
            "🤖 **AI Assistant Offline**\n\n"
            "Please enter a Gemini API key in the sidebar to enable AI features."
        )

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
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

    except Exception as e:
        return f"⚠️ Sorry, something went wrong while generating the response: {str(e)}"

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

if get_gemini_api_key():
    st.sidebar.success("✅ Gemini AI Available")
else:
    st.sidebar.warning("⚠️ Gemini API key not configured")

@st.cache_data(ttl=1800)
def load_data(years=None):
    """
    Load data from S3 using cache_utils.
    TTL: 30 minutes - data doesn't change frequently.
    Using st.cache_data because DataFrame is serializable.
    """
    return cache_utils.get_combined_metadata(years)

df = load_data()

col1, col2 = st.columns([2, 1])

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

with col2:
    st.subheader("📄 Case Selection")

    if df is not None and len(df) > 0:
        search_term = st.text_input("Search cases", key="chatbot_case_search")
        
        if search_term:
            import search
            filtered_df = search.search_cases(df, search_term)
        else:
            filtered_df = df.head(50)

        if not filtered_df.empty:
            case_options = ["None"] + filtered_df["title"].head(50).tolist()
            selected_case_display = st.selectbox(
                "Choose a case",
                case_options,
                key="chatbot_case_select"
            )

            if selected_case_display != "None":
                case_row = filtered_df[filtered_df["title"] == selected_case_display]
                if not case_row.empty:
                    st.session_state.selected_case = case_row.iloc[0]
    else:
        st.info("Case data not available")

if send_button and user_question.strip():
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_question
    })

    status_box = st.info("⚖️ Generating legal analysis...")

    try:
        context = ""
        case_ctx = None

        if st.session_state.get("selected_case") is not None:
            case_ctx = st.session_state.selected_case.to_dict()
            context = f"{case_ctx.get('title', 'Unknown')} ({case_ctx.get('year', 'Unknown')})"

        response = get_legal_response(user_question, context)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
            "case_context": case_ctx
        })

        status_box.success("✅ Analysis complete")

    except Exception as e:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"⚠️ An error occurred: {str(e)}"
        })
        status_box.warning("⚠️ Temporary issue")

    st.rerun()

if clear_button:
    st.session_state.chat_history = []
    if "selected_case" in st.session_state:
        del st.session_state.selected_case
    st.rerun()

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
""")
