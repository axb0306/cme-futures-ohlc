# CME Futures OHLCV Data

Historical market data for CME micro/mini futures, downloaded from TopstepX API.

## Symbols

| Symbol | Name | Exchange |
|--------|------|----------|
| **MNQ** | Micro E-mini Nasdaq-100 | CME |
| **MES** | Micro E-mini S&P 500 | CME |
| **MGC** | Micro Gold | COMEX |
| **MCL** | Micro WTI Crude Oil | NYMEX |

## Timeframes

Each symbol folder contains:

| File | Timeframe | Description |
|------|-----------|-------------|
| `SYMBOL_tick_*.csv` | Tick | 1-tick bars |
| `SYMBOL_1min_*.csv` | 1 min | |
| `SYMBOL_5min_*.csv` | 5 min | |
| `SYMBOL_15min_*.csv` | 15 min | |
| `SYMBOL_30min_*.csv` | 30 min | |
| `SYMBOL_1h_*.csv` | 1 hour | |
| `SYMBOL_4h_*.csv` | 4 hours | |
| `SYMBOL_daily_*.csv` | Daily | |

## File Naming

```
SYMBOL_TIMEFRAME_STARTDATE_ENDDATE.csv
```

Example: `MNQ_5min_20260120_20260320.csv` — MNQ 5-minute bars from Jan 20 to Mar 20, 2026.

## CSV Format

```csv
datetime,open,high,low,close,volume
2026-01-20T18:00:00,21545.25,21548.50,21543.00,21547.75,142
```

All timestamps are in UTC.

## Auto-Update

Data is updated nightly via `update_data.py` (requires `config.json` with TopstepX API credentials — see `config.example.json`).

Schedule: **01:00 UTC+3 (22:00 UTC)**, Tuesday–Saturday.

## Setup

```bash
cp config.example.json config.json
# Edit config.json with your TopstepX API credentials
pip install requests
python3 update_data.py
```

## Data Source

All data is from [TopstepX](https://www.topstep.com/) via the ProjectX Gateway API.
