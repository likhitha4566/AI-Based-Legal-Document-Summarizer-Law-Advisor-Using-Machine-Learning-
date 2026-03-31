import re

CLAUSE_LIBRARY = {
    "Payment Terms": {
        "keywords": ["payment", "fees", "invoice", "amount", "salary"],
        "risk": 10
    },
    "Confidentiality": {
        "keywords": ["confidential", "non-disclosure", "nda"],
        "risk": 5
    },
    "Termination": {
        "keywords": ["terminate", "termination", "cancel", "breach"],
        "risk": 20
    },
    "Liability": {
        "keywords": ["liability", "damages", "loss", "penalty"],
        "risk": 25
    },
    "Data Protection": {
        "keywords": ["data", "privacy", "personal information", "without consent"],
        "risk": 30
    },
    "Arbitration": {
        "keywords": ["arbitration", "arbitrator", "dispute resolution"],
        "risk": 15
    }
}


def detect_clauses(text):
    text_lower = text.lower()
    detected = []
    total_risk = 0

    for clause, data in CLAUSE_LIBRARY.items():
        for word in data["keywords"]:
            if word in text_lower:
                detected.append(clause)
                total_risk += data["risk"]
                break

    risk_score = min(total_risk, 100)

    return list(set(detected)), risk_score