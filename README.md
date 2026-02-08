# Coming Home Middlesex — System Data Analyst POC (End-to-End)

End-to-end mini project:
- Generate synthetic HMIS-style data (calibrated to published totals)
- ETL to produce KPIs + data quality watchlist
- Charts + short PDF report
- Tableau-ready extract

## Run
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.generate_data
python -m src.etl_build_metrics
python -m src.analysis
