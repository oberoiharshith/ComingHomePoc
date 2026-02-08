import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(__file__))

OUT_CLIENTS = os.path.join(BASE, "data/raw/clients.csv")
OUT_ENG = os.path.join(BASE, "data/raw/program_engagements.csv")
OUT_ACCESS = os.path.join(BASE, "data/raw/access_site_engagements.csv")


def main(seed: int = 42):
    rng = np.random.default_rng(seed)
    random.seed(seed)

    # Calibrated to publicly reported totals (Coming Home Annual Report 2022–2023)
    TOTAL_CLIENTS = 2495
    YEAR_SPLIT = {2022: 1047, 2023: 1448}
    EXITS_TOTAL = 2261
    EXITS_PERM_HOUSING = 855

    # Program volumes (reported program counts used as anchors)
    PROGRAM_SIZES = {"HHCM": 291, "SHI": 358, "CEA": 240}
    PROGRAM_SIZES["OTHER_COC"] = TOTAL_CLIENTS - sum(PROGRAM_SIZES.values())

    # Demographic distributions (based on report charts; approximations)
    age_groups = ["Under 5","5-12","13-17","18-24","25-34","35-44","45-54","55-64","65+"]
    age_probs = np.array([0.05,0.06,0.03,0.05,0.18,0.16,0.18,0.14,0.15])
    age_probs = age_probs / age_probs.sum()

    race_groups = [
        "Black/African American/African",
        "White",
        "Hispanic/Latino & White",
        "Hispanic/Latino & Black",
        "Other",
    ]
    race_probs = np.array([0.49, 0.20, 0.18, 0.04, 0.09])

    gender_groups = ["Male", "Female", "Other/Unknown"]
    gender_probs = np.array([0.40, 0.58, 0.02])

    hh_types = ["Single Adult", "Family", "Unaccompanied Youth"]
    hh_probs = np.array([0.60, 0.35, 0.05])

    # Disability flags (multi-label)
    disability_types = [
        "Chronic Health Condition",
        "Physical Disability",
        "Developmental Disability",
        "Mental Health Disorder",
        "Drug Use Disorder",
        "Alcohol Use Disorder",
        "HIV/AIDS",
    ]
    disability_base_probs = {
        "Chronic Health Condition": 0.30,
        "Physical Disability": 0.18,
        "Developmental Disability": 0.16,
        "Mental Health Disorder": 0.20,
        "Drug Use Disorder": 0.08,
        "Alcohol Use Disorder": 0.06,
        "HIV/AIDS": 0.01,
    }

    # Income at exit distribution (from report chart; approximated via counts)
    income_bins = [
        "No Income",
        "$151–$250",
        "$251–$500",
        "$501–$1,000",
        "$1,001–$1,500",
        "$1,501–$2,000",
        "$2,001+",
        "Data Not Collected",
    ]
    income_counts = np.array([30, 2, 4, 2, 13, 11, 105, 15], dtype=float)
    income_probs = income_counts / income_counts.sum()

    # Exit destinations (approx from charts)
    hhcm_exit_dest = [
        "Rental by client, with ongoing housing subsidy",
        "Rental by client, no ongoing housing subsidy",
        "Emergency shelter (voucher)",
        "Hotel/motel without voucher",
        "Staying with family (temporary)",
        "Staying with friends (temporary)",
        "Place not meant for habitation",
        "Staying with family (permanent)",
        "No Exit Interview completed",
        "Other",
    ]
    hhcm_exit_probs = np.array([0.23, 0.22, 0.09, 0.02, 0.12, 0.13, 0.12, 0.02, 0.02, 0.03])
    hhcm_exit_probs = hhcm_exit_probs / hhcm_exit_probs.sum()

    shi_exit_dest = [
        "Rental by client, with ongoing housing subsidy",
        "No Exit Interview completed",
        "Deceased",
        "Emergency shelter (voucher)",
        "Staying with family (permanent)",
        "Staying with family (temporary)",
        "Staying with friends (permanent)",
        "Staying with friends (temporary)",
        "Jail/prison/juvenile detention",
        "Long-term care/nursing home",
    ]
    shi_exit_probs = np.array([0.20, 0.14, 0.17, 0.11, 0.06, 0.11, 0.03, 0.09, 0.06, 0.03])
    shi_exit_probs = shi_exit_probs / shi_exit_probs.sum()

    # Providers in system (simulate 17 providers)
    providers = [f"Provider_{i:02d}" for i in range(1, 18)]
    provider_probs = rng.dirichlet(np.ones(len(providers)))  # uneven, realistic

    # Client IDs
    client_ids = [f"C{str(i).zfill(5)}" for i in range(1, TOTAL_CLIENTS + 1)]

    # Assign year totals
    years = [2022] * YEAR_SPLIT[2022] + [2023] * YEAR_SPLIT[2023]
    rng.shuffle(years)

    # Assign primary program
    program_labels = (
        ["HHCM"] * PROGRAM_SIZES["HHCM"]
        + ["SHI"] * PROGRAM_SIZES["SHI"]
        + ["CEA"] * PROGRAM_SIZES["CEA"]
        + ["OTHER_COC"] * PROGRAM_SIZES["OTHER_COC"]
    )
    rng.shuffle(program_labels)

    clients = pd.DataFrame(
        {
            "client_id": client_ids,
            "year": years,
            "household_type": rng.choice(hh_types, size=TOTAL_CLIENTS, p=hh_probs),
            "age_group": rng.choice(age_groups, size=TOTAL_CLIENTS, p=age_probs),
            "race_ethnicity": rng.choice(race_groups, size=TOTAL_CLIENTS, p=race_probs),
            "gender": rng.choice(gender_groups, size=TOTAL_CLIENTS, p=gender_probs),
            "primary_program": program_labels,
            "provider": rng.choice(providers, size=TOTAL_CLIENTS, p=provider_probs),
        }
    )

    for d in disability_types:
        col = f"dis_{d.replace(' ', '_').replace('/', '_')}"
        clients[col] = (rng.random(TOTAL_CLIENTS) < disability_base_probs[d]).astype(int)

    def random_date_in_year(y: int) -> datetime:
        start = datetime(y, 1, 1)
        end = datetime(y, 12, 31)
        return start + timedelta(days=int(rng.integers(0, (end - start).days + 1)))

    # 1 episode per client (simple but realistic for a POC)
    rows = []
    for _, row in clients.iterrows():
        y = int(row["year"])
        entry = random_date_in_year(y)
        prog = row["primary_program"]

        # Program duration assumptions
        if prog == "SHI":
            dur_days = int(np.clip(rng.lognormal(mean=6.0, sigma=0.6), 60, 900))
        elif prog == "HHCM":
            dur_days = int(np.clip(rng.lognormal(mean=5.2, sigma=0.5), 14, 240))
        else:
            dur_days = int(np.clip(rng.lognormal(mean=5.0, sigma=0.6), 7, 365))

        exit_date = entry + timedelta(days=dur_days)

        # Clip to end of 2023 window
        if exit_date > datetime(2023, 12, 31):
            exit_date = datetime(2023, 12, 31)
            exited = 0
        else:
            exited = 1

        # Exit interview completeness
        missing_exit_interview = rng.random() < (0.08 if prog in ["HHCM", "SHI"] else 0.05)
        exit_interview_completed = 0 if missing_exit_interview else 1

        # Permanent housing probability
        perm_prob = 0.32 if prog == "SHI" else (0.35 if prog == "HHCM" else 0.30)
        perm = 1 if (exited and rng.random() < perm_prob) else 0

        # Destination
        if prog == "SHI":
            dest = rng.choice(shi_exit_dest, p=shi_exit_probs)
        elif prog == "HHCM":
            dest = rng.choice(hhcm_exit_dest, p=hhcm_exit_probs)
        else:
            dest = rng.choice(
                [
                    "Rental by client, with ongoing housing subsidy",
                    "Rental by client, no ongoing housing subsidy",
                    "Staying with family (temporary)",
                    "Staying with friends (temporary)",
                    "Emergency shelter (voucher)",
                    "No Exit Interview completed",
                    "Other",
                ],
                p=[0.18, 0.18, 0.18, 0.18, 0.12, 0.06, 0.10],
            )

        if missing_exit_interview:
            dest = "No Exit Interview completed"

        income = rng.choice(income_bins, p=income_probs) if exited else "Data Not Collected"

        rows.append(
            {
                "client_id": row["client_id"],
                "program_name": prog,
                "provider": row["provider"],
                "entry_date": entry.date().isoformat(),
                "exit_date": exit_date.date().isoformat(),
                "exited_flag": exited,
                "exit_interview_completed": exit_interview_completed,
                "exit_destination": dest,
                "income_at_exit_range": income,
                "permanent_housing_flag": perm,
            }
        )

    engagements = pd.DataFrame(rows)

    # Calibrate exact system totals for exits and perm housing
    current_exits = int(engagements["exited_flag"].sum())
    if current_exits != EXITS_TOTAL:
        idx_open = engagements.index[engagements["exited_flag"] == 0].tolist()
        idx_exit = engagements.index[engagements["exited_flag"] == 1].tolist()
        if current_exits < EXITS_TOTAL:
            flip = rng.choice(idx_open, size=EXITS_TOTAL - current_exits, replace=False)
            engagements.loc[flip, "exited_flag"] = 1
        else:
            flip = rng.choice(idx_exit, size=current_exits - EXITS_TOTAL, replace=False)
            engagements.loc[flip, "exited_flag"] = 0

    exited_idx = engagements.index[engagements["exited_flag"] == 1].tolist()
    current_perm = int(engagements.loc[exited_idx, "permanent_housing_flag"].sum())
    if current_perm != EXITS_PERM_HOUSING:
        perm_idx = engagements.index[
            (engagements["exited_flag"] == 1) & (engagements["permanent_housing_flag"] == 1)
        ].tolist()
        nonperm_idx = engagements.index[
            (engagements["exited_flag"] == 1) & (engagements["permanent_housing_flag"] == 0)
        ].tolist()
        if current_perm < EXITS_PERM_HOUSING:
            flip = rng.choice(nonperm_idx, size=EXITS_PERM_HOUSING - current_perm, replace=False)
            engagements.loc[flip, "permanent_housing_flag"] = 1
        else:
            flip = rng.choice(perm_idx, size=current_perm - EXITS_PERM_HOUSING, replace=False)
            engagements.loc[flip, "permanent_housing_flag"] = 0

    engagements.loc[engagements["exit_interview_completed"] == 0, "exit_destination"] = "No Exit Interview completed"

    # Physical access site engagements (reported counts)
    access_sites = [
        ("Unity Square Community Center, New Brunswick", 91),
        ("Middlesex College Resource Hub, Edison", 31),
        ("First Presbyterian Church of Metuchen, Metuchen", 41),
        ("Center for Support, Success & Prosperity, Perth Amboy", 71),
    ]
    access_rows = []
    start = datetime(2023, 6, 1)
    for site, n in access_sites:
        for _ in range(n):
            dt = start + timedelta(days=int(rng.integers(0, 240)))
            access_rows.append({"site": site, "engagement_date": dt.date().isoformat()})
    access_df = pd.DataFrame(access_rows)

    os.makedirs(os.path.join(BASE, "data/raw"), exist_ok=True)
    clients.to_csv(OUT_CLIENTS, index=False)
    engagements.to_csv(OUT_ENG, index=False)
    access_df.to_csv(OUT_ACCESS, index=False)

    print("Wrote:")
    print(" -", OUT_CLIENTS)
    print(" -", OUT_ENG)
    print(" -", OUT_ACCESS)


if __name__ == "__main__":
    main()