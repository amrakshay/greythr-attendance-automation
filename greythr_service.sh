#!/bin/bash

# GreytHR Attendance Automation - Service Management Script
# Complete installation and management for macOS startup service

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="com.greythr.attendance"
PLIST_FILE="$SERVICE_NAME.plist"
PLIST_TEMPLATE="$SERVICE_NAME.plist.template"
LAUNCHAGENTS_DIR="$HOME/Library/LaunchAgents"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🎯 GreytHR Attendance Automation${NC}"
echo -e "${BLUE}================================${NC}"

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if service is loaded
is_service_loaded() {
    launchctl list | grep -q "$SERVICE_NAME" 2>/dev/null
}

# Function to check if service is running
is_service_running() {
    if is_service_loaded; then
        local status=$(launchctl list "$SERVICE_NAME" 2>/dev/null | grep "PID" | awk '{print $3}')
        [[ "$status" != "-" ]] && [[ "$status" != "0" ]]
    else
        false
    fi
}

# Quick installation function (combines both scripts)
quick_install() {
    print_info "Starting quick installation..."
    echo ""
    
    print_info "📁 Project location: $SCRIPT_DIR"
    
    # Check prerequisites
    print_info "Checking prerequisites..."
    
    # Check if .env file exists
    if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
        print_error ".env file not found!"
        echo "Please create your .env file first:"
        echo "1. Copy the example: cp env.example .env"
        echo "2. Edit .env with your GreytHR credentials"
        return 1
    fi
    print_success ".env file found"
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        return 1
    fi
    print_success "Python 3 found: $(python3 --version)"
    
    # Check/create virtual environment
    if [[ ! -d "$SCRIPT_DIR/.venv" ]]; then
        print_info "Creating virtual environment..."
        cd "$SCRIPT_DIR"
        python3 -m venv .venv
        print_success "Virtual environment created"
    fi
    
    # Install dependencies
    print_info "Installing dependencies..."
    cd "$SCRIPT_DIR"
    source .venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    print_success "Dependencies installed"
    
    # Test the script
    print_info "Testing the script..."
    if python3 greythr_api.py --help > /dev/null 2>&1; then
        print_success "Script is working correctly"
    else
        print_error "Script test failed"
        return 1
    fi
    
    # Install service
    install_service_internal
    
    echo ""
    print_success "🎉 Installation completed!"
    echo ""
    echo "What happens next:"
    echo "• The service will automatically start when you log in"
    echo "• It will sign in/out at your configured times"
    echo "• Logs are stored in: $SCRIPT_DIR/logs/"
    echo "• Real-time status: $SCRIPT_DIR/state/current_state.json"
    echo ""
    print_info "Use this script for all management (run without arguments to see menu)"
}

# Internal service installation (shared by quick install and manual install)
install_service_internal() {
    print_info "Installing macOS startup service..."
    
    # Create LaunchAgents directory if it doesn't exist
    mkdir -p "$LAUNCHAGENTS_DIR"
    
    # Generate plist file from template with current directory paths
    if [[ -f "$SCRIPT_DIR/$PLIST_TEMPLATE" ]]; then
        print_info "Generating service configuration from template..."
        # Replace template placeholder with actual project path
        sed "s|{{PROJECT_PATH}}|$SCRIPT_DIR|g" "$SCRIPT_DIR/$PLIST_TEMPLATE" > "$LAUNCHAGENTS_DIR/$PLIST_FILE"
        print_success "Service configuration generated for path: $SCRIPT_DIR"
    else
        print_error "Service template file ($PLIST_TEMPLATE) not found!"
        print_info "Expected location: $SCRIPT_DIR/$PLIST_TEMPLATE"
        return 1
    fi
    
    # Load the service
    if launchctl load "$LAUNCHAGENTS_DIR/$PLIST_FILE" 2>/dev/null; then
        print_success "Service installed and started successfully!"
    else
        print_error "Failed to install service"
        return 1
    fi
    
    # Wait a moment and check status
    sleep 2
    if is_service_running; then
        print_success "Service is running!"
    else
        print_warning "Service installed but may not be running. Check logs for details."
    fi
    
    print_info "Service will now start automatically when you log in."
    print_info "Logs are stored in: $SCRIPT_DIR/logs/"
}

