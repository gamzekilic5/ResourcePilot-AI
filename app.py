from pathlib import Path

from wbs_assistant import extract_text_from_pdf, generate_wbs_from_text, convert_wbs_for_optimization
import pandas as pd
import plotly.express as px
import streamlit as st

from optimizer import optimized_plan, greedy_plan, kpis, planning_notes, apply_what_if
from validation import validate_data
from report import save_report
from evaluation import evaluate_solution
from file_detector import read_any_file, detect_dataset_type, convert_coordinate_dataset, dataset_summary

DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="ResourcePilot Pro",
    page_icon="📊",
    layout="wide"
)

st.title("Resource Pilot")
st.caption("Project resource planning, WBS assignment and decision support dashboard")


TASK_COLUMNS = [
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

RESOURCE_COLUMNS = [
    "resource_id",
    "name",
    "skill",
    "weekly_capacity_hours",
    "availability",
    "cost_per_hour",
    "seniority"
]


TASK_ALIASES = {
    "task_id": ["task id", "id", "task"],
    "project_name": ["project name", "project", "project title"],
    "wbs_level": ["wbs", "wbs level", "work breakdown"],
    "task_name": ["task name", "activity", "work package", "task title"],
    "required_skill": ["required skill", "skill", "expertise", "skill needed"],
    "workload_hours": ["workload", "hours", "effort", "workload hours"],
    "priority": ["priority", "importance"],
    "start_day": ["start", "start day", "begin day"],
    "deadline_day": ["deadline", "deadline day", "due date", "finish day"]
}

RESOURCE_ALIASES = {
    "resource_id": ["resource id", "id", "employee id"],
    "name": ["name", "engineer", "resource name", "employee"],
    "skill": ["skill", "expertise", "department", "area"],
    "weekly_capacity_hours": ["capacity", "weekly capacity", "weekly hours"],
    "availability": ["availability", "available", "status"],
    "cost_per_hour": ["cost", "hourly cost", "cost per hour"],
    "seniority": ["seniority", "level", "experience"]
}


def normalize_text(text):
    return str(text).strip().lower().replace("-", " ").replace("_", " ")


def read_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return None

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if file_name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)

    st.error("Unsupported file type. Please upload CSV or Excel.")
    return None


def guess_column_mapping(df, required_columns, aliases):
    original_columns = list(df.columns)
    normalized_columns = {normalize_text(col): col for col in original_columns}

    mapping = {}

    for required_col in required_columns:
        possible_names = [required_col] + aliases.get(required_col, [])
        found = None

        for name in possible_names:
            norm_name = normalize_text(name)
            if norm_name in normalized_columns:
                found = normalized_columns[norm_name]
                break

        mapping[required_col] = found

    return mapping


def apply_mapping(df, mapping):
    new_df = pd.DataFrame()

    for standard_col, original_col in mapping.items():
        if original_col and original_col in df.columns:
            new_df[standard_col] = df[original_col]
        else:
            new_df[standard_col] = None

    return new_df


def create_template(columns):
    return pd.DataFrame(columns=columns).to_csv(index=False).encode("utf-8")


@st.cache_data
def load_default_data():
    tasks = pd.read_csv(DATA_DIR / "work_packages.csv")
    resources = pd.read_csv(DATA_DIR / "resources.csv")
    return tasks, resources


with st.sidebar:
    st.header("Data Upload")
    st.subheader("Smart File Detection")

    smart_file = st.file_uploader(
        "Upload any data file",
        type=["csv", "xlsx", "txt"],
        key="smart_file"
    )
    uploaded_tasks = st.file_uploader(
        "Upload work packages file",
        type=["csv", "xlsx"]
    )

    uploaded_resources = st.file_uploader(
        "Upload resources file",
        type=["csv", "xlsx"]
    )

    st.subheader("Templates")

    st.download_button(
        "Download Work Packages Template",
        data=create_template(TASK_COLUMNS),
        file_name="work_packages_template.csv",
        mime="text/csv"
    )

    st.download_button(
        "Download Resources Template",
        data=create_template(RESOURCE_COLUMNS),
        file_name="resources_template.csv",
        mime="text/csv"
    )

    st.header("Scenario")

    method = st.selectbox(
        "Planning method",
        ["Optimized", "Greedy"]
    )


