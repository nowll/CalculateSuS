#!/usr/bin/env python3
import sys
import re
import pandas as pd
import numpy as np
from pathlib import Path


def find_sus_columns(columns):
    """
    Cari kolom Q1..Q10 berdasarkan prefix "1.", "2.", ... "10."
    """
    sus_cols = []
    for i in range(1, 11):
        # paling umum: kolom diawali "1." dst
        matches = [c for c in columns if str(c).strip().startswith(f"{i}.")]
        if not matches:
            # fallback: kalau ada spasi aneh atau format beda tapi masih mengandung "i."
            matches = [c for c in columns if f"{i}." in str(c)]
        if not matches:
            raise ValueError(
                f"Tidak ketemu kolom untuk Q{i}. "
                f"Pastikan header pertanyaan mengandung '{i}.' atau edit mapping manual."
            )
        sus_cols.append(matches[0])
    return sus_cols


def to_likert_1_5(x):
    """
    Konversi nilai jawaban ke angka 1..5.
    Mendukung:
      - angka (1..5)
      - string yang mengandung angka 1..5
      - teks Likert ID/EN
    """
    if pd.isna(x):
        return np.nan

    # sudah numeric
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)

    s = str(x).strip()
    # ambil digit 1-5 pertama yang berdiri sendiri
    m = re.search(r"\b([1-5])\b", s)
    if m:
        return float(m.group(1))

    s_low = s.lower()

    # mapping Likert Indonesia/English (kalau kamu pakai opsi teks)
    mapping = {
        "sangat tidak setuju": 1,
        "tidak setuju": 2,
        "netral": 3,
        "setuju": 4,
        "sangat setuju": 5,
        "strongly disagree": 1,
        "disagree": 2,
        "neutral": 3,
        "agree": 4,
        "strongly agree": 5,
    }
    for k, v in mapping.items():
        if k in s_low:
            return float(v)

    return np.nan


def compute_sus(df, sus_cols):
    """
    Hitung SUS:
      - item ganjil (1,3,5,7,9): score = jawaban - 1
      - item genap  (2,4,6,8,10): score = 5 - jawaban
      - SUS = (sum scores) * 2.5
    """
    sus_numeric = df[sus_cols].applymap(to_likert_1_5)

    # validasi nilai harus 1..5
    invalid = (~sus_numeric.apply(lambda c: c.between(1, 5))).sum().sum()
    missing_rows = int(sus_numeric.isna().any(axis=1).sum())

    if invalid > 0:
        raise ValueError(f"Ada {invalid} sel jawaban yang bukan 1..5.")
    if missing_rows > 0:
        raise ValueError(
            f"Ada {missing_rows} responden yang punya jawaban kosong (NaN)."
        )

    odd_idx = [0, 2, 4, 6, 8]  # Q1,Q3,Q5,Q7,Q9
    even_idx = [1, 3, 5, 7, 9]  # Q2,Q4,Q6,Q8,Q10

    odd_scores = sus_numeric.iloc[:, odd_idx] - 1
    even_scores = 5 - sus_numeric.iloc[:, even_idx]
    sus_score = (odd_scores.sum(axis=1) + even_scores.sum(axis=1)) * 2.5

    return sus_score, sus_numeric


def main():
    if len(sys.argv) < 2:
        print("Usage: python hitung_sus.py <path_csv>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"File tidak ditemukan: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)

    # 1) deteksi kolom Q1..Q10
    sus_cols = find_sus_columns(df.columns)

    # 2) hitung SUS
    sus_score, sus_numeric = compute_sus(df, sus_cols)

    # 3) gabungkan hasil
    df_out = df.copy()
    df_out["SUS_Score"] = sus_score.round(2)

    # 4) ringkasan
    summary = {
        "Jumlah responden": int(len(df_out)),
        "SUS rata-rata": float(df_out["SUS_Score"].mean()),
        "Median": float(df_out["SUS_Score"].median()),
        "Std Dev": float(df_out["SUS_Score"].std(ddof=1)),
        "Minimum": float(df_out["SUS_Score"].min()),
        "Maksimum": float(df_out["SUS_Score"].max()),
        ">= 68 (di atas benchmark rata-rata)": int((df_out["SUS_Score"] >= 68).sum()),
        "< 68": int((df_out["SUS_Score"] < 68).sum()),
    }
    summary_df = pd.DataFrame(list(summary.items()), columns=["Metrik", "Nilai"])

    # 5) rata-rata per item (opsional, bagus untuk analisis)
    # kontribusi SUS (0..4)
    odd_scores = sus_numeric.iloc[:, [0, 2, 4, 6, 8]] - 1
    even_scores = 5 - sus_numeric.iloc[:, [1, 3, 5, 7, 9]]
    adj = pd.concat([odd_scores, even_scores], axis=1)
    adj.columns = [f"Adj_Q{i}" for i in range(1, 11)]

    item_summary = pd.DataFrame(
        {
            "Pertanyaan": [f"Q{i}" for i in range(1, 11)],
            "Rata-rata jawaban (1-5)": sus_numeric.mean(axis=0).values,
            "Rata-rata kontribusi SUS (0-4)": adj.mean(axis=0).values,
            "Nama kolom (CSV)": sus_cols,
        }
    )
    item_summary["Rata-rata jawaban (1-5)"] = item_summary[
        "Rata-rata jawaban (1-5)"
    ].round(3)
    item_summary["Rata-rata kontribusi SUS (0-4)"] = item_summary[
        "Rata-rata kontribusi SUS (0-4)"
    ].round(3)

    # 6) export
    out_csv = csv_path.with_name(csv_path.stem + "_SUS.csv")
    out_xlsx = csv_path.with_name(csv_path.stem + "_SUS.xlsx")

    df_out.to_csv(out_csv, index=False)
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name="Ringkasan")
        item_summary.to_excel(writer, index=False, sheet_name="Rata2_per_item")
        df_out.to_excel(writer, index=False, sheet_name="Data+SUS")

    # 7) print hasil ringkas
    print("\n=== RINGKASAN SUS ===")
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"- {k}: {v:.2f}")
        else:
            print(f"- {k}: {v}")

    print(f"\nOutput tersimpan:")
    print(f"- {out_csv}")
    print(f"- {out_xlsx}")


if __name__ == "__main__":
    main()
