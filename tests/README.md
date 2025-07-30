# Tests Directory

This directory contains all test files for the Trade Bot Marketplace project, organized by category.

## Directory Structure

```
tests/
├── api/                    # API endpoint tests
│   ├── test_api_simple.py         # Basic API implementation tests
│   ├── test_api_endpoints.py      # API endpoint functionality tests
│   ├── test_api_integration.py    # Integration tests with mocks
│   ├── test_api_with_server.py    # FastAPI TestClient tests
│   ├── demo_api_functionality.py  # API functionality demonstration
│   └── final_test_summary.py      # Comprehensive test summary
├── bot_trading/           # Bot trading logic tests
│   ├── test_binance_bot.py        # Binance bot specific tests
│   └── test_futures_bot.py        # Futures trading bot tests
├── marketplace/           # Marketplace integration tests
│   └── test_marketplace_api.py    # Original marketplace API tests
└── integration/           # End-to-end integration tests
    └── (future integration tests)
```

## Test Categories

### 1. API Tests (`api/`)
- **test_api_simple.py**: Basic validation of schemas, enums, and functions
- **test_api_endpoints.py**: Database integration tests for API endpoints
- **test_api_integration.py**: Integration tests with mocked dependencies
- **test_api_with_server.py**: FastAPI TestClient-based tests
- **demo_api_functionality.py**: Comprehensive functionality demonstration
- **final_test_summary.py**: Complete workflow validation

### 2. Bot Trading Tests (`bot_trading/`)
- **test_binance_bot.py**: Tests for Binance-specific trading logic
- **test_futures_bot.py**: Tests for futures trading functionality

### 3. Marketplace Tests (`marketplace/`)
- **test_marketplace_api.py**: Original marketplace integration tests

### 4. Integration Tests (`integration/`)
- Reserved for future end-to-end integration tests

## Running Tests

### Prerequisites
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Specific Test Categories

```bash
# Run API tests
python tests/api/test_api_simple.py
python tests/api/demo_api_functionality.py
python tests/api/final_test_summary.py

# Run bot trading tests
python tests/bot_trading/test_binance_bot.py
python tests/bot_trading/test_futures_bot.py

# Run marketplace tests
python tests/marketplace/test_marketplace_api.py
```

### Run All Tests
```bash
# Run comprehensive test suite
python tests/api/final_test_summary.py
```

## Test Results Summary

### API Tests Status: ✅ ALL PASSED
- ✅ Schema validation
- ✅ Function availability
- ✅ Enum validation
- ✅ Validation rules
- ✅ Error handling

### Key APIs Tested
1. **POST /api/bots/register** - Bot registration ✅
2. **PUT /api/bots/update-registration/{id}** - Update registration ✅
3. **GET /api/bots/registrations/{principal_id}** - Get registrations ✅

## Test Coverage

- **Request/Response Schemas**: 100% validated
- **Authentication**: API key validation tested
- **Error Scenarios**: Comprehensive error handling
- **Integration**: ICP Marketplace compatibility
- **Validation Rules**: Timeframes, symbols, enums

## Notes

- All tests use virtual environment (.venv)
- Tests include both unit and integration scenarios
- Mock dependencies used where database access not available
- Comprehensive validation of marketplace bot registration APIs

## Contributing

When adding new tests:
1. Place in appropriate category directory
2. Follow naming convention: `test_*.py`
3. Include docstrings and comments
4. Update this README if adding new categories
