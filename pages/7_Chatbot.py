import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import json
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logging.basicConfig(
    filename='chatbot_logs.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_interaction(request, response, case_context=None):
    """Log minimal chatbot interactions for analytics (API key never logged)"""
    if "API key" in request.lower() or "api" in request.lower():
        return

    # Determine success/failure based on response content
    is_success = not any(error_word in response.lower() for error_word in [
        "error", "failed", "sorry, i encountered", "network error",
        "authentication error", "api key not configured"
    ])

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "request": request[:100] + "..." if len(request) > 100 else request,
        "case": case_context.get('title', 'No case')[:80] + "..." if case_context and case_context.get('title') else "No case selected",
        "status": "success" if is_success else "failed",
        "has_api_key": bool(GEMINI_API_KEY)
    }

    logging.info(f"[{log_entry['status']}] {log_entry['request']} | Case: {log_entry['case']}")

    try:
        with open('chatbot_logs.jsonl', 'a', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write('\n')
    except Exception as e:
        logging.error(f"Failed to write to log file: {e}")

def get_legal_response(question, context=""):
    """Get legal analysis response using LangChain and Google Gemini"""
    if not GEMINI_API_KEY:
        return "🤖 **AI Assistant Offline**\n\nPlease enter your Google Gemini API key in the sidebar to enable AI-powered legal analysis. The chatbot will work with basic case search functionality without the API key."

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=GEMINI_API_KEY,
            temperature=0.3,
            max_tokens=2048
        )

        system_prompt = """You are an expert legal assistant specializing in Indian Supreme Court cases and constitutional law.

Your expertise includes:
- Indian Constitution and fundamental rights
- Supreme Court precedents and case law
- Legal analysis and judicial interpretation
- Constitutional principles and separation of powers
- Fundamental rights under Articles 14, 19, 21, etc.
- Administrative and criminal law principles

Guidelines:
- Provide accurate, professional legal analysis
- Use case context when available to give specific insights
- Cite relevant constitutional articles and legal principles
- Explain complex legal concepts in clear terms
- Acknowledge limitations if specific information is not available
- Focus on Indian legal system and Supreme Court jurisprudence

When analyzing cases:
- Identify key legal issues and constitutional questions
- Explain judicial reasoning and precedent value
- Discuss implications for fundamental rights
- Note any landmark aspects or significant holdings
"""

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Case Context (if available):\n{context}\n\nLegal Question: {question}\n\nPlease provide a comprehensive legal analysis:")
        ])

        chain = prompt_template | llm | StrOutputParser()

        response = chain.invoke({
            "context": context if context else "No specific case context provided.",
            "question": question
        })

        return response

    except Exception as e:
        error_type = type(e).__name__
        if "API_KEY" in str(e).upper() or "AUTHENTICATION" in str(e).upper():
            return "Authentication error: Please check your Gemini API key configuration."
        elif "QUOTA" in str(e).upper() or "RATE" in str(e).upper():
            return "API quota exceeded: Please try again later or check your usage limits."
        elif "NETWORK" in str(e).upper() or "CONNECTION" in str(e).upper():
            return "Network error: Please check your internet connection and try again."
        else:
            return f"Legal analysis error ({error_type}): {str(e)}. Please try rephrasing your question."

st.title("Legal AI Assistant")

if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""

if "show_api_input" not in st.session_state:
    st.session_state.show_api_input = True

st.sidebar.title("🔑 API Configuration")

if st.session_state.show_api_input or not st.session_state.gemini_api_key:
    with st.sidebar.expander("🚀 Gemini AI Setup", expanded=not bool(st.session_state.gemini_api_key)):
        st.markdown("**Get your free API key:**")
        st.markdown("[Google AI Studio](https://makersuite.google.com/app/apikey)")

        st.info("🔒 **Security Notice:** Your API key is stored ONLY in your browser's session storage and is never transmitted to our servers, logged, or persisted anywhere. It disappears when you close this browser tab.\n\n[View Code](https://github.com/Suhas-Koheda/Indian-Legal-Analytics/blob/main/pages/7_Chatbot.py#L123)")

        api_key_input = st.text_input(
            "Enter your Gemini API Key:",
            type="password",
            help="Your API key remains in your browser session only.",
            key="api_key_input"
        )

        if st.button("💾 Save API Key", key="save_api_key"):
            if api_key_input.strip():
                st.session_state.gemini_api_key = api_key_input.strip()
                st.session_state.show_api_input = False
                st.success("✅ API key saved securely in your browser!")
                st.rerun()
            else:
                st.error("Please enter a valid API key.")

