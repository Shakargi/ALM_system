"""
scenarios.py
============
מחשב את השפעת שינויי ריבית (Interest Rate Shocks) על פורטפוליו הלוואות.

המערכת תומכת ב-6 תרחישי Basel/EBA סטנדרטיים + תרחיש מותאם אישית.

מדדים מחושבים:
  - NII (Net Interest Income): הכנסות ריבית נטו בפרק זמן קצר (12 חודשים)
  - EVE (Economic Value of Equity): שינוי בשווי הנוכחי של כל ה-Cash Flows

הנחות:
  - הלוואות ריבית קבועה: לא מושפעות מהשוק (NII ו-EVE שלהן לא משתנים)
  - הלוואות ריבית משתנה: מגיבות מיידית לשוק (repricing בכל חודש)
  - Short-end shock: משפיע על הלוואות משתנות (floating rate)
  - Long-end shock: משפיע על שווי ה-EVE של הלוואות קבועות
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass



# ══════════════════════════════════════════════════════════════════════════════
# תרחישים
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Scenario:
    """
    מייצג תרחיש שינוי עקום ריבית.

    short_shock: שינוי בנקודות בסיס בקצה הקצר (משפיע על ריבית משתנה / NII)
    long_shock : שינוי בנקודות בסיס בקצה הארוך (משפיע על שווי EVE)
    name       : שם התרחיש
    description: תיאור השימוש
    """
    name:        str
    short_shock: float   # בנקודות בסיס (bps)
    long_shock:  float   # בנקודות בסיס (bps)
    description: str

    @property
    def short_shock_pct(self) -> float:
        """short_shock באחוזים (לחישוב ריבית)."""
        return self.short_shock / 10000

    @property
    def long_shock_pct(self) -> float:
        """long_shock באחוזים (לחישוב ריבית)."""
        return self.long_shock / 10000


class Scenarios:
    """
    אוסף התרחישים הסטנדרטיים + factory method לתרחיש מותאם.

    שימוש:
        sc = Scenarios.Parallel_UP()
        result = engine.apply(master_df, sc)
    """

    @staticmethod
    def Parallel_UP() -> Scenario:
        """
        +200bps בכל העקום.
        תרחיש הגרוע ביותר להון כאשר ה-Duration Gap חיובי.
        """
        return Scenario(
            name         = "Parallel Up (+200bp)",
            short_shock  = 200,
            long_shock   = 200,
            description  = "Capital requirement — worst case for positive duration gap"
        )

    @staticmethod
    def Parallel_DOWN() -> Scenario:
        """
        -200bps בכל העקום.
        תרחיש הגרוע ביותר להון כאשר ה-Duration Gap שלילי.
        """
        return Scenario(
            name         = "Parallel Down (-200bp)",
            short_shock  = -200,
            long_shock   = -200,
            description  = "Capital requirement — worst case for negative duration gap"
        )

    @staticmethod
    def Steepener() -> Scenario:
        """
        קצר -100bps, ארוך +100bps (עקום מתלול).
        בוחן סיכון צורת עקום: NII לטווח קצר / EVE לטווח ארוך.
        """
        return Scenario(
            name         = "Steepener",
            short_shock  = -100,
            long_shock   = 100,
            description  = "Curve shape risk — NII short-term / EVE long-term"
        )

    @staticmethod
    def Flattener() -> Scenario:
        """
        קצר +100bps, ארוך -100bps (עקום מתשטח).
        """
        return Scenario(
            name         = "Flattener",
            short_shock  = 100,
            long_shock   = -100,
            description  = "Curve shape risk"
        )

    @staticmethod
    def Short_UP() -> Scenario:
        """
        קצר +250bps, ארוך +100bps.
        בוחן NII sensitivity — פוגע ראשון בהלוואות Floating Rate.
        """
        return Scenario(
            name         = "Short Up (+250bp)",
            short_shock  = 250,
            long_shock   = 100,
            description  = "NII sensitivity — hits floating-rate funding fastest"
        )

    @staticmethod
    def Short_DOWN() -> Scenario:
        """
        קצר -250bps, ארוך -100bps.
        """
        return Scenario(
            name         = "Short Down (-250bp)",
            short_shock  = -250,
            long_shock   = -100,
            description  = "NII sensitivity"
        )

    @staticmethod
    def Custom(short_bps: float, long_bps: float) -> Scenario:
        """
        תרחיש מותאם אישית.
        short_bps / long_bps: שינוי בנקודות בסיס (יכול להיות שלילי).
        """
        return Scenario(
            name         = f"Custom (short={short_bps:+.0f}bp, long={long_bps:+.0f}bp)",
            short_shock  = short_bps,
            long_shock   = long_bps,
            description  = "User-defined scenario"
        )

    @classmethod
    def all_standard(cls) -> list:
        """מחזיר רשימה של כל 6 התרחישים הסטנדרטיים."""
        return [
            cls.Parallel_UP(),
            cls.Parallel_DOWN(),
            cls.Steepener(),
            cls.Flattener(),
            cls.Short_UP(),
            cls.Short_DOWN(),
        ]


# ══════════════════════════════════════════════════════════════════════════════
# מנוע החישוב
# ══════════════════════════════════════════════════════════════════════════════

class ScenarioEngine:
    """
    מקבל את ה-master DataFrame (אחרי fileProcessor.load)
    ומחשב NII ו-EVE לפי כל תרחיש.

    הנחות מבניות:
      - עמודת "Changing Interst" (bool): האם ההלוואה רגישה לשינוי ריבית קצר טווח
      - עמודת 'כמות ריבית (%)' : מרווח מעל פריים (אם משתנה) / ריבית קבועה
      - NII_HORIZON_MONTHS      : חלון NII (ברירת מחדל 12 חודשים)
      - DISCOUNT_RATE           : ריבית היוון ל-EVE (ברירת מחדל 6%)
    """

    NII_HORIZON_MONTHS = 12
    DISCOUNT_RATE      = 0.06

    def __init__(self, master: pd.DataFrame):
        self.master = master.copy()
        self.master['Date'] = pd.to_datetime(self.master['Date'])

    # ── API ראשי ──────────────────────────────────────────────────────────────

    def apply(self, scenario: Scenario) -> dict:
        """
        מריץ תרחיש אחד ומחזיר dict עם:
          - scenario_name : שם התרחיש
          - nii_base      : NII בסיסי (ללא שוק)
          - nii_shocked   : NII אחרי ה-shock
          - nii_delta     : שינוי ב-NII
          - eve_base      : EVE בסיסי
          - eve_shocked   : EVE אחרי ה-shock
          - eve_delta     : שינוי ב-EVE (ΔEVE)
          - loan_details  : DataFrame עם פירוט לכל הלוואה
        """
        loan_details_list = []
        total_base_nii = 0.0
        total_base_eve = 0.0
        total_shocked_nii = 0.0
        total_shocked_eve = 0.0

        # עוברים על כל הלוואה, מחשבים לה את התרחישים, ושומרים את הפירוט
        
        for loan_id, group in self.master.groupby('Loan ID'):
            b_nii, b_eve = self._calc_loan(group, shock_pct=0.0, is_short=True)
            s_nii, _ = self._calc_loan(group, shock_pct=scenario.short_shock_pct, is_short=True)
            _, s_eve = self._calc_loan(group, shock_pct=scenario.long_shock_pct, is_short=False)

            total_base_nii += b_nii
            total_base_eve += b_eve
            total_shocked_nii += s_nii
            total_shocked_eve += s_eve

            loan_details_list.append({
                'Loan ID': loan_id,
                'NII Base (₪)': round(b_nii, 2),
                'NII Shocked (₪)': round(s_nii, 2),
                'ΔNII (₪)': round(s_nii - b_nii, 2),
                'EVE Base (₪)': round(b_eve, 2),
                'EVE Shocked (₪)': round(s_eve, 2),
                'ΔEVE (₪)': round(s_eve - b_eve, 2)
            })

        loan_details_df = pd.DataFrame(loan_details_list)

        return {
            'scenario_name': scenario.name,
            'description':   scenario.description,
            'short_shock_bp': scenario.short_shock,
            'long_shock_bp':  scenario.long_shock,
            'nii_base':      round(total_base_nii,    2),
            'nii_shocked':   round(total_shocked_nii, 2),
            'nii_delta':     round(total_shocked_nii - total_base_nii, 2),
            'eve_base':      round(total_base_eve,    2),
            'eve_shocked':   round(total_shocked_eve, 2),
            'eve_delta':     round(total_shocked_eve - total_base_eve, 2),
            'loan_details':  loan_details_df
        }

    def _calc_portfolio(self, shock_pct: float, is_short: bool) -> tuple:
        """
        מחשב NII ו-EVE לכל הפורטפוליו עם shock נתון.
        is_short=True  → shock על ריבית משתנה (NII)
        is_short=False → shock על ריבית קבועה  (EVE)
        """
        total_nii = 0.0
        total_eve = 0.0

        for _, group in self.master.groupby('Loan ID'):
            n, e = self._calc_loan(group, shock_pct, is_short)
            total_nii += n
            total_eve += e

        return total_nii, total_eve

    def _calc_loan(self, group: pd.DataFrame, shock_pct: float, is_short: bool) -> tuple:
        """
        מחשב NII ו-EVE להלוואה בודדת עם shock נתון.
        """
        is_variable = False
        if "Changing Interest" in group.columns:
            val = group["Changing Interest"].iloc[0]
            is_variable = val in [True, 'True', 'כן', 'Yes', 1]

        payments = group[group['Payment Number'] != 0].copy()
        payments.sort_values(by='Date', inplace=True)
        
        if payments.empty:
            return 0.0, 0.0

        has_zero = (group['Payment Number'] == 0).any()
        if has_zero:
            today = group[group['Payment Number'] == 0]['Date'].iloc[0]
        else:
            today = payments['Date'].iloc[0] - pd.DateOffset(months=1)

        # ── NII ──
        nii_cutoff = today + pd.DateOffset(months=self.NII_HORIZON_MONTHS)
        nii_rows = payments[payments['Date'] <= nii_cutoff].copy()

        nii = 0.0
        if not nii_rows.empty:
            base_interest = pd.to_numeric(nii_rows['Total Interest Repayment'], errors='coerce').sum()

            if is_variable and is_short:
                nii_rows['Prev_Date'] = nii_rows['Date'].shift(1).fillna(today)
                
                nii_rows['t_frac'] = (nii_rows['Date'] - nii_rows['Prev_Date']).dt.days / 365.0
                
                nii_rows['Balance'] = pd.to_numeric(nii_rows['Balance'], errors='coerce').fillna(0)
                
                extra_interest = (nii_rows['Balance'] * shock_pct * nii_rows['t_frac']).sum()
                nii = base_interest + extra_interest
            else:
                nii = base_interest

        # ── EVE ──
        if is_variable:
            disc_annual = self.DISCOUNT_RATE + (shock_pct if is_short else 0)
        else:
            disc_annual = self.DISCOUNT_RATE + (shock_pct if not is_short else 0)

        if disc_annual <= -1:
            eve = float('nan')
        else:
            t_pv = (payments['Date'] - today).dt.days / 365.0
            
            # וידוא שהתזרים הוא מספר
            cf_numeric = pd.to_numeric(payments['Cash Flow'], errors='coerce').fillna(0)
            
            pv_values = cf_numeric / ((1 + disc_annual) ** t_pv)
            eve = pv_values.sum()

        return nii, eve

