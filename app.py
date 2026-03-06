"""
MKE Live Jazz — Streamlit App
Milwaukee live music schedule aggregator.
Deploy to Streamlit Cloud at streamlit.io
"""

import streamlit as st
from datetime import date, timedelta
from scraper import scrape_all_venues

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MKE LIVE JAZZ",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── VENUE METADATA ───────────────────────────────────────────────────────────
VENUES = {
    "estate":   {"label": "THE JAZZ ESTATE",    "color": "#5bbeff", "address": "The Jazz Estate · 2423 N Murray Ave"},
    "centro":   {"label": "BAR CENTRO",          "color": "#3dffa0", "address": "Bar Centro Riverwest · 804 E Center St"},
    "transfer": {"label": "TRANSFER PIZZERIA",   "color": "#ff9f4a", "address": "Transfer Pizzeria Café · 101 W Mitchell St"},
    "pfister":  {"label": "THE PFISTER",         "color": "#c084fc", "address": "The Pfister Lobby Lounge · 424 E Wisconsin Ave"},
}

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Mono:wght@400;700&display=swap');

/* ── Reset & Base ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.stApp { background: #1a1a1a; color: #e8e4d8; font-family: 'Space Mono', monospace; }
section[data-testid="stSidebar"] { display: none; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #333; }

/* ── TICKER ── */
.ticker-wrap {
    background: #f0c020; overflow: hidden; white-space: nowrap;
    padding: 6px 0; border-bottom: 2px solid #d4a800;
}
.ticker-inner {
    display: inline-block;
    animation: scroll-ticker 55s linear infinite;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.85rem; letter-spacing: 3px; color: #000;
}
@keyframes scroll-ticker {
    from { transform: translateX(100vw); }
    to   { transform: translateX(-100%); }
}

