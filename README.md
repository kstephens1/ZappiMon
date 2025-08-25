# ZappiMon

A Python monitoring tool for MyEnergi Zappi devices that tracks grid power flow and sends notifications for excessive exports via Pushover.

## Features

- Monitors MyEnergi Zappi device status via API
- Tracks grid power import/export in real-time
- Stores all readings in SQLite database with timestamps
- Provides 24-hour statistics and trends
- Sends push notifications for excessive exports (>1000W)
- Secure credential management using environment variables
- Respects API rate limits and best practices
- Comprehensive test suite with pytest

## Setup

### Prerequisites

- Python 3.7+
- MyEnergi account with Zappi device
- Pushover account and app token

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ZappiMon
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run tests (optional):
   ```bash
   python -m pytest test_zappimon.py -v
   ```

5. Configure environment variables:
   ```bash
   cp .env.example .env  # If example exists
   # Edit .env with your credentials
   ```

### Configuration

Create a `.env` file in the project root with the following variables:

```env
# MyEnergi API Credentials
MYENERGI_USERNAME=your_myenergi_username
MYENERGI_PASSWORD=your_myenergi_password

# Pushover API Configuration
PUSHOVER_APP_TOKEN=your_pushover_app_token
PUSHOVER_USER_KEY=your_pushover_user_key
```

### Getting API Credentials

#### MyEnergi
- Your MyEnergi username and password are used for digest authentication
- These are the same credentials you use to log into the MyEnergi app

#### Pushover
1. Create an account at [pushover.net](https://pushover.net)
2. Create a new application to get an API token
3. Copy your user key from the Pushover dashboard

## Usage

Run the monitoring script:

```bash
python ZappiMon.py
```

The script will:
- Connect to your Zappi device
- Display current grid power flow (import/export)
- Store each reading in the database with timestamp
- Show 24-hour statistics (average, range, import/export periods)
- Send notifications for excessive exports (>1000W)

## Output Examples

```
Importing: 60          # Normal power import
Exporting: -1500       # Power export
>>>>>>>Excessive Export Alert<<<<<<<  # Alert for exports >1000W

--- Last 24 Hours Statistics ---
Total readings: 45
Average grid: 23.4W
Range: -1200W to 800W
Import periods: 32, Export periods: 13
```

## Security

- All sensitive credentials are stored in the `.env` file
- The `.env` file is excluded from version control via `.gitignore`
- Never commit your actual credentials to the repository

## Testing

The project includes a comprehensive test suite using pytest:

### Running Tests
```bash
# Run all tests
python -m pytest test_zappimon.py -v

# Run specific test scenarios
python -m pytest test_zappimon.py::TestZappiMonIntegration::test_1200w_export_scenario -v -s
python -m pytest test_zappimon.py::TestZappiMonIntegration::test_1200w_import_scenario -v -s
```

### Test Coverage
- **Unit Tests**: Individual function testing (excessive export tracking, notifications, database operations)
- **Integration Tests**: Complete workflow testing with mocked API responses
- **Mock Scenarios**: 1200W export and import scenarios
- **Database Testing**: SQLite operations with temporary databases
- **API Mocking**: MyEnergi and Pushover API responses

## API Rate Limits

The script respects both MyEnergi and Pushover API rate limits:
- MyEnergi: Digest authentication with proper error handling
- Pushover: Respects 10,000 messages/month free tier limit
- Implements proper retry logic and error handling

## License

This project is for personal use. Please respect the terms of service for both MyEnergi and Pushover APIs.
