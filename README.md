# SUS Calculator (Google Forms CSV)

A simple Python script to calculate **System Usability Scale (SUS)** scores from **Google Forms CSV responses** and export:
- SUS score per respondent (0–100)
- Summary stats (mean, median, std dev, min, max)
- Per-item averages (raw 1–5 and SUS contribution 0–4)
- Output files: **CSV** and **Excel (.xlsx)**

## SUS Scoring Rules
SUS uses 10 items with a 1–5 scale:
- Odd items (Q1, Q3, Q5, Q7, Q9): `score = answer - 1`
- Even items (Q2, Q4, Q6, Q8, Q10): `score = 5 - answer`
- Final SUS: `(sum of all item scores) * 2.5`

## Requirements
- Python 3.9+ (recommended)
- Dependencies:
  - pandas
  - openpyxl
- Install: 
```bash
pip install pandas openpyxl
```
## Input Format

Export responses from Google Form to CSV (Form Responses).
The script expects 10 SUS columns labeled like:

1. ...

2. ...

...

10. ...

It supports answers as:
numeric 1..5, or
text Likert (Indonesian/English), e.g. Sangat Setuju, Setuju, etc.

## Usage

Windows example
```bash
python hitung_sus.py "E:\Random\Survei WEB xyz (Responses) - Form Responses 1.csv"
```

macOS/Linux example
```bash
python hitung_sus.py "/path/to/Form Responses 1.csv"
```

## Output

For an input file like:
Form Responses 1.csv

The script generates:
Form Responses 1_SUS.csv
Form Responses 1_SUS.xlsx

Excel sheets:
Ringkasan (summary)
Rata2_per_item (per-item averages)
Data+SUS (original data + SUS score)

## Troubleshooting
"Tidak ketemu kolom untuk Qx"
Your CSV headers may not start with 1., 2., etc.

Fix: edit the script and manually set sus_cols to your exact column names:
```bash
sus_cols = [
    "NAMA_KOLOM_Q1",
    "NAMA_KOLOM_Q2",
    ...
    "NAMA_KOLOM_Q10",
]
```
File not found (Windows path)
Use quotes:
```bash
python hitung_sus.py "E:\folder\file.csv"
```
Or test path exists:
```bash
python -c "from pathlib import Path; p=Path(r'E:\folder\file.csv'); print(p.exists(), p)"
```
