import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(__file__))

RAW_CLIENTS = os.path.join(BASE, "data/raw/clients.csv")
RAW_ENG = os.path.join(BASE, "data/raw/program_engagements.csv")

OUT_KPIS_MONTHLY = os.path.join(BASE, "data/processed/system_kpis_monthly.csv")
OUT_PROGRAM_KPIS = os.path.join(BASE, "data/processed/program_kpis.csv")
OUT_DQ = os.path.join(BASE, "data/processed/data_quality_watchlist.csv")
OUT_TABLEAU = os.path.join(BASE, "data/processed/tableau_extract.csv")


def month_floor(d: pd.Series) -> pd.Series:
    dt = pd.to_datetime(d, errors="coerce")
    return dt.dt.to_period("M").dt.to_timestamp()


def main():
    clients = pd.read_csv(RAW_CLIENTS)
    eng = pd.read_csv(RAW_ENG)

    eng["entry_date"] = pd.to_datetime(eng["entry_date"])
    eng["exit_date"] = pd.to_datetime(eng["exit_date"])
    eng["entry_month"] = month_floor(eng["entry_date"])
    eng["exit_month"] = month_floor(eng["exit_date"])
    eng["days_in_program"] = (eng["exit_date"] - eng["entry_date"]).dt.days.clip(lower=0)

    df = eng.merge(clients, on="client_id", how="left", validate="many_to_one", suffixes=("", "_client"))

    # Monthly KPIs
    monthly = (
        df.groupby("exit_month", dropna=False)
        .agg(
            exited_clients=("exited_flag", "sum"),
            exits_to_perm_housing=("permanent_housing_flag", "sum"),
            missing_exit_interviews=("exit_interview_completed", lambda s: (s == 0).sum()),
            median_days_in_program=("days_in_program", "median"),
        )
        .reset_index()
        .sort_values("exit_month")
    )
    monthly["perm_housing_rate"] = (monthly["exits_to_perm_housing"] / monthly["exited_clients"]).fillna(0)
    monthly["missing_exit_interview_rate"] = (monthly["missing_exit_interviews"] / monthly["exited_clients"]).fillna(0)

    os.makedirs(os.path.join(BASE, "data/processed"), exist_ok=True)
    monthly.to_csv(OUT_KPIS_MONTHLY, index=False)

    # Program KPIs
    program = (
        df.groupby(["program_name"], dropna=False)
        .agg(
            total_clients=("client_id", "nunique"),
            exited_clients=("exited_flag", "sum"),
            exits_to_perm_housing=("permanent_housing_flag", "sum"),
            median_days_in_program=("days_in_program", "median"),
            missing_exit_interviews=("exit_interview_completed", lambda s: (s == 0).sum()),
        )
        .reset_index()
    )
    program["perm_housing_rate"] = (program["exits_to_perm_housing"] / program["exited_clients"]).fillna(0)
    program["missing_exit_interview_rate"] = (program["missing_exit_interviews"] / program["exited_clients"]).fillna(0)
    program.to_csv(OUT_PROGRAM_KPIS, index=False)

    # Data Quality Watchlist
    df["income_missing_flag"] = df["income_at_exit_range"].isin(["Data Not Collected"]) & (df["exited_flag"] == 1)

    dq = (
        df.groupby(["provider", "program_name"], dropna=False)
        .agg(
            exited_clients=("exited_flag", "sum"),
            missing_exit_interviews=("exit_interview_completed", lambda s: (s == 0).sum()),
            missing_income=("income_missing_flag", "sum"),
            median_days_in_program=("days_in_program", "median"),
        )
        .reset_index()
    )
    dq["missing_exit_interview_rate"] = (dq["missing_exit_interviews"] / dq["exited_clients"]).fillna(0)
    dq["missing_income_rate"] = (dq["missing_income"] / dq["exited_clients"]).fillna(0)
    dq["watch_flag"] = (
        (dq["exited_clients"] >= 30)
        & ((dq["missing_exit_interview_rate"] > 0.12) | (dq["missing_income_rate"] > 0.10))
    ).astype(int)

    dq.sort_values(
        ["watch_flag", "missing_exit_interview_rate", "missing_income_rate"],
        ascending=[False, False, False],
    ).to_csv(OUT_DQ, index=False)

    # Tableau extract (flattened)
    tableau_cols = [
        "client_id",
        "program_name",
        "provider",
        "entry_date",
        "exit_date",
        "days_in_program",
        "exited_flag",
        "permanent_housing_flag",
        "exit_interview_completed",
        "exit_destination",
        "income_at_exit_range",
        "year",
        "household_type",
        "age_group",
        "race_ethnicity",
        "gender",
    ]
    df[tableau_cols].to_csv(OUT_TABLEAU, index=False)

    print("Wrote:")
    print(" -", OUT_KPIS_MONTHLY)
    print(" -", OUT_PROGRAM_KPIS)
    print(" -", OUT_DQ)
    print(" -", OUT_TABLEAU)


if __name__ == "__main__":
    main()
