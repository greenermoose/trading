# Growth Switch + LEAPS Signal App

## Project Requirements Document (PRD)

**Version:** 1.0  
**Goal:** Build a decision-support application that outperforms buy-and-hold QQQM total return over time.

Create a no-build Vue app that runs in a browser and uses IndexedDB to persist data.

---

## 1. Purpose

Build a personal investment trading decision-support app that:

1. Ingests a **user-managed watchlist of ~25 growth tickers**
2. Continuously pulls **current market data from configurable online sources**
3. Computes technical and volatility signals
4. Outputs **clear daily actions**:
   - Whether to **hold QQQM** or **allocate a portion to individual stock(s)**
   - Whether to **buy LEAPS calls** on any watchlist ticker, including **exact expiration and strike**

The app will recommend **"Hold QQQM" most days**. Action signals should be high-conviction only.

**Non-goal:** Automatic trade execution. The app produces recommendations; the user executes manually.

**Audience:** Single user, technically capable, requires transparency, auditability, and configurable rules.

---

## 2. Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Deterministic outputs** | Given identical data and settings, recommendations must be repeatable |
| **Explainable signals** | Every recommendation displays supporting metrics and threshold comparisons |
| **Bias to inaction** | Only trigger actions when confidence criteria are fully met |
| **Configurable strategy** | All indicators, thresholds, risk parameters, and LEAPS rules editable via config file without code changes |
| **Data-source abstraction** | Swap data providers without modifying strategy logic |

---

## 3. User Experience

### 3.1 Daily Dashboard (Landing Page)

The dashboard must answer these questions at a glance:

**Header:**
- Today's date (user's local timezone)
- Data freshness timestamp (when market data was last updated)

**Portfolio Posture Recommendation (primary display, prominent):**
- `HOLD QQQM` (default state)
- OR `ALLOCATE TO: [TICKER]` with percentage allocation

**Options Recommendation:**
- `NO LEAPS TODAY`
- OR `BUY LEAPS: [TICKER] [EXPIRATION] [STRIKE] CALL @ ~$[PRICE] (Target Δ: [DELTA])`

**Rationale Panel:**
- Signal checklist (which rules passed/failed)
- Confidence score
- One-sentence summary explanation

**Evidence Panel (expandable):**
- Daily and weekly charts with overlays
- Volatility metrics (BB bandwidth, ATR)
- IV percentile (when available)
- Relative strength vs QQQM

**Change Log:**
- Signals that crossed thresholds since yesterday
- Score changes for top candidates

### 3.2 Watchlist Management

- Add/remove tickers (validate against data provider)
- Tag tickers with categories (e.g., "AI", "Semis", "Software", "Healthcare")
- Optional notes field per ticker (thesis, earnings date, etc.)
- Display current score and rank for each ticker

### 3.3 Settings Interface

**Strategy Parameters:**
- All threshold values
- Indicator weights
- Scoring formula parameters

**Risk Controls:**
- Maximum allocation percentage to individual stocks
- Maximum concurrent stock positions
- Maximum LEAPS premium at risk
- Cooldown periods

**Data Sources:**
- Select active equity data provider
- Select active options data provider
- API key management (secure storage)

**System:**
- Timezone selection
- Trading calendar (market holidays)
- Update schedule configuration

---

## 4. Functional Requirements

### 4.1 Watchlist Management

| ID | Requirement |
|----|-------------|
| FR-1 | User can maintain a list of 1–50 equity tickers |
| FR-2 | App validates tickers exist and are supported by active data provider |
| FR-3 | Watchlist and all settings persist locally (SQLite + config file) |
| FR-4 | Watchlist changes trigger immediate data fetch for new tickers |

### 4.2 Market Data Ingestion

| ID | Requirement |
|----|-------------|
| FR-5 | App fetches daily OHLCV (Open, High, Low, Close, Volume) for: QQQM, all watchlist tickers, SPY (benchmark) |
| FR-6 | App fetches sufficient history for indicator calculation (minimum 252 trading days + 52 weeks) |
| FR-7 | Data layer implements `MarketDataProvider` interface (see Section 8) |
| FR-8 | App supports multiple provider adapters; user selects active provider in settings |
| FR-9 | Initial supported providers: Yahoo Finance adapter, Alpha Vantage adapter, Stooq adapter |
| FR-10 | Data updates run on configurable schedule (default: daily at 6:00 PM ET on trading days) |
| FR-11 | Manual refresh button available in UI |

