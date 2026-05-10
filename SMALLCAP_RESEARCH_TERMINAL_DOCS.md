# SmallCap Research Terminal — Documentation

> **Version:** 1.0.0  
> **Stack:** Python · FastAPI · yfinance · SEC EDGAR API · Chart.js · Vanilla JS  
> **Mode:** Local application — no subscription, no API keys required  
> **Inspired by:** Flash Research · MOMO Screener · Finviz · BamSEC · Yahoo Finance

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Installation & Setup](#3-installation--setup)
4. [Backend API Reference](#4-backend-api-reference)
5. [Frontend Modules](#5-frontend-modules)
6. [Features by Platform Inspiration](#6-features-by-platform-inspiration)
7. [Data Sources](#7-data-sources)
8. [UI / UX Design System](#8-ui--ux-design-system)
9. [Current Limitations & Roadmap](#9-current-limitations--roadmap)

---

## 1. Overview

**SmallCap Research Terminal** is a locally-run stock research application focused on U.S. small-cap and micro-cap equities. It consolidates functionality from five premium/free platforms into a single dark-themed terminal interface that runs entirely on your machine without any subscription fees or external API keys.

The application provides a full analysis stack for a selected ticker: real-time price data, float structure, SEC filing history with dilution/warrant detection, institutional ownership breakdown, options chain, financial statements, and aggregated news — all in a single-page dashboard that updates on demand.

### Core Use Cases

- **Day traders / momentum traders** — identify gap-up/gap-down small caps with unusual relative volume
- **Swing traders** — assess float structure, short interest, and institutional activity
- **Fundamental researchers** — review SEC filings for dilution risk, warrant exposure, and ownership concentration
- **Risk managers** — detect S-1, S-3, and 424B4 filings that signal potential share dilution

---

## 2. Architecture

```
stockapp/
├── backend/
│   └── main.py            # FastAPI application — all API endpoints
└── frontend/
    ├── index.html          # Single-page application (SPA)
    └── static/             # Static assets (CSS, JS if separated)
```

### Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend framework | FastAPI (Python) | REST API, async routing, CORS |
| Market data | yfinance | Price history, fundamentals, options, holders |
| SEC data | SEC EDGAR REST API | Filings, CIK lookup, submission history |
| Frontend | Vanilla JS + HTML/CSS | SPA dashboard, no build step required |
| Charting | Chart.js 4.4 | Price/volume chart with multi-period selector |
| Icons | Font Awesome 6.5 | UI iconography |
| Fonts | JetBrains Mono + Space Grotesk | Terminal aesthetic |

### Data Flow

```
User enters ticker
       │
       ▼
Frontend (index.html)
       │  HTTP GET /api/ticker/{symbol}
       ▼
FastAPI Backend (main.py)
       │
       ├── yfinance.Ticker(symbol).info          → Price, fundamentals, float
       ├── yfinance.Ticker(symbol).history()     → OHLCV candles
       ├── yfinance.Ticker(symbol).news          → News feed
       ├── yfinance.Ticker(symbol).options       → Options chain
       ├── yfinance.Ticker(symbol).institutional_holders → 13F data
       ├── yfinance.Ticker(symbol).insider_transactions  → Form 4 data
       └── SEC EDGAR API (data.sec.gov)          → Filings, CIK, warrant detection
              │
              ▼
       JSON responses → Frontend renders each module
```

---

## 3. Installation & Setup

### Requirements

```
Python 3.9+
pip
```

### Install dependencies

```bash
pip install fastapi uvicorn yfinance requests beautifulsoup4 pandas aiohttp httpx
```

### Run the application

```bash
cd stockapp/backend
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Access the terminal

Open your browser at:

```
http://localhost:8000
```

The frontend is served directly by the FastAPI backend from `frontend/index.html`. No separate web server is needed.

---

## 4. Backend API Reference

All endpoints return JSON. No authentication required for local use.

---

### `GET /`

Serves the frontend `index.html` application.

---

### `GET /api/ticker/{symbol}`

**Ticker Overview** — the primary endpoint called when a ticker is selected.

**Parameters:**
- `symbol` (path) — stock ticker symbol, e.g. `SOUN`, `MARA`

**Returns:**

| Field | Type | Description |
|---|---|---|
| `symbol` | string | Normalized ticker symbol |
| `company_name` | string | Full company name |
| `sector` | string | GICS sector classification |
| `industry` | string | Industry sub-classification |
| `exchange` | string | Listing exchange (NYSE, NASDAQ, etc.) |
| `cap_class` | string | `Micro Cap` / `Small Cap` / `Mid Cap` / `Large Cap` |
| `market_cap` | int | Market capitalization in USD |
| `current_price` | float | Last traded price (4 decimal places) |
| `prev_close` | float | Previous session closing price |
| `price_change` | float | Absolute price change |
| `price_change_pct` | float | Percentage price change |
| `gap_pct` | float | Gap % = (today open − prev close) / prev close × 100 |
| `volume` | int | Current session volume |
| `avg_volume` | int | 30-day average volume |
| `relative_volume` | float | Current volume / average volume (RVOL) |
| `float_shares` | int | Freely tradable shares (float) |
| `shares_outstanding` | int | Total shares outstanding |
| `short_ratio` | float | Days to cover (short ratio) |
| `short_percent_float` | float | Short interest as % of float |
| `beta` | float | 5-year monthly beta vs S&P 500 |
| `pe_ratio` | float | Trailing twelve-month P/E ratio |
| `eps` | float | Trailing twelve-month EPS |
| `52w_high` | float | 52-week high price |
| `52w_low` | float | 52-week low price |
| `description` | string | Business summary (first 500 chars) |
| `website` | string | Company website URL |
| `country` | string | Country of incorporation |
| `employees` | int | Full-time employees |

**Cap classification thresholds:**
- Micro Cap: market cap < $300M
- Small Cap: $300M – $2B
- Mid Cap: $2B – $10B
- Large Cap: > $10B

---

### `GET /api/ticker/{symbol}/history`

**Price History** — OHLCV data for charting.

**Query Parameters:**
- `period` — `1mo`, `3mo` (default), `6mo`, `1y`

**Returns:** Array of candles

```json
{
  "candles": [
    {
      "date": "2025-01-15",
      "open": 3.4200,
      "high": 3.7100,
      "low": 3.3800,
      "close": 3.6500,
      "volume": 14200000
    }
  ]
}
```

---

### `GET /api/ticker/{symbol}/financials`

**Financial Statements** — income statement, balance sheet, and cash flow (annual and quarterly).

**Returns:**

```json
{
  "income": [
    {
      "period": "2024-12-31",
      "Total Revenue": 45200000,
      "Gross Profit": 12000000,
      "Net Income": -3400000,
      "EBITDA": 1200000,
      "Operating Income": -2100000
    }
  ],
  "balance": [
    {
      "period": "2024-12-31",
      "Total Assets": 98000000,
      "Cash And Cash Equivalents": 12000000,
      "Long Term Debt": 8500000
    }
  ],
  "cashflow": [...],
  "key_stats": {
    "revenue_growth": 0.18,
    "profit_margins": -0.07,
    "return_on_equity": -0.23,
    "debt_to_equity": 0.43,
    "current_ratio": 2.1,
    "enterprise_value": 210000000
  }
}
```

**Key statistics included:**

| Stat | Description |
|---|---|
| `revenue_growth` | YoY revenue growth rate |
| `earnings_growth` | YoY earnings growth rate |
| `profit_margins` | Net profit margin |
| `operating_margins` | Operating profit margin |
| `return_on_equity` | ROE |
| `return_on_assets` | ROA |
| `debt_to_equity` | Leverage ratio |
| `current_ratio` | Liquidity ratio |
| `book_value` | Book value per share |
| `price_to_book` | P/B ratio |
| `enterprise_value` | EV in USD |
| `ebitda` | EBITDA in USD |

---

### `GET /api/ticker/{symbol}/sec`

**SEC EDGAR Filings** — filing history, dilution risk assessment, and warrant detection.

**Process:**
1. Looks up the company's CIK from `sec.gov/files/company_tickers.json`
2. Fetches the full submission history from `data.sec.gov/submissions/CIK{cik}.json`
3. Filters for key form types: `10-K`, `10-Q`, `8-K`, `S-1`, `S-1/A`, `424B4`, `S-3`, `S-3/A`, `DEF 14A`, `SC 13G`, `SC 13D`, `4`, `3`, `NT 10-K`
4. Identifies filings that typically accompany dilution events or warrants

**Returns:**

| Field | Type | Description |
|---|---|---|
| `cik` | string | SEC CIK number (zero-padded to 10 digits) |
| `company_name` | string | Company name as registered with SEC |
| `filings` | array | Up to 30 most recent key filings |
| `potential_warrant_filings` | array | Filings most likely to contain warrant terms |
| `has_dilution_risk_filings` | bool | True if any S-1, S-1/A, 424B4, S-3, or S-3/A is found |
| `offering_count` | int | Number of primary offerings (S-1 + 424B4) |
| `s3_count` | int | Number of shelf registrations (S-3) |

Each filing entry includes:

```json
{
  "form": "S-1",
  "date": "2023-09-14",
  "document": "s-1.htm",
  "url": "https://www.sec.gov/Archives/edgar/data/.../s-1.htm",
  "accession": "0001234567-23-000123"
}
```

**Dilution/Warrant Risk Logic:**

| Form Type | Risk Level | Meaning |
|---|---|---|
| `S-1` / `S-1/A` | 🔴 High | IPO or secondary offering — often includes warrants |
| `424B4` | 🔴 High | Final prospectus for a public offering |
| `S-3` / `S-3/A` | 🟡 Medium | Shelf registration — allows future share issuance |
| `8-K` | 🟡 Medium | Material event — may include PIPE deals with warrants |
| `SC 13D` / `SC 13G` | ℹ️ Info | Large shareholder disclosure |

---

### `GET /api/ticker/{symbol}/institutional`

**Ownership & Insider Data** — institutional holders (13F), mutual fund holders, insider transactions (Form 4).

**Returns:**

| Field | Type | Description |
|---|---|---|
| `total_institutional_pct` | float | % of shares held by institutions |
| `insider_pct` | float | % held by insiders |
| `float_shares` | int | Float used as denominator |
| `institutional_holders` | array | Up to 20 top institutional holders |
| `mutualfund_holders` | array | Up to 10 mutual fund holders |
| `insider_transactions` | array | Up to 15 most recent Form 4 transactions |

**Institutional holder entry:**
```json
{
  "holder": "BlackRock Inc.",
  "shares": 4200000,
  "date_reported": "2024-09-30",
  "pct_held": 0.0312,
  "value": 18900000
}
```

**Insider transaction entry:**
```json
{
  "insider": "John Smith",
  "relation": "Chief Executive Officer",
  "transaction": "Buy",
  "date": "2024-11-01",
  "shares": 50000,
  "value": 225000,
  "ownership": 0.041
}
```

---

### `GET /api/ticker/{symbol}/news`

**News Feed** — up to 15 most recent news articles related to the ticker.

**Returns:**
```json
{
  "news": [
    {
      "title": "Company announces Q3 earnings beat",
      "summary": "First 200 characters of article summary...",
      "url": "https://...",
      "published": "2025-04-28",
      "source": "Reuters",
      "type": "NEWS"
    }
  ]
}
```

Source: yfinance news feed (aggregated from Yahoo Finance).

---

### `GET /api/ticker/{symbol}/options`

**Options Chain** — calls and puts for the nearest expiration date.

**Returns:**

| Field | Description |
|---|---|
| `expirations` | Up to 8 available expiration dates |
| `nearest_expiration` | ISO date of the nearest expiration |
| `calls` | Up to 20 call contracts |
| `puts` | Up to 20 put contracts |

**Per contract:**
```json
{
  "strike": 5.0,
  "lastPrice": 0.45,
  "bid": 0.42,
  "ask": 0.48,
  "volume": 3200,
  "openInterest": 8400,
  "impliedVolatility": 142.5,
  "inTheMoney": true
}
```

---

### `GET /api/screener/smallcaps`

**Small Cap Scanner** — batch data for the sidebar watchlist.

Fetches a curated list of active small-cap tickers and returns sorted results by absolute gap percentage.

**Returns:**
```json
{
  "tickers": [
    {
      "symbol": "SOUN",
      "name": "SoundHound AI",
      "price": 4.82,
      "market_cap": 1820000000,
      "sector": "Technology",
      "float_shares": 342000000,
      "relative_volume": 2.34,
      "gap_pct": 8.12
    }
  ]
}
```

Tickers are sorted by `|gap_pct|` descending — largest movers appear first.

---

## 5. Frontend Modules

The entire frontend is a single HTML file (`index.html`) with embedded CSS and JavaScript. No build step, no framework, no bundler.

---

### 5.1 Header & Search Bar

- **Ticker input field** — type any US ticker symbol and press Enter or click "Analizar"
- **Filter pills** — `Todos` · `Gap Up` · `Gap Down` · `RVOL+`
  - Gap Up: `gap_pct > 0`
  - Gap Down: `gap_pct < 0`
  - RVOL+: `relative_volume > 1.5`
- Filters update the sidebar in real time without a network call

---

### 5.2 Sidebar — Small Cap Scanner

Displays the watchlist loaded from `/api/screener/smallcaps`.

**Per ticker row shows:**
- Ticker symbol (bold monospace)
- Short company name
- RVOL ratio and float size
- Current price
- Gap % with directional arrow (▲ green / ▼ red)

Clicking any ticker loads the full analysis in the main panel. The active ticker is highlighted with a blue left border.

The refresh button (↺) re-fetches the scanner data on demand.

---

### 5.3 Ticker Header

Displayed immediately after a ticker is loaded.

**Left block:**
- Symbol (large, monospace)
- Full company name
- **Badges:** Sector · Cap Class · Exchange · Country · Industry

**Right block:**
- Current price (4 decimal precision)
- Absolute and percentage change from previous close
- Gap pill (shown only if gap ≠ 0) — green for gap up, red for gap down

---

### 5.4 Stats Strip

A horizontally scrollable bar of 11 key metrics displayed in compact boxes:

| Metric | Source | Notes |
|---|---|---|
| Volume | yfinance | Current session |
| Avg Volume | yfinance | 30-day average |
| RVOL | Calculated | Volume / Avg Volume; highlighted yellow >1.2x, red >2x |
| Float | yfinance | `floatShares` field |
| Market Cap | yfinance | USD |
| Short % Float | yfinance | Red if > 20% |
| 52W High | yfinance | |
| 52W Low | yfinance | |
| Beta | yfinance | |
| P/E (TTM) | yfinance | |
| EPS (TTM) | yfinance | |

---

### 5.5 Tab System — 6 Analysis Panels

Navigation tabs load each panel on demand. Data for all panels is fetched in parallel as soon as a ticker is selected.

---

#### Tab 1 — Overview

Three sub-sections:

**Price Chart**
- Line chart overlay with volume bars (Chart.js)
- Period selector: 1M / 3M / 6M / 1Y
- Blue line for close price, green/red bars for volume
- Tooltip shows price and volume on hover

**Float & Share Structure**
- Visual segmented bar: Float (blue) vs Restricted shares (dark)
- Shows float as % of total shares outstanding
- Risk classification:
  - Float < 5M shares → `⚠ Float muy bajo — alta volatilidad`
  - Float < 20M shares → `Float bajo — momentum posible`
  - Float ≥ 20M shares → `Float moderado/alto`
- Short ratio and total shares outstanding shown below

**Business Description**
- First 500 characters of `longBusinessSummary` from yfinance
- Website link (external, opens in new tab)

**Metrics Grid**
- 16 key metrics in a responsive grid:
  - Price, Market Cap, Float, Shares Outstanding
  - Volume, Avg Volume, RVOL, Gap %
  - Short % Float, Short Ratio, Beta
  - P/E, EPS, 52W High, 52W Low, Employees

---

#### Tab 2 — Financials

**Key Statistics Grid (12 metrics):**
Revenue Growth, Earnings Growth, Profit Margin, Operating Margin, ROE, ROA, Debt/Equity, Current Ratio, Book Value, P/B, Enterprise Value, EBITDA

**Income Statement table** (up to 4 periods):
Total Revenue · Gross Profit · Operating Income · Net Income

**Balance Sheet table** (up to 4 periods):
Total Assets · Total Liabilities · Cash & Equivalents · Long Term Debt

**Cash Flow table** (up to 4 periods):
Operating Cash Flow · Free Cash Flow · CapEx · Issuance of Capital Stock

All monetary values are auto-formatted: `$1.23B`, `$456.7M`, `$89K`.

---

#### Tab 3 — SEC / Warrants

**Dilution Risk Banner**
- 🔴 **Red alert** if any S-1, S-1/A, 424B4, S-3, or S-3/A is found in filing history — shows offering count and shelf registration count
- 🟢 **Green confirmation** if no offering filings are detected

**Recent SEC Filings list** (up to 25):
- Color-coded form badges: `10-K` blue · `10-Q` cyan · `8-K` yellow · `S-1`/`424B4` red · `S-3` light red · `Form 4` purple · `DEF 14A` green
- Filing date
- Direct link to the document on SEC EDGAR

**Potential Warrant/Dilution Filings** (up to 8):
- Isolated list of filings most likely to contain warrant terms or share issuance provisions
- Includes explanatory guide on how to interpret each form type

**SEC Summary metrics:**
- CIK number · Total filings in history · Offering count · S-3 count

**Links:** Direct link to the company's full EDGAR page.

---

#### Tab 4 — Ownership

**Ownership Distribution bars:**
- Institutional % (blue bar)
- Insider % (purple bar)
- Public/Retail % (gray bar, calculated as remainder)
- Contextual interpretation note: high institutional ownership vs. low

**Top Mutual Fund Holders** (up to 6):
- Fund name and shares held

**Institutional Holders table** (up to 20, sourced from 13F filings):
- Institution name · Shares · % of float · Value in USD · Date reported

**Insider Transactions table** (up to 15, sourced from Form 4):
- Insider name · Relationship/title · Transaction type (Buy/Sell, color-coded green/red) · Shares · Value · Date

---

#### Tab 5 — Opciones (Options)

- Shows the nearest expiration date and up to 8 available expiration dates
- **Calls table** and **Puts table** side by side (up to 20 contracts each):
  - Strike · Last Price · Bid/Ask · Volume · Open Interest · Implied Volatility % · ITM/OTM label
- ITM (In The Money) rows are highlighted with a subtle green background

---

#### Tab 6 — Noticias (News)

- Up to 15 most recent news items for the selected ticker
- Per item: headline (linked), source name, publication date, content type tag, summary preview (200 chars)
- Sources aggregated by Yahoo Finance (Reuters, Bloomberg, Benzinga, etc.)

---

## 6. Features by Platform Inspiration

### Inspired by Flash Research

| Feature | Implementation |
|---|---|
| Gap % calculation | `(today_open − prev_close) / prev_close × 100` in `/api/ticker/{symbol}` |
| Gap pill in header | Green/red badge displayed in ticker header |
| Gap-sorted scanner | Sidebar sorted by `\|gap_pct\|` descending |
| Gap Up / Gap Down filters | Filter pills in the header bar |
| Relative volume (RVOL) | `volume / avg_volume` calculated server-side |
| Historical price chart | Chart.js with multi-period selector (1M/3M/6M/1Y) |
| Float as key metric | Displayed in stats strip, float section, and metrics grid |

### Inspired by MOMO Screener

| Feature | Implementation |
|---|---|
| RVOL highlighting | Yellow (>1.2x), Red (>2x) in stats strip |
| Float breakdown visualization | Segmented bar chart (float vs restricted) |
| Float risk classification | Automatic label based on float size thresholds |
| Short interest % | `short_percent_float` in stats strip, red if >20% |
| Pre-market/aftermarket data | Handled natively by yfinance |
| Multi-ticker sidebar scanner | Batch loader via `/api/screener/smallcaps` |
| Filter by momentum | Gap Up / Gap Down / RVOL+ pills |

### Inspired by Finviz

| Feature | Implementation |
|---|---|
| Sector & industry badges | Displayed in ticker header |
| Cap classification | Micro/Small/Mid/Large Cap badge |
| 52-week high/low | In stats strip |
| P/E, EPS, Beta | In stats strip and metrics grid |
| Insider transactions | Full table in Ownership tab |
| Analyst-style key stats | Financials tab key statistics grid |
| Exchange badge | In ticker header |

### Inspired by BamSEC

| Feature | Implementation |
|---|---|
| SEC EDGAR filing browser | Full filing list in SEC tab with direct document links |
| CIK lookup | Via `sec.gov/files/company_tickers.json` |
| Form type color coding | 10-K blue · 10-Q cyan · 8-K yellow · S-1/424B4 red |
| Dilution risk detection | Automatic alert when S-1/S-3/424B4 filings present |
| Warrant risk identification | Isolated "potential warrant filings" section |
| Direct document links | Each filing links to the actual SEC document |
| Shelf registration tracking | S-3 count displayed in SEC summary metrics |
| Offering count | Total S-1 + 424B4 count displayed |

### Inspired by Yahoo Finance

| Feature | Implementation |
|---|---|
| Income Statement | yfinance `income_stmt`, 4 periods, 5 line items |
| Balance Sheet | yfinance `balance_sheet`, 4 periods, 6 line items |
| Cash Flow Statement | yfinance `cash_flow`, 4 periods, 4 line items |
| Key statistics | 12 valuation/profitability metrics |
| Options chain | Full calls + puts table for nearest expiration |
| News feed | Up to 15 articles via yfinance news |
| Institutional holders | yfinance `institutional_holders` (13F-sourced) |
| Mutual fund holders | yfinance `mutualfund_holders` |
| Insider transactions | yfinance `insider_transactions` (Form 4-sourced) |
| Historical OHLCV | yfinance `history()` for all charting |

---

## 7. Data Sources

| Data Type | Source | Cost | Latency |
|---|---|---|---|
| Price, fundamentals, stats | Yahoo Finance via `yfinance` | Free | ~15 min delayed |
| OHLCV history (up to 40 years) | Yahoo Finance via `yfinance` | Free | Daily |
| News feed | Yahoo Finance via `yfinance` | Free | Near real-time |
| Options chain | Yahoo Finance via `yfinance` | Free | ~15 min delayed |
| Institutional holders (13F) | Yahoo Finance via `yfinance` | Free | Quarterly |
| Mutual fund holders | Yahoo Finance via `yfinance` | Free | Quarterly |
| Insider transactions (Form 4) | Yahoo Finance via `yfinance` | Free | ~1-2 day delay |
| SEC filings (all types) | SEC EDGAR REST API | Free | Minutes after filing |
| CIK lookup | `sec.gov/files/company_tickers.json` | Free | Static |
| Submission history | `data.sec.gov/submissions/CIK{cik}.json` | Free | Minutes after filing |

### SEC EDGAR Endpoints Used

```
https://www.sec.gov/files/company_tickers.json   → CIK lookup table
https://data.sec.gov/submissions/CIK{cik}.json   → Company submission history
https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}  → Document URLs
```

### Rate Limiting Notes

- `yfinance` uses Yahoo Finance's unofficial API — no official rate limit but aggressive polling may trigger temporary blocks. A `0.1s` sleep is applied between tickers in batch screener calls.
- SEC EDGAR enforces a soft limit of ~10 requests/second. The app includes the required `User-Agent` header as per SEC guidelines.

---

## 8. UI / UX Design System

### Color Palette

| Token | Hex | Usage |
|---|---|---|
| `--bg` | `#0a0c10` | Page background |
| `--bg2` | `#0f1218` | Header, sidebar, cards |
| `--bg3` | `#151a22` | Chart area, metric boxes |
| `--bg4` | `#1c2230` | Active states, table hover |
| `--border` | `#1e2a3a` | All borders |
| `--text` | `#e2e8f4` | Primary text |
| `--text2` | `#8b9ab5` | Secondary text |
| `--text3` | `#4a5878` | Muted/label text |
| `--accent` | `#3b82f6` | Primary accent, active tabs |
| `--green` | `#22c55e` | Positive values, gains |
| `--red` | `#ef4444` | Negative values, risk alerts |
| `--yellow` | `#f59e0b` | Warnings, medium risk |
| `--purple` | `#a855f7` | Insider data |
| `--cyan` | `#06b6d4` | Exchange badges, 10-Q |

### Typography

- **Data / numbers:** `JetBrains Mono` — monospace for prices, tickers, values
- **Labels / UI:** `Space Grotesk` — humanist sans-serif for readability

### Filing Badge Color Coding

| Form | Color | Risk |
|---|---|---|
| 10-K | Blue | Informational |
| 10-Q | Cyan | Informational |
| 8-K | Yellow | Watch |
| S-1 / S-1/A / 424B4 | Red | High dilution risk |
| S-3 / S-3/A | Light red | Medium dilution risk |
| Form 4 / Form 3 | Purple | Insider activity |
| DEF 14A | Green | Proxy — vote related |
| Other | Gray | General |

### Responsive Behavior

- Desktop: 2-column layout (280px sidebar + main content)
- Mobile (<900px): sidebar hidden, full-width main content, all grids collapse to single column

---

## 9. Current Limitations & Roadmap

### Known Limitations

| Limitation | Detail |
|---|---|
| Price data is delayed | yfinance returns ~15 min delayed quotes for free; no real-time streaming |
| Scanner is static | The sidebar watchlist uses a hardcoded list of active small caps, not a live universe scan |
| Warrant detection is heuristic | The app flags filings by form type (S-1, S-3, 424B4) — it does not parse document text to confirm the presence of warrants |
| Options data is nearest expiration only | Full multi-expiration chain not loaded by default |
| Insider transaction data latency | yfinance Form 4 data may lag 1–2 days |
| No persistent storage | No watchlists, no saved notes, no trade journal — session state is in memory only |

### Suggested Roadmap (v2.0+)

#### Scanner Improvements
- [ ] Connect to a real-time data source (Polygon.io free tier, Alpaca, or Tradier sandbox) for live price streaming
- [ ] Dynamic universe: scan all US equities under $2B market cap with float < 50M
- [ ] MOMO-style HOD/LOD counter (new intraday highs/lows hit count)
- [ ] Pre-market gap scanner running from 4:00 AM EST

#### SEC / Warrant Analysis
- [ ] Full-text search within SEC documents (mimics BamSEC Pro)
- [ ] Parse 424B4 prospectus text to extract warrant exercise prices and expiration dates
- [ ] Diff viewer: compare two versions of the same filing side by side
- [ ] S-3 remaining capacity tracker (shelf availability)

#### Fundamental Analysis
- [ ] Multi-ticker comparison view (side-by-side financials)
- [ ] Financial ratio history charts (P/E over time, margins trend)
- [ ] Earnings calendar and earnings surprise history

#### Trading Tools
- [ ] Gap statistics engine (Flash Research-style): historical gap fill rate by size bucket
- [ ] No-code backtester: test long/short strategies on historical gap data
- [ ] VWAP and moving average overlays on price chart

#### User Features
- [ ] Persistent watchlists (SQLite local storage)
- [ ] Notes per ticker
- [ ] Alert system: notify when RVOL > threshold or gap exceeds X%
- [ ] Export to CSV/Excel

#### Alternative Data Sources
- [ ] Alpha Vantage integration (free tier): real-time quotes
- [ ] Polygon.io (free tier): WebSocket for live trades
- [ ] OpenBB Platform integration as optional backend

---

## Appendix A — API Response Status Codes

| Code | Meaning |
|---|---|
| `200` | Success |
| `400` | Bad request (invalid ticker, data fetch error) |
| `404` | Endpoint not found |
| `500` | Internal server error |

Errors return:
```json
{
  "detail": "Error message describing the failure"
}
```

---

## Appendix B — Screener Default Ticker List

The sidebar scanner pre-loads with the following active small-cap watchlist (editable in `main.py` under `get_smallcap_screener()`):

```python
["SOUN", "MARA", "RIOT", "CLOV", "BBIG", "MVIS", "CWEN", "SPWR",
 "ARVL", "GOEV", "WKHS", "NKLA", "RIDE", "HYLN", "FSR", "LCID",
 "FFIE", "MULN", "WRAP", "EZFL", "IDAI", "PPBT", "DRUG", "TPVG",
 "PROG", "CNTX", "GBOX", "IMPP", "GFAI", "RDBX", "ESSC", "AGRI"]
```

Replace or extend this list with your preferred tickers. In a future version this will be replaced by a live screener query.

---

*SmallCap Research Terminal — local research tool for educational and informational purposes only. Not financial advice.*
