"""
Complete training script for all 7 Hospital DSS AI Agents.
Generates data, trains models, evaluates, saves with versioning.

Usage:
    python train_agents.py           # Train all agents
    python train_agents.py --agent resource   # Train specific agent
    python train_agents.py --generate-only    # Only generate data
"""
import os
import sys
import json
import pickle
import logging
import argparse
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, mean_absolute_error, mean_squared_error, r2_score,
)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('training.log', encoding='utf-8'),
    ],
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "training_data")
MODEL_DIR = os.path.join(BASE_DIR, "saved_models")
REPORT_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


def save_model(model, name: str, version: str = None, metadata: dict = None):
    """Save model with versioning."""
    if version is None:
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = os.path.join(MODEL_DIR, f"{name}_v{version}.pkl")
    latest_path = os.path.join(MODEL_DIR, f"{name}_latest.pkl")

    with open(model_path, "wb") as f:
        pickle.dump({"model": model, "version": version, "metadata": metadata or {}}, f)
    with open(latest_path, "wb") as f:
        pickle.dump({"model": model, "version": version, "metadata": metadata or {}}, f)

    logger.info(f"Model saved: {model_path}")
    return model_path


def load_model(name: str):
    """Load latest model."""
    path = os.path.join(MODEL_DIR, f"{name}_latest.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


def save_report(report: dict, name: str):
    """Save evaluation report as JSON."""
    path = os.path.join(REPORT_DIR, f"{name}_report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"Report saved: {path}")


# ═══════════════════════════════════════════════════════════════
# 1. RESOURCE ALLOCATION AGENT
# ═══════════════════════════════════════════════════════════════
def train_resource_agent():
    logger.info("=" * 60)
    logger.info("Training Resource Allocation Agent (RandomForest)")
    logger.info("=" * 60)

    df = pd.read_csv(os.path.join(DATA_DIR, "resource_allocation.csv"))
    logger.info(f"Loaded {len(df)} samples")

    # Features
    feature_cols = [
        "day_of_week", "hour", "month", "total_beds",
        "occupied_beds", "free_beds", "occupancy_rate",
        "avg_stay_days", "admissions_today", "discharges_today",
    ]
    # Encode ward
    le_ward = LabelEncoder()
    df["ward_encoded"] = le_ward.fit_transform(df["ward"])
    feature_cols.append("ward_encoded")

    X = df[feature_cols].values
    y_realloc = df["needs_reallocation"].values
    y_urgency = df["urgency_level"].values

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y_realloc, test_size=0.2, random_state=42)

    # Train: RandomForest for reallocation need
    rf_model = RandomForestClassifier(
        n_estimators=100, max_depth=10, min_samples_split=5, random_state=42, n_jobs=-1,
    )
    rf_model.fit(X_train, y_train)
    y_pred = rf_model.predict(X_test)

    # Evaluate
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    # Cross-validation
    cv_scores = cross_val_score(rf_model, X, y_realloc, cv=5, scoring='accuracy')

    logger.info(f"Accuracy:  {acc:.4f}")
    logger.info(f"Precision: {prec:.4f}")
    logger.info(f"Recall:    {rec:.4f}")
    logger.info(f"F1 Score:  {f1:.4f}")
    logger.info(f"CV Scores: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # Feature importance
    importances = dict(zip(feature_cols, rf_model.feature_importances_))
    top_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:5]
    logger.info(f"Top features: {top_features}")

    # Train: GradientBoosting for urgency level
    X_train_u, X_test_u, y_train_u, y_test_u = train_test_split(X, y_urgency, test_size=0.2, random_state=42)
    gb_model = GradientBoostingClassifier(
        n_estimators=80, max_depth=5, learning_rate=0.1, random_state=42,
    )
    gb_model.fit(X_train_u, y_train_u)
    y_pred_u = gb_model.predict(X_test_u)
    acc_u = accuracy_score(y_test_u, y_pred_u)
    logger.info(f"Urgency classifier accuracy: {acc_u:.4f}")

    report = {
        "agent": "resource_allocation",
        "model_type": "RandomForestClassifier + GradientBoostingClassifier",
        "samples": len(df),
        "features": feature_cols,
        "reallocation_metrics": {
            "accuracy": round(acc, 4), "precision": round(prec, 4),
            "recall": round(rec, 4), "f1": round(f1, 4),
            "cv_mean": round(cv_scores.mean(), 4), "cv_std": round(cv_scores.std(), 4),
        },
        "urgency_metrics": {"accuracy": round(acc_u, 4)},
        "feature_importance": {k: round(v, 4) for k, v in importances.items()},
        "trained_at": datetime.now().isoformat(),
    }

    save_model({"rf": rf_model, "gb": gb_model, "le_ward": le_ward, "scaler": None},
               "resource_agent", metadata=report)
    save_report(report, "resource_agent")
    return report


# ═══════════════════════════════════════════════════════════════
# 2. SCHEDULING AGENT
# ═══════════════════════════════════════════════════════════════
def train_scheduling_agent():
    logger.info("=" * 60)
    logger.info("Training Scheduling Agent (Optimization + ML)")
    logger.info("=" * 60)

    df = pd.read_csv(os.path.join(DATA_DIR, "scheduling.csv"))
    logger.info(f"Loaded {len(df)} samples")

    # Encode categoricals
    le_specialty = LabelEncoder()
    le_type = LabelEncoder()
    le_status = LabelEncoder()
    df["specialty_enc"] = le_specialty.fit_transform(df["specialty"])
    df["type_enc"] = le_type.fit_transform(df["appointment_type"])
    df["status_enc"] = le_status.fit_transform(df["status"])

    # --- Model 1: Conflict prediction ---
    feature_cols = ["day_of_week", "hour", "minute", "specialty_enc", "type_enc",
                    "duration_minutes", "doctor_daily_load", "wait_days"]
    X = df[feature_cols].values
    y = df["has_conflict"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    conflict_model = GradientBoostingClassifier(
        n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42,
    )
    conflict_model.fit(X_train, y_train)
    y_pred = conflict_model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cv_scores = cross_val_score(conflict_model, X, y, cv=5, scoring='f1')
    logger.info(f"Conflict model - Accuracy: {acc:.4f}, F1: {f1:.4f}")
    logger.info(f"CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # --- Model 2: Optimal slot scoring ---
    X_opt = df[feature_cols].values
    y_opt = df["optimal_score"].values

    from sklearn.ensemble import RandomForestRegressor
    X_train_o, X_test_o, y_train_o, y_test_o = train_test_split(X_opt, y_opt, test_size=0.2, random_state=42)

    slot_model = RandomForestRegressor(n_estimators=80, max_depth=8, random_state=42, n_jobs=-1)
    slot_model.fit(X_train_o, y_train_o)
    y_pred_o = slot_model.predict(X_test_o)

    mae = mean_absolute_error(y_test_o, y_pred_o)
    r2 = r2_score(y_test_o, y_pred_o)
    logger.info(f"Slot scoring - MAE: {mae:.4f}, R²: {r2:.4f}")

    report = {
        "agent": "scheduling",
        "model_type": "GradientBoosting (conflict) + RandomForestRegressor (scoring)",
        "samples": len(df),
        "conflict_metrics": {
            "accuracy": round(acc, 4), "f1": round(f1, 4),
            "cv_f1_mean": round(cv_scores.mean(), 4),
        },
        "slot_scoring_metrics": {"mae": round(mae, 4), "r2": round(r2, 4)},
        "trained_at": datetime.now().isoformat(),
    }

    save_model({
        "conflict": conflict_model, "slot_scorer": slot_model,
        "le_specialty": le_specialty, "le_type": le_type,
    }, "scheduling_agent", metadata=report)
    save_report(report, "scheduling_agent")
    return report


# ═══════════════════════════════════════════════════════════════
# 3. MONITORING AGENT (IsolationForest for anomalies)
# ═══════════════════════════════════════════════════════════════
def train_monitoring_agent():
    logger.info("=" * 60)
    logger.info("Training Monitoring Agent (IsolationForest)")
    logger.info("=" * 60)

    df = pd.read_csv(os.path.join(DATA_DIR, "monitoring.csv"))
    logger.info(f"Loaded {len(df)} samples")

    le_type = LabelEncoder()
    df["type_enc"] = le_type.fit_transform(df["resource_type"])

    feature_cols = ["type_enc", "quantity", "min_quantity", "normal_range_low",
                    "normal_range_high", "usage_rate_daily", "days_until_empty",
                    "hour", "day_of_week"]

    df_filled = df[feature_cols].fillna(0)
    X = df_filled.values
    y_true = df["is_anomaly"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # IsolationForest - unsupervised anomaly detection
    contamination = y_true.mean()
    iso_model = IsolationForest(
        n_estimators=150, contamination=min(contamination, 0.3),
        max_samples='auto', random_state=42, n_jobs=-1,
    )
    iso_model.fit(X_scaled)

    # Predict: -1 = anomaly, 1 = normal
    y_pred_iso = iso_model.predict(X_scaled)
    y_pred_binary = (y_pred_iso == -1).astype(int)

    acc = accuracy_score(y_true, y_pred_binary)
    prec = precision_score(y_true, y_pred_binary, zero_division=0)
    rec = recall_score(y_true, y_pred_binary, zero_division=0)
    f1 = f1_score(y_true, y_pred_binary, zero_division=0)

    logger.info(f"Anomaly detection - Accuracy: {acc:.4f}")
    logger.info(f"Precision: {prec:.4f}, Recall: {rec:.4f}, F1: {f1:.4f}")

    # Supervised model for alert level classification
    le_alert = LabelEncoder()
    y_alert = le_alert.fit_transform(df["alert_level"])

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_alert, test_size=0.2, random_state=42)
    alert_model = RandomForestClassifier(n_estimators=80, max_depth=8, random_state=42)
    alert_model.fit(X_train, y_train)
    y_pred_alert = alert_model.predict(X_test)
    alert_acc = accuracy_score(y_test, y_pred_alert)
    logger.info(f"Alert level classifier accuracy: {alert_acc:.4f}")

    report = {
        "agent": "monitoring",
        "model_type": "IsolationForest (anomaly) + RandomForest (alert level)",
        "samples": len(df),
        "contamination_rate": round(contamination, 4),
        "anomaly_metrics": {
            "accuracy": round(acc, 4), "precision": round(prec, 4),
            "recall": round(rec, 4), "f1": round(f1, 4),
        },
        "alert_classifier_accuracy": round(alert_acc, 4),
        "trained_at": datetime.now().isoformat(),
    }

    save_model({
        "isolation_forest": iso_model, "alert_classifier": alert_model,
        "scaler": scaler, "le_type": le_type, "le_alert": le_alert,
    }, "monitoring_agent", metadata=report)
    save_report(report, "monitoring_agent")
    return report


# ═══════════════════════════════════════════════════════════════
# 4. PREDICTIVE AGENT (Time Series)
# ═══════════════════════════════════════════════════════════════
def train_predictive_agent():
    logger.info("=" * 60)
    logger.info("Training Predictive Agent (Time Series)")
    logger.info("=" * 60)

    df = pd.read_csv(os.path.join(DATA_DIR, "predictive_timeseries.csv"))
    logger.info(f"Loaded {len(df)} samples")

    # Feature engineering
    feature_cols = ["day_of_week", "month", "year", "is_holiday"]

    # Lag features
    df["patients_lag1"] = df["total_patients"].shift(1).fillna(df["total_patients"].mean())
    df["patients_lag7"] = df["total_patients"].shift(7).fillna(df["total_patients"].mean())
    df["patients_rolling7"] = df["total_patients"].rolling(7, min_periods=1).mean()
    df["patients_rolling30"] = df["total_patients"].rolling(30, min_periods=1).mean()
    feature_cols += ["patients_lag1", "patients_lag7", "patients_rolling7", "patients_rolling30"]

    X = df[feature_cols].values
    y_patients = df["total_patients"].values
    y_beds = df["beds_needed"].values

    # Train/test split (time-based)
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y_patients[:split_idx], y_patients[split_idx:]

    # GradientBoosting Regressor for patient count
    from sklearn.ensemble import GradientBoostingRegressor
    patient_model = GradientBoostingRegressor(
        n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42,
    )
    patient_model.fit(X_train, y_train)
    y_pred = patient_model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    logger.info(f"Patient prediction - MAE: {mae:.2f}, RMSE: {rmse:.2f}, R²: {r2:.4f}")

    # Bed demand model
    y_train_b, y_test_b = y_beds[:split_idx], y_beds[split_idx:]
    bed_model = GradientBoostingRegressor(
        n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42,
    )
    bed_model.fit(X_train, y_train_b)
    y_pred_b = bed_model.predict(X_test)
    mae_b = mean_absolute_error(y_test_b, y_pred_b)
    r2_b = r2_score(y_test_b, y_pred_b)
    logger.info(f"Bed demand - MAE: {mae_b:.2f}, R²: {r2_b:.4f}")

    report = {
        "agent": "predictive",
        "model_type": "GradientBoostingRegressor (patients + beds)",
        "samples": len(df),
        "train_size": split_idx,
        "test_size": len(df) - split_idx,
        "patient_metrics": {"mae": round(mae, 2), "rmse": round(rmse, 2), "r2": round(r2, 4)},
        "bed_metrics": {"mae": round(mae_b, 2), "r2": round(r2_b, 4)},
        "features": feature_cols,
        "trained_at": datetime.now().isoformat(),
    }

    save_model({
        "patient_model": patient_model, "bed_model": bed_model,
    }, "predictive_agent", metadata=report)
    save_report(report, "predictive_agent")
    return report


# ═══════════════════════════════════════════════════════════════
# 5. RECOMMENDATION AGENT (TF-IDF + Cosine Similarity)
# ═══════════════════════════════════════════════════════════════
def train_recommendation_agent():
    logger.info("=" * 60)
    logger.info("Training Recommendation Agent (TF-IDF + Cosine)")
    logger.info("=" * 60)

    df = pd.read_csv(os.path.join(DATA_DIR, "recommendations.csv"))
    logger.info(f"Loaded {len(df)} samples")

    # TF-IDF on conditions for patient similarity
    tfidf = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
    conditions_tfidf = tfidf.fit_transform(df["conditions"].str.replace("|", " "))
    logger.info(f"TF-IDF matrix shape: {conditions_tfidf.shape}")

    # Similarity matrix (for a subset to save memory)
    sample_idx = np.random.choice(len(df), min(500, len(df)), replace=False)
    sample_matrix = conditions_tfidf[sample_idx]
    sim_matrix = cosine_similarity(sample_matrix)
    avg_similarity = sim_matrix[sim_matrix < 1.0].mean()
    logger.info(f"Average patient similarity: {avg_similarity:.4f}")

    # Risk level classifier
    le_risk = LabelEncoder()
    y_risk = le_risk.fit_transform(df["risk_level"])

    feature_cols = ["age", "n_conditions", "n_previous_visits",
                    "days_since_last_visit", "compliance_score"]
    le_gender = LabelEncoder()
    df["gender_enc"] = le_gender.fit_transform(df["gender"])
    feature_cols.append("gender_enc")
    le_spec = LabelEncoder()
    df["spec_enc"] = le_spec.fit_transform(df["specialty"])
    feature_cols.append("spec_enc")

    X = df[feature_cols].values
    X_train, X_test, y_train, y_test = train_test_split(X, y_risk, test_size=0.2, random_state=42)

    risk_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    risk_model.fit(X_train, y_train)
    y_pred = risk_model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    cv_scores = cross_val_score(risk_model, X, y_risk, cv=5, scoring='accuracy')
    logger.info(f"Risk classifier - Accuracy: {acc:.4f}")
    logger.info(f"CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    logger.info(f"\n{classification_report(y_test, y_pred, target_names=le_risk.classes_)}")

    # Follow-up predictor
    y_follow = df["needs_followup"].values
    X_train_f, X_test_f, y_train_f, y_test_f = train_test_split(X, y_follow, test_size=0.2, random_state=42)
    follow_model = LogisticRegression(max_iter=1000, random_state=42)
    follow_model.fit(X_train_f, y_train_f)
    follow_acc = accuracy_score(y_test_f, follow_model.predict(X_test_f))
    follow_f1 = f1_score(y_test_f, follow_model.predict(X_test_f))
    logger.info(f"Follow-up predictor - Accuracy: {follow_acc:.4f}, F1: {follow_f1:.4f}")

    report = {
        "agent": "recommendation",
        "model_type": "TF-IDF + CosineSimlarity + RandomForest (risk) + LogisticRegression (followup)",
        "samples": len(df),
        "tfidf_features": conditions_tfidf.shape[1],
        "avg_patient_similarity": round(avg_similarity, 4),
        "risk_classifier": {
            "accuracy": round(acc, 4),
            "cv_mean": round(cv_scores.mean(), 4),
            "cv_std": round(cv_scores.std(), 4),
        },
        "followup_predictor": {
            "accuracy": round(follow_acc, 4), "f1": round(follow_f1, 4),
        },
        "trained_at": datetime.now().isoformat(),
    }

    save_model({
        "tfidf": tfidf, "risk_model": risk_model, "follow_model": follow_model,
        "le_risk": le_risk, "le_gender": le_gender, "le_spec": le_spec,
    }, "recommendation_agent", metadata=report)
    save_report(report, "recommendation_agent")
    return report


# ═══════════════════════════════════════════════════════════════
# 6. NOTIFICATION AGENT (Priority rules + ML)
# ═══════════════════════════════════════════════════════════════
def train_notification_agent():
    logger.info("=" * 60)
    logger.info("Training Notification Agent (Priority Queue + ML)")
    logger.info("=" * 60)

    df = pd.read_csv(os.path.join(DATA_DIR, "notifications.csv"))
    logger.info(f"Loaded {len(df)} samples")

    le_type = LabelEncoder()
    le_priority = LabelEncoder()
    le_role = LabelEncoder()
    le_channel = LabelEncoder()

    df["type_enc"] = le_type.fit_transform(df["notification_type"])
    df["priority_enc"] = le_priority.fit_transform(df["priority"])
    df["role_enc"] = le_role.fit_transform(df["user_role"])
    df["channel_enc"] = le_channel.fit_transform(df["channel"])

    # Priority prediction model
    feature_cols = ["type_enc", "hour", "day_of_week", "role_enc", "time_sensitivity_hours"]
    X = df[feature_cols].values
    y = df["priority_enc"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    priority_model = GradientBoostingClassifier(
        n_estimators=80, max_depth=5, learning_rate=0.1, random_state=42,
    )
    priority_model.fit(X_train, y_train)
    y_pred = priority_model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    cv_scores = cross_val_score(priority_model, X, y, cv=5, scoring='accuracy')
    logger.info(f"Priority classifier - Accuracy: {acc:.4f}")
    logger.info(f"CV Accuracy: {cv_scores.mean():.4f}")

    # Push notification prediction
    X_push = df[feature_cols + ["priority_enc"]].values
    y_push = df["should_push"].values
    X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(X_push, y_push, test_size=0.2, random_state=42)
    push_model = LogisticRegression(max_iter=500, random_state=42)
    push_model.fit(X_train_p, y_train_p)
    push_acc = accuracy_score(y_test_p, push_model.predict(X_test_p))
    logger.info(f"Push notification model - Accuracy: {push_acc:.4f}")

    report = {
        "agent": "notification",
        "model_type": "GradientBoosting (priority) + LogisticRegression (push)",
        "samples": len(df),
        "priority_metrics": {
            "accuracy": round(acc, 4),
            "cv_mean": round(cv_scores.mean(), 4),
        },
        "push_model_accuracy": round(push_acc, 4),
        "priority_classes": list(le_priority.classes_),
        "trained_at": datetime.now().isoformat(),
    }

    save_model({
        "priority_model": priority_model, "push_model": push_model,
        "le_type": le_type, "le_priority": le_priority,
        "le_role": le_role, "le_channel": le_channel,
    }, "notification_agent", metadata=report)
    save_report(report, "notification_agent")
    return report


# ═══════════════════════════════════════════════════════════════
# 7. HELP AGENT (TF-IDF Q&A with multilingual support)
# ═══════════════════════════════════════════════════════════════
def train_help_agent():
    logger.info("=" * 60)
    logger.info("Training Help Agent (TF-IDF multilingual Q&A)")
    logger.info("=" * 60)

    qa_path = os.path.join(DATA_DIR, "help_agent_qa.json")
    with open(qa_path, "r", encoding="utf-8") as f:
        qa_data = json.load(f)

    pairs = qa_data["qa_pairs"]
    logger.info(f"Loaded {len(pairs)} Q&A pairs")

    # Build corpus: combine RO and RU questions + keywords
    corpus_questions = []
    corpus_answers_ro = []
    corpus_answers_ru = []
    corpus_categories = []
    corpus_keywords = []

    for pair in pairs:
        # Romanian question
        corpus_questions.append(pair["question_ro"])
        corpus_answers_ro.append(pair["answer_ro"])
        corpus_answers_ru.append(pair["answer_ru"])
        corpus_categories.append(pair["category"])
        corpus_keywords.append(" ".join(pair["keywords"]))

        # Russian question (for multilingual support)
        corpus_questions.append(pair["question_ru"])
        corpus_answers_ro.append(pair["answer_ro"])
        corpus_answers_ru.append(pair["answer_ru"])
        corpus_categories.append(pair["category"])
        corpus_keywords.append(" ".join(pair["keywords"]))

    # TF-IDF on questions + keywords combined
    combined_text = [f"{q} {k}" for q, k in zip(corpus_questions, corpus_keywords)]

    tfidf = TfidfVectorizer(
        max_features=500, ngram_range=(1, 3),
        sublinear_tf=True, min_df=1,
    )
    tfidf_matrix = tfidf.fit_transform(combined_text)
    logger.info(f"TF-IDF matrix: {tfidf_matrix.shape}")

    # Category classifier
    le_cat = LabelEncoder()
    y_cat = le_cat.fit_transform(corpus_categories)

    from sklearn.svm import LinearSVC
    cat_model = LinearSVC(max_iter=2000, random_state=42)
    cat_model.fit(tfidf_matrix, y_cat)

    # Cross-validate
    cv_scores = cross_val_score(cat_model, tfidf_matrix, y_cat, cv=min(5, len(set(y_cat))), scoring='accuracy')
    logger.info(f"Category classifier CV accuracy: {cv_scores.mean():.4f}")

    # Test retrieval accuracy
    correct = 0
    total = len(pairs)
    for pair in pairs:
        query = pair["question_ro"]
        query_vec = tfidf.transform([query + " " + " ".join(pair["keywords"])])
        sims = cosine_similarity(query_vec, tfidf_matrix).flatten()
        best_idx = sims.argmax()
        retrieved_answer = corpus_answers_ro[best_idx]
        if retrieved_answer == pair["answer_ro"]:
            correct += 1

    retrieval_acc = correct / total
    logger.info(f"Retrieval accuracy (RO): {retrieval_acc:.4f}")

    # Test Russian retrieval
    correct_ru = 0
    for pair in pairs:
        query = pair["question_ru"]
        query_vec = tfidf.transform([query + " " + " ".join(pair["keywords"])])
        sims = cosine_similarity(query_vec, tfidf_matrix).flatten()
        best_idx = sims.argmax()
        retrieved_answer = corpus_answers_ru[best_idx]
        if retrieved_answer == pair["answer_ru"]:
            correct_ru += 1

    retrieval_acc_ru = correct_ru / total
    logger.info(f"Retrieval accuracy (RU): {retrieval_acc_ru:.4f}")

    report = {
        "agent": "help",
        "model_type": "TF-IDF + CosineSimilarity + LinearSVC (category)",
        "qa_pairs": len(pairs),
        "languages": ["ro", "ru"],
        "categories": list(le_cat.classes_),
        "tfidf_features": tfidf_matrix.shape[1],
        "category_cv_accuracy": round(cv_scores.mean(), 4),
        "retrieval_accuracy_ro": round(retrieval_acc, 4),
        "retrieval_accuracy_ru": round(retrieval_acc_ru, 4),
        "trained_at": datetime.now().isoformat(),
    }

    save_model({
        "tfidf": tfidf, "tfidf_matrix": tfidf_matrix,
        "cat_model": cat_model, "le_cat": le_cat,
        "corpus_questions": corpus_questions,
        "corpus_answers_ro": corpus_answers_ro,
        "corpus_answers_ru": corpus_answers_ru,
        "corpus_categories": corpus_categories,
        "corpus_keywords": corpus_keywords,
        "qa_data": qa_data,
    }, "help_agent", metadata=report)
    save_report(report, "help_agent")
    return report


# ═══════════════════════════════════════════════════════════════
# GENERATE DATA + MAIN
# ═══════════════════════════════════════════════════════════════
def generate_data():
    """Generate all synthetic training data."""
    logger.info("Generating synthetic training data...")
    from generate_training_data import (
        generate_resource_data, generate_scheduling_data,
        generate_monitoring_data, generate_predictive_data,
        generate_recommendation_data, generate_notification_data,
    )
    generate_resource_data()
    generate_scheduling_data()
    generate_monitoring_data()
    generate_predictive_data()
    generate_recommendation_data()
    generate_notification_data()
    logger.info("All training data generated.")


def train_all():
    """Train all agents and generate combined report."""
    reports = {}

    agents = {
        "resource": train_resource_agent,
        "scheduling": train_scheduling_agent,
        "monitoring": train_monitoring_agent,
        "predictive": train_predictive_agent,
        "recommendation": train_recommendation_agent,
        "notification": train_notification_agent,
        "help": train_help_agent,
    }

    for name, train_fn in agents.items():
        try:
            reports[name] = train_fn()
        except Exception as e:
            logger.error(f"Failed to train {name}: {e}")
            reports[name] = {"error": str(e)}

    # Combined report
    combined = {
        "training_session": datetime.now().isoformat(),
        "agents_trained": len([r for r in reports.values() if "error" not in r]),
        "agents_failed": len([r for r in reports.values() if "error" in r]),
        "reports": reports,
    }
    save_report(combined, "combined_training")

    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE - Summary:")
    logger.info("=" * 60)
    for name, report in reports.items():
        if "error" in report:
            logger.info(f"  {name}: FAILED - {report['error']}")
        else:
            logger.info(f"  {name}: OK")
    logger.info("=" * 60)

    return combined


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Hospital DSS AI Agents")
    parser.add_argument("--agent", type=str, help="Train specific agent", default=None)
    parser.add_argument("--generate-only", action="store_true", help="Only generate training data")
    args = parser.parse_args()

    if args.generate_only:
        generate_data()
        sys.exit(0)

    # Check if data exists
    csv_files = ["resource_allocation.csv", "scheduling.csv", "monitoring.csv",
                 "predictive_timeseries.csv", "recommendations.csv", "notifications.csv"]
    missing = [f for f in csv_files if not os.path.exists(os.path.join(DATA_DIR, f))]
    if missing:
        logger.info(f"Missing data files: {missing}. Generating...")
        generate_data()

    if args.agent:
        agent_map = {
            "resource": train_resource_agent,
            "scheduling": train_scheduling_agent,
            "monitoring": train_monitoring_agent,
            "predictive": train_predictive_agent,
            "recommendation": train_recommendation_agent,
            "notification": train_notification_agent,
            "help": train_help_agent,
        }
        if args.agent in agent_map:
            agent_map[args.agent]()
        else:
            logger.error(f"Unknown agent: {args.agent}. Available: {list(agent_map.keys())}")
    else:
        train_all()