### 4.3 Options Data Ingestion

| ID | Requirement |
|----|-------------|
| FR-12 | App implements `OptionsDataProvider` interface for options chain data |
| FR-13 | When options provider is configured, fetch for each LEAPS candidate: available expirations, strikes, bid/ask prices, delta (if available), implied volatility (if available) |
| FR-14 | Graceful degradation: if no options provider configured, display "LEAPS signal triggered—connect options provider for exact contract" |
| FR-15 | Initial supported options providers: Yahoo Finance options adapter, CBOE delayed data adapter |

### 4.4 Indicator Engine

Compute the following indicators on **daily** and **weekly** timeframes:

**Required Indicators:**

| Indicator | Parameters | Timeframes |
|-----------|------------|------------|
| EMA | 20-period | Daily, Weekly |
| SMA | 50-period | Daily, Weekly |
| SMA | 200-period | Daily, Weekly |
| SMA Slope | 50-period, 10-period lookback | Weekly |
| RSI | 14-period | Daily, Weekly |
| Rate of Change (ROC) | 12-period | Weekly |
| Bollinger Bands | 20-period, 2 std dev | Daily, Weekly |
| Bollinger Bandwidth | 20-period | Daily, Weekly |
| Bollinger Bandwidth Percentile | 52-week lookback | Weekly |
| ATR | 14-period | Daily |
| Relative Strength Ratio | Ticker/QQQM | Daily, Weekly |
| RS Ratio Slope | 10-period lookback | Weekly |

| ID | Requirement |
|----|-------------|
| FR-16 | All indicators computed consistently across all tickers |
| FR-17 | Indicator calculations have unit tests with known input/output pairs |
| FR-18 | Each computed indicator value stored with timestamp for audit trail |
| FR-19 | Weekly indicators computed using Friday close (or last trading day of week) |

### 4.5 Stock Opportunity Scoring

| ID | Requirement |
|----|-------------|
| FR-20 | Each watchlist ticker receives a **Stock Opportunity Score** (0–100) |
| FR-21 | Score computed from weighted criteria (see Section 7.1 for default formula) |
| FR-22 | Score components individually visible in UI for transparency |

### 4.6 Decision Logic: Stock Allocation

**Default Behavior:** Hold 100% QQQM

**Allocation Trigger Conditions (all must be true):**
1. Best ticker score ≥ `AllocationScoreThreshold` (default: 75)
2. Best ticker score exceeds second-best by ≥ `MinScoreSeparation` (default: 10 points)
3. Cooldown period satisfied: no allocation change in last `CooldownDays` (default: 5 trading days)
4. Weekly trend filter passed: 20 EMA > 50 SMA on weekly chart

**Allocation Rules:**

| Score Range | Allocation from QQQM to Stock |
|-------------|-------------------------------|
| 75–84 | 25% |
| 85–94 | 40% |
| 95–100 | 50% |

| ID | Requirement |
|----|-------------|
| FR-23 | App computes allocation recommendation based on score and rules above |
| FR-24 | Maximum 2 individual stock positions at any time |
| FR-25 | If 2 positions already held, new signal only triggers if new score > lowest held position score by ≥ 15 points |

**Exit Conditions (return allocation to QQQM):**
1. Stock score falls below `ExitScoreThreshold` (default: 55)
2. Relative strength ratio (vs QQQM) declines for 3 consecutive weeks
3. Price closes below 50-day SMA for 3 consecutive days
4. User-defined stop-loss triggered (configurable, default: -15% from entry)

| ID | Requirement |
|----|-------------|
| FR-26 | App evaluates exit conditions daily for all held positions |
| FR-27 | Exit recommendation displayed with same prominence as entry |

### 4.7 Decision Logic: LEAPS Calls

**LEAPS signals operate independently from stock allocation signals.**

**LEAPS Trigger Conditions (all must be true):**
1. Weekly trend filter: 20 EMA > 50 SMA > 200 SMA
2. 50 SMA slope positive (rising)
3. Weekly RSI between 50–70 and rising (higher than 4 weeks ago)
4. Bollinger Bandwidth percentile ≤ 25 (volatility compressed)
5. Relative strength ratio vs QQQM rising over 4 weeks
6. Stock Opportunity Score ≥ 70
7. If IV data available: IV percentile ≤ 50

