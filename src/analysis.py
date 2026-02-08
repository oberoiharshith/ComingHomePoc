import os
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

BASE = os.path.dirname(os.path.dirname(__file__))

CLIENTS = os.path.join(BASE, "data/raw/clients.csv")
ENG = os.path.join(BASE, "data/raw/program_engagements.csv")
MONTHLY = os.path.join(BASE, "data/processed/system_kpis_monthly.csv")
PROGRAM = os.path.join(BASE, "data/processed/program_kpis.csv")
DQ = os.path.join(BASE, "data/processed/data_quality_watchlist.csv")

OUT_MD = os.path.join(BASE, "outputs/report.md")
OUT_PDF = os.path.join(BASE, "outputs/report.pdf")
FIG_DIR = os.path.join(BASE, "outputs/figures")


def save_fig(path: str):
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE, "outputs"), exist_ok=True)

    clients = pd.read_csv(CLIENTS)
    eng = pd.read_csv(ENG)
    monthly = pd.read_csv(MONTHLY, parse_dates=["exit_month"])
    program = pd.read_csv(PROGRAM)
    dq = pd.read_csv(DQ)

    # 1) Permanent housing rate by program
    program_sorted = program.sort_values("perm_housing_rate", ascending=False)
    plt.figure(figsize=(8, 4))
    plt.bar(program_sorted["program_name"], program_sorted["perm_housing_rate"])
    plt.title("Permanent Housing Rate by Program (Synthetic, Calibrated)")
    plt.ylabel("Rate")
    save_fig(os.path.join(FIG_DIR, "perm_housing_rate_by_program.png"))

    # 2) Monthly exits vs perm housing
    plt.figure(figsize=(8, 4))
    plt.plot(monthly["exit_month"], monthly["exited_clients"], label="Exits")
    plt.plot(monthly["exit_month"], monthly["exits_to_perm_housing"], label="Permanent Housing Exits")
    plt.title("Monthly Exits vs Permanent Housing Exits")
    plt.xlabel("Month")
    plt.ylabel("Clients")
    plt.legend()
    save_fig(os.path.join(FIG_DIR, "monthly_exits.png"))

    # 3) Equity: perm housing by race
    df = eng.merge(clients, on="client_id", how="left")
    exited = df[df["exited_flag"] == 1].copy()
    equity = (
        exited.groupby("race_ethnicity")
        .agg(exited_clients=("client_id", "nunique"), perm_exits=("permanent_housing_flag", "sum"))
        .reset_index()
    )
    equity["perm_rate"] = equity["perm_exits"] / equity["exited_clients"]
    equity = equity.sort_values("perm_rate", ascending=False)

    plt.figure(figsize=(9, 4))
    plt.bar(equity["race_ethnicity"], equity["perm_rate"])
    plt.title("Permanent Housing Rate by Race/Ethnicity (Synthetic)")
    plt.ylabel("Rate")
    plt.xticks(rotation=25, ha="right")
    save_fig(os.path.join(FIG_DIR, "perm_rate_by_race.png"))

    # Top watchlist (optional helper file)
    watch = dq[dq["watch_flag"] == 1].copy().head(10)
    watch.to_csv(os.path.join(BASE, "outputs/watchlist_top10.csv"), index=False)

    # Markdown report
    md = f"""# System Performance & Data Quality POC (Middlesex CoC)

This is an end-to-end mini-project using **synthetic HMIS-style client episodes** calibrated to publicly reported Coming Home system totals (2022–2023).

## Calibrated totals (synthetic)
- Total clients: {clients['client_id'].nunique():,}
- Total exits: {int(eng['exited_flag'].sum()):,}
- Exits to permanent housing: {int(eng.loc[eng['exited_flag']==1,'permanent_housing_flag'].sum()):,}

## Outputs
- Monthly KPIs: `data/processed/system_kpis_monthly.csv`
- Program KPIs: `data/processed/program_kpis.csv`
- Data quality watchlist: `data/processed/data_quality_watchlist.csv`
- Tableau extract: `data/processed/tableau_extract.csv`
- Figures: `outputs/figures/`
"""
    with open(OUT_MD, "w") as f:
        f.write(md)

    # Simple PDF report (2 pages)
    c = canvas.Canvas(OUT_PDF, pagesize=letter)
    width, height = letter

    def header(title: str):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 1 * inch, title)
        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, height - 1.25 * inch, "System Performance & Data Quality POC (Synthetic, calibrated)")
        c.line(1 * inch, height - 1.35 * inch, width - 1 * inch, height - 1.35 * inch)

    header("Coming Home Middlesex — Data Analyst POC")
    c.setFont("Helvetica", 11)
    y = height - 1.7 * inch
    bullets = [
        f"Total clients: {clients['client_id'].nunique():,}",
        f"Total exits: {int(eng['exited_flag'].sum()):,}",
        f"Permanent housing exits: {int(eng.loc[eng['exited_flag']==1,'permanent_housing_flag'].sum()):,}",
        "Outputs: monthly KPIs, program KPIs, equity cuts, and a data quality watchlist.",
    ]
    for b in bullets:
        c.drawString(1.05 * inch, y, f"• {b}")
        y -= 0.22 * inch

    fig1 = os.path.join(FIG_DIR, "perm_housing_rate_by_program.png")
    c.drawImage(fig1, 1 * inch, y - 3.0 * inch, width=6.5 * inch, height=3.0 * inch, preserveAspectRatio=True)

    c.showPage()
    header("Equity view + data quality")

    c.setFont("Helvetica", 11)
    y = height - 1.7 * inch
    notes = [
        "Equity lens: compare permanent housing outcomes by race/ethnicity and age group.",
        "Operational lens: prioritize exit interview and income completeness improvements.",
        "This framework can plug into live HMIS exports for monthly/quarterly reporting.",
    ]
    for n in notes:
        c.drawString(1.05 * inch, y, f"• {n}")
        y -= 0.22 * inch

    fig2 = os.path.join(FIG_DIR, "perm_rate_by_race.png")
    c.drawImage(fig2, 1 * inch, y - 2.8 * inch, width=6.5 * inch, height=2.8 * inch, preserveAspectRatio=True)

    c.save()

    print("Wrote:")
    print(" -", OUT_MD)
    print(" -", OUT_PDF)
    print(" -", FIG_DIR)


if __name__ == "__main__":
    main()
