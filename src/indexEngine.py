import numpy as np
import numpy_financial as npf
import pandas as pd


class IndexEngine:

    # ── Per-loan scalar calculations ──────────────────────────────────────────

    def calcLTV(self, loan_amount: float, collateral_amount: float) -> float:
        return (loan_amount / collateral_amount) * 100

    def calcDSCR(self, pgi: float, vl: float, opex: float, monthly_payment: float) -> float:
        if monthly_payment == 0:
            return 0
        noi_monthly = pgi - vl - opex
        return noi_monthly / monthly_payment

    def calcIRR(self, CFs: list):
        m_irr = npf.irr(CFs)
        if m_irr is None or np.isnan(m_irr):
            return 0.0, 0.0
        annual_irr = (1 + m_irr) ** 12 - 1
        return annual_irr, m_irr

    def calcDuration(self, CFs: list):
        """Macaulay Duration in months. CFs[0] must be the initial outflow (negative)."""
        m_irr = npf.irr(CFs)
        if m_irr is None or np.isnan(m_irr) or m_irr <= -1:
            return 0

        future_cfs = CFs[1:]
        pv_sum = 0
        weighted_sum = 0
        for t, cf in enumerate(future_cfs, start=1):
            pv = cf / ((1 + m_irr) ** t)
            pv_sum += pv
            weighted_sum += t * pv

        if abs(pv_sum) < 1e-6:
            return 0
        return weighted_sum / pv_sum

    # ── Batch calculation over the full master DataFrame ──────────────────────

    def calcAll(self, master: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Runs dynamic LTV (per payment row), DSCR, IRR, and Duration for every loan.

        LTV is calculated per payment using the Collateral Value column — which
        already reflects any mid-schedule appraiser revaluations — against the
        outstanding balance (End Period Balance) at that point in time.
        The summary LTV reported per loan is the weighted average across all periods.

        Parameters
        ----------
        master : pd.DataFrame
            The single master DataFrame from fileProcessor.load().
            Must contain a 'Collateral Value' column.
        params : dict
            { loan_id: {'pgi': float, 'vl': float, 'opex': float} }
            Collateral is read directly from the master — no manual input needed.

        Returns
        -------
        pd.DataFrame with one row per loan.
        """
        rows = []

        for loan_id, group in master.groupby('Loan ID'):
            p = params.get(str(loan_id), {})

            loan_amount  = abs(group['Cash Flow'].iloc[0])
            cfs          = group['Cash Flow'].tolist()
            payments     = group[group['Payment Number'] != 0].copy()

            if payments.empty:
                continue

            debt_service = payments['Total Monthly Repayment'].mean()

            # ── Dynamic LTV ───────────────────────────────────────────────────
            # Per payment: LTV = outstanding balance / collateral value at that row.
            # Collateral Value already reflects any mid-schedule appraiser revaluation.
            valid = payments.dropna(subset=['End Period Balance', 'Collateral Value'])
            valid = valid[valid['Collateral Value'] > 0]
            valid = valid[valid['End Period Balance'] > 0]


            if valid.empty:
                avg_ltv    = None
                min_ltv    = None
                max_ltv    = None
            else:
                ltv_series = (valid['End Period Balance'] / valid['Collateral Value']) * 100
                avg_ltv    = round(ltv_series.mean(), 2)
                min_ltv    = round(ltv_series.min(), 2)
                max_ltv    = round(ltv_series.max(), 2)

            # ── DSCR ──────────────────────────────────────────────────────────
            dscr = self.calcDSCR(
                pgi=float(p.get('pgi', 0)),
                vl=float(p.get('vl', 0)),
                opex=float(p.get('opex', 0)),
                monthly_payment=debt_service,
            )

            # ── IRR & Duration ────────────────────────────────────────────────
            duration = self.calcDuration(cfs)
            try:
                irr_annual, _ = self.calcIRR(cfs)
            except Exception:
                irr_annual = None

            rows.append({
                'Loan ID':           loan_id,
                'Client':            group['Client'].iloc[0],
                'Loan Type':         group['Loan Type'].iloc[0],
                'Amortization Type': group['Amortization Type'].iloc[0],
                'Loan Amount':       loan_amount,
                'Avg LTV (%)':       avg_ltv,
                'Min LTV (%)':       min_ltv,
                'Max LTV (%)':       max_ltv,
                'DSCR':              round(dscr, 3),
                'Duration (months)': round(duration, 2),
                'IRR (annual)':      round(irr_annual, 4) if irr_annual is not None else None,
            })

        return pd.DataFrame(rows)
