"""Agent 7: Help Agent (Medical FAQ Assistant)
Uses trained TF-IDF model for multilingual Q&A (Romanian + Russian).
Falls back to keyword matching if trained model is unavailable.
"""
import os
import json
import pickle
import logging
import numpy as np
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "saved_models", "help_agent_latest.pkl")
QA_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "training_data", "help_agent_qa.json")


class HelpAgent(BaseAgent):
    name = "help"
    description = "Medical FAQ virtual assistant (RO + RU)"

    def __init__(self, db=None):
        super().__init__(db)
        self._model_data = None
        self._qa_data = None
        self._load_model()

    def _load_model(self):
        """Load trained TF-IDF model if available."""
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    data = pickle.load(f)
                self._model_data = data.get("model", data)
                logger.info("Help Agent: Loaded trained TF-IDF model")
                return
            except Exception as e:
                logger.warning(f"Help Agent: Could not load model: {e}")

        # Fallback: load Q&A JSON directly
        if os.path.exists(QA_PATH):
            try:
                with open(QA_PATH, "r", encoding="utf-8") as f:
                    self._qa_data = json.load(f)
                logger.info(f"Help Agent: Loaded {len(self._qa_data['qa_pairs'])} Q&A pairs from JSON")
            except Exception as e:
                logger.warning(f"Help Agent: Could not load Q&A data: {e}")

    def _detect_language(self, text: str) -> str:
        """Simple language detection: Russian uses Cyrillic characters."""
        cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        return "ru" if cyrillic_count > len(text) * 0.3 else "ro"

    def answer(self, question: str) -> dict:
        """Answer a medical question using trained model or keyword fallback.
        Always attaches a `booking_intent` field so the client can offer a
        'Programează acum' shortcut when the user wants to make an appointment.
        """
        lang = self._detect_language(question)

        # Method 1: Trained TF-IDF model
        if self._model_data and "tfidf" in self._model_data:
            result = self._answer_with_tfidf(question, lang)
        # Method 2: JSON Q&A with keyword matching
        elif self._qa_data:
            result = self._answer_with_keywords(question, lang)
        # Method 3: Hardcoded fallback
        else:
            result = self._fallback_answer(lang)

        # Attach booking intent regardless of answer source
        result["booking_intent"] = self.detect_booking_intent(question)
        return result

    def _answer_with_tfidf(self, question: str, lang: str) -> dict:
        """Use trained TF-IDF + cosine similarity for retrieval."""
        from sklearn.metrics.pairwise import cosine_similarity

        tfidf = self._model_data["tfidf"]
        tfidf_matrix = self._model_data["tfidf_matrix"]
        answers_ro = self._model_data["corpus_answers_ro"]
        answers_ru = self._model_data["corpus_answers_ru"]
        categories = self._model_data["corpus_categories"]
        questions = self._model_data["corpus_questions"]

        query_vec = tfidf.transform([question])
        sims = cosine_similarity(query_vec, tfidf_matrix).flatten()

        # Get top 5 matches
        top_indices = sims.argsort()[-5:][::-1]
        best_idx = top_indices[0]
        confidence = float(sims[best_idx])

        if confidence < 0.05:
            return self._fallback_answer(lang)

        answers = answers_ru if lang == "ru" else answers_ro

        related = []
        for idx in top_indices[1:4]:
            if sims[idx] > 0.05:
                related.append(questions[idx])

        return {
            "answer": answers[best_idx],
            "category": categories[best_idx],
            "confidence": round(min(1.0, confidence * 2), 2),
            "language": lang,
            "related_questions": related,
            "method": "tfidf",
        }

    def _answer_with_keywords(self, question: str, lang: str) -> dict:
        """Keyword-based matching on Q&A JSON data."""
        question_lower = question.lower()
        pairs = self._qa_data["qa_pairs"]

        scores = []
        for pair in pairs:
            score = 0
            for keyword in pair.get("keywords", []):
                if keyword.lower() in question_lower:
                    score += 2
                elif any(kw in question_lower for kw in keyword.lower().split()):
                    score += 1
            # Also match against the question text
            q_field = "question_ru" if lang == "ru" else "question_ro"
            q_words = set(pair.get(q_field, "").lower().split())
            common = set(question_lower.split()) & q_words
            score += len(common) * 0.5
            scores.append((score, pair))

        scores.sort(key=lambda x: x[0], reverse=True)

        if scores and scores[0][0] > 0:
            best = scores[0][1]
            confidence = min(1.0, scores[0][0] / 6)
            answer_field = "answer_ru" if lang == "ru" else "answer_ro"
            q_field = "question_ru" if lang == "ru" else "question_ro"

            related = [s[1][q_field] for s in scores[1:4] if s[0] > 0]

            return {
                "answer": best[answer_field],
                "category": best["category"],
                "confidence": round(confidence, 2),
                "language": lang,
                "related_questions": related,
                "method": "keywords",
            }

        return self._fallback_answer(lang)

    def _fallback_answer(self, lang: str) -> dict:
        """Default answer when no match is found."""
        if lang == "ru":
            answer = (
                "Не удалось найти конкретный ответ на ваш вопрос. "
                "Рекомендуем записаться на консультацию к врачу-специалисту "
                "для получения персонализированных рекомендаций. "
                "В экстренных случаях звоните 112."
            )
        else:
            answer = (
                "Nu am găsit un răspuns specific pentru întrebarea dumneavoastră. "
                "Vă recomandăm să programați o consultație cu un medic specialist "
                "pentru a primi sfaturi personalizate. "
                "În caz de urgență, sunați la 112."
            )

        return {
            "answer": answer,
            "category": "general",
            "confidence": 0,
            "language": lang,
            "related_questions": [],
            "method": "fallback",
        }

    # ── Booking intent detection (NLP) ──────────────────────────
    # Extracts: intent ("book"|"cancel"|"info"|None), specialty, date hint
    _BOOK_KEYWORDS = [
        "programar", "programez", "programa", "rezerv", "vreau o consult",
        "doresc o consult", "consult", "vizita la medic", "vreau la medic",
        "запис", "записа", "прием", "визит", "хочу на прием", "book",
    ]
    _CANCEL_KEYWORDS = [
        "anulez", "anulare", "renunt", "sterg programar", "nu mai vreau",
        "отмен", "убрать запись", "cancel",
    ]

    # Map user terms → canonical specialty names used in the DB
    _SPECIALTY_SYNONYMS = {
        "cardiolog": "Cardiologie",
        "inima": "Cardiologie", "tensiune": "Cardiologie",
        "кардиолог": "Cardiologie", "сердц": "Cardiologie",
        "neurolog": "Neurologie",
        "cap": "Neurologie", "migrena": "Neurologie",
        "невролог": "Neurologie", "мигрен": "Neurologie",
        "pediatr": "Pediatrie",
        "copil": "Pediatrie", "bebelus": "Pediatrie",
        "педиатр": "Pediatrie", "ребен": "Pediatrie",
        "ortoped": "Ortopedie",
        "oas": "Ortopedie", "fractur": "Ortopedie",
        "ортопед": "Ortopedie", "кост": "Ortopedie",
        "dermatolog": "Dermatologie",
        "piele": "Dermatologie", "acnee": "Dermatologie",
        "дерматолог": "Dermatologie", "кожа": "Dermatologie",
        "chirurg": "Chirurgie Generală",
        "хирург": "Chirurgie Generală",
        "intern": "Medicină Internă",
        "general": "Medicină Internă",
        "ginecolog": "Ginecologie",
        "гинеколог": "Ginecologie",
        "urolog": "Urologie",
        "уролог": "Urologie",
        "oftalmolog": "Oftalmologie", "ochi": "Oftalmologie",
        "офтальмолог": "Oftalmologie", "глаз": "Oftalmologie",
        "orl": "ORL", "ureche": "ORL", "gat": "ORL", "nas": "ORL",
        "ухо": "ORL", "горло": "ORL",
        "psihiatr": "Psihiatrie",
        "психиатр": "Psihiatrie",
        "radiolog": "Radiologie",
        "рентген": "Radiologie",
        "anestez": "Anestezie",
    }

    _URGENT_KEYWORDS = ["urgent", "azi", "astazi", "acum", "imediat", "срочн", "сегодня", "немедл"]

    def detect_booking_intent(self, text: str) -> dict:
        """Detect if user wants to book/cancel an appointment and extract entities.
        Returns: {intent, specialty, urgent, date_hint, raw_match}
        """
        t = text.lower().strip()
        if not t:
            return {"intent": None}

        intent = None
        if any(k in t for k in self._CANCEL_KEYWORDS):
            intent = "cancel"
        elif any(k in t for k in self._BOOK_KEYWORDS):
            intent = "book"

        specialty = None
        for syn, canon in self._SPECIALTY_SYNONYMS.items():
            if syn in t:
                specialty = canon
                break

        urgent = any(k in t for k in self._URGENT_KEYWORDS)

        # Date hints (relative)
        date_hint = None
        if "maine" in t or "завтра" in t:
            date_hint = "tomorrow"
        elif "azi" in t or "astazi" in t or "сегодня" in t:
            date_hint = "today"
        elif "saptamana" in t or "неделе" in t:
            date_hint = "this_week"

        return {
            "intent": intent,
            "specialty": specialty,
            "urgent": urgent,
            "date_hint": date_hint,
            "language": self._detect_language(text),
        }

    def run(self) -> dict:
        """Return available FAQ categories and stats."""
        if self._qa_data:
            categories = {}
            for pair in self._qa_data["qa_pairs"]:
                cat = pair["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(pair["question_ro"])
            return {
                "total_pairs": len(self._qa_data["qa_pairs"]),
                "languages": ["ro", "ru"],
                "categories": categories,
                "model_loaded": self._model_data is not None,
            }

        return {
            "total_pairs": 0,
            "languages": ["ro", "ru"],
            "categories": {},
            "model_loaded": False,
        }
