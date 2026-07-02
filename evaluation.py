def evaluate_solution(plan, resources):
    total_tasks = len(plan)
    fully_assigned = len(plan[plan["status"] == "Fully Assigned"])
    high_risk = len(plan[plan["risk_level"] == "High"])

    total_capacity = resources["weekly_capacity_hours"].sum()
    used_capacity = resources["used_capacity"].sum()

    assignment_rate = 0
    if total_tasks > 0:
        assignment_rate = fully_assigned / total_tasks * 100

    utilization_rate = 0
    if total_capacity > 0:
        utilization_rate = used_capacity / total_capacity * 100

    high_risk_rate = 0
    if total_tasks > 0:
        high_risk_rate = high_risk / total_tasks * 100

    capacity_balance_score = max(0, 100 - abs(80 - utilization_rate))
    risk_score = max(0, 100 - high_risk_rate)

    overall_score = (
        assignment_rate * 0.45
        + capacity_balance_score * 0.30
        + risk_score * 0.25
    )

    if overall_score >= 80:
        quality_label = "Good"
    elif overall_score >= 60:
        quality_label = "Moderate"
    else:
        quality_label = "Needs Review"

    return {
        "assignment_rate": round(assignment_rate, 2),
        "utilization_rate": round(utilization_rate, 2),
        "high_risk_rate": round(high_risk_rate, 2),
        "capacity_balance_score": round(capacity_balance_score, 2),
        "risk_score": round(risk_score, 2),
        "overall_score": round(overall_score, 2),
        "quality_label": quality_label
    }