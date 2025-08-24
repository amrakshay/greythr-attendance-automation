/**
 * GreytHR Dashboard JavaScript
 * Phase 1: Basic functionality and structure
 */

class GreytHRDashboard {
    constructor() {
        this.apiBaseUrl = '/api';
        this.refreshInterval = 30000; // 30 seconds
        this.refreshTimer = null;
        this.isInitializing = true;
        
        this.init();
    }
    
    async init() {
        console.log('GreytHR Dashboard initializing...');
        
        // Initialize components
        this.initEventListeners();
        
        // Load initial data
        await this.loadInitialData();
        

        
        // Start auto-refresh
        this.startAutoRefresh();
        
        this.isInitializing = false;
        console.log('GreytHR Dashboard ready - Full featured web UI');
    }
    
    async loadInitialData() {
        console.log('Loading initial dashboard data...');
        try {
            // Show loading state
            this.showLoadingState();
            
            // Initially disable all service buttons until we know the status
            this.disableAllServiceButtons();
            
            // Fetch dashboard overview
            const overview = await this.fetchDashboardOverview();
            if (overview) {
                this.updateDashboard(overview);
            }
            
            this.hideLoadingState();
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showErrorState('Failed to load dashboard data');
        }
    }
    
    initEventListeners() {
        // Service management button event listeners
        const startBtn = document.getElementById('btn-start');
        const stopBtn = document.getElementById('btn-stop');
        const restartBtn = document.getElementById('btn-restart');
        
        if (startBtn) {
            startBtn.addEventListener('click', () => this.handleStartService());
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.handleStopService());
        }
        
        if (restartBtn) {
            restartBtn.addEventListener('click', () => this.handleRestartService());
        }
        
