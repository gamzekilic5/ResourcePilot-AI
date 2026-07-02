#  ResourcePilot

**AI-assisted project resource planning and decision support platform**

ResourcePilot is a prototype decision support platform designed for project-based organizations. The system combines optimization techniques with AI-assisted planning workflows to support resource allocation, workload analysis, and project planning.

Unlike conventional AI systems, ResourcePilot does **not** make critical planning decisions autonomously. AI is intended to assist the user by generating recommendations and draft planning artifacts, while the final allocation is performed through optimization models and confirmed by the user.

---

##  Features

- Resource allocation using optimization-based planning
- Work Breakdown Structure (WBS) management
- Resource utilization dashboard
- Project risk evaluation
- Solution quality evaluation
- What-if scenario analysis
- Validation of uploaded project data
- CSV and Excel file support
- Planning report generation
- Prototype PDF-to-WBS assistant

---

##  System Workflow

```
Project Data
      │
      ▼
Data Validation
      │
      ▼
Optimization Model
      │
      ▼
Resource Assignment
      │
      ▼
Dashboard & Reports
```

Future versions will include an AI-assisted document understanding module that generates draft WBS structures from project documentation before optimization.

---

## Technologies

- Python
- Streamlit
- OR-Tools
- Pandas
- Plotly
- OpenPyXL

---

##  Current Modules

- Data Upload
- Validation Layer
- Optimization Engine
- Resource Dashboard
- Solution Evaluation
- Planning Reports
- PDF to Draft WBS (Prototype)

---

##  Future Improvements

- RAG-based document understanding
- AI Planning Assistant
- Automatic document classification
- Smart column mapping
- Multi-objective optimization
- Database integration
- ERP integration
- Role-based user management
- REST API support

---

##  Project Philosophy

ResourcePilot follows a **human-in-the-loop** decision support approach.

The optimization engine performs critical planning decisions based on mathematical models, while AI is used only for assisting users with document understanding, recommendations, and planning support.

This design aims to reduce hallucination risks and increase transparency in project planning.

---

##  Project Structure

```
ResourcePilot/
│
├── app.py
├── optimizer.py
├── validation.py
├── evaluation.py
├── report.py
├── wbs_assistant.py
├── requirements.txt
├── README.md
├── data/
└── outputs/
```

---

##  Installation

```bash
git clone https://github.com/YOUR_USERNAME/ResourcePilot.git

cd ResourcePilot

python3 -m pip install -r requirements.txt

python3 -m streamlit run app.py
```

---

##  License

This project is developed for educational and portfolio purposes.