# Regular installation function (for menu option)
install_service() {
    print_info "Installing GreytHR Attendance Automation as startup service..."
    
    # Check if .env file exists
    if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
        print_error ".env file not found!"
        print_info "Please create a .env file with your GreytHR credentials first:"
        print_info "cp env.example .env"
        print_info "Then edit .env with your actual credentials"
        return 1
    fi
    
    # Check if virtual environment exists
    if [[ ! -d "$SCRIPT_DIR/.venv" ]]; then
        print_error "Virtual environment not found!"
        print_info "Please create and activate the virtual environment first:"
        print_info "python3 -m venv .venv"
        print_info "source .venv/bin/activate"
        print_info "pip install -r requirements.txt"
        return 1
    fi
    
    install_service_internal
}

# Stop service function
stop_service() {
    print_info "Stopping GreytHR Attendance service..."
    
    if is_service_loaded; then
        if launchctl stop "$SERVICE_NAME" 2>/dev/null; then
            print_success "Service stopped successfully!"
        else
            print_warning "Service may have already been stopped"
        fi
    else
        print_warning "Service is not loaded"
    fi
}

# Start service function
start_service() {
    print_info "Starting GreytHR Attendance service..."
    
    if is_service_loaded; then
        if launchctl start "$SERVICE_NAME" 2>/dev/null; then
            print_success "Service started successfully!"
        else
            print_error "Failed to start service"
        fi
    else
        print_error "Service is not installed. Please install it first."
    fi
}

# Restart service function
restart_service() {
    print_info "Restarting GreytHR Attendance service..."
    stop_service
    sleep 2
    start_service
}

# Uninstall service function
uninstall_service() {
    print_info "Uninstalling GreytHR Attendance service..."
    
    if is_service_loaded; then
        # Stop and unload the service
        launchctl stop "$SERVICE_NAME" 2>/dev/null || true
        if launchctl unload "$LAUNCHAGENTS_DIR/$PLIST_FILE" 2>/dev/null; then
            print_success "Service unloaded successfully!"
        fi
    fi
    
    # Remove the plist file
    if [[ -f "$LAUNCHAGENTS_DIR/$PLIST_FILE" ]]; then
        rm "$LAUNCHAGENTS_DIR/$PLIST_FILE"
        print_success "Service configuration removed!"
    fi
    
    # Remove lock file if it exists
    if [[ -f "$SCRIPT_DIR/greythr_attendance.lock" ]]; then
        rm "$SCRIPT_DIR/greythr_attendance.lock"
        print_success "Lock file removed!"
    fi
    
    print_success "Service uninstalled completely!"
}

