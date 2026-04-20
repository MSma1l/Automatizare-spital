"""Agent 8: Registration Agent
Extracts patient registration fields (name, birth date, phone, address, insurance, email)
from unstructured text (ID card, insurance card, intake form, etc.).

Hybrid approach:
  1) Regex + keyword rules (high-precision for structured fields)
  2) Trained scikit-learn classifier that labels each input line with its field type
     (used for noisy free-text where the label is missing)
"""
import os
import re
import json
import pickle
import logging
from datetime import datetime
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "models", "saved_models", "registration_agent_latest.pkl"
)


# ── Label keywords (RO + RU) ───────────────────────────────────────
LABELS = {
    "first_name": ["prenume", "prenumele", "имя"],
    "last_name":  ["nume", "numele", "nume de familie", "фамилия"],
    "full_name":  ["nume complet", "nume și prenume", "пациент", "nume pacient"],
    "birth_date": ["data nașterii", "data nasterii", "nascut", "născut",
                   "дата рождения", "dob", "n."],
    "gender":     ["sex", "gen", "пол"],
    "phone":      ["telefon", "tel", "mobil", "phone", "телефон"],
    "address":    ["adresa", "adresă", "domiciliu", "адрес", "locatie"],
    "insurance_number": ["asigurare", "nr asigurare", "număr asigurare",
                         "cnp", "полис", "страховка", "cnas", "nr. asigurare"],
    "email":      ["email", "e-mail", "mail", "эл. почта", "почта"],
}

# Flip: keyword -> field
KEYWORD_TO_FIELD: dict[str, str] = {}
for field, kws in LABELS.items():
    for kw in kws:
        KEYWORD_TO_FIELD[kw.lower()] = field


GENDER_MAP = {
    "m": "male", "masculin": "male", "male": "male", "мужской": "male", "муж": "male",
    "f": "female", "feminin": "female", "female": "female", "женский": "female", "жен": "female",
}


# ── Regex patterns ─────────────────────────────────────────────────
DATE_PATTERNS = [
    # DD.MM.YYYY / DD/MM/YYYY / DD-MM-YYYY
    re.compile(r"\b(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})\b"),
    # YYYY-MM-DD / YYYY.MM.DD / YYYY/MM/DD
    re.compile(r"\b(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})\b"),
    # DD MM YYYY (space separated — Moldovan ID card format: "10 12 2004")
    re.compile(r"\b(\d{1,2})\s+(\d{1,2})\s+(\d{4})\b"),
]
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3}[\s.-]?\d{3,4}(?:[\s.-]?\d{2,4})?")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
INSURANCE_PATTERN = re.compile(r"\b(?:RO|MD|CNP)?\s*\d{10,16}\b", re.IGNORECASE)
# Moldovan ID card document number: letter(s) + 7-9 digits (e.g. B37050258)
MD_ID_DOCNO_PATTERN = re.compile(r"\b[A-Z]{1,2}\d{7,9}\b")
# Words that are all-caps (possible name on Moldovan ID card)
ALLCAPS_WORD = re.compile(r"^[A-ZÎÂĂȘȚÂÎ]{3,}$")

# Keywords that identify a Moldovan ID card layout (labels-above-value)
MD_ID_MARKERS = [
    "buletin de identitate", "republica moldova", "agentia servicii publice",
    "agenția servicii publice", "cetatenia", "cetățenia", "гражданство",
    "data nasterii", "data nașterii", "дата рождения",
    "data emiterii", "data expirarii", "data expirării",
]


def _normalize_date(s: str) -> str | None:
    """Return YYYY-MM-DD or None."""
    for pat in DATE_PATTERNS:
        m = pat.search(s)
        if not m:
            continue
        a, b, c = m.groups()
        try:
            if len(a) == 4:
                dt = datetime(int(a), int(b), int(c))
            else:
                dt = datetime(int(c), int(b), int(a))
            return dt.date().isoformat()
        except ValueError:
            continue
    return None


def _find_all_dates(s: str) -> list[str]:
    """Return all dates in text as YYYY-MM-DD, in order of appearance."""
    results: list[tuple[int, str]] = []
    for pat in DATE_PATTERNS:
        for m in pat.finditer(s):
            a, b, c = m.groups()
            try:
                if len(a) == 4:
                    dt = datetime(int(a), int(b), int(c))
                else:
                    dt = datetime(int(c), int(b), int(a))
                results.append((m.start(), dt.date().isoformat()))
            except ValueError:
                continue
    # Sort by position, dedup preserving order
    seen: set = set()
    out: list[str] = []
    for _, iso in sorted(results, key=lambda x: x[0]):
        if iso not in seen:
            seen.add(iso)
            out.append(iso)
    return out


