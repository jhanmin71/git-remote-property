import pandas as pd


def basic_groupby(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in df.columns:
        return pd.DataFrame()

    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) == 0:
        return df.groupby(column).size().reset_index(name="건수")

    grouped = df.groupby(column)[list(numeric_cols)].agg(["count", "mean", "min", "max"])
    grouped.columns = ["_".join([c, stat]) for c, stat in grouped.columns]
    grouped = grouped.reset_index()
    return grouped