# Reset service function
reset_service() {
    print_info "Resetting GreytHR Attendance service..."
    print_warning "This will remove ALL accumulated data (logs, activities, state)"
    
    # Stop the service first
    if is_service_loaded; then
        print_info "Stopping service..."
        launchctl stop "$SERVICE_NAME" 2>/dev/null || true
        sleep 2
    fi
    
    # Remove lock file if it exists
    if [[ -f "$SCRIPT_DIR/greythr_attendance.lock" ]]; then
        rm "$SCRIPT_DIR/greythr_attendance.lock"
        print_success "Lock file removed"
    fi
    
    # Clean up data directories
    local dirs_cleaned=0
    
    # Clean logs directory
    if [[ -d "$SCRIPT_DIR/logs" ]] && [[ -n "$(ls -A "$SCRIPT_DIR/logs" 2>/dev/null)" ]]; then
        print_info "Cleaning logs directory..."
        rm -rf "$SCRIPT_DIR/logs"/*
        print_success "Logs directory cleaned"
        ((dirs_cleaned++))
    fi
    
    # Clean activities directory
    if [[ -d "$SCRIPT_DIR/activities" ]] && [[ -n "$(ls -A "$SCRIPT_DIR/activities" 2>/dev/null)" ]]; then
        print_info "Cleaning activities directory..."
        rm -rf "$SCRIPT_DIR/activities"/*
        print_success "Activities directory cleaned"
        ((dirs_cleaned++))
    fi
    
    # Clean state directory
    if [[ -d "$SCRIPT_DIR/state" ]] && [[ -n "$(ls -A "$SCRIPT_DIR/state" 2>/dev/null)" ]]; then
        print_info "Cleaning state directory..."
        rm -rf "$SCRIPT_DIR/state"/*
        print_success "State directory cleaned"
        ((dirs_cleaned++))
    fi
    
    if [[ $dirs_cleaned -eq 0 ]]; then
        print_info "No data files found to clean"
    else
        print_success "Cleaned $dirs_cleaned data directories"
    fi
    
    # Restart the service if it was loaded
    if is_service_loaded; then
        print_info "Restarting service with clean slate..."
        launchctl start "$SERVICE_NAME" 2>/dev/null
        sleep 2
        
        if is_service_running; then
            print_success "Service restarted successfully!"
        else
            print_warning "Service may not have started properly. Check logs for details."
        fi
    else
        print_warning "Service is not installed. Use --install to set it up first."
    fi
    
    print_success "🎉 Reset completed! Service is running with fresh data."
}

# Status function
check_status() {
    print_info "Checking GreytHR Attendance service status..."
    echo ""
    
    if is_service_loaded; then
        print_success "Service is installed"
        
        if is_service_running; then
            local pid=$(launchctl list "$SERVICE_NAME" 2>/dev/null | grep "PID" | awk '{print $3}')
            print_success "Service is running (PID: $pid)"
        else
            print_warning "Service is installed but not running"
        fi
        
        # Show last few log entries if available
        local log_file="$SCRIPT_DIR/logs/launchd_stdout.log"
        if [[ -f "$log_file" ]]; then
            echo ""
            print_info "Recent log entries:"
            tail -5 "$log_file" | sed 's/^/  /'
        fi
    else
        print_error "Service is not installed"
    fi
    
    # Check for lock file
    if [[ -f "$SCRIPT_DIR/greythr_attendance.lock" ]]; then
        local lock_pid=$(cat "$SCRIPT_DIR/greythr_attendance.lock" 2>/dev/null || echo "unknown")
        print_info "Lock file exists (PID: $lock_pid)"
    fi
    
    # Check state file
    if [[ -f "$SCRIPT_DIR/state/current_state.json" ]]; then
        print_info "State file exists - dashboard data available"
    fi
}

# View logs function
view_logs() {
    local log_files=()
    
    # Find available log files
    [[ -f "$SCRIPT_DIR/logs/launchd_stdout.log" ]] && log_files+=("stdout")
    [[ -f "$SCRIPT_DIR/logs/launchd_stderr.log" ]] && log_files+=("stderr")
    [[ -f "$SCRIPT_DIR/logs/greythr_attendance_$(date +%Y-%m-%d).log" ]] && log_files+=("application")
    
    if [[ ${#log_files[@]} -eq 0 ]]; then
        print_warning "No log files found"
        return
    fi
    
    echo ""
    echo "Available log files:"
    for i in "${!log_files[@]}"; do
        echo "$((i+1)). ${log_files[i]}"
    done
    echo "$((${#log_files[@]}+1)). All logs (combined)"
    echo ""
    
    read -p "Choose log file to view (1-$((${#log_files[@]}+1))): " choice
    
    case $choice in
        1) [[ -f "$SCRIPT_DIR/logs/launchd_stdout.log" ]] && tail -f "$SCRIPT_DIR/logs/launchd_stdout.log" ;;
        2) [[ -f "$SCRIPT_DIR/logs/launchd_stderr.log" ]] && tail -f "$SCRIPT_DIR/logs/launchd_stderr.log" ;;
        3) [[ -f "$SCRIPT_DIR/logs/greythr_attendance_$(date +%Y-%m-%d).log" ]] && tail -f "$SCRIPT_DIR/logs/greythr_attendance_$(date +%Y-%m-%d).log" ;;
        $((${#log_files[@]}+1)))
            print_info "Showing combined logs (Ctrl+C to exit)..."
            tail -f "$SCRIPT_DIR/logs/"*.log 2>/dev/null || print_warning "No log files to tail"
            ;;
        *) print_error "Invalid choice" ;;
    esac
}

# Edit configuration function
edit_config() {
    local config_file="$SCRIPT_DIR/.env"
    
    if [[ -f "$config_file" ]]; then
        print_info "Opening configuration file for editing..."
        ${EDITOR:-vi} "$config_file"
        print_info "Configuration updated. Restart the service to apply changes."
    else
        print_error "Configuration file not found: $config_file"
        print_info "Create it from the template: cp env.example .env"
    fi
}

# Help function
show_help() {
    echo ""
    print_info "GreytHR Attendance Automation - Help"
    echo "===================================="
    echo ""
    echo "This script manages the GreytHR attendance automation as a macOS startup service."
    echo ""
    echo "Quick Start:"
    echo "  1. cp env.example .env"
    echo "  2. Edit .env with your credentials"
    echo "  3. $0 --install (or run without arguments and choose option 1)"
    echo ""
    echo "Command Line Options:"
    echo "  --install     Quick installation (creates venv, installs deps, starts service)"
    echo "  --status      Check service status"
    echo "  --start       Start the service"
    echo "  --stop        Stop the service"
    echo "  --restart     Restart the service"
    echo "  --reset       Reset service (removes all logs/activities/state + restart)"
    echo "  --uninstall   Remove the service completely"
    echo "  --logs        View logs interactively"
    echo "  --help        Show this help"
    echo ""
    echo "Manual Commands:"
    echo "  Start service:    launchctl start $SERVICE_NAME"
    echo "  Stop service:     launchctl stop $SERVICE_NAME"  
    echo "  Check status:     launchctl list $SERVICE_NAME"
    echo "  View logs:        tail -f $SCRIPT_DIR/logs/launchd_stdout.log"
    echo ""
    echo "Files and Directories:"
    echo "  Service template: $SCRIPT_DIR/$PLIST_TEMPLATE"
    echo "  Service config:   $LAUNCHAGENTS_DIR/$PLIST_FILE"
    echo "  Application logs: $SCRIPT_DIR/logs/"
    echo "  State data:       $SCRIPT_DIR/state/"
    echo "  Lock file:        $SCRIPT_DIR/greythr_attendance.lock"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check if .env file exists and contains correct credentials"
    echo "  2. Verify virtual environment is set up: ls -la .venv/"
    echo "  3. Check application logs for errors"
    echo "  4. Remove lock file if service won't start: rm greythr_attendance.lock"
    echo ""
}

# Main menu
show_menu() {
    echo ""
    echo "Choose an action:"
    echo "1. 🚀 Quick Install (setup everything and start)"
    echo "2. 📦 Install service only"
    echo "3. ▶️  Start service"
    echo "4. ⏹️  Stop service"  
    echo "5. 🔄 Restart service"
    echo "6. 📊 Check status"
    echo "7. 📋 View logs"
    echo "8. 🔧 Edit configuration (.env)"
    echo "9. 🔄 Reset service (clean all data + restart)"
    echo "10. ❌ Uninstall service"
    echo "11. ❓ Show help"
    echo "12. 🚪 Exit"
    echo ""
}

# Handle command line arguments
if [[ $# -gt 0 ]]; then
    case $1 in
        --install|-i)
            quick_install
            exit $?
            ;;
        --status|-s)
            check_status
            exit 0
            ;;
        --start)
            start_service
            exit $?
            ;;
        --stop)
            stop_service
            exit $?
            ;;
        --restart|-r)
            restart_service
            exit $?
            ;;
        --uninstall|-u)
            read -p "Are you sure you want to uninstall the service? (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                uninstall_service
            else
                print_info "Uninstall cancelled"
            fi
            exit 0
            ;;
        --reset)
            read -p "Are you sure you want to reset the service and remove all data? (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                reset_service
            else
                print_info "Reset cancelled"
            fi
            exit 0
            ;;
        --logs|-l)
            view_logs
            exit 0
            ;;
        --help|-h|help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for available options"
            exit 1
            ;;
    esac
fi

# Interactive menu loop
main() {
    while true; do
        show_menu
        read -p "Enter your choice (1-12): " choice
        
        case $choice in
            1) quick_install ;;
            2) install_service ;;
            3) start_service ;;
            4) stop_service ;;
            5) restart_service ;;
            6) check_status ;;
            7) view_logs ;;
            8) edit_config ;;
            9) 
                read -p "Are you sure you want to reset the service and remove all data? (y/N): " confirm
                if [[ $confirm =~ ^[Yy]$ ]]; then
                    reset_service
                else
                    print_info "Reset cancelled"
                fi
                ;;
            10) 
                read -p "Are you sure you want to uninstall the service? (y/N): " confirm
                if [[ $confirm =~ ^[Yy]$ ]]; then
                    uninstall_service
                else
                    print_info "Uninstall cancelled"
                fi
                ;;
            11) show_help ;;
            12) 
                print_info "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please enter 1-12."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function
main
