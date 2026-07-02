import re
import pandas as pd
from pypdf import PdfReader


SKILL_KEYWORDS = {
    "Software": ["software", "application", "system", "platform", "development", "code"],
    "Data Analysis": ["data", "analysis", "dashboard", "report", "metric", "kpi"],
    "Industrial Engineering": ["process", "optimization", "capacity", "workflow", "efficiency"],
    "Project Management": ["planning", "coordination", "schedule", "timeline", "management"],
    "System Engineering": ["requirement", "architecture", "integration", "validation"],
    "Electronics": ["sensor", "hardware", "circuit", "embedded", "electronic"]
}


def extract_text_from_pdf(uploaded_pdf):
    reader = PdfReader(uploaded_pdf)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def clean_text(text):
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_into_sentences(text):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 30]


def detect_skill(sentence):
    sentence_lower = sentence.lower()

    scores = {}

    for skill, keywords in SKILL_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in sentence_lower)
        scores[skill] = score

    best_skill = max(scores, key=scores.get)

    if scores[best_skill] == 0:
        return "Project Management"

    return best_skill


def estimate_priority(sentence):
    sentence_lower = sentence.lower()

    high_words = ["critical", "urgent", "important", "risk", "must", "required", "mandatory"]
    medium_words = ["should", "support", "improve", "analyze", "develop"]

    if any(word in sentence_lower for word in high_words):
        return 5

    if any(word in sentence_lower for word in medium_words):
        return 4

    return 3


def estimate_workload(sentence):
    length = len(sentence)

    if length > 250:
        return 48

    if length > 150:
        return 32

    return 24


def generate_wbs_from_text(text, project_name="Imported Project"):
    text = clean_text(text)
    sentences = split_into_sentences(text)

    selected_sentences = sentences[:12]

    rows = []

    for i, sentence in enumerate(selected_sentences, start=1):
        task_name = create_task_name(sentence)

        rows.append({
            "task_id": f"PDF_T{i}",
            "project_name": project_name,
            "wbs_level": f"1.{i}",
            "task_name": task_name,
            "required_skill": detect_skill(sentence),
            "workload_hours": estimate_workload(sentence),
            "priority": estimate_priority(sentence),
            "start_day": max(1, i * 2),
            "deadline_day": max(7, i * 2 + 10),
            "source_text": sentence
        })

    return pd.DataFrame(rows)


def create_task_name(sentence):
    words = sentence.split()

    important_words = [
        word.strip(",.:;()")
        for word in words
        if len(word.strip(",.:;()")) > 4
    ]

    title = " ".join(important_words[:5])

    if not title:
        title = "Project Task"

    return title.title()


def convert_wbs_for_optimization(wbs_df):
    required_columns = [
        "task_id",
        "project_name",
        "wbs_level",
        "task_name",
        "required_skill",
        "workload_hours",
        "priority",
        "start_day",
        "deadline_day"
    ]

    return wbs_df[required_columns].copy()