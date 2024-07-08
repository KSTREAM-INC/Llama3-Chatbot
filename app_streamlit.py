import streamlit as st
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.embeddings import FastEmbedEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from utils.conversational_chain import LLMHandler
from utils.summary_chain import SummaryDocument
import config.chain_config as cfg
import os
import shutil

import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the LLM
if cfg.model_name != "llama3":
    llm = ChatOpenAI(model_name=cfg.model_name, temperature=cfg.temperature)
    embeddings = OpenAIEmbeddings(model=cfg.embeddings_model)
else:
    llm = Ollama(model="llama3")
    embeddings = FastEmbedEmbeddings()

FILE_TYPES = ['txt', 'pdf', 'docx', 'doc', 'csv']

# Ensure that all necessary directories exist
if not os.path.exists("temp"):
    os.makedirs("temp")

def clear_cache():
    keys = list(st.session_state.keys())
    for key in keys:
        st.session_state.pop(key)
    
    shutil.rmtree(cfg.VECTOR_STORE_DIR, ignore_errors=True)

# Streamlit UI components
st.set_page_config(page_title="Chat with Your Documents", layout="wide")
st.title("Chat with Your Documents")
st.sidebar.title("Upload Documents")

# Styling
st.markdown(
    """
    <style>
    .reportview-container {
        background: #f5f5f5;
    }
    .sidebar .sidebar-content {
        background: #e6f7ff;
    }
    .block-container {
        padding: 2rem;
    }
    </style>
    """, unsafe_allow_html=True
)

# Add instructions
st.sidebar.markdown("Upload a PDF or CSV file to summarize its content and chat with it.")

# File uploader
uploaded_file = st.sidebar.file_uploader("Upload a file", type=FILE_TYPES, on_change=clear_cache)

# Persistent state for chat history
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

if uploaded_file:
    # Save the uploaded file temporarily
    temp_file_path = f"temp/{uploaded_file.name}"
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Display file icon
    file_type_icon = "📄" if uploaded_file.type == "application/pdf" else "🗂️"
    st.sidebar.success(f"{file_type_icon} Document uploaded successfully!")

    # Initialize the document summary handler and conversation handler
    summary_handler = SummaryDocument(llm, temp_file_path)
    conversation_handler = LLMHandler(
        llm, 
        temp_file_path, 
        embeddings
    )

    # Summarize the document
    if st.sidebar.button("Summarize Document"):
        st.header("Document Summary")
        with st.spinner("Summarizing the document..."):
            response_placeholder = st.empty()
            full_response = ""
            try:
                docs, sumchain = summary_handler.summarize()
                for chunk in sumchain.stream(docs):
                    full_response += chunk
                    response_placeholder.text(full_response)
                # st.write(summary)
            except Exception as e:
                st.error(f"Error during summarization: {str(e)}")

    # Chat with the document
    st.header("Chat with Your Document")
    user_input = st.text_input("Ask a question about the document:", key="user_input")
    
    if st.button("Send", key="send_button"):
        if user_input:
            with st.spinner("Generating response..."):
                response_placeholder = st.empty()
                full_response = ""
                try:
                    conchain = conversation_handler.create_chain()
                    for chunk in conchain.stream({"input": user_input, "chat_history": conversation_handler.chat_history}):
                        full_response += chunk
                        response_placeholder.text(full_response)

                    conversation_handler.chat_history.extend(
                        [
                            HumanMessage(content=user_input),
                            AIMessage(full_response),
                        ]
                    )
                    logger.info("Chat response generated successfully.")

                    st.session_state.chat_history.extend(conversation_handler.chat_history[-2:])
                except Exception as e:
                    st.error(f"Error during chat: {str(e)}")

    # Display chat history
    if st.session_state.chat_history:
        st.subheader("Chat History")
        for message in st.session_state.chat_history:
            if isinstance(message, HumanMessage):
                st.markdown(f"**You:** {message.content}")
            elif isinstance(message, AIMessage):
                st.markdown(f"**AI:** {message.content}")

else:
    st.sidebar.info("Please upload a document to get started.")

# # Display status messages and logs
# if 'status_messages' not in st.session_state:
#     st.session_state['status_messages'] = []

# if st.session_state.status_messages:
#     st.sidebar.subheader("Status")
#     for msg in st.session_state.status_messages:
#         st.sidebar.write(msg)
