#!/usr/bin/env python3
"""
Synthetic data generator for the Food Delivery App.
Generates CSV files for users, sessions, events, and experiment groups.
Run: python3 generate_data.py
"""

import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

OUTPUT_DIR = "data/raw"
NUM_USERS = 10_000

CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Surat"
]
CITY_WEIGHTS = [0.20, 0.18, 0.15, 0.12, 0.10, 0.08, 0.07, 0.04, 0.03, 0.03]

DEVICES = ["android", "ios"]
DEVICE_WEIGHTS = [0.74, 0.26]
APP_VERSIONS = ["3.1", "3.2", "3.3", "3.4"]

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)
DATE_RANGE_DAYS = (END_DATE - START_DATE).days

EXPERIMENT_START = datetime(2024, 10, 1)
EXPERIMENT_END = datetime(2024, 12, 31)

FUNNEL_STEPS = [
    "app_open",
    "restaurant_click",
    "menu_view",
    "add_to_cart",
    "checkout_started",
    "order_placed",
]

BASE_PROBS = {
    "app_open": 1.00,
    "restaurant_click": 0.72,
    "menu_view": 0.76,
    "add_to_cart": 0.58,
    "checkout_started": 0.68,
    "order_placed": 0.56,
}

HOUR_WEIGHTS = [
    0.5, 0.3, 0.2, 0.1, 0.1, 0.2,
    0.5, 1.0, 1.5, 1.5, 1.5, 2.0,
    3.0, 3.5, 2.5, 2.0, 1.5, 1.5,
    2.0, 3.0, 3.5, 3.5, 2.5, 1.0,
]
HOUR_WEIGHTS = [w / sum(HOUR_WEIGHTS) for w in HOUR_WEIGHTS]


def prepare_environment() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    random.seed(42)
    np.random.seed(42)


def generate_users() -> pd.DataFrame:
    fake = Faker("en_IN")
    users = []

    for user_id in range(1, NUM_USERS + 1):
        signup_offset = random.randint(0, DATE_RANGE_DAYS)
        signup_date = START_DATE + timedelta(days=signup_offset)
        days_since_signup = (END_DATE - signup_date).days
        user_type = "new" if days_since_signup <= 30 else "returning"

        users.append({
            "user_id": user_id,
            "signup_date": signup_date.date(),
            "city": random.choices(CITIES, weights=CITY_WEIGHTS, k=1)[0],
            "device_type": random.choices(DEVICES, weights=DEVICE_WEIGHTS, k=1)[0],
            "user_type": user_type,
        })

    users_df = pd.DataFrame(users)
    users_df.to_csv(os.path.join(OUTPUT_DIR, "users.csv"), index=False)
    return users_df


def generate_sessions(users_df: pd.DataFrame) -> pd.DataFrame:
    sessions = []
    session_id = 1

    for _, user in users_df.iterrows():
        if user["user_type"] == "returning":
            num_sessions = random.randint(2, 8)
        else:
            num_sessions = random.randint(1, 3)

        signup_dt = datetime.combine(user["signup_date"], datetime.min.time())
        max_offset = max((END_DATE - signup_dt).days, 0)

        for _ in range(num_sessions):
            session_day_offset = random.randint(0, max_offset)
            session_date = signup_dt + timedelta(days=session_day_offset)
            hour = random.choices(list(range(24)), weights=HOUR_WEIGHTS, k=1)[0]
            session_start = session_date.replace(
                hour=hour,
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
                microsecond=0,
            )

            sessions.append({
                "session_id": session_id,
                "user_id": user["user_id"],
                "session_start": session_start,
                "app_version": random.choices(
                    APP_VERSIONS,
                    weights=[0.05, 0.10, 0.30, 0.55],
                    k=1,
                )[0],
            })
            session_id += 1

    sessions_df = pd.DataFrame(sessions)
    sessions_df.to_csv(os.path.join(OUTPUT_DIR, "sessions.csv"), index=False)
    return sessions_df


def generate_experiment_groups(sessions_df: pd.DataFrame) -> pd.DataFrame:
    experiment_sessions = sessions_df[
        (sessions_df["session_start"] >= EXPERIMENT_START) &
        (sessions_df["session_start"] <= EXPERIMENT_END)
    ]
    experiment_user_ids = experiment_sessions["user_id"].unique()

    experiment_groups = [
        {
            "user_id": user_id,
            "experiment_group": random.choices(["control", "treatment"], weights=[0.50, 0.50], k=1)[0],
        }
        for user_id in experiment_user_ids
    ]

    exp_df = pd.DataFrame(experiment_groups)
    exp_df.to_csv(os.path.join(OUTPUT_DIR, "experiment_groups.csv"), index=False)
    return exp_df