| ID | Requirement |
|----|-------------|
| FR-28 | LEAPS signal evaluated independently; can trigger even if no stock allocation signal |
| FR-29 | LEAPS signal can apply to QQQM itself (buy QQQM LEAPS), not just watchlist stocks |

**Contract Selection Rules:**

| Parameter | Rule |
|-----------|------|
| Expiration | Nearest expiration with DTE between 450–640 days; prefer closest to 540 DTE |
| Strike | Target delta 0.70; if delta unavailable, select strike ~5% ITM |
| Type | Call only |
| Price | Mid = (Bid + Ask) / 2; warn if spread > 10% of mid |

| ID | Requirement |
|----|-------------|
| FR-30 | When options chain available, output exact contract: underlying, expiration date, strike price, estimated cost |
| FR-31 | When options chain unavailable, output target parameters: underlying, target DTE range, target delta/moneyness |

**LEAPS Risk Controls:**

| ID | Requirement |
|----|-------------|
| FR-32 | Maximum 1 LEAPS position at a time (simple mode; configurable to allow 2) |
| FR-33 | Maximum premium per position: configurable dollar amount (default: $5,000) |
| FR-34 | Cooldown: no new LEAPS signal for same underlying within 30 days of last LEAPS purchase |

### 4.8 Recommendation Output

| ID | Requirement |
|----|-------------|
| FR-35 | App produces structured daily recommendation object containing: action type, ticker(s), allocation percentages, LEAPS contract details (if applicable), confidence score, rule pass/fail breakdown, one-sentence rationale |
| FR-36 | Recommendation persisted to database with timestamp |
| FR-37 | Full recommendation history queryable and exportable |

### 4.9 Notifications

| ID | Requirement |
|----|-------------|
| FR-38 | Optional email notification when recommendation changes from previous day |
| FR-39 | Notification includes: new action, previous action, key metrics that changed |
| FR-40 | Notification settings configurable (on/off, email address) |

### 4.10 Backtesting

| ID | Requirement |
|----|-------------|
| FR-41 | Built-in backtester runs strategy over historical data |
| FR-42 | Backtest date range configurable (default: 5 years) |
| FR-43 | Backtest compares strategy equity curve to: buy-and-hold QQQM, buy-and-hold SPY |
| FR-44 | Backtest outputs: total return, CAGR, maximum drawdown, volatility (annualized std dev), Sharpe ratio (assume 4% risk-free rate), win rate (% of trades profitable), average win / average loss |
| FR-45 | Backtest generates trade list with: entry date, exit date, ticker, entry price, exit price, return % |
| FR-46 | Backtest generates signal diagnostics: frequency of each rule triggering, which rules most predictive |
| FR-47 | LEAPS backtesting: estimate LEAPS returns using delta approximation (LEAPS return ≈ stock return × delta × leverage factor) |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement |
|----|-------------|
| NFR-1 | Daily refresh completes in < 30 seconds for 25 tickers (with cached historical data) |
| NFR-2 | App caches historical data; daily updates fetch only new data |
| NFR-3 | UI renders dashboard in < 2 seconds |

### 5.2 Reliability

| ID | Requirement |
|----|-------------|
| NFR-4 | Handle API failures gracefully: retry with exponential backoff (3 attempts) |
| NFR-5 | Handle rate limits: queue requests, respect provider limits |
| NFR-6 | On data fetch failure: use last known good data, display warning with staleness duration |
| NFR-7 | Validate all incoming data (no NaN, no future dates, price > 0) |

### 5.3 Auditability

| ID | Requirement |
|----|-------------|
| NFR-8 | Store raw price data snapshots (never overwrite; append only) |
| NFR-9 | Store computed indicators with version of calculation logic |
| NFR-10 | Store all recommendations with full rule evaluation details |
| NFR-11 | All stored data queryable by date range |

### 5.4 Security

| ID | Requirement |
|----|-------------|
| NFR-12 | API keys stored in environment variables or OS keychain; never in config files |
| NFR-13 | No broker credentials required or accepted |
| NFR-14 | Local-only operation by default (no external data transmission except to data providers) |

### 5.5 Portability

| ID | Requirement |
|----|-------------|
| NFR-15 | App runs on macOS, Windows, and Linux |
| NFR-16 | No OS-specific dependencies in core logic |
| NFR-17 | Single-command installation process |

---

## 6. Technical Architecture

