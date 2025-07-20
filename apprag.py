import streamlit as st
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.title("🧠 Simple RAG AI (Beginner Version)")

# Upload or enter text
st.subheader("📄 Upload, Paste Text, or Excel File")
uploaded_file = st.file_uploader("Choose a .txt or .xlsx/.xls file", type=["txt", "xlsx", "xls"])
text_input = st.text_area("Or paste text here")

# Question input
query = st.text_input("❓ Ask a question")

# Load text from file or input
text = ""

if uploaded_file:
    if uploaded_file.name.endswith(".txt"):
        text = uploaded_file.read().decode("utf-8")
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(uploaded_file, sheet_name=None)  # Load all sheets
            all_text = []
            for sheet_name, sheet_data in df.items():
                all_text.append(f"Sheet: {sheet_name}\n")
                all_text.append(sheet_data.astype(str).apply(lambda x: " ".join(x), axis=1).str.cat(sep="\n"))
            text = "\n".join(all_text)
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")
elif text_input:
    text = text_input

# Text splitting
def split_text(text, chunk_size=300):
    sentences = re.split(r'(?<=[.?!])\s+', text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# Retrieve relevant answer
def retrieve_answer(chunks, query):
    if not chunks or not query:
        return "Please upload text and ask a question."
    
    vectorizer = TfidfVectorizer().fit(chunks + [query])
    vectors = vectorizer.transform(chunks + [query])
    
    similarity = cosine_similarity(vectors[-1], vectors[:-1])
    best_idx = similarity.argmax()
    return chunks[best_idx]

# Display answer
if text and query:
    chunks = split_text(text)
    answer = retrieve_answer(chunks, query)
    st.markdown("### 🧠 Retrieved Answer:")
    st.write(answer)
