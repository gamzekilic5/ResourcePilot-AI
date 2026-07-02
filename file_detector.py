import pandas as pd


def read_any_file(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file), "excel"

    if file_name.endswith(".csv") or file_name.endswith(".txt"):
        try:
            df = pd.read_csv(uploaded_file)
            if df.shape[1] == 1:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=r"\s+", header=None)
                return df, "space_separated"
            return df, "csv"
        except Exception:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=r"\s+", header=None)
            return df, "space_separated"

    return None, "unsupported"


def detect_dataset_type(df):
    columns = [str(c).lower().strip() for c in df.columns]

    work_package_keywords = [
        "task_id", "project_name", "wbs_level", "task_name",
        "required_skill", "workload_hours", "priority", "deadline_day"
    ]

    resource_keywords = [
        "resource_id", "name", "skill", "weekly_capacity_hours",
        "availability", "cost_per_hour", "seniority"
    ]

    work_score = sum(1 for col in columns if col in work_package_keywords)
    resource_score = sum(1 for col in columns if col in resource_keywords)

    if work_score >= 4:
        return "Work Package Dataset"

    if resource_score >= 4:
        return "Resource Dataset"

    if df.shape[1] == 3:
        numeric_cols = 0
        for col in df.columns:
            if pd.to_numeric(df[col], errors="coerce").notna().mean() > 0.8:
                numeric_cols += 1

        if numeric_cols == 3:
            return "Coordinate Dataset"

    return "Unknown Dataset"


def convert_coordinate_dataset(df):
    converted = df.copy()
    converted.columns = ["point_id", "x", "y"]
    return converted


def dataset_summary(df, file_type, dataset_type):
    return {
        "file_type": file_type,
        "dataset_type": dataset_type,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns)
    }