# QuantEdge

Research-only daily momentum backtest using MarketDataHub PostgreSQL.

## Run

Install the free PostgreSQL driver psycopg (version 3) in the project environment.
Set MKD_DSN to a dedicated read-only MKD connection using local configuration.
Provide an exchange-calendar session manifest (JSON array), for example:

```json
[{"day":"2026-11-16","opens_at":"2026-11-16T09:00:00+01:00","cutoff":"2026-11-16T19:00:00+01:00"}]
```

Use actual exchange sessions and explicit timezone-aware timestamps; the example is illustrative, not a complete calendar.

```bash
python -m quantedge.research_cli --instrument-id "$INSTRUMENT_ID" --provider "$PROVIDER" --currency EUR --history-start 2024-01-01 --sessions sessions.json
python -m unittest discover -s tests
```

Only qualified MKD revisions available at each cutoff are eligible. Missing execution sessions abort. Historical signals are simulated at the next recorded open. The strategy needs 253 observations and uses positive 12-1 momentum. The report is research-only, with no broker integration. Real PostgreSQL acceptance, calendar completeness, and provenance coverage must be verified before operational use.
