import pandas as pd


def amortizationConfig(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps the raw Hebrew columns to English names.
    Works on the full master DataFrame — no splitting needed.
    """
    final_schedule = pd.DataFrame()

    final_schedule['Payment Number']           = df['# תשלום']
    final_schedule['Date']                     = pd.to_datetime(df['תאריך'])
    final_schedule['Balance']                  = df['יתרה']
    final_schedule['Total Monthly Repayment']  = df['לוח סילוקין כולל מע"מ']
    final_schedule['Total Interest Repayment'] = df['הוצאות ריבית']
    final_schedule['Total Fund Repayment']     = df['תשלום ע"ח קרן']
    final_schedule['Fees/OPEX']                = df['עמלת תפעול חודשית']
    final_schedule['VAT']                      = df['מע"מ']
    final_schedule['End Period Balance']       = df['יתרת קרן עדכנית']
    final_schedule['Cash Flow']                = df['Cash Flow']
    final_schedule['Loan Type']                = df['סוג הלוואה']
    final_schedule['Amortization Type']        = df['סוג פירעון']
    final_schedule['Client']                   = df['שם לקוח']
    final_schedule['Loan ID']                  = df['LoanID']
    final_schedule['Collateral Value']         = df['ערך בטוחה']
    final_schedule['Changing Interest']        = df['ריבית משתנה']
    final_schedule['Interest']                 = df['כמות ריבית']


    return final_schedule.reset_index(drop=True)


def load(path: str) -> pd.DataFrame:
    """
    Loads the Excel file and returns a single configured master DataFrame.
    Replaces the old amortizationSeperator + list-comprehension pattern.
    """
    df_raw = pd.read_excel(path)
    return amortizationConfig(df_raw)