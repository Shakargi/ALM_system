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
        rows = []

        for loan_id, group in master.groupby('Loan ID'):
            p = params.get(str(loan_id), {})

            # 1. סידור כרונולוגי של התשלומים חובה!
            group = group.sort_values('Payment Number')

            # 2. המרת עמודות קריטיות למספרים
            group['Cash Flow'] = pd.to_numeric(group['Cash Flow'], errors='coerce').fillna(0)
            
            payments = group[group['Payment Number'] != 0].copy()
            if payments.empty:
                continue
                
            payments['Balance'] = pd.to_numeric(payments['Balance'], errors='coerce').fillna(0)

            # 3. זיהוי אם ההלוואה התחילה מהאמצע או מההתחלה
            has_payment_zero = (group['Payment Number'] == 0).any()

            if has_payment_zero:
                # הלוואה רגילה מההתחלה
                row_zero = group[group['Payment Number'] == 0]
                loan_amount = float(abs(row_zero['Cash Flow'].iloc[0]))
                cfs = group['Cash Flow'].tolist()
                
                # הבטחת תזרים פותח שלילי
                if cfs[0] > 0:
                    cfs[0] = -cfs[0]
            else:
                # הלוואה מהאמצע - סכום ההלוואה/ההשקעה הוא יתרת הפתיחה העדכנית
                loan_amount = float(payments['Balance'].iloc[0]) 
                cfs = group['Cash Flow'].tolist()
                # הוספת התזרים השלילי לזמן 0
                cfs = [-loan_amount] + cfs

            # חישוב ההחזר החודשי הממוצע
            if 'Total Monthly Repayment' in payments.columns:
                debt_service = float(pd.to_numeric(payments['Total Monthly Repayment'], errors='coerce').mean())
            elif 'Cash Flow' in payments.columns:
                debt_service = float(payments['Cash Flow'].mean())
            else:
                debt_service = 0.0

            # 4. חישוב Dynamic LTV (שימוש ביתרת הפתיחה - Balance)
            valid = payments.dropna(subset=['Balance', 'Collateral Value'])
            valid = valid[pd.to_numeric(valid['Collateral Value'], errors='coerce') > 0]

            if valid.empty:
                avg_ltv, min_ltv, max_ltv = None, None, None
            else:
                valid_collateral = pd.to_numeric(valid['Collateral Value'], errors='coerce')
                ltv_series = (valid['Balance'] / valid_collateral) * 100
                
                avg_ltv    = round(ltv_series.mean(), 2)
                min_ltv    = round(ltv_series.min(), 2)
                max_ltv    = round(ltv_series.max(), 2)

            # ── חישוב DSCR ─────────────────────────────────────────────────
            dscr = self.calcDSCR(
                pgi=float(p.get('pgi', 0)),
                vl=float(p.get('vl', 0)),
                opex=float(p.get('opex', 0)),
                monthly_payment=debt_service,
            )

            # ── חישוב IRR ו-Duration ───────────────────────────────────────
            duration = self.calcDuration(cfs)
            try:
                irr_annual, _ = self.calcIRR(cfs)
            except Exception:
                irr_annual = None

            rows.append({
                'Loan ID':           loan_id,
                'Client':            group['Client'].iloc[0] if 'Client' in group.columns else '',
                'Loan Type':         group['Loan Type'].iloc[0] if 'Loan Type' in group.columns else '',
                'Amortization Type': group['Amortization Type'].iloc[0] if 'Amortization Type' in group.columns else '',
                'Loan Amount':       loan_amount,
                'Avg LTV (%)':       avg_ltv,
                'Min LTV (%)':       min_ltv,
                'Max LTV (%)':       max_ltv,
                'DSCR':              round(dscr, 3),
                'Duration (months)': round(duration, 2),
                'IRR (annual)':      round(irr_annual, 4) if irr_annual is not None else None,
            })

        return pd.DataFrame(rows)
