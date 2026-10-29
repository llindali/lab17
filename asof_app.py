"""Lab 17: compare current FRED observations with an ALFRED vintage."""
from datetime import date, datetime
from io import StringIO
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

SERIES = {
    'BAA': "Moody's Baa corporate bond yield",
    'FEDFUNDS': 'Effective federal funds rate',
    'DGS10': '10-year Treasury yield',
    'MORTGAGE30US': '30-year fixed mortgage rate',
}


def parse_csv(text):
    """Use the returned column name: ALFRED may append its vintage to the ID."""
    frame = pd.read_csv(StringIO(text), na_values=['.', ''])
    if len(frame.columns) != 2:
        raise ValueError('Expected a date column and one series column.')
    dates = pd.to_datetime(frame.iloc[:, 0], errors='coerce')
    values = pd.to_numeric(frame.iloc[:, 1], errors='coerce')
    result = pd.Series(values.to_numpy(), index=dates, name='Value')
    result = result[result.index.notna()].dropna().sort_index()
    if result.index.has_duplicates:
        raise ValueError('Unexpected duplicate observation dates.')
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def download_current(series_id):
    url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?' + urlencode({'id': series_id})
    with urlopen(url, timeout=40) as response:
        text = response.read().decode('utf-8-sig')
    return parse_csv(text), datetime.now(ZoneInfo('America/Indianapolis')).isoformat(timespec='seconds')


@st.cache_data(ttl=3600, show_spinner=False)
def download_asof(series_id, asof):
    # Request the actual vintage; filtering today's file cannot undo revisions.
    url = 'https://alfred.stlouisfed.org/graph/alfredgraph.csv?' + urlencode(
        {'id': series_id, 'vintage_date': asof.isoformat()})
    with urlopen(url, timeout=40) as response:
        text = response.read().decode('utf-8-sig')
    values = parse_csv(text)
    # Defensive date guard; vintage selection, above, establishes availability.
    values = values.loc[values.index <= pd.Timestamp(asof)]
    return values, datetime.now(ZoneInfo('America/Indianapolis')).isoformat(timespec='seconds')


def compare(current, vintage):
    """Compare full histories, independently of the chart start date."""
    common = current.index.intersection(vintage.index)
    revisions = int(((current.loc[common] - vintage.loc[common]).abs() > 1e-9).sum())
    last = vintage.index[-1] if not vintage.empty else None
    return {
        'Last date known then': last.date().isoformat() if last is not None else None,
        'Value known then': float(vintage.iloc[-1]) if last is not None else None,
        'Last date today': current.index[-1].date().isoformat() if not current.empty else None,
        'Value today': float(current.iloc[-1]) if not current.empty else None,
        'Later observations': int((current.index > last).sum()) if last is not None else len(current),
        'Revised shared dates': revisions,
    }


def main():
    st.set_page_config(page_title='Lab 17 | Point-in-Time Audit', layout='wide')
    today = datetime.now(ZoneInfo('America/Indianapolis')).date()
    st.title('Point-in-Time Rates Audit')
    st.caption(f'Data from FRED and ALFRED, Federal Reserve Bank of St. Louis; downloaded {today}. '
               'Built with AI help; a learning demonstration, not investment advice.')
    selected = st.sidebar.multiselect('Series', list(SERIES), default=list(SERIES),
                                      format_func=lambda s: f'{s} — {SERIES[s]}')
    extra = st.sidebar.text_input('Add a FRED series ID', 'DGS10').strip().upper()
    start = st.sidebar.date_input('Chart start date', date(2020, 1, 1),
                                  min_value=date(1776, 1, 1), max_value=today)
    asof = st.sidebar.date_input('As known on', today, min_value=date(1776, 1, 1), max_value=today)
    if st.sidebar.button('Refresh downloads'):
        st.cache_data.clear()
    st.info('The vintage is the information available by the selected date, not today’s data '
            'cut off at that observation date. Date-only vintages do not establish intraday availability.')
    if extra and extra not in selected:
        selected.append(extra)
    rows = []
    for series_id in selected:
        if not re.fullmatch(r'[A-Z0-9_]+', series_id):
            st.error(f'{series_id}: use a valid FRED series ID.')
            continue
        st.subheader(f'{series_id} — {SERIES.get(series_id, "Custom series")}')
        st.markdown(f'[FRED source and units](https://fred.stlouisfed.org/series/{series_id})')
        try:
            current, current_time = download_current(series_id)
            vintage, vintage_time = download_asof(series_id, asof)
            if current.empty:
                raise ValueError('No numeric observations returned for this series.')
            chart = current.loc[current.index >= pd.Timestamp(start)]
            if chart.empty:
                st.warning('No current observations after the chart start date.')
            else:
                st.line_chart(chart.rename(series_id))
            row = compare(current, vintage)
            st.caption(f'Last observation known on {asof}: {row["Last date known then"] or "none"}. '
                       f'Fetched current: {current_time}; vintage: {vintage_time}.')
            rows.append({'Series': f'https://fred.stlouisfed.org/series/{series_id}', **row})
            if vintage.empty:
                st.warning('No observations were available in this vintage.')
            with st.expander('Inspect observations and revisions'):
                detail = pd.concat([vintage.rename('As known then'), current.rename('Today')], axis=1)
                detail['Change'] = detail['Today'] - detail['As known then']
                st.dataframe(detail.sort_index(ascending=False), width='stretch')
        except Exception as exc:
            st.error(f'{series_id}: download or parsing failed ({exc}). Other series continue.')
    st.subheader('Availability and revisions — full history')
    st.caption('Later observations count valid current observations after the last known date; '
               'revisions compare nonmissing values on matching observation dates. '
               'The two latest-value columns may describe different dates; inspect shared dates above.')
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch',
                     column_config={'Series': st.column_config.LinkColumn('Series', display_text=r'series/(.*)')})
    else:
        st.warning('Select at least one valid series with available data.')


if __name__ == '__main__':
    main()
