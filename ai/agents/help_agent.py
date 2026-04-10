"""Agent 7: Help Agent (Medical FAQ Assistant)
Virtual assistant using a local transformer model (DistilBERT) for medical Q&A.
"""
import os
import json
import logging
import numpy as np
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Medical FAQ knowledge base (Romanian)
MEDICAL_FAQ = [
    {
        "question": "Ce fac dacă am febră mare?",
        "answer": "Dacă aveți febră peste 38.5°C, luați un antitermic (paracetamol). Beți multe lichide și odihniți-vă. Dacă febra persistă mai mult de 3 zile sau depășește 40°C, prezentați-vă la urgențe.",
        "category": "urgente",
        "keywords": ["febra", "temperatura", "cald", "frisoane"],
    },
    {
        "question": "Am dureri de cap severe. Ce trebuie să fac?",
        "answer": "Durerile de cap pot avea multe cauze. Luați un analgezic (paracetamol/ibuprofen). Dacă durerea este bruscă și foarte intensă, aveți vedere încețoșată sau vomitați, mergeți la urgențe imediat - ar putea fi o urgență neurologică.",
        "category": "neurologie",
        "keywords": ["durere cap", "cefalee", "migrena", "cap"],
    },
    {
        "question": "Cum pot programa o consultație?",
        "answer": "Pentru a programa o consultație: 1) Accesați secțiunea 'Programare' din meniul principal. 2) Alegeți specialitatea dorită. 3) Selectați medicul. 4) Alegeți data și ora disponibilă. 5) Confirmați programarea. Veți primi o notificare de confirmare.",
        "category": "sistem",
        "keywords": ["programare", "consultatie", "rezervare", "medic"],
    },
    {
        "question": "Am dureri de piept. Este grav?",
        "answer": "Durerile de piept pot fi grave. Dacă aveți durere în piept care se extinde spre brațul stâng, dificultăți de respirație, transpirații reci, SUNAȚI IMEDIAT LA 112. Acestea pot fi simptome de infarct miocardic. Nu așteptați!",
        "category": "urgente",
        "keywords": ["durere piept", "inima", "infarct", "respiratie"],
    },
    {
        "question": "Ce investigații trebuie să fac anual?",
        "answer": "Investigații recomandate anual: hemoleucogramă completă, glicemie, profil lipidic, funcție hepatică și renală, sumar urină. După 40 ani: EKG, ecografie abdominală. Femei: examen ginecologic, mamografie (după 40 ani). Bărbați: PSA (după 50 ani).",
        "category": "preventie",
        "keywords": ["investigatii", "analize", "control", "anual", "preventie"],
    },
    {
        "question": "Cum îmi pot accesa istoricul medical?",
        "answer": "Istoricul medical se găsește în secțiunea 'Istoric' din meniul principal. Acolo puteți vedea toate consultațiile anterioare, notele medicului și recomandările primite. Puteți descărca rapoarte PDF pentru fiecare consultație.",
        "category": "sistem",
        "keywords": ["istoric", "medical", "consultatie", "raport"],
    },
    {
        "question": "Am simptome de răceală. Ce recomandați?",
        "answer": "Pentru simptome de răceală: odihniți-vă, beți multe lichide calde, luați vitamina C. Paracetamol pentru febră/dureri. Dacă simptomele persistă peste 7 zile sau se agravează (tuse cu sânge, dificultăți de respirație), programați o consultație.",
        "category": "general",
        "keywords": ["raceala", "gripa", "tuse", "nas", "gat"],
    },
    {
        "question": "Când trebuie să merg la urgențe?",
        "answer": "Mergeți la urgențe în caz de: durere severă de piept, dificultăți respiratorii, pierderea conștienței, sângerare abundentă, fracturi evidente, reacții alergice severe, durere abdominală intensă, AVC (paralizie facială, tulburări de vorbire), febră >40°C.",
        "category": "urgente",
        "keywords": ["urgente", "urgenta", "grav", "spital", "112"],
    },
    {
        "question": "Cum pot comunica cu medicul meu?",
        "answer": "Puteți comunica cu medicul prin secțiunea 'Mesaje' din aplicație. Aveți acces la chat text și video consultații. Conversațiile se creează automat după ce aveți o programare cu un medic.",
        "category": "sistem",
        "keywords": ["mesaj", "chat", "comunicare", "medic", "video"],
    },
    {
        "question": "Ce este tensiunea arterială normală?",
        "answer": "Tensiunea arterială normală este sub 120/80 mmHg. Pre-hipertensiune: 120-139/80-89. Hipertensiune stadiul 1: 140-159/90-99. Hipertensiune stadiul 2: ≥160/≥100. Dacă aveți valori peste 140/90 constant, consultați un cardiolog.",
        "category": "cardiologie",
        "keywords": ["tensiune", "arteriala", "hipertensiune", "tensiunea"],
    },
]


class HelpAgent(BaseAgent):
    name = "help"
    description = "Medical FAQ virtual assistant"

    def __init__(self, db=None):
        if db:
            super().__init__(db)
        self.faq_data = MEDICAL_FAQ
        self._embeddings = None

    def _compute_keyword_score(self, query: str, faq_entry: dict) -> float:
        """Compute similarity score based on keyword matching."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        score = 0
        for keyword in faq_entry["keywords"]:
            if keyword.lower() in query_lower:
                score += 2
            elif any(kw in query_lower for kw in keyword.lower().split()):
                score += 1

        # Bonus for category match
        common_words = query_words & set(faq_entry.get("category", "").lower().split())
        score += len(common_words)

        return score

    def answer(self, question: str) -> dict:
        """Answer a medical question using keyword matching and FAQ database."""
        scores = []
        for faq in self.faq_data:
            score = self._compute_keyword_score(question, faq)
            scores.append((score, faq))

        scores.sort(key=lambda x: x[0], reverse=True)

        if scores[0][0] > 0:
            best = scores[0][1]
            confidence = min(1.0, scores[0][0] / 5)
            return {
                "answer": best["answer"],
                "category": best["category"],
                "confidence": round(confidence, 2),
                "related_questions": [s[1]["question"] for s in scores[1:4] if s[0] > 0],
            }

        return {
            "answer": "Nu am găsit un răspuns specific pentru întrebarea dumneavoastră. "
                      "Vă recomandăm să programați o consultație cu un medic specialist "
                      "pentru a primi sfaturi personalizate.",
            "category": "general",
            "confidence": 0,
            "related_questions": [faq["question"] for faq in self.faq_data[:3]],
        }

    def run(self) -> dict:
        """Return available FAQ categories and questions."""
        categories = {}
        for faq in self.faq_data:
            cat = faq["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(faq["question"])

        return {
            "categories": categories,
            "total_questions": len(self.faq_data),
        }
