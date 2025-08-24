# GreytHR Attendance Automation - Web UI Dashboard

A modern FastAPI-based web interface for monitoring and managing the GreytHR attendance automation system.

## 🚀 Quick Start

1. **Setup the project:**
   ```bash
   ./scripts/setup.sh
   ```

2. **Start development server:**
   ```bash
   ./scripts/run_dev.sh
   ```

3. **Access the dashboard:**
   - Dashboard: http://127.0.0.1:8000
   - API Documentation: http://127.0.0.1:8000/docs
   - ReDoc: http://127.0.0.1:8000/redoc

## 📋 Features (Planned)

### Phase 1: Core Foundation ✅
- [x] FastAPI application with health checks
- [x] Configuration management
- [x] Project structure following established patterns
- [x] Development scripts

### Phase 2: Dashboard API (In Progress)
- [ ] Real-time status monitoring
- [ ] Integration with GreytHR state files
- [ ] System health checks

### Phase 3: Frontend UI (Planned)
- [ ] Responsive dashboard with Bootstrap 5
- [ ] Real-time status updates
- [ ] Service management controls

### Phase 4: Service Operations (Planned)
- [ ] Start/stop/restart GreytHR service
- [ ] Manual attendance operations
- [ ] Configuration management

### Phase 5: Historical Data (Planned)
- [ ] Activities history viewer
- [ ] Log file management
- [ ] Search and filtering

### Phase 6: Real-time Features (Planned)
- [ ] WebSocket integration
- [ ] Live log streaming
- [ ] Push notifications

## 🛠️ Project Structure

```
web_ui/
├── main.py                 # FastAPI application entry point
├── src/
│   ├── app_utils.py       # Application utilities
│   ├── logging_config.py  # Logging configuration
│   ├── dependencies.py    # FastAPI dependencies
│   └── database/
│       └── connection.py  # File system operations
├── conf/
│   ├── default_config.yaml      # Main configuration
│   ├── default-config.properties # Server properties
│   └── logging_config.yaml      # Logging setup
├── scripts/
│   ├── setup.sh          # Project setup
│   ├── run_dev.sh        # Development server
│   └── run_tests.sh      # Test runner
├── logs/                 # Application logs
└── requirements.txt      # Python dependencies
```

## ⚙️ Configuration

### Main Configuration (`conf/default_config.yaml`)
- Server settings (host, port)
- GreytHR project integration path
- UI preferences
- Logging configuration

### Properties Configuration (`conf/default-config.properties`)
- Server properties
- Security settings
- Cache configuration

### Environment Variables
- `WEBUI_HOST`: Override server host
- `WEBUI_PORT`: Override server port  
- `GREYTHR_PROJECT_PATH`: Path to GreytHR project
- `WEBUI_LOG_LEVEL`: Logging level

## 🔧 Development

### Prerequisites
- Python 3.8+
- GreytHR Attendance Automation project

### Setup Development Environment
```bash
# Clone and setup
cd web_ui
./scripts/setup.sh

# Start development server
./scripts/run_dev.sh
```

### Running Tests
```bash
# All tests
./scripts/run_tests.sh

# With coverage
./scripts/run_tests.sh coverage

# Fast tests only
./scripts/run_tests.sh fast
```

## 🏗️ Architecture

This project follows the established FastAPI patterns:
- **Controller-Repository-Routes-Schemas** pattern
- **Dependency injection** for services
- **Configuration management** via YAML/Properties files
- **Async file operations** for performance
- **Modular design** with feature-based modules

## 📖 API Documentation

Once running, visit:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 🔗 Integration

This web UI integrates with the existing GreytHR attendance automation by:
- Reading state from `state/current_state.json`
- Accessing historical data from `activities/` directory
- Viewing logs from `logs/` directory
- Controlling service via `greythr_service.sh`

## 📝 Phase Implementation Status

- **Phase 1**: ✅ Core Foundation Complete
- **Phase 2**: 🚧 Dashboard API (Next)
- **Phase 3**: ⏳ Frontend UI
- **Phase 4**: ⏳ Service Operations
- **Phase 5**: ⏳ Historical Data
- **Phase 6**: ⏳ Real-time Features

## 🤝 Contributing

This project follows the same patterns as the main GreytHR automation system. When adding new features:

1. Follow the Controller-Repository-Routes-Schemas pattern
2. Add appropriate tests
3. Update configuration as needed
4. Document new APIs in docstrings

## 📄 License

Same as the main GreytHR Attendance Automation project.
