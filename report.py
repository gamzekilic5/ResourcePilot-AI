from pathlib import Path

def save_report(plan, resources, notes, kpis, output_dir="outputs"):
    Path(output_dir).mkdir(exist_ok=True)

    path = Path(output_dir) / "planning_report.txt"

    with open(path, "w", encoding="utf-8") as f:
        f.write("ResourcePilot Pro - Planning Report\n")
        f.write("=" * 40 + "\n\n")

        f.write("KPIs\n")
        for key, value in kpis.items():
            f.write(f"- {key}: {value}\n")

        f.write("\nPlanning Notes\n")
        for note in notes:
            f.write(f"- {note}\n")

        f.write("\nAssignment Plan\n")
        f.write(plan.to_string(index=False))

        f.write("\n\nResource Utilization\n")
        f.write(resources.to_string(index=False))

    return path
