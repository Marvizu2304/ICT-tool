from __future__ import annotations
import pandas as pd
import numpy as np

class FormulaContext:
    """
    A simple hook-based processor. Customize `apply_all` with your own business logic.
    Replace the sample logic with your real formulas.
    """
    def __init__(self, sheet: str | None = None):
        self.sheet = sheet

    def read_excel(self, file_path: str) -> pd.DataFrame:
        df = pd.read_excel(file_path, sheet_name=self.sheet or 0)
        return df

    def apply_all(self, df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """
        Example transformations you can fully customize:
        - Add calculated columns
        - Aggregate by categorical/time columns
        - Build summary tables
        Return a dict of sheet_name -> dataframe to write to Excel.
        """
        out = {}

        # --- 1) Ensure a datetime column if present ---
        df = df.copy()
        date_cols = [c for c in df.columns if "date" in c.lower() or "fecha" in c.lower()]
        if date_cols:
            c = date_cols[0]
            df[c] = pd.to_datetime(df[c], errors="coerce")
            df["Year"] = df[c].dt.year
            df["Month"] = df[c].dt.month
        else:
            # if no date column, create a dummy sequence index
            df["SeqIndex"] = np.arange(1, len(df) + 1)

        # --- 2) Add example calculated columns ---
        num_cols = df.select_dtypes(include=[float, int]).columns.tolist()
        if len(num_cols) >= 2:
            a, b = num_cols[0], num_cols[1]
            df[f"{a}_plus_{b}"] = df[a] + df[b]
            df[f"{a}_minus_{b}"] = df[a] - df[b]
            # avoid division by zero
            df[f"{a}_over_{b}"] = df[a] / df[b].replace({0: pd.NA})
        # Add a normalized column for the first numeric field
        if num_cols:
            first = num_cols[0]
            df[f"{first}_zscore"] = (df[first] - df[first].mean()) / (df[first].std(ddof=0) or 1)

        out["Calculations"] = df

        # --- 3) Monthly aggregation example (if Year/Month present) ---
        if "Year" in df.columns and "Month" in df.columns and num_cols:
            agg_map = {c: "sum" for c in num_cols[:4]}  # limit to first few numeric cols
            monthly = df.groupby(["Year", "Month"], dropna=False).agg(agg_map).reset_index()
            out["Monthly_Summary"] = monthly

        # --- 4) Simple numeric summary sheet ---
        summary = df.describe(include="all").transpose()
        out["Data_Profile"] = summary

        return out
