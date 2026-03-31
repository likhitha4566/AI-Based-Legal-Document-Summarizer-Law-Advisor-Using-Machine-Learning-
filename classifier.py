import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from document_utils import read_docx, read_pdf, read_txt

def load_dataset():
    texts, labels = [], []

    for label in ["legal", "illegal"]:
        folder = f"dataset/{label}"
        for file in os.listdir(folder):
            path = os.path.join(folder, file)

            if file.endswith(".docx"):
                text = read_docx(path)
            elif file.endswith(".pdf"):
                text = read_pdf(path)
            else:
                text = read_txt(path)

            texts.append(text)
            labels.append(label)

    return texts, labels

dataset_texts, dataset_labels = load_dataset()
vectorizer = TfidfVectorizer(stop_words="english")
X = vectorizer.fit_transform(dataset_texts)

def predict_compliance(uploaded_text):
    q_vec = vectorizer.transform([uploaded_text])
    scores = cosine_similarity(q_vec, X)[0]

    best_idx = scores.argmax()
    label = dataset_labels[best_idx]
    confidence = round(scores[best_idx] * 100, 2)

    return label.upper(), confidence
