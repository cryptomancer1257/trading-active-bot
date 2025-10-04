# Migration 028: Update Exchange Type Enum

## What This Does
Updates `exchange_type` enum to:
- ❌ Remove: COINBASE
- ✅ Add: OKX, BITGET, MULTI

## Run Migration

```bash
# Method 1: Direct MySQL
mysql -u botuser -pbotpassword123 -h 127.0.0.1 -P 3307 -D bot_marketplace < migrations/versions/028_update_exchange_type_enum.sql

# Method 2: Using source command
mysql -u botuser -pbotpassword123 -h 127.0.0.1 -P 3307 -D bot_marketplace
> source migrations/versions/028_update_exchange_type_enum.sql;
> exit;
```

## Verify

```bash
mysql -u botuser -pbotpassword123 -h 127.0.0.1 -P 3307 -D bot_marketplace -e "
SHOW COLUMNS FROM bots WHERE Field='exchange_type';
"
```

Expected output:
```
Field          | Type                                                | Null | Key | Default | Extra
exchange_type  | enum('BINANCE','BYBIT','OKX','BITGET','HUOBI','KRAKEN','MULTI') | YES  |     | BINANCE | 
```

## After Migration
Restart your FastAPI server:
```bash
# Kill current server (Ctrl+C)
# Then restart
```

## Rollback (if needed)
```sql
ALTER TABLE bots 
MODIFY COLUMN exchange_type ENUM(
  'BINANCE',
  'COINBASE',
  'KRAKEN',
  'BYBIT',
  'HUOBI'
) DEFAULT 'BINANCE';
```