        // Add click handlers for any remaining disabled buttons
        document.querySelectorAll('button[disabled]').forEach(button => {
            button.addEventListener('click', this.showComingSoon);
        });
    }
    
    showComingSoon(event) {
        event.preventDefault();
        const buttonText = event.target.textContent.trim();
        
        // Create a temporary toast notification
        const toast = document.createElement('div');
        toast.className = 'toast position-fixed top-0 end-0 m-3';
        toast.style.zIndex = '1060';
        toast.innerHTML = `
            <div class="toast-header">
                <i class="bi bi-info-circle text-primary me-2"></i>
                <strong class="me-auto">Coming Soon</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                <strong>${buttonText}</strong> will be available in upcoming phases.
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Show toast using Bootstrap
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 3000
        });
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    // API methods for fetching data
    
    async fetchDashboardOverview() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dashboard/overview`);
            if (response.ok) {
                return await response.json();
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        } catch (error) {
            console.error('Failed to fetch dashboard overview:', error);
            return null;
        }
    }
    
    async fetchSystemStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dashboard/status`);
            if (response.ok) {
                return await response.json();
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        } catch (error) {
            console.error('Failed to fetch system status:', error);
            return null;
        }
    }
    
    async fetchTodaySummary() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dashboard/summary`);
            if (response.ok) {
                return await response.json();
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        } catch (error) {
            console.error('Failed to fetch today summary:', error);
            return null;
        }
    }
    
    async fetchRecentActivities() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dashboard/recent-activities?limit=5`);
            if (response.ok) {
                return await response.json();
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        } catch (error) {
            console.error('Failed to fetch recent activities:', error);
            return [];
        }
    }
    
    async fetchQuickStats() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dashboard/quick-stats`);
            if (response.ok) {
                return await response.json();
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        } catch (error) {
            console.error('Failed to fetch quick stats:', error);
            return null;
        }
    }
    
    async fetchSystemAlerts() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/dashboard/alerts`);
            if (response.ok) {
                return await response.json();
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        } catch (error) {
            console.error('Failed to fetch system alerts:', error);
            return [];
        }
    }
    
    // Service Management API methods
    
    async handleStartService() {
        try {
            // Check if button is disabled
            const startBtn = document.getElementById('btn-start');
            if (startBtn && startBtn.disabled) {
                console.log('Start button is disabled, ignoring click');
                return;
            }
            
            this.setButtonLoading('btn-start', true);
            
            const response = await fetch(`${this.apiBaseUrl}/service/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'start',
                    force: false
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccessToast(`Service started successfully! ${result.message}`);
                // Refresh dashboard to show updated status
                await this.refreshDashboard();
            } else {
                this.showErrorToast(`Failed to start service: ${result.message}`);
            }
            
        } catch (error) {
            console.error('Start service error:', error);
            this.showErrorToast('Failed to start service');
        } finally {
            this.setButtonLoading('btn-start', false);
        }
    }
    
    async handleStopService() {
        try {
            // Check if button is disabled
            const stopBtn = document.getElementById('btn-stop');
            if (stopBtn && stopBtn.disabled) {
                console.log('Stop button is disabled, ignoring click');
                return;
            }
            
            // Show confirmation dialog
            const confirmed = await this.showConfirmationDialog(
                'Stop Service',
                'Are you sure you want to stop the GreytHR service? This will disable automatic attendance.',
                'warning'
            );
            
            if (!confirmed) return;
            
            this.setButtonLoading('btn-stop', true);
            
            const response = await fetch(`${this.apiBaseUrl}/service/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'stop',
                    force: false
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccessToast(`Service stopped successfully! ${result.message}`);
                // Refresh dashboard to show updated status
                await this.refreshDashboard();
            } else {
                this.showErrorToast(`Failed to stop service: ${result.message}`);
            }
            
        } catch (error) {
            console.error('Stop service error:', error);
            this.showErrorToast('Failed to stop service');
        } finally {
            this.setButtonLoading('btn-stop', false);
        }
    }
    
    async handleRestartService() {
        try {
            // Check if button is disabled
            const restartBtn = document.getElementById('btn-restart');
            if (restartBtn && restartBtn.disabled) {
                console.log('Restart button is disabled, ignoring click');
                return;
            }
            
            // Show confirmation dialog
            const confirmed = await this.showConfirmationDialog(
                'Restart Service',
                'Are you sure you want to restart the GreytHR service? This will briefly interrupt the automation.',
                'warning'
            );
            
            if (!confirmed) return;
            
            this.setButtonLoading('btn-restart', true);
            
            const response = await fetch(`${this.apiBaseUrl}/service/restart`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccessToast(`Service restart successful! ${result.message}`);
                // Refresh dashboard to show updated status
                await this.refreshDashboard();
            } else {
                this.showErrorToast(`Service restart failed: ${result.message}`);
            }
            
        } catch (error) {
            console.error('Service restart error:', error);
            this.showErrorToast('Failed to restart service');
        } finally {
            this.setButtonLoading('btn-restart', false);
        }
    }
    
    // Service management helper methods
    
    updateServiceButtonStates(status) {
        const startBtn = document.getElementById('btn-start');
        const stopBtn = document.getElementById('btn-stop');
        const restartBtn = document.getElementById('btn-restart');
        
        // Determine if service is running based on status data
        const isRunning = status.is_running || status.daemon_running || false;
        
        if (startBtn) {
            startBtn.disabled = isRunning;
            startBtn.title = isRunning ? 'Service is already running' : 'Start the GreytHR service';
            
            // Add visual indication
            if (isRunning) {
                startBtn.classList.add('opacity-50');
                startBtn.style.cursor = 'not-allowed';
            } else {
                startBtn.classList.remove('opacity-50');
                startBtn.style.cursor = 'pointer';
            }
        }
        
        if (stopBtn) {
            stopBtn.disabled = !isRunning;
            stopBtn.title = !isRunning ? 'Service is not running' : 'Stop the GreytHR service';
            
            // Add visual indication
            if (!isRunning) {
                stopBtn.classList.add('opacity-50');
                stopBtn.style.cursor = 'not-allowed';
            } else {
                stopBtn.classList.remove('opacity-50');
                stopBtn.style.cursor = 'pointer';
            }
        }
        
        if (restartBtn) {
            restartBtn.disabled = !isRunning;
            restartBtn.title = !isRunning ? 'Service is not running' : 'Restart the GreytHR service';
            
            // Add visual indication
            if (!isRunning) {
                restartBtn.classList.add('opacity-50');
                restartBtn.style.cursor = 'not-allowed';
            } else {
                restartBtn.classList.remove('opacity-50');
                restartBtn.style.cursor = 'pointer';
            }
        }
        
        console.log(`Service buttons updated: Running=${isRunning}, Start=${!isRunning}, Stop/Restart=${isRunning}`);
    }
    
    setButtonLoading(buttonId, loading) {
        const button = document.getElementById(buttonId);
        if (!button) return;
        
        const spinner = button.querySelector('.spinner-border');
        const text = button.querySelector('.btn-text');
        
        if (loading) {
            button.disabled = true;
            if (spinner) spinner.classList.remove('d-none');
            if (text) text.style.opacity = '0.7';
        } else {
            button.disabled = false;
            if (spinner) spinner.classList.add('d-none');
            if (text) text.style.opacity = '1';
            
            // Re-apply button state logic after loading is complete
            setTimeout(() => {
                this.refreshButtonStates();
            }, 100);
        }
    }
    
    async refreshButtonStates() {
        try {
            // Get current status and update button states
            const status = await this.fetchSystemStatus();
            if (status) {
                this.updateServiceButtonStates(status);
            }
        } catch (error) {
            console.error('Failed to refresh button states:', error);
        }
    }
    
    disableAllServiceButtons() {
        const buttons = ['btn-start', 'btn-stop', 'btn-restart'];
        buttons.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                button.disabled = true;
                button.title = 'Loading service status...';
                button.classList.add('opacity-50');
                button.style.cursor = 'not-allowed';
            }
        });
    }
    
    async showConfirmationDialog(title, message, type = 'warning') {
        return new Promise((resolve) => {
            // Create modal
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.setAttribute('tabindex', '-1');
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-exclamation-triangle text-${type} me-2"></i>
                                ${title}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${message}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-${type}" id="confirm-btn">Confirm</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Show modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            // Handle confirmation
            const confirmBtn = modal.querySelector('#confirm-btn');
            confirmBtn.addEventListener('click', () => {
                bsModal.hide();
                resolve(true);
            });
            
            // Handle cancellation
            modal.addEventListener('hidden.bs.modal', () => {
                modal.remove();
                resolve(false);
            });
        });
    }
    
    showSuccessToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast position-fixed top-0 end-0 m-3';
        toast.style.zIndex = '1060';
        toast.innerHTML = `
            <div class="toast-header">
                <i class="bi bi-check-circle text-success me-2"></i>
                <strong class="me-auto">Success</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 5000
        });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    showErrorToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast position-fixed top-0 end-0 m-3';
        toast.style.zIndex = '1060';
        toast.innerHTML = `
            <div class="toast-header">
                <i class="bi bi-exclamation-circle text-danger me-2"></i>
                <strong class="me-auto">Error</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 7000
        });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    async refreshDashboard() {
        try {
            console.log('Refreshing dashboard data...');
            await this.updateDashboard();
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
        }
    }
    
    updateStatusCard(cardId, status) {
        // Will be implemented in Phase 2
        const card = document.getElementById(cardId);
        if (card) {
            // Update card content based on status
            console.log(`Updating ${cardId} with status:`, status);
        }
    }
    
    startAutoRefresh() {
        // Will be implemented in Phase 2
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(async () => {
            await this.refreshDashboard();
        }, this.refreshInterval);
        
        console.log(`Auto-refresh started (${this.refreshInterval / 1000}s interval)`);
    }
    
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
            console.log('Auto-refresh stopped');
        }
    }
    
    async refreshDashboard() {
        console.log('Refreshing dashboard data...');
        
        try {
            const overview = await this.fetchDashboardOverview();
            if (overview) {
                this.updateDashboard(overview);
            }
        } catch (error) {
            console.error('Dashboard refresh failed:', error);
            this.showErrorToast('Failed to refresh dashboard data');
        }
    }
    
    updateDashboard(overview) {
        console.log('Updating dashboard with overview data:', overview);
        
        // Update system status
        this.updateSystemStatus(overview.system_status);
        
        // Update today's summary
        this.updateTodaySummary(overview.today_summary);
        
        // Update recent activities
        this.updateRecentActivities(overview.recent_activities);
        
        // Update quick stats
        this.updateQuickStats(overview.quick_stats);
        
        // Update service button states based on current status
        this.updateServiceButtonStates(overview.system_status || {});
        
        // Update alerts
        this.updateAlerts(overview.alerts);
    }
    
    updateSystemStatus(status) {
        console.log('Updating system status:', status);
        
        // Update service status card
        const serviceCard = document.querySelector('.card.border-primary');
        if (serviceCard) {
            const badge = serviceCard.querySelector('.badge');
            const statusText = serviceCard.querySelector('.card-text');
            const lastCheck = serviceCard.querySelector('small');
            
            if (badge && statusText) {
                if (status.daemon_running) {
                    badge.className = 'badge bg-success';
                    badge.textContent = 'Running';
                    statusText.innerHTML = `<span class="badge bg-success">Running</span>`;
                } else {
                    badge.className = 'badge bg-danger';
                    badge.textContent = 'Stopped';
                    statusText.innerHTML = `<span class="badge bg-danger">Stopped</span>`;
                }
            }
            
            if (lastCheck) {
                lastCheck.textContent = `PID: ${status.script_pid || 'N/A'}`;
            }
        }
        
        // Update uptime card
        const uptimeCard = document.querySelector('.card.border-secondary');
        if (uptimeCard) {
            const uptimeText = uptimeCard.querySelector('.card-text strong');
            const uptimeSmall = uptimeCard.querySelector('small');
            
            if (uptimeText) {
                uptimeText.textContent = status.uptime_formatted;
            }
            
            if (uptimeSmall) {
                uptimeSmall.textContent = `Memory: ${status.memory_usage_mb}MB`;
            }
        }
        
        // Update navbar status indicator
        const navbarStatus = document.querySelector('.navbar-text');
        if (navbarStatus) {
            const indicator = navbarStatus.querySelector('.status-indicator');
            const text = navbarStatus.querySelector('span:last-child') || navbarStatus;
            
            if (indicator) {
                indicator.className = status.daemon_running 
                    ? 'status-indicator status-healthy' 
                    : 'status-indicator status-error';
            }
            
            if (text) {
                text.textContent = status.daemon_running ? 'System Online' : 'System Offline';
            }
        }
    }
    
    updateTodaySummary(summary) {
        console.log('Updating today summary:', summary);
        
        // Update signin card
        const signinCard = document.querySelector('.card.border-success');
        if (signinCard) {
            const badge = signinCard.querySelector('.badge');
            const statusText = signinCard.querySelector('.card-text');
            const timeText = signinCard.querySelector('small');
            
            if (badge && statusText) {
                if (summary.signin_completed) {
                    badge.className = 'badge bg-success';
                    badge.textContent = 'Completed';
                    statusText.innerHTML = `<span class="badge bg-success">Completed</span>`;
                } else {
                    badge.className = 'badge bg-warning';
                    badge.textContent = 'Pending';
                    statusText.innerHTML = `<span class="badge bg-warning">Pending</span>`;
                }
            }
            
            if (timeText) {
                timeText.textContent = summary.signin_time 
                    ? `At ${summary.signin_time}` 
                    : 'Not completed';
            }
        }
        
        // Update signout card
        const signoutCard = document.querySelector('.card.border-info');
        if (signoutCard) {
            const badge = signoutCard.querySelector('.badge');
            const statusText = signoutCard.querySelector('.card-text');
            const timeText = signoutCard.querySelector('small');
            
            if (badge && statusText) {
                if (summary.signout_completed) {
                    badge.className = 'badge bg-success';
                    badge.textContent = 'Completed';
                    statusText.innerHTML = `<span class="badge bg-success">Completed</span>`;
                } else {
                    badge.className = 'badge bg-warning';
                    badge.textContent = 'Pending';
                    statusText.innerHTML = `<span class="badge bg-warning">Pending</span>`;
                }
            }
            
            if (timeText) {
                timeText.textContent = summary.signout_time 
                    ? `At ${summary.signout_time}` 
                    : 'Not scheduled';
            }
        }
    }
    
    updateRecentActivities(activities) {
        console.log('Updating recent activities:', activities);
        
        const activitiesList = document.querySelector('.list-group.list-group-flush');
        if (!activitiesList || !activities.length) return;
        
        // Clear existing activities
        activitiesList.innerHTML = '';
        
        // Add new activities
        activities.forEach(activity => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            let icon = 'bi-info-circle text-secondary';
            let statusText = activity.status;
            
            if (activity.status === 'Complete') {
                icon = 'bi-check-circle text-success';
            } else if (activity.status === 'Partial') {
                icon = 'bi-exclamation-circle text-warning';
            } else if (activity.status === 'Failed') {
                icon = 'bi-x-circle text-danger';
            }
            
            item.innerHTML = `
                <div>
                    <i class="${icon} me-2"></i>
                    ${activity.date} - ${statusText}
                </div>
                <small class="text-muted">${activity.day_of_week}</small>
            `;
            
            activitiesList.appendChild(item);
        });
    }
    
    updateQuickStats(stats) {
        console.log('Updating quick stats:', stats);
        // Quick stats will be displayed in additional UI elements in future phases
    }
    
    updateAlerts(alerts) {
        console.log('Updating alerts:', alerts);
        
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert.mt-3:not(.alert-info)');
        existingAlerts.forEach(alert => alert.remove());
        
        // Add new alerts
        if (alerts && alerts.length > 0) {
            const quickActionsCard = document.querySelector('.card .card-body');
            if (quickActionsCard) {
                alerts.forEach(alert => {
                    const alertElement = this.createAlertElement(alert);
                    quickActionsCard.appendChild(alertElement);
                });
            }
        }
    }
    
    createAlertElement(alert) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${this.getBootstrapAlertClass(alert.type)} alert-dismissible fade show mt-3`;
        alertDiv.setAttribute('role', 'alert');
        
        alertDiv.innerHTML = `
            <i class="bi bi-info-circle"></i>
            <strong>${alert.title}</strong> ${alert.message}
            ${alert.dismissible ? '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' : ''}
        `;
        
        return alertDiv;
    }
    
    getBootstrapAlertClass(alertType) {
        const mapping = {
            'error': 'danger',
            'warning': 'warning',
            'info': 'info',
            'success': 'success'
        };
        return mapping[alertType] || 'info';
    }
    
    showLoadingState() {
        const cards = document.querySelectorAll('.status-card');
        cards.forEach(card => {
            card.style.opacity = '0.6';
        });
    }
    
    hideLoadingState() {
        const cards = document.querySelectorAll('.status-card');
        cards.forEach(card => {
            card.style.opacity = '1';
        });
    }
    
    showErrorState(message) {
        const container = document.querySelector('.container.my-4');
        if (container) {
            const errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-danger alert-dismissible fade show';
            errorAlert.setAttribute('role', 'alert');
            errorAlert.innerHTML = `
                <i class="bi bi-exclamation-triangle"></i>
                <strong>Error:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            container.insertBefore(errorAlert, container.firstChild);
        }
    }
    
    showErrorToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast position-fixed top-0 end-0 m-3';
        toast.style.zIndex = '1060';
        toast.innerHTML = `
            <div class="toast-header">
                <i class="bi bi-exclamation-triangle text-danger me-2"></i>
                <strong class="me-auto">Error</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 5000
        });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    // Utility methods
    
    formatUptime(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
        if (seconds < 86400) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        return `${days}d ${hours}h`;
    }
    
    formatDateTime(isoString) {
        return new Date(isoString).toLocaleString();
    }
    
    getStatusBadgeClass(status) {
        const statusMap = {
            'completed': 'bg-success',
            'pending': 'bg-warning',
            'failed': 'bg-danger',
            'running': 'bg-primary',
            'stopped': 'bg-secondary'
        };
        return statusMap[status] || 'bg-secondary';
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new GreytHRDashboard();
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GreytHRDashboard;
}