/* ── HEADER ── */
.mke-header {
    background: #1a1a1a;
    border-bottom: 1px solid #2d2d2d;
    padding: 18px 36px 16px;
    display: flex; align-items: flex-end; justify-content: space-between;
    flex-wrap: wrap; gap: 12px;
}
.mke-logo {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem; letter-spacing: 4px;
    color: #f0c020; line-height: 1;
}
.mke-subtitle {
    font-size: 0.6rem; letter-spacing: 3px; color: #666;
    margin-top: 2px;
}
.mke-meta {
    text-align: right; font-size: 0.62rem; color: #888; letter-spacing: 1px;
}
.mke-meta .dot { color: #f0c020; }

/* ── FILTER SECTION ── */
.filter-section {
    background: #1a1a1a;
    border-bottom: 1px solid #2d2d2d;
    padding: 14px 36px;
}
.filter-label {
    font-size: 0.6rem; letter-spacing: 2px; color: #555;
    margin-bottom: 8px; display: flex; align-items: center; gap: 8px;
}
.filter-label::before { content: "◆"; color: #f0c020; font-size: 0.5rem; }

/* ── VENUE TABS ── */
.venue-tabs-wrap {
    background: #1a1a1a;
    border-bottom: 1px solid #2d2d2d;
    padding: 0 36px;
    display: flex; align-items: stretch; gap: 2px;
    overflow-x: auto;
}
.venue-tab {
    padding: 14px 18px;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.95rem; letter-spacing: 2px;
    color: #555; background: transparent;
    border: none; border-bottom: 3px solid transparent;
    cursor: pointer; white-space: nowrap;
    transition: all 0.15s; text-decoration: none;
}
.venue-tab.active { color: #e8e4d8; }
.venue-tab:hover:not(.active) { color: #999; }

/* ── VENUE ADDRESS LIST ── */
.venue-addresses {
    background: #1a1a1a;
    padding: 10px 36px 12px;
    border-bottom: 1px solid #2d2d2d;
    font-size: 0.62rem; color: #555; letter-spacing: 0.5px;
    display: flex; flex-wrap: wrap; gap: 6px 20px;
}
.addr-item { display: flex; align-items: center; gap: 6px; }
.addr-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }

/* ── VIEW TOGGLE ── */
.view-toggle-row {
    background: #1a1a1a;
    padding: 12px 36px;
    display: flex; align-items: center; gap: 8px;
    border-bottom: 1px solid #2d2d2d;
}
.view-btn-custom {
    padding: 7px 16px;
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem; letter-spacing: 1.5px;
    background: transparent; color: #555;
    border: 1px solid #2d2d2d; cursor: pointer;
    transition: all 0.15s;
}
.view-btn-custom.active {
    border-color: #f0c020; color: #f0c020; background: #1f1e10;
}
.show-count-badge {
    margin-left: auto;
    font-size: 0.65rem; color: #555; letter-spacing: 1px;
}
.show-count-badge span { color: #e8e4d8; }

/* ── SCHEDULE ── */
.schedule-wrap { padding: 24px 36px 80px; }

.day-header {
    display: flex; align-items: baseline; gap: 12px;
    padding-bottom: 8px; margin-bottom: 8px;
    border-bottom: 1px solid #2d2d2d; margin-top: 32px;
}
.day-header:first-child { margin-top: 0; }
.day-name { font-family: 'Bebas Neue', sans-serif; font-size: 2rem; letter-spacing: 4px; color: #e8e4d8; }
.day-full { font-size: 0.58rem; color: #555; letter-spacing: 2px; }
.day-count {
    margin-left: auto; font-size: 0.55rem; letter-spacing: 1.5px;
    border: 1px solid #2d2d2d; color: #555; padding: 2px 8px;
}

/* ── SHOW ROW ── */
.show-row {
    display: grid;
    grid-template-columns: 78px 4px 1fr auto;
    align-items: center;
    padding: 13px 16px;
    background: #1f1f1f;
    border: 1px solid #272727;
    border-left: none;
    margin-bottom: 3px;
    gap: 16px;
    transition: all 0.15s;
    text-decoration: none; color: inherit;
}
.show-row:hover { background: #252525; border-color: #383838; }
.show-row a { text-decoration: none; color: inherit; }

.show-time { font-family: 'Bebas Neue', sans-serif; font-size: 1.25rem; letter-spacing: 2px; color: #f0c020; line-height: 1; }
.show-time .ap { font-size: 0.55rem; font-family: 'Space Mono', monospace; color: #555; display: block; }
.venue-stripe { width: 4px; height: 38px; border-radius: 1px; }

.show-artist { font-size: 0.95rem; font-weight: 700; margin-bottom: 3px; letter-spacing: 0.5px; }
.show-sub { font-size: 0.58rem; color: #555; letter-spacing: 0.5px; display: flex; gap: 8px; flex-wrap: wrap; }
.show-sub .ven { font-size: 0.58rem; }
.show-sub .pipe { color: #333; }

.show-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 5px; min-width: 80px; }
.price-pill {
    font-size: 0.55rem; letter-spacing: 1px; padding: 2px 8px;
    border: 1px solid #2d2d2d; color: #555;
}
.price-free   { border-color: #3dffa0; color: #3dffa0; }
.price-paid   { border-color: #f0c020; color: #f0c020; }
.price-tba    { border-color: #333; color: #444; }
.ticket-lnk   { font-size: 0.52rem; color: #f0c020; text-decoration: none; border-bottom: 1px dotted #f0c020; }

/* ── GRID ── */
.grid-wrap {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 10px;
    padding: 24px 36px 80px;
}
.show-card {
    background: #1f1f1f;
    border: 1px solid #272727;
    padding: 18px; position: relative; overflow: hidden;
    text-decoration: none; color: inherit;
    transition: border-color 0.15s;
    display: block;
}
.show-card:hover { border-color: #3a3a3a; }
.card-top-stripe { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.card-venue-label { font-size: 0.52rem; letter-spacing: 2px; margin-bottom: 10px; }
.card-date { font-size: 0.58rem; color: #555; letter-spacing: 1px; margin-bottom: 6px; display: flex; justify-content: space-between; }
.card-artist { font-size: 1.05rem; font-weight: 700; letter-spacing: 0.5px; line-height: 1.25; margin-bottom: 6px; }
.card-notes { font-size: 0.58rem; color: #666; margin-bottom: 12px; }
.card-footer { display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #272727; padding-top: 10px; margin-top: auto; }

/* ── ERROR / EMPTY ── */
.error-banner {
    margin: 16px 36px;
    background: rgba(255,79,107,0.08);
    border: 1px solid rgba(255,79,107,0.25);
    padding: 12px 18px; font-size: 0.68rem; color: #ff4f6b;
    letter-spacing: 0.5px;
}
.empty-msg {
    text-align: center; padding: 60px 20px;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem; letter-spacing: 4px; color: #333;
}

/* ── STATUS INDICATOR ── */
.scrape-status {
    display: flex; gap: 12px; flex-wrap: wrap;
    padding: 10px 36px; background: #161616;
    border-bottom: 1px solid #222;
    font-size: 0.58rem; letter-spacing: 1px;
}
.status-item { display: flex; align-items: center; gap: 6px; }
.status-dot { width: 5px; height: 5px; border-radius: 50%; }
.s-ok { color: #3dffa0; }
.s-err { color: #ff4f6b; }

/* ── STREAMLIT BUTTON OVERRIDES ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid #f0c020 !important;
    color: #f0c020 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 2px !important;
    padding: 8px 20px !important;
    border-radius: 0 !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #f0c020 !important;
    color: #000 !important;
}
/* Submit show button */
.submit-btn > button {
    background: #f0c020 !important;
    color: #000 !important;
    border-color: #f0c020 !important;
}
.submit-btn > button:hover {
    background: #d4a800 !important;
}

/* Date input overrides */
.stDateInput > label { color: #555 !important; font-size: 0.58rem !important; letter-spacing: 2px !important; }
.stDateInput input { background: #1f1f1f !important; color: #e8e4d8 !important; border: 1px solid #2d2d2d !important; border-radius: 0 !important; font-family: 'Space Mono', monospace !important; }

/* Quick date buttons */
.quick-btns .stButton > button {
    border-color: #2d2d2d !important; color: #555 !important;
    padding: 6px 12px !important; font-size: 0.6rem !important;
}
.quick-btns .stButton > button:hover {
    border-color: #f0c020 !important; color: #f0c020 !important; background: transparent !important;
}

/* Multiselect / select hide */
div[data-testid="stHorizontalBlock"] > div { gap: 6px !important; }
</style>
""", unsafe_allow_html=True)


# ─── SESSION STATE INIT ────────────────────────────────────────────────────────
if "shows" not in st.session_state:
    st.session_state.shows = []
    st.session_state.statuses = {}
    st.session_state.last_updated = None
    st.session_state.loaded = False

if "venue_filter" not in st.session_state:
    st.session_state.venue_filter = "ALL"

if "view" not in st.session_state:
    st.session_state.view = "schedule"

if "date_from" not in st.session_state:
    st.session_state.date_from = None
    st.session_state.date_to = None


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def fmt_time(t: str) -> tuple[str, str]:
    """Return (display_time, am_pm) from 'HH:MM'."""
    if not t or t == "—":
        return "—", ""
    try:
        h, m = map(int, t.split(":"))
        ap = "PM" if h >= 12 else "AM"
        dh = h - 12 if h > 12 else (12 if h == 0 else h)
        return f"{dh}:{m:02d}", ap
    except Exception:
        return t, ""


def price_class(p: str) -> str:
    if not p:
        return "price-tba"
    pl = p.lower()
    if "free" in pl or "no cover" in pl:
        return "price-free"
    if re.search(r"\$\d+", pl):
        return "price-paid"
    return "price-tba"


def apply_filters(shows: list[dict]) -> list[dict]:
    filtered = shows
    # Venue filter
    if st.session_state.venue_filter != "ALL":
        filtered = [s for s in filtered if s["venue_id"] == st.session_state.venue_filter]
    # Date filter
    if st.session_state.date_from:
        filtered = [s for s in filtered if s["date"] >= st.session_state.date_from]
    if st.session_state.date_to:
        filtered = [s for s in filtered if s["date"] <= st.session_state.date_to]
    return filtered


def do_scrape():
    with st.spinner(""):
        shows, statuses = scrape_all_venues()
    st.session_state.shows = shows
    st.session_state.statuses = statuses
    st.session_state.last_updated = date.today().strftime("DATA PULLED %b %-d, %Y").upper()
    st.session_state.loaded = True


# Auto-load on first visit
if not st.session_state.loaded:
    do_scrape()

import re

# ─── TICKER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ticker-wrap">
  <span class="ticker-inner">
    ♩ THE JAZZ ESTATE &nbsp;·&nbsp; 2423 N MURRAY AVE &nbsp;&nbsp;&nbsp;
    ♩ BAR CENTRO RIVERWEST &nbsp;·&nbsp; 804 E CENTER ST &nbsp;&nbsp;&nbsp;
    ♩ TRANSFER PIZZERIA CAFÉ &nbsp;·&nbsp; 101 W MITCHELL ST &nbsp;&nbsp;&nbsp;
    ♩ THE PFISTER LOBBY LOUNGE &nbsp;·&nbsp; 424 E WISCONSIN AVE &nbsp;&nbsp;&nbsp;
    ♩ MKE LIVE JAZZ &nbsp;·&nbsp; MILWAUKEE MUSIC SCHEDULE &nbsp;&nbsp;&nbsp;
    ♩ THE JAZZ ESTATE &nbsp;·&nbsp; 2423 N MURRAY AVE &nbsp;&nbsp;&nbsp;
    ♩ BAR CENTRO RIVERWEST &nbsp;·&nbsp; 804 E CENTER ST &nbsp;&nbsp;&nbsp;
  </span>
</div>
""", unsafe_allow_html=True)

# ─── HEADER ───────────────────────────────────────────────────────────────────
visible_shows = apply_filters(st.session_state.shows)
n_venues = len({s["venue_id"] for s in st.session_state.shows})

col_logo, col_meta, col_btns = st.columns([4, 3, 3])

with col_logo:
    st.markdown("""
    <div style="padding: 18px 0 12px 36px;">
      <div class="mke-logo">MKE LIVE JAZZ</div>
      <div class="mke-subtitle">MILWAUKEE MUSIC SCHEDULE</div>
    </div>
    """, unsafe_allow_html=True)

with col_meta:
    last_upd = st.session_state.last_updated or "NOT YET LOADED"
    st.markdown(f"""
    <div style="padding: 22px 0 0 0; font-size: 0.65rem; color: #888; letter-spacing: 1.5px; line-height: 1.9;">
      <span style="color:#f0c020">●</span> {n_venues} VENUES<br>
      {last_upd}
    </div>
    """, unsafe_allow_html=True)

with col_btns:
    st.markdown('<div style="padding: 18px 36px 0 0; display: flex; gap: 8px; justify-content: flex-end;">', unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    with b1:
        if st.button("↺  REFRESH", key="refresh_main"):
            do_scrape()
            st.rerun()
    with b2:
        st.markdown('<div class="submit-btn">', unsafe_allow_html=True)
        st.link_button("+ SUBMIT A SHOW", "mailto:info@example.com")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<hr style="border:none;border-top:1px solid #2d2d2d;margin:0"/>', unsafe_allow_html=True)

# ─── SCRAPE STATUS ────────────────────────────────────────────────────────────
if st.session_state.statuses:
    status_html = '<div class="scrape-status">'
    for vid, msg in st.session_state.statuses.items():
        color = VENUES[vid]["color"]
        cls = "s-ok" if msg.startswith("✓") else "s-err"
        status_html += (
            f'<span class="status-item">'
            f'<span class="status-dot" style="background:{color}"></span>'
            f'<span class="{cls}">{VENUES[vid]["label"]}: {msg}</span>'
            f'</span>'
        )
    status_html += "</div>"
    st.markdown(status_html, unsafe_allow_html=True)

# ─── DATE FILTER ──────────────────────────────────────────────────────────────
st.markdown('<div class="filter-section">', unsafe_allow_html=True)
st.markdown('<div class="filter-label">DATE SEARCH</div>', unsafe_allow_html=True)

dc1, dc2, dc3, dc4, dc5, dc6, dc7, dc8 = st.columns([2, 0.3, 2, 0.8, 0.8, 0.8, 1, 1])

with dc1:
    d_from = st.date_input("FROM", value=None, min_value=date.today(), key="input_from", label_visibility="collapsed")
    if d_from:
        st.session_state.date_from = d_from

with dc2:
    st.markdown('<div style="padding-top:8px;color:#555;text-align:center">→</div>', unsafe_allow_html=True)

with dc3:
    d_to = st.date_input("TO", value=None, min_value=date.today(), key="input_to", label_visibility="collapsed")
    if d_to:
        st.session_state.date_to = d_to

st.markdown('<div class="quick-btns" style="display:contents">', unsafe_allow_html=True)
with dc4:
    if st.button("TODAY", key="q_today"):
        st.session_state.date_from = date.today()
        st.session_state.date_to = date.today()
        st.rerun()
with dc5:
    if st.button("WEEKEND", key="q_weekend"):
        today = date.today()
        days_to_fri = (4 - today.weekday()) % 7
        fri = today + timedelta(days=days_to_fri)
        st.session_state.date_from = fri
        st.session_state.date_to = fri + timedelta(days=2)
        st.rerun()
with dc6:
    if st.button("THIS WEEK", key="q_week"):
        today = date.today()
        st.session_state.date_from = today
        st.session_state.date_to = today + timedelta(days=(6 - today.weekday()))
        st.rerun()
with dc7:
    if st.button("THIS MONTH", key="q_month"):
        today = date.today()
        import calendar as cal_mod
        last_day = cal_mod.monthrange(today.year, today.month)[1]
        st.session_state.date_from = today
        st.session_state.date_to = date(today.year, today.month, last_day)
        st.rerun()
with dc8:
    if st.button("✕  CLEAR", key="q_clear"):
        st.session_state.date_from = None
        st.session_state.date_to = None
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)  # filter-section

# ─── VENUE TABS ───────────────────────────────────────────────────────────────
tab_html = '<div class="venue-tabs-wrap">'

# ALL tab
active_all = "active" if st.session_state.venue_filter == "ALL" else ""
tab_html += f'<span class="venue-tab {active_all}" style="border-bottom-color:{"#f0c020" if active_all else "transparent"}">ALL</span>'

for vid, meta in VENUES.items():
    active = "active" if st.session_state.venue_filter == vid else ""
    color = meta["color"] if active else "transparent"
    tab_html += (
        f'<span class="venue-tab {active}" '
        f'style="border-bottom-color:{color};color:{"#e8e4d8" if active else "#555"}">'
        f'{meta["label"]}</span>'
    )

tab_html += "</div>"
st.markdown(tab_html, unsafe_allow_html=True)

# Actual clickable venue buttons (Streamlit)
vcols = st.columns([1, 2, 2, 2.5, 2, 2.5, 2])
with vcols[0]:
    if st.button("ALL", key="vf_all"):
        st.session_state.venue_filter = "ALL"
        st.rerun()
for i, (vid, meta) in enumerate(VENUES.items()):
    with vcols[i + 1]:
        if st.button(meta["label"], key=f"vf_{vid}"):
            st.session_state.venue_filter = vid
            st.rerun()

# ─── VENUE ADDRESSES ──────────────────────────────────────────────────────────
addr_html = '<div class="venue-addresses">'
for meta in VENUES.values():
    addr_html += (
        f'<span class="addr-item">'
        f'<span class="addr-dot" style="background:{meta["color"]}"></span>'
        f'<span>{meta["address"]}</span>'
        f'</span>'
    )
addr_html += "</div>"
st.markdown(addr_html, unsafe_allow_html=True)

# ─── VIEW TOGGLE + COUNT ──────────────────────────────────────────────────────
visible = apply_filters(st.session_state.shows)
n = len(visible)

v1, v2, v3 = st.columns([1, 1, 8])
with v1:
    if st.button("◆ SCHEDULE", key="view_sched"):
        st.session_state.view = "schedule"
        st.rerun()
with v2:
    if st.button("⊞ GRID", key="view_grid"):
        st.session_state.view = "grid"
        st.rerun()
with v3:
    st.markdown(
        f'<div class="show-count-badge" style="padding-top:8px">'
        f'<span>{n}</span> SHOWS'
        f'</div>',
        unsafe_allow_html=True
    )

st.markdown('<hr style="border:none;border-top:1px solid #2d2d2d;margin:0 0 0 0"/>', unsafe_allow_html=True)

# ─── SHOWS DISPLAY ────────────────────────────────────────────────────────────
if not visible:
    if st.session_state.loaded:
        st.markdown('<div class="empty-msg">NO SHOWS FOUND</div>', unsafe_allow_html=True)
else:
    # Group by date
    grouped: dict[date, list] = {}
    for show in visible:
        grouped.setdefault(show["date"], []).append(show)

    if st.session_state.view == "schedule":
        html = '<div class="schedule-wrap">'

        for event_date, day_shows in sorted(grouped.items()):
            day_name = event_date.strftime("%A").upper()
            date_full = event_date.strftime("%B %-d, %Y").upper()

            html += (
                f'<div class="day-header">'
                f'<span class="day-name">{day_name}</span>'
                f'<span class="day-full">{date_full}</span>'
                f'<span class="day-count">{len(day_shows)} SHOW{"S" if len(day_shows)!=1 else ""}</span>'
                f'</div>'
            )

            for show in day_shows:
                t, ap = fmt_time(show["time"])
                venue_meta = VENUES.get(show["venue_id"], {})
                stripe_color = venue_meta.get("color", "#444")
                venue_label = venue_meta.get("label", show["venue"])
                venue_color = venue_meta.get("color", "#555")

                pc = price_class(show["price"] or "")
                price_disp = show["price"] or "TBA"

                notes_html = ""
                if show.get("notes"):
                    notes_html = f'<span class="pipe">·</span><span style="font-style:italic">{show["notes"][:60]}</span>'

                ticket_html = ""
                if show.get("ticket_url"):
                    ticket_html = f'<a class="ticket-lnk" href="{show["ticket_url"]}" target="_blank">TICKETS →</a>'

                row_href = show.get("ticket_url", "#")
                html += f"""
<a class="show-row" href="{row_href}" target="{'_blank' if show.get('ticket_url') else '_self'}">
  <div class="show-time">{t}<span class="ap">{ap}</span></div>
  <div class="venue-stripe" style="background:{stripe_color}"></div>
  <div class="show-info">
    <div class="show-artist">{show['artist']}</div>
    <div class="show-sub">
      <span class="ven" style="color:{venue_color}">{venue_label}</span>
      {notes_html}
    </div>
  </div>
  <div class="show-meta">
    <span class="price-pill {pc}">{price_disp}</span>
    {ticket_html}
  </div>
</a>"""

        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    else:  # GRID
        html = '<div class="grid-wrap">'
        for show in visible:
            t, ap = fmt_time(show["time"])
            venue_meta = VENUES.get(show["venue_id"], {})
            stripe_color = venue_meta.get("color", "#444")
            venue_label = venue_meta.get("label", show["venue"])
            venue_color = venue_meta.get("color", "#555")

            date_disp = show["date"].strftime("%a, %b %-d").upper()
            pc = price_class(show["price"] or "")
            price_disp = show["price"] or "TBA"

            ticket_html = ""
            if show.get("ticket_url"):
                ticket_html = f'<a class="ticket-lnk" href="{show["ticket_url"]}" target="_blank" onclick="event.stopPropagation()">TICKETS →</a>'

            notes_html = f'<div class="card-notes">{show["notes"][:60]}</div>' if show.get("notes") else ""

            html += f"""
<a class="show-card" href="{show.get('ticket_url','#')}" target="{'_blank' if show.get('ticket_url') else '_self'}">
  <div class="card-top-stripe" style="background:{stripe_color}"></div>
  <div class="card-venue-label" style="color:{venue_color}">{venue_label}</div>
  <div class="card-date"><span>{date_disp}</span><span>{t} {ap}</span></div>
  <div class="card-artist">{show['artist']}</div>
  {notes_html}
  <div class="card-footer">
    <span class="price-pill {pc}">{price_disp}</span>
    {ticket_html}
  </div>
</a>"""

        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
sources_html = (
    '<div style="padding:20px 36px;border-top:1px solid #1f1f1f;'
    'font-size:0.58rem;color:#333;letter-spacing:1px;">'
    'SOURCES: '
)
links = [
    ("The Jazz Estate", "https://www.estatemke.com/events"),
    ("Bar Centro Riverwest", "https://centrocaferiverwest.com/events-calendar/"),
    ("Transfer Pizzeria Café", "https://www.transfermke.com/events"),
    ("The Pfister Hotel", "https://www.thepfisterhotel.com/happenings?category=Live%20Music"),
]
sources_html += " · ".join(
    f'<a href="{url}" target="_blank" style="color:#444;text-decoration:none;border-bottom:1px solid #333">{name}</a>'
    for name, url in links
)
sources_html += "</div>"
st.markdown(sources_html, unsafe_allow_html=True)
