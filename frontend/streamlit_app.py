import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load configuration
load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Streamlit UI setup
st.set_page_config(
    page_title="Chat with Your PDF",
    page_icon="📄",
    layout="centered"
)

st.title("📄 Chat with Your PDF")


# --- Sidebar: PDF Upload + Management ---
with st.sidebar:
    st.header("Upload / Manage PDF")

    uploaded = st.file_uploader(
        "Upload a PDF file",
        type=["pdf"],
    )

    if st.button("Process PDF", use_container_width=True) and uploaded:
        with st.spinner("Uploading & indexing your PDF..."):
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
            try:
                r = requests.post(f"{API_URL}/pdf/upload", files=files, timeout=120)
                r.raise_for_status()
                data = r.json()
                st.session_state["pdf_id"] = data["pdf_id"]
                st.session_state["messages"] = []
                st.success(f"✅ PDF processed — ID: {data['pdf_id']} (Chunks: {data['chunks']})")

            except Exception as e:
                st.error(f"❌ Upload failed: {e}")

    if "pdf_id" in st.session_state:
        if st.button("🗑 Delete Current PDF", use_container_width=True):
            pid = st.session_state["pdf_id"]
            try:
                r = requests.delete(f"{API_URL}/pdf/{pid}")
                if r.ok:
                    del st.session_state["pdf_id"]
                    st.session_state["messages"] = []
                    st.success(f"Deleted PDF: {pid}")
                else:
                    st.error("Failed to delete PDF")
            except Exception as e:
                st.error(e)


# --- Chat Area ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "pdf_id" not in st.session_state:
    st.info("Upload a PDF to begin chatting!")
else:
    st.caption(f"📌 Active PDF ID: `{st.session_state['pdf_id']}`")

    # Display existing messages
    for role, content in st.session_state["messages"]:
        with st.chat_message(role):
            st.markdown(content)

    # Chat input
    prompt = st.chat_input("Ask something from your PDF...")
    if prompt:
        st.session_state["messages"].append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    payload = {
                        "pdf_id": st.session_state["pdf_id"],
                        "question": prompt
                    }
                    r = requests.post(
                        f"{API_URL}/query/ask",
                        json=payload,
                        timeout=120
                    )
                    if not r.ok:
                        st.error(f"Error: {r.text}")
                    else:
                        data = r.json()
                        answer = data.get("answer", "⚠ No answer found")
                        contexts = data.get("contexts", [])

                        st.markdown(answer)
                        st.session_state["messages"].append(("assistant", answer))

                        with st.expander("📌 Retrieved Context Chunks"):
                            for i, c in enumerate(contexts, start=1):
                                st.markdown(f"**Chunk {i}**\n\n{c}")

                except Exception as e:
                    st.error(f"Error communicating with backend: {e}")