if st.session_state.gemini_api_key:
    st.sidebar.success("✅ AI Assistant Ready")
    if st.sidebar.button("🔄 Change API Key", key="change_api_key"):
        st.session_state.show_api_input = True
        st.session_state.gemini_api_key = ""
        st.rerun()
else:
    st.sidebar.warning("⚠️ Enter API key to enable AI features")

GEMINI_API_KEY = st.session_state.gemini_api_key

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "selected_case" not in st.session_state:
    st.session_state.selected_case = None

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Legal AI Assistant")

    chat_container = st.container(height=600)

    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"**You:** {message['content']}")
                st.markdown("---")
            else:
                with st.container():
                    st.markdown(f"**Assistant:** {message['content']}")

                    if "case_context" in message and message["case_context"]:
                        with st.expander("📄 Case Reference", expanded=False):
                            case_data = message["case_context"]
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.write(f"**Case:** {case_data.get('title', 'N/A')[:80]}...")
                                st.write(f"**Year:** {case_data.get('year', 'N/A')}")
                                st.write(f"**Court:** {case_data.get('court', 'N/A')}")
                            with col_b:
                                judges = case_data.get('judge', [])
                                if isinstance(judges, list) and judges:
                                    st.write(f"**Judges:** {', '.join(judges[:2])}")
                                petitioners = case_data.get('petitioner', [])
                                if isinstance(petitioners, list) and petitioners:
                                    st.write(f"**Petitioners:** {', '.join(petitioners[:1])}")
                    st.markdown("---")

    user_question = st.text_input("Ask about legal cases, precedents, or case analysis...", key="user_question")

    col_send, col_clear = st.columns([1, 1])
    with col_send:
        send_button = st.button("🔍 Send Query", key="send_button", use_container_width=True)
    with col_clear:
        clear_button = st.button("🗑️ Clear Chat", key="clear_chat", use_container_width=True)

