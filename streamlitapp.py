import streamlit as st
import requests

# Backend API URLs
PROCESS_VIDEO_URL = "http://localhost:8000/process-video"
ASK_QUESTION_URL = "http://localhost:8000/ask-question"

st.title("YouTube Video Talker Chatbot")

# Sidebar for video processing
st.sidebar.header("Process YouTube Video")
youtube_url = st.sidebar.text_input("Enter YouTube Video URL:")
if st.sidebar.button("Process Video"):
    if youtube_url:
        with st.spinner("Processing video..."):
            response = requests.post(PROCESS_VIDEO_URL, data={"youtube_url": youtube_url})
            if response.status_code == 200:
                st.sidebar.success("Video processed successfully. You can now ask questions.")
            else:
                st.sidebar.error(f"Error: {response.json().get('detail', 'Unknown error')}")
    else:
        st.sidebar.error("Please enter a YouTube video URL.")

# Chat interface
st.header("Chat with the YouTube Video")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def display_chat():
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.write(f"*You:* {chat['content']}")
        elif chat["role"] == "assistant":
            st.write(f"*Bot:* {chat['content']}")

# Input for user question
user_question = st.text_input("Ask a question:")
if st.button("Send"):
    if user_question:
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        with st.spinner("Fetching response..."):
            response = requests.post(ASK_QUESTION_URL, data={"question": user_question})
            if response.status_code == 200:
                bot_response = response.json().get("response", "No response received.")
                st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
            else:
                bot_response = f"Error: {response.json().get('detail', 'Unknown error')}"
                st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
    else:
        st.error("Please enter a question.")

# Display chat history
display_chat()