### 6.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                           Frontend                              │
│                    (Web UI - Local Server)                      │
│  ┌───────────┐ ┌───────────┐ ┌──────────┐ ┌─────────┐ ┌───────┐ │
│  │ Dashboard │ │ Watchlist │ │ Settings │ │Backtest │ │ Logs  │ │
│  └───────────┘ └───────────┘ └──────────┘ └─────────┘ └───────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           Backend                               │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │    Scheduler     │───▶│  Update Pipeline │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                   │                             │
│           ┌───────────────────────┼───────────────────────┐     │
│           ▼                       ▼                       ▼     │
│  ┌─────────────────┐    ┌─────────────────┐   ┌───────────────┐ │
│  │  Data Providers │    │ Indicator Engine│   │Strategy Engine│ │
│  │  ├─ Equity      │    │                 │   │ ├─ Scorer     │ │
│  │  └─ Options     │    │                 │   │ ├─ Allocator  │ │
│  └─────────────────┘    └─────────────────┘   │ └─ LEAPS      │ │
│           │                       │           └───────────────┘ │
│           ▼                       ▼                    │        │
│  ┌─────────────────────────────────────────────────────┘        │
│  │                                                              │
│  ▼                                                              │
│  ┌─────────────────────┐    ┌──────────────────┐                │
│  │     Storage         │    │    Backtester    │                │
│  │  (IndexedDB + JSON) │◀──▶│                  │                │
│  └─────────────────────┘    └──────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Module Specifications

**Module: `data_provider_equity`**
- Interface: `MarketDataProvider`
- Adapters: `YahooFinanceAdapter`, `AlphaVantageAdapter`, `StooqAdapter`
- Output: Standardized OHLCV DataFrame

**Module: `data_provider_options`**
- Interface: `OptionsDataProvider`
- Adapters: `YahooOptionsAdapter`, `CBOEAdapter`
- Output: Standardized options chain DataFrame

**Module: `indicator_engine`**
- Input: OHLCV DataFrame
- Output: DataFrame with all computed indicators
- Must be stateless and deterministic

**Module: `strategy_engine`**
- Submodules: `scorer`, `allocator`, `leaps_selector`
- Input: Indicator DataFrame + Config
- Output: Scores, allocation recommendations, LEAPS recommendations

**Module: `recommendation_engine`**
- Combines strategy outputs into final recommendation
- Applies risk controls and cooldowns
- Generates human-readable rationale

**Module: `storage`**
- SQLite database for: prices, indicators, recommendations, backtest results
- JSON/YAML files for: user settings, watchlist, strategy config

**Module: `backtester`**
- Runs historical simulation
- Uses same strategy engine (no special backtest logic)
- Outputs performance metrics and trade log

**Module: `scheduler`**
- Triggers daily updates
- Respects market calendar (skip weekends/holidays)
- Configurable run time

### 6.3 Storage Schema

**Table: `prices`**
```sql
CREATE TABLE prices (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    provider TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, provider)
);
```

**Table: `indicators`**
```sql
CREATE TABLE indicators (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    timeframe TEXT NOT NULL,  -- 'daily' or 'weekly'
    indicator_name TEXT NOT NULL,
    value REAL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, timeframe, indicator_name)
);
```

**Table: `recommendations`**
```sql
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    recommendation_type TEXT NOT NULL,  -- 'HOLD', 'ALLOCATE', 'LEAPS', 'EXIT'
    primary_ticker TEXT,
    allocation_pct REAL,
    leaps_expiration DATE,
    leaps_strike REAL,
    leaps_price_estimate REAL,
    confidence_score REAL,
    rationale TEXT,
    rule_details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Table: `backtest_runs`**
```sql
CREATE TABLE backtest_runs (
    id INTEGER PRIMARY KEY,
    run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    start_date DATE,
    end_date DATE,
    config_snapshot JSON,
    total_return REAL,
    cagr REAL,
    max_drawdown REAL,
    sharpe_ratio REAL,
    trade_count INTEGER,
    win_rate REAL
);
```

**Table: `backtest_trades`**
```sql
CREATE TABLE backtest_trades (
    id INTEGER PRIMARY KEY,
    run_id INTEGER REFERENCES backtest_runs(id),
    entry_date DATE,
    exit_date DATE,
    symbol TEXT,
    trade_type TEXT,  -- 'STOCK' or 'LEAPS'
    entry_price REAL,
    exit_price REAL,
    allocation_pct REAL,
    return_pct REAL
);
```

---

## 7. Strategy Configuration

### 7.1 Default Scoring Formula

**Stock Opportunity Score (0–100) = Weighted Sum of Components:**

| Component | Weight | Scoring Logic |
|-----------|--------|---------------|
| Trend Alignment | 25 | +25 if 20 EMA > 50 SMA > 200 SMA (weekly); +15 if 20 > 50 only; +0 otherwise |
| RS Momentum | 20 | +20 if RS ratio vs QQQM rising 4+ weeks; +10 if rising 2–3 weeks; +0 otherwise |
| RSI Position | 15 | +15 if weekly RSI 50–70; +10 if 40–50 or 70–80; +0 if <40 or >80 |
| Volatility Setup | 15 | +15 if BB width percentile ≤ 20; +10 if ≤ 35; +5 if ≤ 50; +0 otherwise |
| Price vs MAs | 15 | +15 if price > 20 EMA > 50 SMA (daily); +10 if price > 50 SMA; +0 otherwise |
| Volume Trend | 10 | +10 if 20-day avg volume > 50-day avg volume; +5 if within 10%; +0 otherwise |

### 7.2 Default Configuration File

```yaml
# config.yaml

