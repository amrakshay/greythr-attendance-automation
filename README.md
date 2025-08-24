# 🎯 GreytHR Attendance Automation

Automatically sign in and out of GreytHR at your configured times. Works on macOS and starts automatically when you log in.

## 🚀 Quick Setup

1. **Configure your credentials:**
   ```bash
   cp env.example .env
   # Edit .env with your GreytHR URL, username, and password
   ```

2. **Install and start:**
   ```bash
   ./greythr_service.sh --install
   ```

That's it! The automation will now:
- ✅ Start automatically when you log in to macOS
- ✅ Sign in at your configured time (e.g., 9:00 AM)
- ✅ Sign out at your configured time (e.g., 7:00 PM)
- ✅ Skip weekends automatically
- ✅ Retry if there are network issues
- ✅ Keep detailed logs

## ⚙️ Configuration (.env file)

```bash
# Basic Configuration
GREYTHR_URL=https://your-company.greythr.com
GREYTHR_USERNAME=your_username
GREYTHR_PASSWORD=your_password
SIGNIN_TIME=09:00
SIGNOUT_TIME=19:00
TEST_MODE=false  # Set to true for weekend testing

# Retry Configuration
RETRY_STRATEGY=exponential     # exponential or fixed
MAX_RETRY_ATTEMPTS=5          # Max retry attempts per action
BASE_RETRY_DELAY=300          # Base delay for exponential (seconds)
FIXED_RETRY_DELAY=300         # Fixed delay for fixed strategy (seconds)
```

### Retry Strategies

**Exponential Backoff (Default):**
- Delays increase: 5min → 15min → 45min → 135min → 405min
- Best for temporary network issues
- Reduces server load over time

**Fixed Delay:**
- Same delay for all retries: 5min → 5min → 5min → 5min → 5min
- Predictable retry intervals
- Good for rate-limited APIs

## 🛠️ Management

Use the service script for all management:
```bash
./greythr_service.sh
```

**Command Line Options:**
```bash
./greythr_service.sh --install    # Quick install everything
./greythr_service.sh --status     # Check status
./greythr_service.sh --restart    # Restart service
./greythr_service.sh --reset      # Reset (clean all data + restart)
./greythr_service.sh --stop       # Stop service
./greythr_service.sh --logs       # View logs
./greythr_service.sh --uninstall  # Remove service
```

**Or run interactively:**
- Run `./greythr_service.sh` for menu with all options

## 📊 Monitoring

- **Logs**: Check `logs/` directory for detailed logs
- **Status**: View `state/current_state.json` for real-time status
- **Dashboard**: The JSON state file is perfect for building monitoring dashboards

## 🚨 Troubleshooting

**Service won't start?**
- Make sure `.env` file exists and has correct credentials
- Check logs: `./greythr_service.sh --logs`

**Multiple instance error?**
- Remove lock file: `rm greythr_attendance.lock`

**Need to test on weekend?**
- Set `TEST_MODE=true` in .env file
- Restart service: `./greythr_service.sh --restart`

## 🔒 Features

- **Single Instance Protection**: Only one copy runs at a time
- **Automatic Startup**: Starts when you log in to macOS
- **Smart Retry**: Exponential backoff for failed attempts
- **Weekend Skip**: Automatically skips weekends (unless test mode)
- **Comprehensive Logging**: All operations logged with timestamps
- **Real-time State**: JSON file with current status for monitoring

## 📁 Files

- `greythr_service.sh` - Main script (install, manage, monitor)
- `.env` - Your configuration (create from `env.example`)
- `logs/` - All log files
- `state/` - Real-time status data
- `activities/` - Daily attendance records

---

**Need help?** Run `./greythr_service.sh --help` for detailed information.