def _clean_phone(s: str) -> str:
    digits = re.sub(r"[^\d+]", "", s)
    return digits


class RegistrationAgent(BaseAgent):
    name = "registration"
    description = "Extracts patient registration fields from documents/text"

    def __init__(self, db=None):
        super().__init__(db)
        self._model_data = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    data = pickle.load(f)
                self._model_data = data.get("model", data)
                logger.info("Registration Agent: model loaded")
            except Exception as e:
                logger.warning(f"Registration Agent: could not load model: {e}")

    # ── Rule-based extractor ─────────────────────────────────────
    def _rule_extract(self, text: str) -> dict:
        out: dict = {}
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        text_l = text.lower()
        is_md_id = any(marker in text_l for marker in MD_ID_MARKERS)

        # ── Pass 1: "Key: value" on same line ─────────────────────
        for line in lines:
            if ":" in line:
                key, _, value = line.partition(":")
                key_l = key.strip().lower()
                value = value.strip()
                field = KEYWORD_TO_FIELD.get(key_l)
                if not field:
                    for kw, f in KEYWORD_TO_FIELD.items():
                        if key_l.startswith(kw):
                            field = f
                            break
                if field and value:
                    self._assign(out, field, value)

        # ── Pass 2: Moldovan ID card layout — label on one line, value on next ─
        # Handles patterns like:
        #   Numele/Фамилия
        #   GÎSCA
        #   Prenumele/Имя
        #   VLAD
        #   Data nașterii/Дата рождения
        #   10 12 2004
        for i, line in enumerate(lines):
            line_l = line.lower().strip(" \t:/")
            # Match label line — may contain "/Cyrillic" variant
            field = None
            for kw, f in KEYWORD_TO_FIELD.items():
                # exact-ish match with optional /suffix (e.g. "Numele/Фамилия")
                if line_l == kw or line_l.startswith(kw + "/") or line_l.startswith(kw + " "):
                    field = f
                    break
            if not field:
                continue
            # Look at next 1-2 lines for the value
            for j in (1, 2):
                if i + j >= len(lines):
                    break
                val = lines[i + j].strip()
                if not val:
                    continue
                # Skip if next line is itself another label
                if any(val.lower().startswith(kw) for kw in KEYWORD_TO_FIELD):
                    continue
                if field not in out or not out[field]:
                    self._assign(out, field, val)
                    break

        # ── Pass 3: Moldovan ID — positional heuristics when labels are missing ─
        if is_md_id:
            # Document number (doc number) can serve as insurance_number fallback
            for line in lines:
                m = MD_ID_DOCNO_PATTERN.search(line)
                if m and "insurance_number" not in out:
                    out["insurance_number"] = m.group(0)
                    break

            # Use ALL found dates: first=birth, (ignore emission and expiry)
            dates = _find_all_dates(text)
            if dates and "birth_date" not in out:
                # The birth date is typically the smallest (earliest) year
                try:
                    dates_sorted = sorted(dates)
                    out["birth_date"] = dates_sorted[0]
                except Exception:
                    out["birth_date"] = dates[0]

            # Find all-caps single-word names (length > 2) that are NOT labels/countries
            SKIP = {"REPUBLICA", "MOLDOVA", "BULETIN", "IDENTITATE", "MDA", "ROU", "RUS",
                    "AGENTIA", "AGENȚIA", "SERVICII", "PUBLICE", "SEX", "NUMELE",
                    "PRENUMELE", "CETATENIA", "CETĂȚENIA", "DATA", "NASTERII",
                    "NAȘTERII", "EMITERII", "EXPIRARII", "EXPIRĂRII",
                    "ФАМИЛИЯ", "ИМЯ", "ГРАЖДАНСТВО", "ПОЛ", "РОЖДЕНИЯ", "ВЫДАЧИ"}
            allcaps_names = []
            for line in lines:
                # Skip lines that are pure digits/date/doc number
                if re.fullmatch(r"[\d\s./-]+", line):
                    continue
                if MD_ID_DOCNO_PATTERN.search(line):
                    continue
                tokens = [t for t in re.split(r"[\s/,.;:]+", line) if t]
                for t in tokens:
                    tc = t.strip("/-.,:;")
                    if len(tc) >= 3 and tc.upper() == tc and tc.upper() not in SKIP and tc.isalpha():
                        allcaps_names.append(tc)
            # In Moldovan ID: first all-caps name = last_name, second = first_name
            if allcaps_names:
                if "last_name" not in out:
                    out["last_name"] = allcaps_names[0].capitalize()
                if "first_name" not in out and len(allcaps_names) >= 2:
                    out["first_name"] = allcaps_names[1].capitalize()

            # Gender: single letter M or F on its own, near "Sex" label
            if "gender" not in out:
                for i, line in enumerate(lines):
                    if re.search(r"\b(sex|пол)\b", line.lower()):
                        # Scan same line + next 2 lines for single M/F
                        for j in range(i, min(i + 3, len(lines))):
                            m = re.search(r"\b([MFmf])\b", lines[j])
                            if m:
                                out["gender"] = "male" if m.group(1).upper() == "M" else "female"
                                break
                        if "gender" in out:
                            break

        # ── Pass 4: Free-text fallbacks ────────────────────────────
        if "email" not in out:
            m = EMAIL_PATTERN.search(text)
            if m:
                out["email"] = m.group(0).lower()

        if "phone" not in out:
            # Skip phone extraction on MD ID cards unless an explicit phone label
            # exists — the document number looks like a phone otherwise.
            has_phone_label = any(
                kw in text_l
                for kw in ("telefon", "tel.", "mobil", "телефон", "phone")
            )
            if not is_md_id or has_phone_label:
                insurance_digits = re.sub(r"\D", "", out.get("insurance_number", ""))
                for line in lines:
                    # Skip date-looking lines
                    if _normalize_date(line):
                        continue
                    # Skip the line that holds the ID card doc number
                    if MD_ID_DOCNO_PATTERN.search(line):
                        continue
                    m = PHONE_PATTERN.search(line)
                    if m:
                        candidate = _clean_phone(m.group(0))
                        digits = re.sub(r"\D", "", candidate)
                        if not (7 <= len(digits) <= 15):
                            continue
                        # Skip if it's just a substring of the insurance/doc number
                        if insurance_digits and digits in insurance_digits:
                            continue
                        out["phone"] = candidate
                        break

        if "birth_date" not in out:
            for line in lines:
                d = _normalize_date(line)
                if d:
                    out["birth_date"] = d
                    break

        if "insurance_number" not in out:
            phone_digits = re.sub(r"\D", "", out.get("phone", ""))
            for line in lines:
                # ID card doc number is good substitute
                m = MD_ID_DOCNO_PATTERN.search(line)
                if m:
                    out["insurance_number"] = m.group(0)
                    break
                m = INSURANCE_PATTERN.search(line)
                if not m:
                    continue
                candidate = m.group(0).strip()
                if phone_digits and phone_digits in re.sub(r"\D", "", candidate):
                    continue
                if re.fullmatch(r"\d{4}", candidate):
                    continue
                out["insurance_number"] = candidate
                break

        return out

    def _assign(self, out: dict, field: str, value: str):
        if not value:
            return
        if field == "full_name":
            parts = value.split()
            if len(parts) >= 2:
                out.setdefault("last_name", parts[0])
                out.setdefault("first_name", " ".join(parts[1:]))
            else:
                out.setdefault("first_name", value)
        elif field in ("first_name", "last_name"):
            parts = value.split()
            if len(parts) >= 2 and "first_name" not in out and "last_name" not in out:
                # "Nume: Popescu Ion" — treat as full name and split
                out["last_name"] = parts[0]
                out["first_name"] = " ".join(parts[1:])
            else:
                out.setdefault(field, value)
        elif field == "birth_date":
            d = _normalize_date(value)
            if d:
                out["birth_date"] = d
        elif field == "phone":
            out["phone"] = _clean_phone(value)
        elif field == "gender":
            norm = GENDER_MAP.get(value.strip().lower())
            if norm:
                out["gender"] = norm
        elif field == "email":
            m = EMAIL_PATTERN.search(value)
            if m:
                out["email"] = m.group(0).lower()
        elif field == "insurance_number":
            m = INSURANCE_PATTERN.search(value)
            out["insurance_number"] = (m.group(0).strip() if m else value.strip())
        else:
            out[field] = value.strip()

    # ── ML classifier (per-line field labeller) ──────────────────
    def _ml_extract(self, text: str) -> dict:
        """Use trained TF-IDF + classifier to label each line if rule-based missed fields."""
        if not self._model_data:
            return {}
        tfidf = self._model_data["tfidf"]
        clf = self._model_data["clf"]
        le = self._model_data["le"]

        out: dict = {}
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            return out

        X = tfidf.transform(lines)
        try:
            proba = clf.predict_proba(X)
            labels = le.classes_
            for line, row in zip(lines, proba):
                best_idx = row.argmax()
                conf = float(row[best_idx])
                if conf < 0.4:
                    continue
                field = labels[best_idx]
                if field == "none":
                    continue
                # Strip trailing key if "key: value"
                if ":" in line:
                    line = line.split(":", 1)[1].strip()
                if field not in out:
                    self._assign(out, field, line)
        except Exception as e:
            logger.warning(f"ML extract failed: {e}")

        return out

    # ── OCR (image → text) ───────────────────────────────────────
    def parse_image(self, image_bytes: bytes) -> dict:
        """Run OCR on an uploaded image (ID / insurance card / intake form),
        then feed the extracted text through the normal `parse()` pipeline.

        Uses Tesseract with Romanian+Russian+English language models.
        """
        try:
            import pytesseract
            from PIL import Image, ImageOps, ImageFilter
            import io
        except ImportError as e:
            return {
                "extracted": {}, "confidence": 0.0, "fields_found": 0,
                "method": "ocr_unavailable", "error": f"OCR dependencies missing: {e}",
                "ocr_text": "",
            }

        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Preprocess: grayscale + auto-contrast + slight sharpen — improves
            # OCR accuracy on phone photos of ID cards considerably.
            img = ImageOps.exif_transpose(img)  # honor EXIF orientation
            img = img.convert("L")
            img = ImageOps.autocontrast(img)
            img = img.filter(ImageFilter.SHARPEN)

            # Try multi-language OCR: ron+rus+eng
            try:
                text = pytesseract.image_to_string(img, lang="ron+rus+eng")
            except pytesseract.TesseractError:
                # Fall back to english-only if language packs are missing
                text = pytesseract.image_to_string(img)
        except Exception as e:
            return {
                "extracted": {}, "confidence": 0.0, "fields_found": 0,
                "method": "ocr_failed", "error": str(e), "ocr_text": "",
            }

        if not text.strip():
            return {
                "extracted": {}, "confidence": 0.0, "fields_found": 0,
                "method": "ocr_empty", "ocr_text": "",
            }

        result = self.parse(text)
        result["method"] = f"ocr+{result.get('method', 'rules')}"
        result["ocr_text"] = text
        return result

    # ── Public API ───────────────────────────────────────────────
    def parse(self, text: str) -> dict:
        if not text or not text.strip():
            return {"extracted": {}, "confidence": 0.0, "fields_found": 0, "method": "empty"}

        extracted = self._rule_extract(text)

        # Fill gaps via ML
        ml = self._ml_extract(text)
        for k, v in ml.items():
            extracted.setdefault(k, v)

        # Compute confidence heuristically: coverage of important fields
        important = ["first_name", "last_name", "birth_date", "phone", "insurance_number"]
        found = sum(1 for k in important if k in extracted)
        confidence = round(found / len(important), 2)

        # Propose email if missing but names exist
        if "email" not in extracted and extracted.get("first_name") and extracted.get("last_name"):
            fn = extracted["first_name"].split()[0].lower()
            ln = extracted["last_name"].split()[-1].lower()
            fn = re.sub(r"[^a-z]", "", fn)
            ln = re.sub(r"[^a-z]", "", ln)
            if fn and ln:
                extracted["email_suggestion"] = f"{fn}.{ln}@patient.hospital.md"

        return {
            "extracted": extracted,
            "confidence": confidence,
            "fields_found": len(extracted),
            "method": "hybrid" if ml else "rules",
        }

    def run(self) -> dict:
        """Agent status / self-describe."""
        return {
            "agent": self.name,
            "description": self.description,
            "model_loaded": self._model_data is not None,
            "supported_fields": list({v for v in KEYWORD_TO_FIELD.values()} | {"email"}),
            "languages": ["ro", "ru"],
        }
