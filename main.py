from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import yfinance as yf
import requests
import json
import re
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional
import time
import os

app = FastAPI(title="SmallCap Research Terminal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_path):
    try:
        os.makedirs(static_path, exist_ok=True)
    except OSError:
        pass # Ignore in Vercel's read-only file system

if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

HEADERS = {
    "User-Agent": "SmallCapResearch/1.0 research@smallcap.app",
    "Accept": "application/json"
}

# ─── ROOT ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(index_path)

# ─── TICKER OVERVIEW ─────────────────────────────────────────────────────────

@app.get("/api/ticker/{symbol}")
async def get_ticker_overview(symbol: str):
    symbol = symbol.upper().strip()
    try:
        tk = yf.Ticker(symbol)
        info = tk.info

        # Float shares
        float_shares = info.get("floatShares") or info.get("sharesOutstanding", 0)
        shares_outstanding = info.get("sharesOutstanding", 0)

        # Market cap classification
        market_cap = info.get("marketCap", 0)
        if market_cap < 300_000_000:
            cap_class = "Micro Cap"
        elif market_cap < 2_000_000_000:
            cap_class = "Small Cap"
        elif market_cap < 10_000_000_000:
            cap_class = "Mid Cap"
        else:
            cap_class = "Large Cap"

        # Price data
        hist = tk.history(period="5d")
        current_price = float(hist["Close"].iloc[-1]) if not hist.empty else info.get("currentPrice", 0)
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else info.get("previousClose", 0)
        price_change = current_price - prev_close
        price_change_pct = (price_change / prev_close * 100) if prev_close else 0

        # Volume
        avg_volume = info.get("averageVolume", 0)
        current_volume = int(hist["Volume"].iloc[-1]) if not hist.empty else 0
        relative_volume = round(current_volume / avg_volume, 2) if avg_volume else 0

        # Gap calculation (today open vs yesterday close)
        gap_pct = 0
        if not hist.empty and len(hist) > 1:
            today_open = float(hist["Open"].iloc[-1])
            gap_pct = round((today_open - prev_close) / prev_close * 100, 2) if prev_close else 0

        return {
            "symbol": symbol,
            "company_name": info.get("longName", symbol),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "exchange": info.get("exchange", "N/A"),
            "cap_class": cap_class,
            "market_cap": market_cap,
            "current_price": round(current_price, 4),
            "prev_close": round(prev_close, 4),
            "price_change": round(price_change, 4),
            "price_change_pct": round(price_change_pct, 2),
            "gap_pct": gap_pct,
            "volume": current_volume,
            "avg_volume": avg_volume,
            "relative_volume": relative_volume,
            "float_shares": float_shares,
            "shares_outstanding": shares_outstanding,
            "short_ratio": info.get("shortRatio", 0),
            "short_percent_float": info.get("shortPercentOfFloat", 0),
            "beta": info.get("beta", None),
            "pe_ratio": info.get("trailingPE", None),
            "eps": info.get("trailingEps", None),
            "52w_high": info.get("fiftyTwoWeekHigh", None),
            "52w_low": info.get("fiftyTwoWeekLow", None),
            "description": info.get("longBusinessSummary", "")[:500] if info.get("longBusinessSummary") else "",
            "website": info.get("website", ""),
            "country": info.get("country", ""),
            "employees": info.get("fullTimeEmployees", None),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching ticker data: {str(e)}")

# ─── PRICE HISTORY ────────────────────────────────────────────────────────────

@app.get("/api/ticker/{symbol}/history")
async def get_price_history(symbol: str, period: str = "3mo"):
    symbol = symbol.upper().strip()
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period=period)
        if hist.empty:
            return {"candles": []}
        data = []
        for idx, row in hist.iterrows():
            data.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(float(row["Close"]), 4),
                "volume": int(row["Volume"]),
            })
        return {"candles": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── FINANCIALS ───────────────────────────────────────────────────────────────

@app.get("/api/ticker/{symbol}/financials")
async def get_financials(symbol: str):
    symbol = symbol.upper().strip()
    try:
        tk = yf.Ticker(symbol)
        info = tk.info

        # Income statement
        try:
            income = tk.income_stmt
            income_data = []
            if income is not None and not income.empty:
                for col in income.columns[:4]:
                    row = {"period": str(col)[:10]}
                    for metric in ["Total Revenue", "Gross Profit", "Net Income", "EBITDA", "Operating Income"]:
                        if metric in income.index:
                            val = income.loc[metric, col]
                            row[metric] = int(val) if pd.notna(val) else None
                    income_data.append(row)
        except:
            income_data = []

        # Balance sheet
        try:
            balance = tk.balance_sheet
            balance_data = []
            if balance is not None and not balance.empty:
                for col in balance.columns[:4]:
                    row = {"period": str(col)[:10]}
                    for metric in ["Total Assets", "Total Liabilities Net Minority Interest",
                                   "Total Equity Gross Minority Interest", "Cash And Cash Equivalents",
                                   "Long Term Debt", "Common Stock"]:
                        if metric in balance.index:
                            val = balance.loc[metric, col]
                            row[metric] = int(val) if pd.notna(val) else None
                    balance_data.append(row)
        except:
            balance_data = []

        # Cash flow
        try:
            cashflow = tk.cash_flow
            cf_data = []
            if cashflow is not None and not cashflow.empty:
                for col in cashflow.columns[:4]:
                    row = {"period": str(col)[:10]}
                    for metric in ["Operating Cash Flow", "Free Cash Flow",
                                   "Capital Expenditure", "Issuance Of Capital Stock"]:
                        if metric in cashflow.index:
                            val = cashflow.loc[metric, col]
                            row[metric] = int(val) if pd.notna(val) else None
                    cf_data.append(row)
        except:
            cf_data = []

        return {
            "income": income_data,
            "balance": balance_data,
            "cashflow": cf_data,
            "key_stats": {
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "profit_margins": info.get("profitMargins"),
                "operating_margins": info.get("operatingMargins"),
                "return_on_equity": info.get("returnOnEquity"),
                "return_on_assets": info.get("returnOnAssets"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "book_value": info.get("bookValue"),
                "price_to_book": info.get("priceToBook"),
                "enterprise_value": info.get("enterpriseValue"),
                "ebitda": info.get("ebitda"),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── INSTITUTIONAL OWNERSHIP ──────────────────────────────────────────────────

@app.get("/api/ticker/{symbol}/institutional")
async def get_institutional(symbol: str):
    symbol = symbol.upper().strip()
    try:
        tk = yf.Ticker(symbol)

        # Institutional holders
        try:
            inst = tk.institutional_holders
            inst_data = []
            if inst is not None and not inst.empty:
                for _, row in inst.iterrows():
                    inst_data.append({
                        "holder": str(row.get("Holder", "")),
                        "shares": int(row.get("Shares", 0)) if pd.notna(row.get("Shares", 0)) else 0,
                        "date_reported": str(row.get("Date Reported", ""))[:10],
                        "pct_held": float(row.get("% Out", 0)) if pd.notna(row.get("% Out", 0)) else 0,
                        "value": int(row.get("Value", 0)) if pd.notna(row.get("Value", 0)) else 0,
                    })
        except:
            inst_data = []

        # Mutual fund holders
        try:
            mf = tk.mutualfund_holders
            mf_data = []
            if mf is not None and not mf.empty:
                for _, row in mf.iterrows():
                    mf_data.append({
                        "holder": str(row.get("Holder", "")),
                        "shares": int(row.get("Shares", 0)) if pd.notna(row.get("Shares", 0)) else 0,
                        "date_reported": str(row.get("Date Reported", ""))[:10],
                        "pct_held": float(row.get("% Out", 0)) if pd.notna(row.get("% Out", 0)) else 0,
                        "value": int(row.get("Value", 0)) if pd.notna(row.get("Value", 0)) else 0,
                    })
        except:
            mf_data = []

        # Insider transactions
        try:
            insider = tk.insider_transactions
            insider_data = []
            if insider is not None and not insider.empty:
                for _, row in insider.head(15).iterrows():
                    insider_data.append({
                        "insider": str(row.get("Insider", "")),
                        "relation": str(row.get("Relation", "")),
                        "transaction": str(row.get("Transaction", "")),
                        "date": str(row.get("Start Date", ""))[:10],
                        "shares": int(row.get("Shares", 0)) if pd.notna(row.get("Shares", 0)) else 0,
                        "value": int(row.get("Value", 0)) if pd.notna(row.get("Value", 0)) else 0,
                        "ownership": float(row.get("% Owned", 0)) if pd.notna(row.get("% Owned", 0)) else 0,
                    })
        except:
            insider_data = []

        info = tk.info
        total_inst_pct = info.get("heldPercentInstitutions", 0)
        insider_pct = info.get("heldPercentInsiders", 0)
        float_shares = info.get("floatShares", 0)

        return {
            "total_institutional_pct": round(total_inst_pct * 100, 2) if total_inst_pct else 0,
            "insider_pct": round(insider_pct * 100, 2) if insider_pct else 0,
            "float_shares": float_shares,
            "institutional_holders": inst_data[:20],
            "mutualfund_holders": mf_data[:10],
            "insider_transactions": insider_data,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── NEWS ─────────────────────────────────────────────────────────────────────

@app.get("/api/ticker/{symbol}/news")
async def get_news(symbol: str):
    symbol = symbol.upper().strip()
    try:
        tk = yf.Ticker(symbol)
        news_raw = tk.news
        news = []
        for item in (news_raw or [])[:15]:
            content = item.get("content", {})
            pub_date = content.get("pubDate", "")
            title = content.get("title", item.get("title", ""))
            summary = content.get("summary", "")
            provider = content.get("provider", {})
            provider_name = provider.get("displayName", "") if isinstance(provider, dict) else ""
            url = ""
            click_through = content.get("clickThroughUrl", {})
            if isinstance(click_through, dict):
                url = click_through.get("url", "")
            if not url:
                url = item.get("link", "")
            if title:
                news.append({
                    "title": title,
                    "summary": summary[:200] if summary else "",
                    "url": url,
                    "published": pub_date[:10] if pub_date else "",
                    "source": provider_name,
                    "type": content.get("contentType", "NEWS"),
                })
        return {"news": news}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── SEC / BAMSEC-STYLE FILINGS ───────────────────────────────────────────────

@app.get("/api/ticker/{symbol}/sec")
async def get_sec_filings(symbol: str):
    symbol = symbol.upper().strip()
    try:
        # Get CIK from SEC
        search_url = f"https://efts.sec.gov/LATEST/search-index?q=%22{symbol}%22&dateRange=custom&startdt=2020-01-01&forms=S-1,10-K,10-Q,8-K,424B4,S-3,S-11"
        cik_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK={symbol}&type=&dateb=&owner=include&count=1&search_text=&action=getcompany&output=atom"

        # Get company CIK via tickers.json
        tickers_resp = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=HEADERS, timeout=10
        )
        cik = None
        company_name = symbol
        if tickers_resp.status_code == 200:
            tickers_data = tickers_resp.json()
            for key, val in tickers_data.items():
                if val.get("ticker", "").upper() == symbol:
                    cik = str(val["cik_str"]).zfill(10)
                    company_name = val.get("title", symbol)
                    break

        if not cik:
            return {"filings": [], "warrants": [], "cik": None, "message": "CIK not found for this ticker"}

        # Get recent filings
        filings_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        filings_resp = requests.get(filings_url, headers=HEADERS, timeout=10)

        filings = []
        warrants = []
        has_warrants = False
        warrant_info = []

        if filings_resp.status_code == 200:
            data = filings_resp.json()
            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            descriptions = recent.get("primaryDocument", [])
            accession = recent.get("accessionNumber", [])

            warrant_forms = {"S-1", "S-1/A", "424B4", "S-3", "S-3/A", "8-K", "6-K", "SC 13G", "SC 13D"}
            key_forms = {"10-K", "10-Q", "8-K", "S-1", "S-1/A", "424B4", "S-3", "S-3/A",
                         "DEF 14A", "SC 13G", "SC 13D", "4", "3", "NT 10-K"}

            for i, form in enumerate(forms[:80]):
                date = dates[i] if i < len(dates) else ""
                doc = descriptions[i] if i < len(descriptions) else ""
                acc = accession[i].replace("-", "") if i < len(accession) else ""
                doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{doc}" if acc and doc else ""

                entry = {
                    "form": form,
                    "date": date,
                    "document": doc,
                    "url": doc_url,
                    "accession": accession[i] if i < len(accession) else "",
                }

                if form in key_forms:
                    filings.append(entry)

                # Warrant detection
                if form in warrant_forms:
                    warrant_keywords = ["warrant", "warrants", "exercisable", "exercise price"]
                    form_lower = form.lower()
                    desc_lower = doc.lower()
                    if any(kw in form_lower or kw in desc_lower for kw in warrant_keywords):
                        has_warrants = True
                        warrant_info.append(entry)
                    # S-1 and 424B4 filings typically involve warrants in small caps
                    if form in {"S-1", "S-1/A", "424B4", "S-3"}:
                        warrant_info.append(entry)

        # Remove duplicate warrant entries
        seen = set()
        unique_warrants = []
        for w in warrant_info:
            key = w["accession"]
            if key not in seen:
                seen.add(key)
                unique_warrants.append(w)

        return {
            "cik": cik,
            "company_name": company_name,
            "filings": filings[:30],
            "potential_warrant_filings": unique_warrants[:10],
            "has_dilution_risk_filings": len([f for f in filings if f["form"] in {"S-1", "S-1/A", "424B4", "S-3", "S-3/A"}]) > 0,
            "offering_count": len([f for f in filings if f["form"] in {"S-1", "S-1/A", "424B4"}]),
            "s3_count": len([f for f in filings if f["form"] in {"S-3", "S-3/A"}]),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── OPTIONS CHAIN ────────────────────────────────────────────────────────────

@app.get("/api/ticker/{symbol}/options")
async def get_options(symbol: str):
    symbol = symbol.upper().strip()
    try:
        tk = yf.Ticker(symbol)
        expirations = tk.options
        if not expirations:
            return {"expirations": [], "calls": [], "puts": []}

        # Get nearest expiration
        exp = expirations[0]
        chain = tk.option_chain(exp)

        def process_chain(df):
            out = []
            for _, row in df.head(20).iterrows():
                out.append({
                    "strike": float(row.get("strike", 0)),
                    "lastPrice": float(row.get("lastPrice", 0)),
                    "bid": float(row.get("bid", 0)),
                    "ask": float(row.get("ask", 0)),
                    "volume": int(row.get("volume", 0)) if pd.notna(row.get("volume", 0)) else 0,
                    "openInterest": int(row.get("openInterest", 0)) if pd.notna(row.get("openInterest", 0)) else 0,
                    "impliedVolatility": round(float(row.get("impliedVolatility", 0)) * 100, 1),
                    "inTheMoney": bool(row.get("inTheMoney", False)),
                })
            return out

        return {
            "expirations": list(expirations[:8]),
            "nearest_expiration": exp,
            "calls": process_chain(chain.calls),
            "puts": process_chain(chain.puts),
        }
    except Exception as e:
        return {"expirations": [], "calls": [], "puts": [], "error": str(e)}

# ─── SMALL CAP SCREENER ───────────────────────────────────────────────────────

@app.get("/api/screener/smallcaps")
async def get_smallcap_screener():
    """Returns a curated list of small cap tickers for gap/momentum scanning"""
    # Sample watchlist of active small caps - in production this would pull from a data source
    default_tickers = [
        "SOUN", "MARA", "RIOT", "CLOV", "BBIG", "MVIS", "CWEN", "SPWR",
        "ARVL", "GOEV", "WKHS", "NKLA", "RIDE", "HYLN", "FSR", "LCID",
        "FFIE", "MULN", "WRAP", "EZFL", "IDAI", "PPBT", "DRUG", "TPVG",
        "PROG", "CNTX", "GBOX", "IMPP", "GFAI", "RDBX", "ESSC", "AGRI"
    ]

    results = []
    for sym in default_tickers[:15]:
        try:
            tk = yf.Ticker(sym)
            info = tk.info
            mc = info.get("marketCap", 0)
            if mc and mc < 2_000_000_000:
                hist = tk.history(period="2d")
                price = float(hist["Close"].iloc[-1]) if not hist.empty else 0
                vol = int(hist["Volume"].iloc[-1]) if not hist.empty else 0
                avg_vol = info.get("averageVolume", 1)
                rv = round(vol / avg_vol, 2) if avg_vol else 0
                gap = 0
                if len(hist) > 1:
                    today_open = float(hist["Open"].iloc[-1])
                    prev_close = float(hist["Close"].iloc[-2])
                    gap = round((today_open - prev_close) / prev_close * 100, 2) if prev_close else 0
                results.append({
                    "symbol": sym,
                    "name": info.get("shortName", sym),
                    "price": round(price, 4),
                    "market_cap": mc,
                    "sector": info.get("sector", "N/A"),
                    "float_shares": info.get("floatShares", 0),
                    "relative_volume": rv,
                    "gap_pct": gap,
                })
            time.sleep(0.1)
        except:
            continue

    results.sort(key=lambda x: abs(x.get("gap_pct", 0)), reverse=True)
    return {"tickers": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
