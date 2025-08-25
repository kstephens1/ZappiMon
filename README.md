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
- Node.js 14+ (for npm scripts - optional but recommended)
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

   **Note**: The npm scripts are configured to use `python3` and `pip3` to work with macOS virtual environments where `python` might not be available.

**Important**: Always activate your virtual environment before running npm commands:
```bash
source .venv/bin/activate
npm run lint
```

3. Install dependencies:
   ```bash
   # Using npm (recommended)
   npm install
   
   # Or using pip directly
   pip3 install -r requirements.txt
   ```

4. Run tests (optional):
   ```bash
   # Using npm (recommended)
   npm test
   
   # Or using pytest directly
   python3 -m pytest test_zappimon.py -v
   ```

5. Configure environment variables:
   ```bash
   # Using npm (recommended)
   npm run env:setup
   
   # Or manually
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

### Quick Start

Run the monitoring script:

```bash
# Using npm (recommended)
npm start
# or
npm run dev
# or
npm run monitor

# Or using Python directly
python3 ZappiMon.py
```

### Available Commands

The project includes npm-style scripts for common development tasks:

#### 🚀 **Running the Application**
```bash
npm start          # Start ZappiMon
npm run dev        # Development mode (same as start)
npm run monitor    # Alternative command to run
npm run check      # Verify module loads correctly
```

#### 🧪 **Testing Commands**
```bash
npm test           # Run all tests with verbose output
npm run test:watch # Run tests with short traceback
npm run test:coverage # Run tests with code coverage
npm run test:unit  # Run only unit tests
npm run test:integration # Run only integration tests
```

#### 🛠️ **Development Commands**
```bash
npm run lint       # Run flake8 linting
npm run format     # Format code with black
npm run format:check # Check code formatting
npm run clean      # Clean Python cache files
npm run db:reset   # Remove database file
```

#### 📦 **Setup Commands**
```bash
npm install        # Install production dependencies
npm run install:dev # Install development dependencies
npm run setup      # Setup project (env + install)
npm run setup:dev  # Setup project for development
npm run env:setup  # Create .env file
```

#### 🆘 **Utility Commands**
```bash
npm run help       # Show all available commands
npm run version    # Display version information
```

### Alternative: Using Make

If you prefer Make over npm:
```bash
make help          # Show all commands
make run           # Run ZappiMon
make test          # Run tests
make install       # Install dependencies
make setup         # Setup project
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

#### Using npm (Recommended)
```bash
# Run all tests
npm test

# Run tests with short traceback (faster feedback)
npm run test:watch

# Run tests with code coverage
npm run test:coverage

# Run specific test types
npm run test:unit        # Unit tests only
npm run test:integration # Integration tests only
```

#### Using pytest directly
```bash
# Run all tests
python3 -m pytest test_zappimon.py -v

# Run specific test scenarios
python3 -m pytest test_zappimon.py::TestZappiMonIntegration::test_1200w_export_scenario -v -s
python3 -m pytest test_zappimon.py::TestZappiMonIntegration::test_1200w_import_scenario -v -s

# Run with coverage
python3 -m pytest test_zappimon.py --cov=ZappiMon --cov=database --cov-report=html --cov-report=term
```

#### Using Make
```bash
make test              # Run all tests
make test-watch        # Run tests with short traceback
make test-coverage     # Run tests with coverage
make test-unit         # Unit tests only
make test-integration  # Integration tests only
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