if uploaded_tasks and uploaded_resources:
    raw_tasks_df = read_uploaded_file(uploaded_tasks)
    raw_resources_df = read_uploaded_file(uploaded_resources)

    st.subheader("Column Mapping")

    st.caption(
        "The system tries to match uploaded file columns automatically. "
        "Please review the mapping before generating the plan."
    )

    task_guess = guess_column_mapping(raw_tasks_df, TASK_COLUMNS, TASK_ALIASES)
    resource_guess = guess_column_mapping(raw_resources_df, RESOURCE_COLUMNS, RESOURCE_ALIASES)

    left_map, right_map = st.columns(2)

    task_mapping = {}
    resource_mapping = {}

    with left_map:
        st.write("Work Packages Mapping")

        for col in TASK_COLUMNS:
            options = [None] + list(raw_tasks_df.columns)
            default_index = options.index(task_guess[col]) if task_guess[col] in options else 0

            task_mapping[col] = st.selectbox(
                f"{col}",
                options=options,
                index=default_index,
                key=f"task_map_{col}"
            )

    with right_map:
        st.write("Resources Mapping")

        for col in RESOURCE_COLUMNS:
            options = [None] + list(raw_resources_df.columns)
            default_index = options.index(resource_guess[col]) if resource_guess[col] in options else 0

            resource_mapping[col] = st.selectbox(
                f"{col}",
                options=options,
                index=default_index,
                key=f"resource_map_{col}"
            )

    tasks_df = apply_mapping(raw_tasks_df, task_mapping)
    resources_df = apply_mapping(raw_resources_df, resource_mapping)

else:
    tasks_df, resources_df = load_default_data()


with st.sidebar:
    unavailable = st.multiselect(
        "Set unavailable resources",
        options=list(resources_df["name"]) if "name" in resources_df.columns else []
    )


resources_df = apply_what_if(resources_df, unavailable)
if smart_file is not None:
    detected_df, detected_file_type = read_any_file(smart_file)

    if detected_df is not None:
        detected_type = detect_dataset_type(detected_df)
        summary = dataset_summary(detected_df, detected_file_type, detected_type)

        st.subheader("Smart File Detection Result")

        d1, d2, d3, d4 = st.columns(4)

        d1.metric("Detected Type", summary["dataset_type"])
        d2.metric("File Format", summary["file_type"])
        d3.metric("Rows", summary["rows"])
        d4.metric("Columns", summary["columns"])

        st.write("Detected Columns:")
        st.write(summary["column_names"])

        if detected_type == "Coordinate Dataset":
            converted_coordinates = convert_coordinate_dataset(detected_df)

            st.success(
                "This file looks like a coordinate dataset. "
                "It was converted into point_id, x, y format."
            )

            st.dataframe(converted_coordinates, use_container_width=True)

            st.download_button(
                "Download Converted Coordinate CSV",
                converted_coordinates.to_csv(index=False).encode("utf-8"),
                "converted_coordinates.csv",
                "text/csv"
            )

        elif detected_type in ["Work Package Dataset", "Resource Dataset"]:
            st.success(
                f"This file looks like a {detected_type}. "
                "You can use it in the related upload area."
            )

            st.dataframe(detected_df, use_container_width=True)

        else:
            st.warning(
                "The system could not confidently classify this file. "
                "Please check the file structure or use the provided templates."
            )

            st.dataframe(detected_df, use_container_width=True)
warnings = validate_data(tasks_df, resources_df)

if warnings:
    st.subheader("Validation")
    for warning in warnings:
        st.warning(warning)


tab1, tab2, tab3, tab4 = st.tabs(
    ["Work Packages", "Resources", "WBS View", "PDF to WBS Assistant"]
)

with tab1:
    st.dataframe(tasks_df, use_container_width=True)

with tab2:
    st.dataframe(resources_df, use_container_width=True)

with tab3:
    required_wbs_cols = [
        "project_name",
        "wbs_level",
        "task_name",
        "required_skill",
        "workload_hours",
        "deadline_day"
]
with tab4:
    st.subheader("PDF to WBS Assistant")

    st.caption(
        "Upload a project description PDF. The system will generate a draft WBS. "
        "The output is only a suggestion and should be reviewed by the user before optimization."
    )

    uploaded_pdf = st.file_uploader(
        "Upload project description PDF",
        type=["pdf"],
        key="wbs_pdf"
    )

    project_name_input = st.text_input(
        "Project name",
        value="Imported Project"
    )

    if uploaded_pdf is not None:
        extracted_text = extract_text_from_pdf(uploaded_pdf)

        if st.button("Generate Draft WBS"):
            draft_wbs = generate_wbs_from_text(
                extracted_text,
                project_name=project_name_input
            )

            st.session_state["draft_wbs"] = draft_wbs

    if "draft_wbs" in st.session_state:
        st.write("Draft WBS generated from PDF:")
        st.dataframe(st.session_state["draft_wbs"], use_container_width=True)

        st.warning(
            "This WBS is automatically generated from the PDF. "
            "Please review task names, required skills, workload and deadlines before using it."
        )

        optimization_ready_wbs = convert_wbs_for_optimization(
            st.session_state["draft_wbs"]
        )

        st.download_button(
            "Download WBS as work_packages.csv",
            optimization_ready_wbs.to_csv(index=False).encode("utf-8"),
            "work_packages_from_pdf.csv",
            "text/csv"
        )

    if all(col in tasks_df.columns for col in required_wbs_cols):
        st.dataframe(
            tasks_df[required_wbs_cols],
            use_container_width=True
        )
    else:
        st.warning("WBS View cannot be shown because some required columns are missing.")


