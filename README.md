# MKE LIVE JAZZ 🎵
### Milwaukee live music schedule aggregator

Scrapes 4 Milwaukee venues in real-time and displays an interactive show schedule.

**Live venues:**
- [The Jazz Estate](https://www.estatemke.com/events) — 2423 N Murray Ave
- [Bar Centro Riverwest](https://centrocaferiverwest.com/events-calendar/) — 804 E Center St
- [Transfer Pizzeria Café](https://www.transfermke.com/events) — 101 W Mitchell St
- [The Pfister Hotel](https://www.thepfisterhotel.com/happenings?category=Live%20Music) — 424 E Wisconsin Ave

---

## 🚀 Deploy to Streamlit Cloud (Free)

### Step 1 — Fork this repo to your GitHub
1. Go to [github.com](https://github.com) and sign in (create a free account if needed)
2. Click **"+"** → **New repository**
3. Name it `mke-live-jazz`
4. Set to **Public**, click **Create repository**
5. Upload these 3 files:
   - `app.py`
   - `scraper.py`
   - `requirements.txt`

   (Drag & drop them into the GitHub file upload UI, or use the GitHub desktop app)

### Step 2 — Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **"New app"**
4. Fill in:
   - **Repository:** `your-username/mke-live-jazz`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Click **Deploy!**

Streamlit Cloud will install dependencies and launch your app in ~2 minutes.  
Your app gets a public URL like `https://your-username-mke-live-jazz-app-xxxxx.streamlit.app`

---

## 🔄 Refreshing Data
- Click the **↺ REFRESH** button in the app to re-scrape all venues on demand
- Scraping takes ~15–30 seconds (one HTTP request per venue)
- No API keys or accounts needed — pure HTTP scraping

## 🔧 Running Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📁 Files
```
mke-live-jazz/
├── app.py          — Streamlit frontend
├── scraper.py      — Venue scrapers (BeautifulSoup + requests)
├── requirements.txt
└── README.md
```

## ➕ Adding Venues
In `scraper.py`, add a new `scrape_myvenue()` function following the same pattern.
Then in `app.py`, add the venue to the `VENUES` dict with a label, color, and address.