watchlist:
  symbols: []  # User populates
  tags: {}     # symbol: [tag1, tag2]

benchmarks:
  primary: QQQM
  secondary: SPY

data_sources:
  equity_provider: yahoo
  options_provider: yahoo
  # API keys loaded from environment variables

schedule:
  update_time: "18:00"  # 6 PM
  timezone: "America/New_York"

indicators:
  ema_periods: [20]
  sma_periods: [50, 200]
  rsi_period: 14
  bb_period: 20
  bb_std: 2
  atr_period: 14
  roc_period: 12
  slope_lookback: 10
  rs_lookback_weeks: 4

scoring:
  weights:
    trend_alignment: 25
    rs_momentum: 20
    rsi_position: 15
    volatility_setup: 15
    price_vs_ma: 15
    volume_trend: 10

allocation_rules:
  score_threshold: 75
  min_score_separation: 10
  cooldown_days: 5
  max_positions: 2
  tiers:
    - min_score: 75
      max_score: 84
      allocation_pct: 25
    - min_score: 85
      max_score: 94
      allocation_pct: 40
    - min_score: 95
      max_score: 100
      allocation_pct: 50

exit_rules:
  score_threshold: 55
  rs_decline_weeks: 3
  below_50sma_days: 3
  stop_loss_pct: 15

leaps_rules:
  enabled: true
  min_dte: 450
  max_dte: 640
  target_dte: 540
  target_delta: 0.70
  fallback_itm_pct: 5
  max_iv_percentile: 50
  min_score: 70
  max_positions: 1
  max_premium_usd: 5000
  cooldown_days: 30
  allow_qqqm_leaps: true

risk_controls:
  require_weekly_trend_filter: true
  max_total_allocation_pct: 50

notifications:
  enabled: false
  email: ""

backtest:
  default_years: 5
  risk_free_rate: 0.04
  leaps_leverage_factor: 3.0
```

---

## 8. Interface Specifications

### 8.1 MarketDataProvider Interface

```python
from abc import ABC, abstractmethod
from datetime import date
import pandas as pd

