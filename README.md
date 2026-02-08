## Project Overview

This is an end-to-end system analytics proof of concept demonstrating reporting, data quality monitoring, and program evaluation in a homelessness services and Continuum of Care (CoC) context.

The project demonstrates:
- System-level performance reporting
- Program flow and length-of-stay analysis
- Data quality monitoring across providers
- Tableau-based stakeholder-facing dashboards

All client-level records are **synthetic** and calibrated to **publicly reported system totals** to ensure privacy while maintaining realistic HMIS structure.

---

## Key Deliverables

### 📊 Tableau Dashboard (Primary)
System performance and data quality dashboard built using a Tableau-ready extract.

**Tableau Public link:**  
https://public.tableau.com/views/ComingHomeMiddlesexSystemDataAnalystPOC/Dashboard1

---

### 📄 PDF Summary Report
Concise written summary of metrics, equity lens, and operational insights.

**Report:**  
`outputs/report.pdf`

---

### ⚙️ Data Pipeline & Analysis
- Synthetic HMIS-style data generation
- ETL to system KPIs and data quality watchlists
- Reproducible Python workflow

---

## How to Run Locally

```bash
pip install -r requirements.txt
python -m src.generate_data
python -m src.etl_build_metrics
python -m src.analysis
