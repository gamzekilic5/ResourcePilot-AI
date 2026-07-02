def validate_data(tasks, resources):
    warnings = []

    required_task_cols = {
        "task_id", "project_name", "wbs_level", "task_name",
        "required_skill", "workload_hours", "priority",
        "start_day", "deadline_day"
    }

    required_resource_cols = {
        "resource_id", "name", "skill", "weekly_capacity_hours",
        "availability", "cost_per_hour", "seniority"
    }

    missing_tasks = required_task_cols - set(tasks.columns)
    missing_resources = required_resource_cols - set(resources.columns)

    if missing_tasks:
        warnings.append("Missing task columns: " + ", ".join(sorted(missing_tasks)))

    if missing_resources:
        warnings.append("Missing resource columns: " + ", ".join(sorted(missing_resources)))

    if warnings:
        return warnings

    if tasks["task_id"].duplicated().any():
        warnings.append("Duplicate task IDs found.")

    if resources["resource_id"].duplicated().any():
        warnings.append("Duplicate resource IDs found.")

    if tasks["workload_hours"].le(0).any():
        warnings.append("Some tasks have zero or negative workload.")

    if resources["weekly_capacity_hours"].le(0).any():
        warnings.append("Some resources have zero or negative weekly capacity.")

    if tasks["priority"].lt(1).any() or tasks["priority"].gt(5).any():
        warnings.append("Priority values should be between 1 and 5.")

    if (tasks["deadline_day"] < tasks["start_day"]).any():
        warnings.append("Some tasks have deadline earlier than start day.")

    task_skills = set(tasks["required_skill"].dropna().unique())
    available_resource_skills = set(
        resources.loc[resources["availability"] == 1, "skill"].dropna().unique()
    )

    uncovered_skills = task_skills - available_resource_skills

    if uncovered_skills:
        warnings.append(
            "No available resource found for skill(s): "
            + ", ".join(sorted(uncovered_skills))
        )

    return warnings