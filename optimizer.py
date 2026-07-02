import pandas as pd

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except Exception:
    ORTOOLS_AVAILABLE = False


def optimized_plan(tasks, resources):
    if not ORTOOLS_AVAILABLE:
        return greedy_plan(tasks, resources)

    tasks = tasks.copy().reset_index(drop=True)
    resources = resources.copy().reset_index(drop=True)

    model = cp_model.CpModel()
    x = {}

    for i, task in tasks.iterrows():
        for j, res in resources.iterrows():
            if task["required_skill"] == res["skill"] and int(res["availability"]) == 1:
                x[i, j] = model.NewBoolVar(f"x_{i}_{j}")

    for i in range(len(tasks)):
        model.Add(sum(x.get((i, j), 0) for j in range(len(resources))) <= 1)

    for j, res in resources.iterrows():
        model.Add(
            sum(int(tasks.loc[i, "workload_hours"]) * x.get((i, j), 0)
                for i in range(len(tasks))) <= int(res["weekly_capacity_hours"])
        )

    objective_terms = []
    for i, task in tasks.iterrows():
        priority_weight = int(task["priority"]) * 100
        deadline_weight = max(1, 40 - int(task["deadline_day"])) * 5
        workload_weight = int(task["workload_hours"])
        score = priority_weight + deadline_weight + workload_weight

        for j in range(len(resources)):
            if (i, j) in x:
                objective_terms.append(score * x[i, j])

    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    solver.Solve(model)

    resources["used_capacity"] = 0
    resources["remaining_capacity"] = resources["weekly_capacity_hours"]

    rows = []

    for i, task in tasks.iterrows():
        assigned_name = "No suitable resource"
        assigned_hours = 0
        unassigned_hours = float(task["workload_hours"])
        status = "Unassigned"
        reason = get_unassigned_reason(task, resources)

        for j, res in resources.iterrows():
            if (i, j) in x and solver.Value(x[i, j]) == 1:
                assigned_name = res["name"]
                assigned_hours = float(task["workload_hours"])
                unassigned_hours = 0
                status = "Fully Assigned"
                reason = (
                    f"Assigned to {res['name']} because the required skill matches "
                    f"({task['required_skill']}) and enough capacity is available."
                )

                resources.loc[j, "used_capacity"] += assigned_hours
                resources.loc[j, "remaining_capacity"] -= assigned_hours
                break

        rows.append(make_assignment_row(task, assigned_name, assigned_hours, unassigned_hours, status, reason))

    plan = pd.DataFrame(rows)
    resources = add_utilization(resources)
    return plan, resources


def greedy_plan(tasks, resources):
    tasks = tasks.copy()
    resources = resources.copy()

    resources["remaining_capacity"] = resources["weekly_capacity_hours"]
    resources["used_capacity"] = 0

    tasks["urgency_score"] = tasks.apply(urgency_score, axis=1)
    tasks = tasks.sort_values("urgency_score", ascending=False)

    rows = []

    for _, task in tasks.iterrows():
        skill = task["required_skill"]
        workload = float(task["workload_hours"])

        candidates = resources[
            (resources["skill"] == skill)
            & (resources["availability"] == 1)
            & (resources["remaining_capacity"] > 0)
        ].copy()

        if candidates.empty:
            reason = get_unassigned_reason(task, resources)
            rows.append(make_assignment_row(task, "No suitable resource", 0, workload, "Unassigned", reason))
            continue

        selected = candidates.sort_values("remaining_capacity", ascending=False).iloc[0]
        assigned = min(workload, float(selected["remaining_capacity"]))
        unassigned = workload - assigned

        idx = resources[resources["resource_id"] == selected["resource_id"]].index[0]
        resources.loc[idx, "remaining_capacity"] -= assigned
        resources.loc[idx, "used_capacity"] += assigned

        if unassigned == 0:
            status = "Fully Assigned"
            reason = (
                f"Assigned to {selected['name']} because the required skill matches "
                f"({skill}) and the resource has enough remaining capacity."
            )
        else:
            status = "Partially Assigned"
            reason = (
                f"Assigned partially to {selected['name']} because the required skill matches "
                f"({skill}), but remaining capacity is not enough to cover the full workload."
            )

        rows.append(make_assignment_row(task, selected["name"], assigned, unassigned, status, reason))

    plan = pd.DataFrame(rows)
    resources = add_utilization(resources)
    return plan, resources


