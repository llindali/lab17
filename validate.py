"""Run the lab's checks against live downloads; never supplies app data."""
from datetime import date
from pathlib import Path
import pandas as pd
from asof_app import download_current, download_asof, compare


def main():
    lines = ['# Live validation', '', f'Run date: {date.today()}. All values below came from live CSV downloads.', '',
             '| Series | Vintage | Last observation | Value | Later observations | Revised shared dates | Result |',
             '|---|---|---|---:|---:|---:|---|']
    expected = {'BAA': ('2026-09-01', 6.47), 'FEDFUNDS': ('2026-09-01', 3.75),
                'DGS10': ('2026-10-02', 5.28), 'MORTGAGE30US': ('2026-10-01', 7.28)}
    current_data = {}
    for sid, (last, value) in expected.items():
        current, _ = download_current(sid)
        vintage, _ = download_asof(sid, date(2026, 10, 5))
        current_data[sid] = current
        row = compare(current, vintage)
        passed = row['Last date known then'] == last and abs(row['Value known then'] - value) < 1e-9
        lines.append(f'| {sid} | 2026-10-05 | {row["Last date known then"]} | {row["Value known then"]} | {row["Later observations"]} | {row["Revised shared dates"]} | {"PASS" if passed else "FAIL"} |')
        assert passed, (sid, row)
    current, _ = download_current('PAYEMS')
    vintage, _ = download_asof('PAYEMS', date(2025, 1, 15))
    row = compare(current, vintage)
    december = float(current.loc['2024-12-01'])
    assert row['Last date known then'] == '2024-12-01' and row['Value known then'] == 159536
    assert december < 159536 and row['Revised shared dates'] > 0
    lines += [f'| PAYEMS | 2025-01-15 | 2024-12-01 | 159536 | {row["Later observations"]} | {row["Revised shared dates"]} | PASS |', '',
              f'PAYEMS December 2024: vintage = 159,536; current = {december:,.0f} thousand jobs. Same-date change = {december-159536:,.0f} thousand jobs.', '',
              '## Selected-series comparison', '', '| As known on | Last DGS10 observation | Value (%) | Later observations | Revisions |', '|---|---|---:|---:|---:|']
    for day in [date(2026, 9, 30), date.today()]:
        v, _ = download_asof('DGS10', day)
        r = compare(current_data['DGS10'], v)
        lines.append(f'| {day} | {r["Last date known then"]} | {r["Value known then"]} | {r["Later observations"]} | {r["Revised shared dates"]} |')
    lines += ['', '## Three source-page comparisons', '', '| Observation | Download (%) | FRED page (%) | Result |', '|---|---:|---:|---|']
    for day, value in [('2026-10-27',4.99),('2026-10-26',5.00),('2026-10-23',5.00)]:
        actual = float(current_data['DGS10'].loc[day])
        assert actual == value
        lines.append(f'| {day} | {actual:.2f} | {value:.2f} | PASS |')
    lines += ['', 'Source page inspected during preparation: https://fred.stlouisfed.org/series/DGS10',
              'These source-page comparisons were checked with AI assistance; the student’s own three-value check remains an in-class activity.']
    Path('validation.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
