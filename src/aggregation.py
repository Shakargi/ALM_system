import pandas as pd


class aggregation:

    def __init__(self, master: pd.DataFrame):
        """
        Receives the single master DataFrame (output of fileProcessor.load).
        All operations run on it directly — no list of DataFrames needed.
        """
        self.master = master

    # ── Public API ────────────────────────────────────────────────────────────

    def aggregate(self, **criteria) -> pd.DataFrame:
        """
        Filters the master DataFrame by any column=value criteria, then
        aggregates Total Monthly Repayment into a monthly time series.

        Example:
            agg.aggregate(Loan_Type='משכנתא דרגה 1')
            agg.aggregate()  # full portfolio
        """
        df = self._filter(self.master, criteria)

        # Exclude disbursement rows (Payment Number == 0)
        df = df[df['Payment Number'] != 0].copy()

        df['Month'] = df['Date'].dt.to_period('M')

        monthly = (
            df.groupby('Month')['Total Monthly Repayment']
            .sum()
            .reset_index()
        )

        monthly['Month'] = monthly['Month'].dt.to_timestamp()
        monthly = monthly[monthly['Total Monthly Repayment'] != 0].reset_index(drop=True)
        monthly.insert(0, 'Payment Number', range(1, len(monthly) + 1))
        monthly['Cumulative Repayment'] = monthly['Total Monthly Repayment'].cumsum()

        return monthly

    def loan_ids(self, **criteria) -> list:
        """Returns unique Loan IDs that match the given criteria."""
        return self._filter(self.master, criteria)['Loan ID'].unique().tolist()

    def for_loan(self, loan_id: str) -> pd.DataFrame:
        """Returns all rows for a single loan."""
        return self.master[self.master['Loan ID'] == loan_id].copy()

    def count_loans(self, **criteria) -> int:
        """Returns the number of distinct loans matching the criteria."""
        return self._filter(self.master, criteria)['Loan ID'].nunique()

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _filter(df: pd.DataFrame, criteria: dict) -> pd.DataFrame:
        """Applies column==value filters to df. Unknown columns are ignored."""
        for col, val in criteria.items():
            if col in df.columns:
                df = df[df[col] == val]
        if df.empty:
            raise ValueError(f"No rows matched the given criteria: {criteria}")
        return df