def urgency_score(row):
    priority = int(row["priority"]) * 10
    deadline_pressure = max(1, 30 - int(row["deadline_day"]))
    workload = float(row["workload_hours"]) / 10
    return priority + deadline_pressure + workload


def get_unassigned_reason(task, resources):
    skill = task["required_skill"]
    workload = float(task["workload_hours"])

    matching_skill = resources[
        (resources["skill"] == skill)
        & (resources["availability"] == 1)
    ]

    if matching_skill.empty:
        return f"No available resource has the required skill: {skill}."

    enough_capacity = matching_skill[matching_skill["weekly_capacity_hours"] >= workload]

    if enough_capacity.empty:
        return (
            f"Resources with skill {skill} exist, but their available capacity is not enough "
            f"for the required workload of {workload} hours."
        )

    return (
        f"Resources with skill {skill} exist, but optimization selected other higher-priority "
        f"or more urgent tasks first."
    )


def make_assignment_row(task, assigned_resource, assigned_hours, unassigned_hours, status, reason):
    risk = calculate_risk(task, status, unassigned_hours)

    return {
        "task_id": task["task_id"],
        "project_name": task["project_name"],
        "wbs_level": task["wbs_level"],
        "task_name": task["task_name"],
        "required_skill": task["required_skill"],
        "assigned_resource": assigned_resource,
        "assigned_hours": assigned_hours,
        "unassigned_hours": unassigned_hours,
        "priority": task["priority"],
        "start_day": task["start_day"],
        "deadline_day": task["deadline_day"],
        "status": status,
        "risk_level": risk,
        "reason": reason
    }


def calculate_risk(task, status, unassigned_hours):
    if status == "Fully Assigned":
        if int(task["priority"]) >= 5 and int(task["deadline_day"]) <= 14:
            return "Medium"
        return "Low"

    if status == "Partially Assigned":
        workload = float(task["workload_hours"])
        if unassigned_hours > workload * 0.4:
            return "High"
        return "Medium"

    return "High"


def add_utilization(resources):
    resources["utilization_rate"] = (
        resources["used_capacity"] / resources["weekly_capacity_hours"] * 100
    ).round(2)
    return resources


def kpis(plan, resources):
    total_capacity = resources["weekly_capacity_hours"].sum()
    used_capacity = resources["used_capacity"].sum()

    return {
        "tasks": len(plan),
        "resources": len(resources),
        "assigned": len(plan[plan["status"] == "Fully Assigned"]),
        "high_risk": len(plan[plan["risk_level"] == "High"]),
        "utilization": round((used_capacity / total_capacity) * 100, 2) if total_capacity else 0,
        "total_cost": round((resources["used_capacity"] * resources["cost_per_hour"]).sum(), 2)
    }


def planning_notes(plan, resources):
    notes = []

    high_risk = plan[plan["risk_level"] == "High"]
    unassigned = plan[plan["status"] == "Unassigned"]
    overloaded = resources[resources["utilization_rate"] >= 90]
    idle = resources[resources["utilization_rate"] <= 20]

    if not high_risk.empty:
        notes.append(
            f"{len(high_risk)} task(s) are high risk. Review unassigned workload and skill availability."
        )

    if not unassigned.empty:
        missing_skills = ", ".join(sorted(unassigned["required_skill"].unique()))
        notes.append(
            f"Unassigned tasks require these skill areas: {missing_skills}."
        )

    if not overloaded.empty:
        overloaded_names = ", ".join(overloaded["name"].tolist())
        notes.append(
            f"Highly utilized resources: {overloaded_names}. Workload balance should be reviewed."
        )

    if not idle.empty:
        idle_names = ", ".join(idle["name"].tolist())
        notes.append(
            f"Low utilization detected for: {idle_names}. These resources may support other tasks if skills match."
        )

    if not notes:
        notes.append("The current plan appears balanced based on the available data.")

    return notes


def apply_what_if(resources, unavailable_resource_names):
    resources = resources.copy()

    if unavailable_resource_names:
        resources.loc[resources["name"].isin(unavailable_resource_names), "availability"] = 0

    return resources