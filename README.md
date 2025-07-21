# Trading Bot Marketplace

A comprehensive backend marketplace for trading bot rental.

## Project Structure

```
bot_marketplace/
├── core/                 # Core application files
│   ├── main.py          # FastAPI application
│   ├── tasks.py         # Celery background tasks
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic schemas
│   ├── crud.py          # Database operations
│   ├── database.py      # Database configuration
│   ├── security.py      # Authentication
│   ├── bot_manager.py   # Bot lifecycle management
│   └── bot_base_classes.py # Base classes loader
├── services/            # External services
│   ├── binance_integration.py
│   ├── exchange_factory.py
│   ├── s3_manager.py
│   ├── sendgrid_email_service.py
│   ├── gmail_smtp_service.py
│   └── email_templates.py
├── utils/               # Utility functions
│   ├── celery_app.py
│   ├── run_beat.py
│   └── run_celery.py
├── api/                 # API endpoints
│   └── endpoints/
├── bots/                # Bot SDK and examples
│   └── bot_sdk/
├── config/              # Configuration files
│   ├── docker.env
│   └── requirements.txt
├── scripts/             # Utility scripts
├── tests/               # Test files
├── docs/                # Documentation
├── logs/                # Log files
├── temp/                # Temporary files
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Quick Start

```bash
# Start with Docker
docker-compose up -d

# Or run manually
pip install -r config/requirements.txt
python main.py
python utils/run_celery.py
python utils/run_beat.py
```

## Documentation

See `docs/` folder for detailed documentation.
