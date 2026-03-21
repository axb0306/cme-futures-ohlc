# CME Futures OHLCV Data

Historical market data for 51 CME/COMEX/NYMEX/CBOT futures contracts, downloaded from TopstepX API. Updated nightly.

## Symbols

### Micro Indices
| Symbol | Name |
|--------|------|
| **MNQ** | Micro E-mini Nasdaq-100 |
| **MES** | Micro E-mini S&P 500 |
| **MYM** | Micro E-mini Dow Jones |
| **M2K** | Micro E-mini Russell 2000 |

### E-mini Indices
| Symbol | Name |
|--------|------|
| **NQ** | E-mini Nasdaq-100 |
| **ES** | E-mini S&P 500 |
| **YM** | E-mini Dow Jones |
| **RTY** | E-mini Russell 2000 |

### Metals
| Symbol | Name |
|--------|------|
| **GC** | Gold |
| **MGC** | Micro Gold |
| **SI** | Silver |
| **SIL** | Micro Silver |
| **HG** | Copper |
| **MHG** | Micro Copper |
| **PL** | Platinum |

### Energy
| Symbol | Name |
|--------|------|
| **CL** | Crude Oil (WTI) |
| **MCL** | Micro Crude Oil |
| **QM** | E-mini Crude Oil |
| **NG** | Natural Gas |
| **MNG** | Micro Natural Gas |
| **QG** | E-mini Natural Gas |
| **HO** | Heating Oil (ULSD) |
| **RB** | RBOB Gasoline |

### Currencies
| Symbol | Name |
|--------|------|
| **6E** | Euro FX |
| **6B** | British Pound |
| **6J** | Japanese Yen |
| **6C** | Canadian Dollar |
| **6A** | Australian Dollar |
| **6S** | Swiss Franc |
| **6N** | New Zealand Dollar |
| **6M** | Mexican Peso |
| **M6E** | E-Micro EUR/USD |
| **M6B** | E-Micro GBP/USD |
| **M6A** | E-Micro AUD/USD |
| **E7** | E-mini Euro FX |

### Treasuries
| Symbol | Name |
|--------|------|
| **ZB** | 30-Year Treasury Bond |
| **ZN** | 10-Year Treasury Note |
| **ZF** | 5-Year Treasury Note |
| **ZT** | 2-Year Treasury Note |
| **TN** | Ultra 10-Year Treasury Note |
| **UB** | Ultra Treasury Bond |

### Agriculture
| Symbol | Name |
|--------|------|
| **ZC** | Corn |
| **ZS** | Soybeans |
| **ZW** | Wheat |
| **ZL** | Soybean Oil |
| **ZM** | Soybean Meal |
| **HE** | Lean Hogs |
| **LE** | Live Cattle |

### Other
| Symbol | Name |
|--------|------|
| **NKD** | Nikkei 225 |
| **MBT** | Micro Bitcoin |
| **MET** | Micro Ether |

## Timeframes

Each symbol folder contains 8 timeframes:

| File | Timeframe |
|------|-----------|
| `SYMBOL_tick_*.csv` | 1-tick bars |
| `SYMBOL_1min_*.csv` | 1 minute |
| `SYMBOL_5min_*.csv` | 5 minutes |
| `SYMBOL_15min_*.csv` | 15 minutes |
| `SYMBOL_30min_*.csv` | 30 minutes |
| `SYMBOL_1h_*.csv` | 1 hour |
| `SYMBOL_4h_*.csv` | 4 hours |
| `SYMBOL_daily_*.csv` | Daily |

## File Naming

```
SYMBOL_TIMEFRAME_STARTDATE_ENDDATE.csv
```

Example: `MNQ_5min_20260120_20260320.csv` — MNQ 5-minute bars from Jan 20 to Mar 20, 2026.

End date in filename is automatically updated when new data is appended.

## CSV Format

```csv
datetime,open,high,low,close,volume
2026-01-20T18:00:00,21545.25,21548.50,21543.00,21547.75,142
```

All timestamps are in UTC.

## Auto-Update

Data is updated nightly via cron on a VPS. The cron job runs:

```
git pull && python3 update_data.py
```

This ensures the latest script is always used before downloading new data.

Schedule: **23:30 UTC (02:30 UTC+3)**, Monday–Friday (covers Tuesday–Saturday market closes).

The script appends new bars to existing CSV files and renames them with the updated end date. Changes are automatically committed and pushed to this repository.

## Setup

```bash
cp config.example.json config.json
# Edit config.json with your TopstepX API credentials
pip install requests
python3 update_data.py
```

### Cron setup (VPS)

```bash
crontab -e
# Add:
30 23 * * 1-5 cd /path/to/cme-futures-ohlc && git pull && python3 update_data.py >> update.log 2>&1
```

## Data Source

All data is from [TopstepX](https://www.topstep.com/) via the [ProjectX Gateway API](https://gateway.docs.projectx.com/).