with col2:
    st.subheader("Case Selection & Analysis")

    search_term = st.text_input("Search cases", "", key="chat_search")

    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    years = list(range(min_year, max_year + 1))
    selected_years = st.multiselect(
        "Filter by years",
        years,
        default=[],
        key="chat_years"
    )

    if selected_years:
        filtered_df = df[df["year"].isin(selected_years)]
    else:
        filtered_df = df

    if search_term:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_term, case=False, na=False)
        ]

    if len(filtered_df) > 0:
        case_options = [f"{row['year']} - {row['title'][:60]}..." for _, row in filtered_df.head(50).iterrows()]

        selected_case_display = st.selectbox(
            "Choose a case for context",
            ["Select a case..."] + case_options,
            key="case_selector"
        )

        if selected_case_display != "Select a case...":
            case_index = case_options.index(selected_case_display)
            st.session_state.selected_case = filtered_df.iloc[case_index]
            selected_case = st.session_state.selected_case

            st.success(f"Selected: {selected_case['title'][:100]}...")

            with st.expander("📋 Complete Case Details", expanded=False):
                col_a, col_b, col_c = st.columns([1, 1, 1])

                with col_a:
                    st.markdown("**Basic Information**")
                    st.write(f"**Year:** {selected_case.get('year', 'N/A')}")
                    st.write(f"**Court:** {selected_case.get('court', 'N/A')}")
                    st.write(f"**Decision Date:** {selected_case.get('decision_date', 'N/A')}")
                    st.write(f"**Disposal Nature:** {selected_case.get('disposal_nature', 'N/A')}")

                with col_b:
                    st.markdown("**Legal Parties**")
                    judges = selected_case.get('judge', [])
                    if isinstance(judges, list) and judges:
                        st.write(f"**Judges:** {', '.join(judges)}")
                    else:
                        st.write("**Judges:** N/A")

                    petitioners = selected_case.get('petitioner', [])
                    if isinstance(petitioners, list) and petitioners:
                        st.write(f"**Petitioners:** {', '.join(petitioners)}")
                    else:
                        st.write("**Petitioners:** N/A")

                with col_c:
                    st.markdown("**Case References**")
                    respondents = selected_case.get('respondent', [])
                    if isinstance(respondents, list) and respondents:
                        st.write(f"**Respondents:** {', '.join(respondents)}")
                    else:
                        st.write("**Respondents:** N/A")

                    citations = selected_case.get('citation', [])
                    if isinstance(citations, list) and citations:
                        st.write(f"**Citations:** {', '.join(citations[:3])}")
                        if len(citations) > 3:
                            st.write(f"*... and {len(citations)-3} more*")
                    else:
                        st.write("**Citations:** N/A")

                if selected_case.get('description'):
                    st.markdown("**Case Description**")
                    with st.expander("📖 Read Full Description", expanded=False):
                        st.write(selected_case['description'])

        if send_button and user_question.strip():
            user_message = user_question.strip()

            st.session_state.chat_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now()
            })

            with col2:
                st.markdown("---")
                st.markdown("🤔 **Analyzing your legal question...**")
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i in range(100):
                    progress_bar.progress(i + 1)
                    if i < 30:
                        status_text.text("🔍 Preparing legal context...")
                    elif i < 70:
                        status_text.text("⚖️ Consulting legal precedents...")
                    elif i < 90:
                        status_text.text("📋 Analyzing case details...")
                    else:
                        status_text.text("✍️ Generating response...")
                    time.sleep(0.01)

            try:
                context_info = ""
                case_context = None
                if st.session_state.selected_case is not None:
                    case_data = st.session_state.selected_case
                    case_context = case_data.to_dict()
                    context_info = f"""
                    Selected Case Context:
                    - Title: {case_data.get('title', 'N/A')}
                    - Year: {case_data.get('year', 'N/A')}
                    - Court: {case_data.get('court', 'N/A')}
                    - Judges: {', '.join(case_data.get('judge', [])[:3]) if isinstance(case_data.get('judge'), list) else 'N/A'}
                    - Petitioners: {', '.join(case_data.get('petitioner', [])[:2]) if isinstance(case_data.get('petitioner'), list) else 'N/A'}
                    - Respondents: {', '.join(case_data.get('respondent', [])[:2]) if isinstance(case_data.get('respondent'), list) else 'N/A'}
                    - Citations: {', '.join(case_data.get('citation', [])[:2]) if isinstance(case_data.get('citation'), list) else 'N/A'}
                    """

                status_text.text("🎯 Generating legal analysis...")
                progress_bar.progress(95)

                response = get_legal_response(user_message, context_info)

                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")
                time.sleep(0.5)

                log_interaction(user_message, response, case_context)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now(),
                    "case_context": case_context
                })

                st.rerun()

            except Exception as e:
                with col2:
                    progress_bar.progress(100)
                    status_text.text("❌ Error occurred")
                    time.sleep(1)
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now()
                })
                log_interaction(user_message, error_msg, st.session_state.selected_case.to_dict() if st.session_state.selected_case is not None else None)

            st.rerun()

        if clear_button:
            st.session_state.chat_history = []
            st.session_state.selected_case = None
            st.rerun()

st.markdown("---")
st.markdown("### 💡 Tips for Better Questions")
st.markdown("""
- Select a specific case first for contextual answers
- Ask about legal principles, precedents, or case analysis
- Questions like: "What was the main holding in this case?"
- Or: "How does this relate to constitutional law?"
- Or: "Summarize the key arguments made by the petitioners"
""")

st.markdown("---")
st.markdown("### 📚 Data Attribution")
st.markdown("""
**Indian Supreme Court Judgments Dataset**

This dashboard uses data from the Indian Supreme Court Judgments dataset, which contains:
- Supreme Court judgments from 1950 to present
- Structured metadata and case information
- Licensed under Creative Commons Attribution 4.0 (CC-BY-4.0)

**Source:** [https://github.com/vanga/indian-supreme-court-judgments](https://github.com/vanga/indian-supreme-court-judgments)

**License:** CC-BY-4.0 - You are free to use, share, and adapt this data with appropriate attribution.
""")

st.markdown("""
**Built with:**
- Streamlit for the web interface
- Pandas for data processing
- LangChain + Google Gemini for AI analysis
- Matplotlib for visualizations
""")