def get_conversion_probs(user_row: pd.Series, is_experiment_session: bool, exp_group: str | None) -> dict:
    probs = BASE_PROBS.copy()

    if user_row["device_type"] == "ios":
        probs["restaurant_click"] += 0.03
        probs["menu_view"] += 0.02
        probs["add_to_cart"] += 0.04
        probs["checkout_started"] += 0.03
        probs["order_placed"] += 0.05

    if user_row["user_type"] == "returning":
        probs["restaurant_click"] += 0.05
        probs["menu_view"] += 0.04
        probs["add_to_cart"] += 0.06
        probs["checkout_started"] += 0.05
        probs["order_placed"] += 0.08

    if is_experiment_session and exp_group == "treatment":
        probs["checkout_started"] += 0.06
        probs["order_placed"] += 0.12

    for step, value in probs.items():
        if step != "app_open":
            probs[step] = min(value, 0.99)

    return probs


def generate_events(
    users_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    exp_df: pd.DataFrame,
) -> pd.DataFrame:
    exp_lookup = exp_df.set_index("user_id")["experiment_group"].to_dict()
    events = []
    event_id = 1

    for idx, session in sessions_df.iterrows():
        uid = int(session["user_id"])
        sid = int(session["session_id"])
        start_time = session["session_start"]
        is_exp_session = EXPERIMENT_START <= start_time <= EXPERIMENT_END
        exp_group = exp_lookup.get(uid)
        user_row = users_df.loc[users_df["user_id"] == uid].iloc[0]
        probs = get_conversion_probs(user_row, is_exp_session, exp_group)
        current_time = start_time

        for step in FUNNEL_STEPS:
            if step == "app_open":
                happens = True
            else:
                happens = random.random() < probs[step]

            if not happens:
                break

            if step == "app_open":
                time_gap = 0
            elif step == "restaurant_click":
                time_gap = random.randint(5, 45)
            elif step == "menu_view":
                time_gap = random.randint(3, 20)
            elif step == "add_to_cart":
                time_gap = random.randint(30, 180)
            elif step == "checkout_started":
                time_gap = random.randint(10, 60)
            else:
                if is_exp_session and exp_group == "treatment":
                    time_gap = random.randint(15, 60)
                else:
                    time_gap = random.randint(45, 180)

            current_time += timedelta(seconds=time_gap)
            events.append({
                "event_id": event_id,
                "session_id": sid,
                "user_id": uid,
                "event_type": step,
                "event_timestamp": current_time,
            })
            event_id += 1

        if idx and idx % 5000 == 0:
            print(f"    Processed {idx:,} / {len(sessions_df):,} sessions...")

    events_df = pd.DataFrame(events)
    events_df.to_csv(os.path.join(OUTPUT_DIR, "events.csv"), index=False)
    return events_df


def validate_data(
    users_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    exp_df: pd.DataFrame,
    events_df: pd.DataFrame,
) -> None:
    print("\n── Funnel Validation ──────────────────────")
    total_sessions = len(sessions_df)

    for step in FUNNEL_STEPS:
        count = events_df[events_df["event_type"] == step]["session_id"].nunique()
        pct = count / total_sessions * 100 if total_sessions else 0
        print(f"  {step:<22} {count:>8,} sessions  ({pct:.1f}%)")

    print("\n── A/B Test Preview ───────────────────────")
    if not exp_df.empty:
        exp_events = events_df.merge(exp_df, on="user_id", how="inner")
        for group in ["control", "treatment"]:
            grp_data = exp_events[exp_events["experiment_group"] == group]
            started = grp_data[grp_data["event_type"] == "checkout_started"]["user_id"].nunique()
            completed = grp_data[grp_data["event_type"] == "order_placed"]["user_id"].nunique()
            conv_rate = completed / started * 100 if started else 0
            print(
                f"  {group:<12} checkout→order: {conv_rate:.1f}%  "
                f"(started={started:,}, placed={completed:,})"
            )
    else:
        print("  No experiment users found in the dataset.")


def main() -> None:
    prepare_environment()
    print("Starting data generation...")

    users_df = generate_users()
    print(f"  ✓ users.csv — {len(users_df):,} rows")
    print(f"    Device split: {users_df['device_type'].value_counts(normalize=True).round(2).to_dict()}")
    print(f"    User type split: {users_df['user_type'].value_counts().to_dict()}")

    sessions_df = generate_sessions(users_df)
    print(f"  ✓ sessions.csv — {len(sessions_df):,} rows")
    print(f"    Avg sessions per user: {len(sessions_df) / len(users_df):.1f}")

    exp_df = generate_experiment_groups(sessions_df)
    print(f"  ✓ experiment_groups.csv — {len(exp_df):,} rows")
    print(f"    Group split: {exp_df['experiment_group'].value_counts().to_dict() if not exp_df.empty else {{}}}")

    print("  Generating events (this may take a moment)...")
    events_df = generate_events(users_df, sessions_df, exp_df)
    print(f"  ✓ events.csv — {len(events_df):,} rows")

    validate_data(users_df, sessions_df, exp_df, events_df)
    print("\nAll files saved to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
