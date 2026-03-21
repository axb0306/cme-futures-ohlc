#!/usr/bin/env python3
"""
Nightly updater — downloads latest bars from TopstepX API,
appends to existing CSVs, and renames files with updated end date.
Pushes changes to git@github.com:axb0306/cme-futures-ohlc.git

Scheduled: 01:00 UTC+3 (22:00 UTC) Tue–Sat
"""
import requests
import time
import os
import glob
import re
import subprocess
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

import json

_config_path = os.path.join(SCRIPT_DIR, "config.json")
if not os.path.exists(_config_path):
    raise FileNotFoundError("config.json not found — copy config.example.json and fill in credentials")
with open(_config_path) as _f:
    _cfg = json.load(_f)

API_BASE = _cfg.get("api_base", "https://api.topstepx.com/api")
USERNAME = _cfg["username"]
API_KEY = _cfg["api_key"]

# Current front-month contracts (update when contracts roll)
CONTRACTS = {
    "MNQ": "CON.F.US.MNQ.M26",
    "MES": "CON.F.US.MES.M26",
    "MGC": "CON.F.US.MGC.J26",
}

TIMEFRAMES = [
    ("1min",  2, 1),
    ("5min",  2, 5),
    ("15min", 2, 15),
    ("30min", 2, 30),
    ("1h",    3, 1),
    ("4h",    3, 4),
    ("daily", 4, 1),
]


def authenticate(session):
    r = session.post(f"{API_BASE}/Auth/loginKey", json={
        'userName': USERNAME, 'apiKey': API_KEY
    })
    data = r.json()
    if not data.get('success'):
        raise Exception(f"Auth failed: {data}")
    session.headers['Authorization'] = f"Bearer {data['token']}"
    print("Auth OK")


def fetch_bars(session, contract_id, start, end, unit, unit_number):
    payload = {
        "contractId": contract_id, "live": False,
        "startTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "unit": unit, "unitNumber": unit_number,
        "limit": 20000, "includePartialBar": False,
    }
    for attempt in range(3):
        r = session.post(f"{API_BASE}/History/retrieveBars", json=payload)
        if r.status_code == 429:
            time.sleep(2 ** attempt + 2)
            continue
        if r.status_code != 200:
            return []
        data = r.json()
        if data.get('success'):
            return data.get('bars', [])
        return []
    return []


def find_existing_file(symbol, tf_label):
    """Find existing CSV matching pattern SYMBOL_TF_STARTDATE_ENDDATE.csv"""
    pattern = os.path.join(SCRIPT_DIR, symbol, f"{symbol}_{tf_label}_*_*.csv")
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    return None


def get_last_datetime(filepath):
    """Read the last line of CSV to get the most recent bar timestamp."""
    with open(filepath, 'rb') as f:
        # Seek to end, read backwards to find last newline
        f.seek(0, 2)
        pos = f.tell() - 2
        while pos > 0:
            f.seek(pos)
            if f.read(1) == b'\n':
                break
            pos -= 1
        last_line = f.readline().decode().strip()
    if last_line and not last_line.startswith('datetime'):
        ts = last_line.split(',')[0]
        # Parse: 2026-03-20T20:55:00
        return datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    return None


def get_start_date_from_filename(filepath):
    """Extract start date from filename like MNQ_5min_20260120_20260320.csv"""
    m = re.search(r'_(\d{8})_\d{8}\.csv$', filepath)
    if m:
        return m.group(1)
    return None


def main():
    now = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"TopstepX Data Update — {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    session = requests.Session()
    session.headers.update({'Content-Type': 'application/json', 'accept': 'text/plain'})
    authenticate(session)

    updated_files = []

    for symbol, contract_id in CONTRACTS.items():
        sym_dir = os.path.join(SCRIPT_DIR, symbol)
        os.makedirs(sym_dir, exist_ok=True)

        for tf_label, unit, unit_number in TIMEFRAMES:
            existing = find_existing_file(symbol, tf_label)

            if existing:
                last_dt = get_last_datetime(existing)
                start_date_str = get_start_date_from_filename(existing)
                if last_dt:
                    # Fetch from last bar + 1 unit
                    fetch_start = last_dt + timedelta(minutes=1)
                else:
                    fetch_start = now - timedelta(days=3)
            else:
                # No existing file — fetch last 3 days
                fetch_start = now - timedelta(days=3)
                start_date_str = fetch_start.strftime("%Y%m%d")

            fetch_end = now
            if fetch_start >= fetch_end:
                print(f"  {symbol} {tf_label}: already up to date")
                continue

            # Fetch new bars
            all_new = []
            chunk_start = fetch_start
            while chunk_start < fetch_end:
                chunk_end = min(chunk_start + timedelta(days=13), fetch_end)
                bars = fetch_bars(session, contract_id, chunk_start, chunk_end, unit, unit_number)
                if bars:
                    all_new.extend(bars)
                chunk_start = chunk_end
                time.sleep(0.3)

            if not all_new:
                print(f"  {symbol} {tf_label}: no new bars")
                continue

            # Deduplicate
            all_new.sort(key=lambda b: b['t'])
            seen = set()
            unique = []

            # Load existing timestamps to avoid dupes
            if existing:
                with open(existing) as f:
                    for line in f:
                        if line.startswith('datetime'):
                            continue
                        ts = line.split(',')[0]
                        seen.add(ts)

            for b in all_new:
                ts = b['t'].replace('+00:00', '').rstrip('Z')
                if ts not in seen:
                    seen.add(ts)
                    unique.append(b)

            if not unique:
                print(f"  {symbol} {tf_label}: no new unique bars")
                continue

            # Append to existing file
            if existing:
                with open(existing, 'a') as f:
                    for b in unique:
                        ts = b['t'].replace('+00:00', '').rstrip('Z')
                        f.write(f"{ts},{b['o']},{b['h']},{b['l']},{b['c']},{b.get('v',0)}\n")
            else:
                existing = os.path.join(sym_dir, f"{symbol}_{tf_label}_temp.csv")
                with open(existing, 'w') as f:
                    f.write("datetime,open,high,low,close,volume\n")
                    for b in unique:
                        ts = b['t'].replace('+00:00', '').rstrip('Z')
                        f.write(f"{ts},{b['o']},{b['h']},{b['l']},{b['c']},{b.get('v',0)}\n")
                start_date_str = unique[0]['t'][:10].replace('-', '')

            # Get new end date from last bar
            last_bar_ts = unique[-1]['t'].replace('+00:00', '').rstrip('Z')
            new_end = last_bar_ts[:10].replace('-', '')

            # Rename file with updated end date
            new_name = os.path.join(sym_dir, f"{symbol}_{tf_label}_{start_date_str}_{new_end}.csv")
            if existing != new_name:
                os.rename(existing, new_name)
                updated_files.append(new_name)

            print(f"  {symbol} {tf_label}: +{len(unique)} bars → {os.path.basename(new_name)}")

    # Git commit and push
    if updated_files:
        print(f"\nPushing {len(updated_files)} updated files to GitHub...")
        subprocess.run(["git", "add", "-A"], check=True)
        msg = f"Update {now.strftime('%Y-%m-%d')}: {len(updated_files)} files updated"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Push OK!")
        else:
            print(f"Push failed: {result.stderr}")
    else:
        print("\nNo updates needed.")

    print("Done!")


if __name__ == "__main__":
    main()