class MarketDataProvider(ABC):
    """Abstract interface for equity market data providers."""
    
    @abstractmethod
    def get_daily_ohlcv(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV data for a symbol.
        
        Returns DataFrame with columns:
            - date (index): datetime
            - open: float
            - high: float
            - low: float  
            - close: float
            - volume: int
        
        Raises:
            SymbolNotFoundError: If symbol doesn't exist
            DataFetchError: If API call fails
        """
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Check if symbol exists and is supported."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return identifier for this provider."""
        pass
```

### 8.2 OptionsDataProvider Interface

```python
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
import pandas as pd

class OptionsDataProvider(ABC):
    """Abstract interface for options chain data providers."""
    
    @abstractmethod
    def get_expirations(self, symbol: str) -> List[date]:
        """Get available expiration dates for symbol."""
        pass
    
    @abstractmethod
    def get_chain(
        self,
        symbol: str,
        expiration: date,
        option_type: str = 'call'
    ) -> pd.DataFrame:
        """
        Fetch options chain for symbol and expiration.
        
        Returns DataFrame with columns:
            - strike: float
            - bid: float
            - ask: float
            - last: float
            - volume: int
            - open_interest: int
            - delta: float (optional, may be NaN)
            - iv: float (optional, may be NaN)
        """
        pass
    
    @abstractmethod
    def get_iv_percentile(
        self,
        symbol: str,
        lookback_days: int = 252
    ) -> Optional[float]:
        """
        Get current IV percentile vs historical.
        Returns None if not available.
        """
        pass
```

### 8.3 Recommendation Output Schema

```python
from dataclasses import dataclass
from datetime import date
from typing import Optional, List, Dict

@dataclass
class RuleResult:
    rule_name: str
    passed: bool
    value: float
    threshold: float
    description: str

@dataclass
class StockRecommendation:
    action: str  # 'HOLD_QQQM', 'ALLOCATE', 'EXIT'
    ticker: Optional[str]
    allocation_pct: Optional[float]
    score: Optional[float]
    rules: List[RuleResult]

@dataclass 
class LeapsRecommendation:
    action: str  # 'NO_LEAPS', 'BUY_LEAPS', 'CHAIN_UNAVAILABLE'
    ticker: Optional[str]
    expiration: Optional[date]
    strike: Optional[float]
    estimated_price: Optional[float]
    target_delta: Optional[float]
    rules: List[RuleResult]

@dataclass
class DailyRecommendation:
    date: date
    data_timestamp: str
    stock: StockRecommendation
    leaps: LeapsRecommendation
    confidence_score: float
    rationale: str
    changes_from_yesterday: List[str]
```

---

## 9. UI Specifications

### 9.1 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  GROWTH SWITCH + LEAPS                           Dec 17, 2025 6:15p │
│  Data as of: Dec 17, 2025 4:00p ET                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                TODAY'S RECOMMENDATION                       │    │
│  │                                                             │    │
│  │    📊 HOLD QQQM (100%)                                      │    │
│  │                                                             │    │
│  │    No high-conviction opportunities today.                  │    │
│  │    Confidence: 92%                                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                LEAPS STATUS                                  │   │
│  │                                                              │   │
│  │    ⏸️  NO LEAPS TODAY                                        │   │
│  │                                                              │   │
│  │    Closest candidate: NVDA (Score: 68, needs 70)             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  TOP 5 WATCHLIST SCORES                          [View All →]       │
│  ┌──────┬───────┬────────────────────────────────────────────────┐  │
│  │ Rank │ Score │ Ticker │ Key Signal                            │  │
│  ├──────┼───────┼────────────────────────────────────────────────┤  │
│  │  1   │  72   │ NVDA   │ RS rising, vol compressed             │  │
│  │  2   │  68   │ AVGO   │ Trend aligned, RSI neutral            │  │
│  │  3   │  61   │ MSFT   │ RS flat, waiting for breakout         │  │
│  │  4   │  58   │ AMZN   │ Below 50 SMA, monitoring              │  │
│  │  5   │  54   │ META   │ RSI overbought, cooling off           │  │
│  └──────┴───────┴────────────────────────────────────────────────┘  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  WHAT CHANGED TODAY                                                 │
│  • NVDA score +4 (RS ratio improved)                                │
│  • AVGO BB width hit 20th percentile (volatility compressed)        │
│  • TSLA exited top 5 (weekly RSI fell below 50)                     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  [📈 Charts]  [⚙️ Settings]  [📋 Watchlist]  [🔬 Backtest] [📜 Log] │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Chart Requirements

**Daily Chart Panel:**
- Candlestick or OHLC bars
- 20 EMA (blue), 50 SMA (orange), 200 SMA (red) overlays
- Bollinger Bands (gray fill)
- Volume bars below
- 6-month default view, zoom to 1M/3M/1Y/All

**Weekly Chart Panel:**
- Same overlays as daily
- 2-year default view

**Relative Strength Panel:**
- Line chart of Ticker/QQQM ratio
- 10-week moving average of ratio
- Highlight rising/falling periods

**Indicator Panel:**
- RSI with 50 line highlighted
- BB Width with percentile annotation

### 9.3 Required UI Views

| View | Purpose |
|------|---------|
| Dashboard | Primary daily decision view (see layout above) |
| Ticker Detail | Deep dive on single ticker: all charts, all indicators, score breakdown, historical scores |
| Watchlist | Manage tickers, bulk view scores, tags |
| Settings | All configuration parameters with save/reset |
| Backtest | Run backtests, view results, compare runs |
| Recommendation Log | Historical recommendations, filterable by date/type |

---

## 10. Implementation Phases

### Phase 1: Core Infrastructure + Equity Signals (MVP)

**Deliverables:**
- SQLite database schema
- Config file parser
- MarketDataProvider interface + Yahoo adapter
- Indicator engine with all required indicators
- Scoring engine
- Basic recommendation engine (stock allocation only)
- CLI interface for testing
- Unit tests for indicators and scoring

**Exit Criteria:**
- Can add tickers to watchlist
- Fetches OHLCV and computes indicators
- Outputs "Hold QQQM" or "Allocate to X" with score and rationale
- Indicators match manual calculations

### Phase 2: Web UI + Full Stock Logic

**Deliverables:**
- Web UI (local server)
- Dashboard view
- Watchlist management view
- Settings view
- Exit signal logic
- Cooldown enforcement
- Recommendation persistence
- Recommendation log view

**Exit Criteria:**
- Full UI navigation working
- Can change settings via UI
- Exit signals evaluated and displayed
- Recommendation history viewable

### Phase 3: Backtesting

**Deliverables:**
- Backtester module
- Backtest configuration UI
- Results visualization
- Trade log export
- Performance comparison charts

**Exit Criteria:**
- Can run 5-year backtest
- Outputs all metrics (CAGR, Sharpe, etc.)
- Generates trade list
- Compares to QQQM buy-and-hold

### Phase 4: LEAPS Signals

**Deliverables:**
- OptionsDataProvider interface + Yahoo adapter
- LEAPS signal logic
- Contract selection logic
- LEAPS UI components
- IV percentile tracking (if available)

**Exit Criteria:**
- LEAPS signals trigger when conditions met
- Outputs exact contract (or target parameters if chain unavailable)
- LEAPS in backtest (delta approximation)

### Phase 5: Polish

**Deliverables:**
- Email notifications
- Additional data provider adapters
- Ticker detail view
- Chart interactivity
- Export functionality
- Error handling improvements
- Documentation

**Exit Criteria:**
- All FR and NFR requirements met
- Runs reliably on macOS, Windows, Linux
- User documentation complete

---

## 11. Testing Requirements

### Unit Tests

| Module | Test Coverage |
|--------|---------------|
| Indicator Engine | Each indicator calculation vs known values |
| Scoring Engine | Score computation with fixed inputs |
| Allocation Logic | Threshold and tier logic |
| Exit Logic | Each exit condition |
| LEAPS Selection | Contract selection rules |
| Data Validation | Edge cases (missing data, NaN, etc.) |

### Integration Tests

| Test | Description |
|------|-------------|
| Data Pipeline | Fetch → Store → Compute → Score |
| Recommendation Flow | Full daily cycle produces valid output |
| Backtest Consistency | Same config produces same results |
| Config Changes | Settings changes reflect in calculations |

### Manual Test Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| New ticker added | Fetches history, computes indicators, shows in watchlist |
| Data provider fails | Shows warning, uses cached data |
| Score crosses threshold | Recommendation changes, logged |
| All indicators computed | No NaN values in output |

---

## 12. Compliance

The application must display the following disclaimer persistently in the UI footer:

> **Disclaimer:** This application provides decision support only and does not constitute financial advice. Past performance does not guarantee future results. The user is solely responsible for all investment decisions. Data may be delayed or incomplete.

---

## 13. Glossary

| Term | Definition |
|------|------------|
| LEAPS | Long-Term Equity Anticipation Securities; options with expiration > 1 year |
| DTE | Days to Expiration |
| Delta | Option greek measuring price sensitivity to underlying |
| ITM | In The Money; call strike below current price |
| OHLCV | Open, High, Low, Close, Volume |
| RS | Relative Strength |
| BB | Bollinger Bands |
| EMA | Exponential Moving Average |
| SMA | Simple Moving Average |
| RSI | Relative Strength Index |
| ATR | Average True Range |
| ROC | Rate of Change |
| IV | Implied Volatility |

---

## 14. Success Metrics

The application is successful if:

1. **Functional:** Produces daily recommendations reliably without crashes or errors
2. **Accurate:** Indicator calculations match manual verification
3. **Usable:** User can understand and act on recommendations within 2 minutes of viewing dashboard
4. **Performant:** Daily update completes in < 30 seconds
5. **Strategic:** Backtest shows positive alpha vs QQQM buy-and-hold over 5-year period (primary goal)
