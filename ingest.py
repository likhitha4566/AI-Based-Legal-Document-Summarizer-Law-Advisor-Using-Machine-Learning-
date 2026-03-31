import os
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

DATASET_PATH = "dataset"
VECTOR_PATH = "vectorstore"

documents = []

def load_docs(folder, label):
    for file in os.listdir(folder):
        path = os.path.join(folder, file)

        if file.endswith(".pdf"):
            loader = PyPDFLoader(path)
            docs = loader.load()
        else:
            loader = TextLoader(path, encoding="utf-8")
            docs = loader.load()

        for d in docs:
            d.metadata["label"] = label
        documents.extend(docs)

load_docs("dataset/legal", "Legal")
load_docs("dataset/illegal", "Illegal")

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks = splitter.split_documents(documents)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

vectorstore = FAISS.from_documents(chunks, embeddings)
vectorstore.save_local(VECTOR_PATH)

print("✅ Vector store created successfully")