if st.button("Generate Plan", type="primary"):
    if warnings:
        st.error("Please fix validation warnings before generating the plan.")
    else:
        if method == "Optimized":
            plan, resource_plan = optimized_plan(tasks_df, resources_df)
        else:
            plan, resource_plan = greedy_plan(tasks_df, resources_df)

        metrics = kpis(plan, resource_plan)
        notes = planning_notes(plan, resource_plan)
        evaluation = evaluate_solution(plan, resource_plan)

        report_path = save_report(
            plan,
            resource_plan,
            notes,
            metrics
        )

        st.session_state["plan"] = plan
        st.session_state["resources"] = resource_plan
        st.session_state["metrics"] = metrics
        st.session_state["notes"] = notes
        st.session_state["evaluation"] = evaluation
        st.session_state["report_path"] = report_path


if "plan" in st.session_state:
    plan = st.session_state["plan"]
    resource_plan = st.session_state["resources"]
    metrics = st.session_state["metrics"]
    notes = st.session_state["notes"]
    evaluation = st.session_state["evaluation"]

    st.subheader("Dashboard")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Tasks", metrics["tasks"])
    c2.metric("Resources", metrics["resources"])
    c3.metric("Assigned", metrics["assigned"])
    c4.metric("Utilization", f'{metrics["utilization"]}%')
    c5.metric("High Risk", metrics["high_risk"])

    st.subheader("Solution Evaluation")

    e1, e2, e3, e4 = st.columns(4)

    e1.metric("Plan Quality", f'{evaluation["overall_score"]}/100')
    e2.metric("Quality Label", evaluation["quality_label"])
    e3.metric("Assignment Rate", f'{evaluation["assignment_rate"]}%')
    e4.metric("High Risk Rate", f'{evaluation["high_risk_rate"]}%')

    st.caption(
        "Plan quality is calculated from assignment rate, resource utilization balance, "
        "and high-risk task ratio. It is a decision-support score, not an absolute guarantee."
    )

    st.subheader("Assignment Plan")
    st.dataframe(plan, use_container_width=True)

    st.subheader("Resource Utilization")
    st.dataframe(resource_plan, use_container_width=True)

    left, right = st.columns(2)

    with left:
        fig = px.bar(
            resource_plan,
            x="name",
            y="utilization_rate",
            color="skill",
            title="Resource Utilization"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        risk = plan["risk_level"].value_counts().reset_index()
        risk.columns = ["risk_level", "count"]

        fig = px.pie(
            risk,
            names="risk_level",
            values="count",
            title="Risk Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Gantt-style Timeline")

    timeline = plan.copy()
    timeline["start_day"] = pd.to_numeric(timeline["start_day"])
    timeline["deadline_day"] = pd.to_numeric(timeline["deadline_day"])
    timeline["duration"] = timeline["deadline_day"] - timeline["start_day"]

    fig = px.bar(
        timeline,
        x="duration",
        y="task_name",
        color="assigned_resource",
        orientation="h",
        base="start_day",
        hover_data=[
            "project_name",
            "required_skill",
            "risk_level",
            "start_day",
            "deadline_day"
        ],
        title="Task Timeline by Planning Day"
    )

    fig.update_layout(
        xaxis_title="Planning Day",
        yaxis_title="Task",
        yaxis=dict(autorange="reversed")
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Planning Notes")

    st.caption(
        "These notes are generated only from the uploaded project and resource data. "
        "They are not external AI predictions."
    )

    for note in notes:
        st.info(note)

    st.download_button(
        "Download Assignment CSV",
        plan.to_csv(index=False).encode("utf-8"),
        "assignment_plan.csv",
        "text/csv"
    )

    st.download_button(
        "Download Resource CSV",
        resource_plan.to_csv(index=False).encode("utf-8"),
        "resource_utilization.csv",
        "text/csv"
    )

    with open(st.session_state["report_path"], "rb") as file:
        st.download_button(
            "Download Planning Report",
            file,
            "planning_report.txt",
            "text/plain"
        )

else:
    st.info("Click Generate Plan to create an assignment plan.")