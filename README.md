# ZappiMon

A Python monitoring tool for MyEnergi Zappi devices that tracks grid power flow and sends notifications for excessive exports via Pushover.

## Features

- Monitors MyEnergi Zappi device status via API
- Tracks grid power import/export in real-time
- Sends push notifications for excessive exports (>1000W)
- Secure credential management using environment variables
- Respects API rate limits and best practices

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
   pip install requests python-dotenv
   ```

4. Configure environment variables:
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
- Send notifications for excessive exports (>1000W)

## Output Examples

```
Importing: 60          # Normal power import
Exporting: -1500       # Power export
>>>>>>>Excessive Export Alert<<<<<<<  # Alert for exports >1000W
```

## Security

- All sensitive credentials are stored in the `.env` file
- The `.env` file is excluded from version control via `.gitignore`
- Never commit your actual credentials to the repository

## API Rate Limits

The script respects both MyEnergi and Pushover API rate limits:
- MyEnergi: Digest authentication with proper error handling
- Pushover: Respects 10,000 messages/month free tier limit
- Implements proper retry logic and error handling

## License

This project is for personal use. Please respect the terms of service for both MyEnergi and Pushover APIs.
