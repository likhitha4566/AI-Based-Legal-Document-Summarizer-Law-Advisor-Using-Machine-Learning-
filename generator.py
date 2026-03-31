# generator.py
# FULLY OFFLINE LEGAL INTELLIGENCE ENGINE

import re
from collections import Counter


# ===============================
# CLAUSE LIBRARY
# ===============================

CLAUSE_LIBRARY = {
    "Payment Terms": {
        "keywords": ["payment", "fees", "invoice", "amount", "salary", "charges"],
        "risk": 10
    },
    "Confidentiality Clause": {
        "keywords": ["confidential", "non-disclosure", "nda", "proprietary"],
        "risk": 5
    },
    "Termination Clause": {
        "keywords": ["terminate", "termination", "cancel", "breach"],
        "risk": 20
    },
    "Liability Clause": {
        "keywords": ["liability", "damages", "loss", "penalty", "compensation"],
        "risk": 25
    },
    "Data Protection Clause": {
        "keywords": ["data", "privacy", "personal information", "without consent"],
        "risk": 30
    },
    "Arbitration Clause": {
        "keywords": ["arbitration", "arbitrator", "dispute resolution"],
        "risk": 15
    },
    "Jurisdiction Clause": {
        "keywords": ["jurisdiction", "governing law", "court"],
        "risk": 10
    }
}


# ===============================
# TEXT PREPROCESSING
# ===============================

def preprocess(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ===============================
# SENTENCE SPLITTING
# ===============================

def split_sentences(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    sentences = [s.strip() for s in sentences if len(s) > 30]
    return sentences


# ===============================
# SENTENCE RANKING (TF-BASED)
# ===============================

def rank_sentences(sentences):

    words = []
    for s in sentences:
        words.extend(re.findall(r'\w+', s.lower()))

    word_freq = Counter(words)

    sentence_scores = {}

    for sentence in sentences:
        score = 0
        for word in re.findall(r'\w+', sentence.lower()):
            score += word_freq[word]
        sentence_scores[sentence] = score

    # Sort sentences by score
    ranked = sorted(sentence_scores, key=sentence_scores.get, reverse=True)

    return ranked[:5]  # top 5 important sentences


# ===============================
# CLAUSE DETECTION
# ===============================

def detect_clauses(text):

    text_lower = text.lower()
    detected = []
    total_risk = 0

    for clause, data in CLAUSE_LIBRARY.items():
        for keyword in data["keywords"]:
            if keyword in text_lower:
                detected.append(clause)
                total_risk += data["risk"]
                break

    return list(set(detected)), min(total_risk, 100)


# ===============================
# RISK LEVEL CLASSIFICATION
# ===============================

def get_risk_level(score):

    if score >= 70:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"


# ===============================
# RISKY SENTENCE DETECTION
# ===============================

def detect_risky_sentences(sentences):

    risky_words = [
        "penalty", "breach", "without consent",
        "illegal", "fraud", "lawsuit",
        "terminate", "damages", "violation"
    ]

    risky_sentences = []

    for sentence in sentences:
        for word in risky_words:
            if word in sentence.lower():
                risky_sentences.append(sentence)
                break

    return risky_sentences[:3]


# ===============================
# MAIN GENERATOR FUNCTION
# ===============================

def generate_answer(context, text):

    text = preprocess(text)

    sentences = split_sentences(text)

    if not sentences:
        return "Document content too short to analyze."

    # Summarization
    summary_sentences = rank_sentences(sentences)
    summary = "\n\n".join(summary_sentences)

    # Clause Detection
    clauses, risk_score = detect_clauses(text)

    # Risk Level
    risk_level = get_risk_level(risk_score)

    # Risky Sentences
    risky_sentences = detect_risky_sentences(sentences)

    return f"""
==============================
DOCUMENT SUMMARY
==============================

{summary}

==============================
DETECTED LEGAL CLAUSES
==============================

{chr(10).join(clauses) if clauses else "No major clauses detected."}

==============================
RISK ANALYSIS
==============================

Risk Score: {risk_score}%
Risk Level: {risk_level}

==============================
HIGH RISK SENTENCES
==============================

{chr(10).join(risky_sentences) if risky_sentences else "No highly risky sentences detected."}

==============================
SYSTEM NOTE
==============================

This report was generated using a fully offline Legal Intelligence Engine.
Clause detection and risk scoring are based on rule-based legal reasoning.
"""