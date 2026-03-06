"""
MKE Live Jazz - Venue Scrapers
Scrapes 4 Milwaukee music venues for upcoming shows.
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import date, datetime
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

TODAY = date.today()


def _resolve_year(month_num: int) -> int:
    """Pick the nearest future year for a given month number."""
    if month_num >= TODAY.month:
        return TODAY.year
    return TODAY.year + 1


def _parse_date(month_str: str, day_str: str) -> date | None:
    month_str = month_str.lower().strip()
    month_num = MONTH_MAP.get(month_str)
    if not month_num:
        return None
    try:
        year = _resolve_year(month_num)
        return date(year, month_num, int(day_str))
    except (ValueError, TypeError):
        return None


def _parse_time_12h(time_str: str) -> str:
    """Convert '7:00 PM' or '9:30 pm' to 'HH:MM' 24-hour."""
    time_str = time_str.strip().upper()
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_str)
    if not m:
        m = re.match(r"(\d{1,2})\s*(AM|PM)", time_str)
        if m:
            h, mins, meridiem = int(m.group(1)), 0, m.group(2)
        else:
            return "20:00"
    else:
        h, mins, meridiem = int(m.group(1)), int(m.group(2)), m.group(3)
    if meridiem == "PM" and h != 12:
        h += 12
    elif meridiem == "AM" and h == 12:
        h = 0
    return f"{h:02d}:{mins:02d}"


# ─────────────────────────────────────────────
# 1. THE JAZZ ESTATE  (estatemke.com/events)
# ─────────────────────────────────────────────
def scrape_estate() -> list[dict]:
    """
    The Estate is a Wix site. Content is server-rendered with
    markdown-style h2 date headers: '## THU MARCH 5'
    followed by artist name, optional ticket links.
    """
    shows = []
    try:
        resp = requests.get(
            "https://www.estatemke.com/events", headers=HEADERS, timeout=20
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Collect all ticket links keyed by position in page
        ticket_links = [
            a["href"]
            for a in soup.find_all("a", href=re.compile(r"tix\.com", re.I))
        ]
        ticket_idx = 0

        # Work on plain text — Wix SSR puts event info in readable text nodes
        text = soup.get_text(separator="\n")
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # Date header pattern: "THU MARCH 5", "FRI MARCH 6", "SAT APRIL 11", etc.
        date_re = re.compile(
            r"^(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s+"
            r"(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+"
            r"(\d{1,2})$",
            re.IGNORECASE,
        )

        # Noise lines to skip
        skip_patterns = re.compile(
            r"^(HOME|EVENTS|COCKTAILS|CONTACT|MORE\.\.\.|"
            r"ALL NIGHT!|TOP OF PAGE|USE TAB TO|SHOW TICKETS|"
            r"ONE SET|NO COVER|TICKETS AND INFO|"
            r"\d{1,2}:\d{2} SHOW|NEXT WEEK|LIVE MUSIC).*$",
            re.IGNORECASE,
        )

        current_date = None
        event_buffer = []

        def flush_buffer(buf, ev_date):
            nonlocal ticket_idx
            if not buf or not ev_date:
                return
            if ev_date < TODAY:
                return
            artist_raw = buf[0]
            # Skip if artist looks like a nav/ui element
            if len(artist_raw) < 3 or re.match(r"^\d", artist_raw):
                return

            artist = artist_raw.title()
            notes_parts = buf[1:3] if len(buf) > 1 else []
            notes = " — ".join(p for p in notes_parts if p and len(p) > 3)

            # Determine price from buffer text
            price = "TBA"
            combined = " ".join(buf).upper()
            if "NO COVER" in combined:
                price = "No Cover"
            elif re.search(r"\$\d+", combined):
                m = re.search(r"\$(\d+)", combined)
                if m:
                    price = f"${m.group(1)}"

            # Determine show times
            times = []
            if re.search(r"7:00|7:30", combined):
                times.append("19:00" if "7:00" in combined else "19:30")
            if re.search(r"9:30", combined):
                times.append("21:30")
            if not times:
                times = ["20:00"]

            ticket_url = ticket_links[ticket_idx] if ticket_idx < len(ticket_links) else None
            if ticket_url:
                ticket_idx += 1

            for i, t in enumerate(times):
                label = "" if i == 0 else "Late Set"
                shows.append({
                    "artist": artist if i == 0 else f"{artist} (Late Show)",
                    "date": ev_date,
                    "time": t,
                    "price": price,
                    "ticket_url": ticket_url if i == 0 else None,
                    "notes": notes[:80] if notes else label or None,
                    "venue": "The Jazz Estate",
                    "venue_id": "estate",
                    "address": "2423 N Murray Ave",
                })

        for line in lines:
            dm = date_re.match(line)
            if dm:
                flush_buffer(event_buffer, current_date)
                event_buffer = []
                current_date = _parse_date(dm.group(1), dm.group(2))
                continue

            if current_date and not skip_patterns.match(line):
                event_buffer.append(line)
            elif date_re.match(line) is None and skip_patterns.match(line):
                # flush on boundary-ish lines
                if len(event_buffer) > 0 and skip_patterns.match(line):
                    flush_buffer(event_buffer, current_date)
                    event_buffer = []

        flush_buffer(event_buffer, current_date)
        log.info(f"Estate: {len(shows)} shows scraped")

    except Exception as e:
        log.error(f"Estate scrape failed: {e}")

    return shows


# ─────────────────────────────────────────────
# 2. CENTRO CAFE RIVER WEST  (centrocaferiverwest.com/events-calendar/)
# ─────────────────────────────────────────────
def scrape_centro() -> list[dict]:
    """
    WordPress site using 'The Events Calendar' plugin.
    Events render as list items with month/day, title, time, optional price.
    """
    shows = []
    try:
        resp = requests.get(
            "https://centrocaferiverwest.com/events-calendar/",
            headers=HEADERS,
            timeout=20,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # The Events Calendar renders in various ways — try multiple selectors
        # Photo list view (what the site uses) — events are <li> items
        # with date in abbr/span elements and title in h2
        event_items = (
            soup.select("li.tribe-events-calendar-list__event-row") or
            soup.select("article[class*='tribe_events']") or
            soup.select("li[class*='tribe-event']") or
            soup.select(".tribe-events-loop .vevent")
        )

        if not event_items:
            # Fallback: parse the raw text which has reliable structure
            return _scrape_centro_text(soup)

        for item in event_items:
            try:
                # Title
                title_el = (
                    item.select_one(".tribe-event-url") or
                    item.select_one("h2 a") or
                    item.select_one("h3 a") or
                    item.select_one("[class*='event-title'] a")
                )
                if not title_el:
                    continue
                artist = title_el.get_text(strip=True)

                # Date
                date_el = item.select_one("abbr.tribe-events-abbr, time[datetime], [class*='date']")
                event_date = None
                if date_el:
                    dt_attr = date_el.get("datetime") or date_el.get("title", "")
                    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", dt_attr)
                    if m:
                        event_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

                if not event_date:
                    # Try month/day divs
                    month_el = item.select_one("[class*='month']")
                    day_el = item.select_one("[class*='day']")
                    if month_el and day_el:
                        event_date = _parse_date(month_el.get_text(strip=True), day_el.get_text(strip=True))

                if not event_date or event_date < TODAY:
                    continue

                # Time
                time_el = item.select_one("[class*='datetime'], [class*='schedule'], .dtstart")
                time_str = "20:00"
                if time_el:
                    raw = time_el.get_text(" ", strip=True)
                    t_match = re.search(r"(\d{1,2}:\d{2}\s*[AP]M)", raw, re.I)
                    if t_match:
                        time_str = _parse_time_12h(t_match.group(1))

                # Price
                price_el = item.select_one("[class*='cost'], [class*='price']")
                price = price_el.get_text(strip=True) if price_el else "TBA"
                if not price or price.lower() in ("free admission", "free"):
                    price = "Free"

                # Ticket URL
                ticket_el = item.select_one("a[href*='ticket'], a[href*='eventbrite'], a[href*='tix']")
                ticket_url = ticket_el["href"] if ticket_el else None

                # Notes (description/subtitle)
                desc_el = item.select_one("[class*='description'], [class*='excerpt']")
                notes = desc_el.get_text(strip=True)[:80] if desc_el else None

                shows.append({
                    "artist": artist,
                    "date": event_date,
                    "time": time_str,
                    "price": price,
                    "ticket_url": ticket_url,
                    "notes": notes,
                    "venue": "Bar Centro Riverwest",
                    "venue_id": "centro",
                    "address": "804 E Center St",
                })
            except Exception as e:
                log.debug(f"Centro item parse error: {e}")
                continue

        if not shows:
            shows = _scrape_centro_text(soup)

        log.info(f"Centro: {len(shows)} shows scraped")

    except Exception as e:
        log.error(f"Centro scrape failed: {e}")

    return shows


def _scrape_centro_text(soup: BeautifulSoup) -> list[dict]:
    """Fallback text parser for Centro Cafe events page."""
    shows = []
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Pattern: "Mar\n5\nEVENT TITLE\n8:00 pm\n-\n10:00 pm\n$10"
    # Month abbreviation line followed by day number
    month_re = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$", re.I)
    day_re = re.compile(r"^\d{1,2}$")
    time_re = re.compile(r"\d{1,2}:\d{2}\s*[ap]m", re.I)
    price_re = re.compile(r"^\$\d+|^free|^no cover", re.I)

    i = 0
    while i < len(lines):
        if month_re.match(lines[i]) and i + 1 < len(lines) and day_re.match(lines[i + 1]):
            month_str = lines[i]
            day_str = lines[i + 1]
            event_date = _parse_date(month_str, day_str)

            if event_date and event_date >= TODAY:
                # Next non-empty line is usually the title
                j = i + 2
                artist = ""
                while j < len(lines) and not artist:
                    candidate = lines[j]
                    if (len(candidate) > 3 and not time_re.search(candidate)
                            and not candidate.strip() == "-"):
                        artist = candidate
                    j += 1

                # Look for times and price in next ~5 lines
                time_str = "20:00"
                price = "TBA"
                for k in range(j, min(j + 6, len(lines))):
                    tl = lines[k]
                    if time_re.search(tl):
                        m = time_re.search(tl)
                        time_str = _parse_time_12h(m.group(0))
                    if price_re.match(tl):
                        price = tl.strip()
                        if price.lower() in ("free", "no cover"):
                            price = price.title()

                if artist:
                    shows.append({
                        "artist": artist,
                        "date": event_date,
                        "time": time_str,
                        "price": price,
                        "ticket_url": None,
                        "notes": None,
                        "venue": "Bar Centro Riverwest",
                        "venue_id": "centro",
                        "address": "804 E Center St",
                    })
            i += 2
        else:
            i += 1

    return shows


# ─────────────────────────────────────────────
# 3. TRANSFER PIZZERIA CAFÉ  (transfermke.com/events)
# ─────────────────────────────────────────────
def scrape_transfer() -> list[dict]:
    """
    Squarespace site. Events have clear date/time/description blocks
    with calendar export links we can use for verification.
    """
    shows = []
    try:
        resp = requests.get(
            "https://www.transfermke.com/events", headers=HEADERS, timeout=20
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Squarespace event list items — each event is an <article> or
        # a list item with a date and title
        event_articles = (
            soup.select("article.eventlist-event") or
            soup.select(".eventlist-event") or
            soup.select("article[class*='event']")
        )

        if not event_articles:
            return _scrape_transfer_text(soup)

        for article in event_articles:
            try:
                # Title
                title_el = (
                    article.select_one(".eventlist-title a") or
                    article.select_one("h1 a, h2 a, h3 a")
                )
                if not title_el:
                    continue
                artist = title_el.get_text(strip=True)

                # Date — Squarespace uses time[datetime] or .eventlist-meta-date
                time_el = article.select_one("time[datetime]")
                event_date = None
                start_time = "18:30"
                if time_el:
                    dt_str = time_el.get("datetime", "")
                    m = re.search(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})", dt_str)
                    if m:
                        event_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                        start_time = f"{m.group(4)}:{m.group(5)}"

                if not event_date:
                    # Try text date like "Thursday, March 5, 2026"
                    date_el = article.select_one(".eventlist-meta-date, [class*='date']")
                    if date_el:
                        raw = date_el.get_text(" ", strip=True)
                        m = re.search(
                            r"(\w+day),?\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
                            raw, re.I
                        )
                        if m:
                            event_date = _parse_date(m.group(2), m.group(3))

                if not event_date or event_date < TODAY:
                    continue

                # Time from meta
                time_blocks = article.select("time[datetime]")
                if len(time_blocks) >= 1:
                    dt_str = time_blocks[0].get("datetime", "")
                    m = re.search(r"T(\d{2}):(\d{2})", dt_str)
                    if m:
                        start_time = f"{m.group(1)}:{m.group(2)}"

                # Description/notes
                desc_el = article.select_one(".eventlist-excerpt, .eventlist-description p")
                notes = None
                if desc_el:
                    raw_notes = desc_el.get_text(" ", strip=True)[:100]
                    notes = raw_notes if len(raw_notes) > 5 else None

                # Ticket / calendar URL
                cal_link = article.select_one("a[href*='google.com/calendar']")
                ticket_url = None
                if cal_link:
                    # Extract event URL from article title link
                    title_link = article.select_one(".eventlist-title a")
                    if title_link and title_link.get("href"):
                        href = title_link["href"]
                        if not href.startswith("http"):
                            href = "https://www.transfermke.com" + href
                        ticket_url = href

                # Price from Transfer is almost always "No Cover" (Martini Jazz Lounge)
                price_el = article.select_one("[class*='price'], [class*='cost']")
                price = "No Cover"
                if price_el:
                    pt = price_el.get_text(strip=True)
                    if pt:
                        price = pt

                shows.append({
                    "artist": artist,
                    "date": event_date,
                    "time": start_time,
                    "price": price,
                    "ticket_url": ticket_url,
                    "notes": notes,
                    "venue": "Transfer Pizzeria Café",
                    "venue_id": "transfer",
                    "address": "101 W Mitchell St",
                })
            except Exception as e:
                log.debug(f"Transfer item parse error: {e}")
                continue

        if not shows:
            shows = _scrape_transfer_text(soup)

        log.info(f"Transfer: {len(shows)} shows scraped")

    except Exception as e:
        log.error(f"Transfer scrape failed: {e}")

    return shows


def _scrape_transfer_text(soup: BeautifulSoup) -> list[dict]:
    """Fallback text parser for Transfer Pizzeria events."""
    shows = []
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Pattern: "Mar\n5\n# [Event Title](url)" or "Thursday, March 5, 2026"
    full_date_re = re.compile(
        r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
        r"(\d{1,2}),?\s+\d{4}",
        re.I
    )
    short_date_re = re.compile(
        r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})$", re.I
    )
    time_re = re.compile(r"(\d{1,2}:\d{2}\s*[AP]M)", re.I)
    title_re = re.compile(r"^#\s*\[(.+?)\]|^Martini Jazz Lounge[:\s]*(.+)", re.I)

    i = 0
    while i < len(lines):
        line = lines[i]
        event_date = None
        artist = None

        # Short date: "Mar\n5"
        sm = short_date_re.match(line)
        if sm and i + 1 < len(lines):
            next_line = lines[i + 1]
            if re.match(r"^\d{1,2}$", next_line):
                event_date = _parse_date(sm.group(1), next_line)
                # Title should be 2 lines ahead
                if i + 2 < len(lines):
                    raw_title = lines[i + 2]
                    tm = title_re.match(raw_title)
                    if tm:
                        artist = (tm.group(1) or tm.group(2) or "").strip()
                    elif len(raw_title) > 3 and not re.match(r"^\d", raw_title):
                        artist = raw_title
                i += 2
            else:
                i += 1
                continue
        else:
            # Full date: "Thursday, March 5, 2026"
            fm = full_date_re.search(line)
            if fm:
                event_date = _parse_date(fm.group(1), fm.group(2))
                # Look back for title
                for back in range(max(0, i - 3), i):
                    candidate = lines[back]
                    tm = title_re.match(candidate)
                    if tm:
                        artist = (tm.group(1) or tm.group(2) or "").strip()
                        break
                    elif (len(candidate) > 5 and not full_date_re.search(candidate)
                          and not time_re.search(candidate)):
                        artist = candidate
                        break

        if event_date and artist and event_date >= TODAY:
            # Find time in surrounding lines
            start_time = "18:30"
            for k in range(i + 1, min(i + 5, len(lines))):
                tm = time_re.search(lines[k])
                if tm:
                    start_time = _parse_time_12h(tm.group(1))
                    break

            # Notes: look for description after time lines
            notes = None
            for k in range(i + 1, min(i + 8, len(lines))):
                candidate = lines[k]
                if (len(candidate) > 20 and not time_re.search(candidate)
                        and not full_date_re.search(candidate)
                        and not short_date_re.match(candidate)):
                    notes = candidate[:80]
                    break

            shows.append({
                "artist": artist,
                "date": event_date,
                "time": start_time,
                "price": "No Cover",
                "ticket_url": None,
                "notes": notes,
                "venue": "Transfer Pizzeria Café",
                "venue_id": "transfer",
                "address": "101 W Mitchell St",
            })

        i += 1

    return shows


# ─────────────────────────────────────────────
# 4. THE PFISTER HOTEL  (thepfisterhotel.com)
# ─────────────────────────────────────────────
def scrape_pfister() -> list[dict]:
    """
    Pfister blocks some crawlers. Try with full browser headers + referrer.
    Falls back to a graceful empty list if blocked.
    """
    shows = []
    pfister_headers = {
        **HEADERS,
        "Referer": "https://www.google.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    }
    try:
        resp = requests.get(
            "https://www.thepfisterhotel.com/happenings?category=Live%20Music",
            headers=pfister_headers,
            timeout=20,
            allow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator="\n")

        # Pfister typically lists events with date + title + time
        # Try to find structured event data
        event_els = (
            soup.select("[class*='event-item'], [class*='happenings-item']") or
            soup.select("article") or
            soup.select(".event")
        )

        date_re = re.compile(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})",
            re.I
        )
        time_re = re.compile(r"(\d{1,2}:\d{2}\s*[AP]M)", re.I)

        for el in event_els:
            try:
                txt = el.get_text("\n", strip=True)
                dm = date_re.search(txt)
                if not dm:
                    continue
                event_date = _parse_date(dm.group(1), dm.group(2))
                if not event_date or event_date < TODAY:
                    continue

                title_el = el.select_one("h1,h2,h3,h4,[class*='title']")
                artist = title_el.get_text(strip=True) if title_el else "Live Music"

                tm = time_re.search(txt)
                time_str = _parse_time_12h(tm.group(1)) if tm else "19:00"

                shows.append({
                    "artist": artist,
                    "date": event_date,
                    "time": time_str,
                    "price": "TBA",
                    "ticket_url": "https://www.thepfisterhotel.com/happenings?category=Live%20Music",
                    "notes": "Pfister Lobby Lounge",
                    "venue": "The Pfister Hotel",
                    "venue_id": "pfister",
                    "address": "424 E Wisconsin Ave",
                })
            except Exception:
                continue

        if not shows:
            # Broad text fallback
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            for i, line in enumerate(lines):
                dm = date_re.search(line)
                if dm:
                    event_date = _parse_date(dm.group(1), dm.group(2))
                    if event_date and event_date >= TODAY:
                        # Look around for an artist name
                        for offset in [-2, -1, 1, 2]:
                            idx = i + offset
                            if 0 <= idx < len(lines):
                                candidate = lines[idx]
                                if (len(candidate) > 4
                                        and not date_re.search(candidate)
                                        and not time_re.search(candidate)):
                                    tm = time_re.search(lines[i]) or time_re.search(
                                        lines[i + 1] if i + 1 < len(lines) else ""
                                    )
                                    shows.append({
                                        "artist": candidate,
                                        "date": event_date,
                                        "time": _parse_time_12h(tm.group(1)) if tm else "19:00",
                                        "price": "TBA",
                                        "ticket_url": "https://www.thepfisterhotel.com/happenings?category=Live%20Music",
                                        "notes": "Pfister Lobby Lounge",
                                        "venue": "The Pfister Hotel",
                                        "venue_id": "pfister",
                                        "address": "424 E Wisconsin Ave",
                                    })
                                    break

        log.info(f"Pfister: {len(shows)} shows scraped")

    except Exception as e:
        log.error(f"Pfister scrape failed (site may block crawlers): {e}")

    return shows


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────
def scrape_all_venues(venue_ids: list[str] | None = None) -> tuple[list[dict], dict[str, str]]:
    """
    Scrape all (or specified) venues. Returns:
      - shows: list of event dicts
      - statuses: {venue_id: "ok N shows" | "error msg"}
    """
    scrapers = {
        "estate": scrape_estate,
        "centro": scrape_centro,
        "transfer": scrape_transfer,
        "pfister": scrape_pfister,
    }

    if venue_ids:
        scrapers = {k: v for k, v in scrapers.items() if k in venue_ids}

    all_shows = []
    statuses = {}

    for vid, fn in scrapers.items():
        try:
            results = fn()
            all_shows.extend(results)
            statuses[vid] = f"✓  {len(results)} shows"
        except Exception as e:
            statuses[vid] = f"✗  {e}"
            log.error(f"{vid} top-level error: {e}")

    # Deduplicate by (artist, date, time, venue_id)
    seen = set()
    deduped = []
    for s in all_shows:
        key = (s["artist"].lower(), str(s["date"]), s["time"], s["venue_id"])
        if key not in seen:
            seen.add(key)
            deduped.append(s)

    # Sort chronologically
    deduped.sort(key=lambda x: (str(x["date"]), x["time"]))
    return deduped, statuses
