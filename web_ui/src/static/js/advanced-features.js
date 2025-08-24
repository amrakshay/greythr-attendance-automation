/**
 * Advanced Features for GreytHR Dashboard
 * Calendar View, Logs Viewer, Export Functionality
 */

class GreytHRAdvancedFeatures {
    constructor() {
        this.apiBaseUrl = '/api';
        this.currentCalendarData = null;
        this.currentLogsData = null;
        this.searchTimeout = null;
    }

    init() {
        console.log('Initializing GreytHR Advanced Features...');
        this.initEventListeners();
        this.initDateSelectors();
    }

    initEventListeners() {
        // Calendar modal events
        const calendarBtn = document.getElementById('btn-calendar-view');
        const logsBtn = document.getElementById('btn-logs-viewer');

        if (calendarBtn) {
            calendarBtn.addEventListener('click', () => this.openCalendarModal());
        }

        if (logsBtn) {
            logsBtn.addEventListener('click', () => this.openLogsModal());
        }

        // Calendar controls
        const monthSelect = document.getElementById('calendar-month');
        const yearSelect = document.getElementById('calendar-year');
        
        if (monthSelect) {
            monthSelect.addEventListener('change', () => this.loadCalendarData());
        }
        
        if (yearSelect) {
            yearSelect.addEventListener('change', () => this.loadCalendarData());
        }

        // Export calendar button
        const exportCalendarBtn = document.getElementById('btn-export-calendar');
        if (exportCalendarBtn) {
            exportCalendarBtn.addEventListener('click', () => this.exportCalendar());
        }

        // Logs controls
        const logSearch = document.getElementById('log-search');
        const logLevel = document.getElementById('log-level');
        const logDate = document.getElementById('log-date');
        const refreshLogsBtn = document.getElementById('btn-refresh-logs');
        const downloadLogsBtn = document.getElementById('btn-download-logs');

        if (logSearch) {
            logSearch.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.filterLogs();
                }, 300);
            });
        }

        if (logLevel) {
            logLevel.addEventListener('change', () => this.filterLogs());
        }

        if (logDate) {
            logDate.addEventListener('change', () => this.filterLogs());
        }

        if (refreshLogsBtn) {
            refreshLogsBtn.addEventListener('click', () => this.loadLogsData());
        }

        if (downloadLogsBtn) {
            downloadLogsBtn.addEventListener('click', () => this.downloadLogs());
        }
    }

    initDateSelectors() {
        // Initialize month selector
        const monthSelect = document.getElementById('calendar-month');
        if (monthSelect) {
            const months = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ];
            
            months.forEach((month, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = month;
                if (index === new Date().getMonth()) {
                    option.selected = true;
                }
                monthSelect.appendChild(option);
            });
        }

        // Initialize year selector
        const yearSelect = document.getElementById('calendar-year');
        if (yearSelect) {
            const currentYear = new Date().getFullYear();
            for (let year = currentYear - 2; year <= currentYear + 1; year++) {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                if (year === currentYear) {
                    option.selected = true;
                }
                yearSelect.appendChild(option);
            }
        }


    }

    // Calendar functionality
    async openCalendarModal() {
        const modal = new bootstrap.Modal(document.getElementById('calendarModal'));
        modal.show();
        await this.loadCalendarData();
    }

    async loadCalendarData() {
        const container = document.getElementById('calendar-container');
        const monthSelect = document.getElementById('calendar-month');
        const yearSelect = document.getElementById('calendar-year');

        if (!monthSelect.value || !yearSelect.value) {
            return;
        }

        try {
            container.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-3 text-muted">Loading calendar data...</p></div>';

            const response = await fetch(`${this.apiBaseUrl}/activities/calendar?year=${yearSelect.value}&month=${monthSelect.value}`);
            
            if (response.ok) {
                const data = await response.json();
                this.currentCalendarData = data;
                this.renderCalendar(data);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Failed to load calendar data:', error);
            this.renderCalendarError();
        }
    }

    renderCalendar(data) {
        const container = document.getElementById('calendar-container');
        const year = parseInt(document.getElementById('calendar-year').value);
        const month = parseInt(document.getElementById('calendar-month').value);

        // Create calendar legend
        const legend = `
            <div class="calendar-legend">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: rgba(25, 135, 84, 0.3);"></div>
                    <span>Attendance Recorded</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: rgba(220, 53, 69, 0.3);"></div>
                    <span>Errors/Issues</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: rgba(13, 110, 253, 0.3);"></div>
                    <span>Today</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #f8f9fa;"></div>
                    <span>No Data</span>
                </div>
            </div>
        `;

        // Create calendar grid
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());

        const today = new Date();
        const calendarHtml = [];

        // Header
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        calendarHtml.push('<div class="calendar-grid">');
        days.forEach(day => {
            calendarHtml.push(`<div class="calendar-header">${day}</div>`);
        });

        // Calendar days
        const currentDate = new Date(startDate);
        for (let i = 0; i < 42; i++) { // 6 weeks max
            const dateStr = currentDate.toISOString().split('T')[0];
            const isCurrentMonth = currentDate.getMonth() === month;
            const isToday = currentDate.toDateString() === today.toDateString();
            const dayData = data.activities[dateStr] || [];

            let classes = ['calendar-day'];
            if (!isCurrentMonth) classes.push('other-month');
            if (isToday) classes.push('today');
            if (dayData.length > 0) classes.push('has-activity');
            if (dayData.some(a => a.status === 'error')) classes.push('has-error');

            calendarHtml.push(`<div class="${classes.join(' ')}" data-date="${dateStr}">`);
            calendarHtml.push(`<div class="calendar-day-number">${currentDate.getDate()}</div>`);

            // Add activities
            dayData.slice(0, 3).forEach(activity => {
                const activityClass = activity.type === 'signin' ? 'signin' : 
                                    activity.type === 'signout' ? 'signout' : 'error';
                calendarHtml.push(`<div class="calendar-activity ${activityClass}" title="${activity.details || activity.message}">${activity.time} ${activity.type}</div>`);
            });

            if (dayData.length > 3) {
                calendarHtml.push(`<div class="calendar-activity" style="color: #6c757d;">+${dayData.length - 3} more</div>`);
            }

            calendarHtml.push('</div>');
            currentDate.setDate(currentDate.getDate() + 1);

            if (currentDate.getMonth() > month + 1 || (currentDate.getMonth() === 0 && month === 11)) {
                break;
            }
        }

        calendarHtml.push('</div>');

        container.innerHTML = legend + calendarHtml.join('');

        // Add click handlers for calendar days
        container.querySelectorAll('.calendar-day').forEach(day => {
            day.addEventListener('click', () => {
                const date = day.dataset.date;
                this.showDayDetails(date);
            });
        });
    }

    renderCalendarError() {
        const container = document.getElementById('calendar-container');
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-exclamation-triangle text-warning" style="font-size: 3rem;"></i>
                <h5 class="mt-3">Failed to Load Calendar</h5>
                <p class="text-muted">Unable to load calendar data. Please try again.</p>
                <button class="btn btn-outline-primary" onclick="window.advancedFeatures.loadCalendarData()">
                    <i class="bi bi-arrow-clockwise"></i>
                    Retry
                </button>
            </div>
        `;
    }

    showDayDetails(date) {
        if (!this.currentCalendarData || !this.currentCalendarData.activities[date]) {
            this.showToast('No data available for this date', 'info');
            return;
        }

        const activities = this.currentCalendarData.activities[date];
        const formattedDate = new Date(date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        let details = `<h6>${formattedDate}</h6>`;
        activities.forEach(activity => {
            const icon = activity.type === 'signin' ? 'box-arrow-in-right' : 
                        activity.type === 'signout' ? 'box-arrow-right' : 'exclamation-triangle';
            const color = activity.status === 'success' ? 'success' : 'danger';
            
            details += `
                <div class="d-flex align-items-center mb-2">
                    <i class="bi bi-${icon} text-${color} me-2"></i>
                    <strong>${activity.time}</strong> - ${activity.type}
                    ${activity.details ? `<br><small class="text-muted">${activity.details}</small>` : ''}
                </div>
            `;
        });

        this.showToast(details, 'info', false, 5000);
    }

    async exportCalendar() {
        if (!this.currentCalendarData) {
            this.showToast('No calendar data to export', 'warning');
            return;
        }

        try {
            const year = document.getElementById('calendar-year').value;
            const month = document.getElementById('calendar-month').value;
            const monthName = new Date(year, month).toLocaleDateString('en-US', { month: 'long' });
            
            const dataStr = JSON.stringify(this.currentCalendarData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            const link = document.createElement('a');
            link.href = URL.createObjectURL(dataBlob);
            link.download = `greythr-calendar-${monthName}-${year}.json`;
            link.click();
            
            this.showToast('Calendar exported successfully', 'success');
        } catch (error) {
            console.error('Export failed:', error);
            this.showToast('Failed to export calendar', 'error');
        }
    }

    // Logs functionality
    async openLogsModal() {
        const modal = new bootstrap.Modal(document.getElementById('logsModal'));
        modal.show();
        await this.loadLogsData();
    }

    async loadLogsData() {
        const container = document.getElementById('logs-container');
        
        try {
            container.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-3 text-muted">Loading system logs...</p></div>';

            const response = await fetch(`${this.apiBaseUrl}/logs/recent?limit=500`);
            
            if (response.ok) {
                const data = await response.json();
                this.currentLogsData = data;
                this.renderLogs(data);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
            this.renderLogsError();
        }
    }

    renderLogs(data) {
        const container = document.getElementById('logs-container');
        
        if (!data.logs || data.logs.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-file-text text-muted" style="font-size: 3rem;"></i>
                    <h5 class="mt-3 text-muted">No Logs Available</h5>
                    <p class="text-muted">No log entries found for the selected criteria.</p>
                </div>
            `;
            return;
        }

        const logsHtml = data.logs.map(log => {
            const levelClass = log.level ? log.level.toLowerCase() : 'info';
            const timestamp = new Date(log.timestamp).toLocaleString();
            
            return `
                <div class="log-line ${levelClass}" data-level="${levelClass}" data-timestamp="${log.timestamp}">
                    <span class="log-timestamp">${timestamp}</span>
                    <span class="log-level ${levelClass}">${log.level || 'INFO'}</span>
                    <span class="log-message">${this.escapeHtml(log.message)}</span>
                </div>
            `;
        }).join('');

        container.innerHTML = `<div class="log-viewer">${logsHtml}</div>`;
        
        // Auto-scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    renderLogsError() {
        const container = document.getElementById('logs-container');
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-exclamation-triangle text-warning" style="font-size: 3rem;"></i>
                <h5 class="mt-3">Failed to Load Logs</h5>
                <p class="text-muted">Unable to load system logs. Please try again.</p>
                <button class="btn btn-outline-primary" onclick="window.advancedFeatures.loadLogsData()">
                    <i class="bi bi-arrow-clockwise"></i>
                    Retry
                </button>
            </div>
        `;
    }

    filterLogs() {
        if (!this.currentLogsData) return;

        const searchTerm = document.getElementById('log-search').value.toLowerCase();
        const levelFilter = document.getElementById('log-level').value;
        const dateFilter = document.getElementById('log-date').value;

        const container = document.getElementById('logs-container');
        const logLines = container.querySelectorAll('.log-line');

        logLines.forEach(line => {
            const message = line.querySelector('.log-message').textContent.toLowerCase();
            const level = line.dataset.level;
            const timestamp = line.dataset.timestamp;
            const logDate = new Date(timestamp).toISOString().split('T')[0];

            let show = true;

            // Search filter
            if (searchTerm && !message.includes(searchTerm)) {
                show = false;
            }

            // Level filter
            if (levelFilter && level !== levelFilter) {
                show = false;
            }

            // Date filter
            if (dateFilter && logDate !== dateFilter) {
                show = false;
            }

            line.style.display = show ? 'block' : 'none';

            // Highlight search terms
            if (show && searchTerm) {
                const messageEl = line.querySelector('.log-message');
                const originalText = messageEl.textContent;
                const highlightedText = originalText.replace(
                    new RegExp(searchTerm, 'gi'),
                    match => `<span class="log-search-highlight">${match}</span>`
                );
                messageEl.innerHTML = highlightedText;
            }
        });
    }

    async downloadLogs() {
        if (!this.currentLogsData) {
            this.showToast('No logs to download', 'warning');
            return;
        }

        try {
            const dataStr = JSON.stringify(this.currentLogsData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            const link = document.createElement('a');
            link.href = URL.createObjectURL(dataBlob);
            link.download = `greythr-logs-${new Date().toISOString().split('T')[0]}.json`;
            link.click();
            
            this.showToast('Logs downloaded successfully', 'success');
        } catch (error) {
            console.error('Download failed:', error);
            this.showToast('Failed to download logs', 'error');
        }
    }



    // Utility methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showToast(message, type = 'info', autoHide = true, delay = 3000) {
        const toast = document.createElement('div');
        toast.className = 'toast position-fixed top-0 end-0 m-3';
        toast.style.zIndex = '1060';
        
        const iconMap = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };

        const colorMap = {
            success: 'success',
            error: 'danger',
            warning: 'warning',
            info: 'info'
        };

        toast.innerHTML = `
            <div class="toast-header">
                <i class="bi bi-${iconMap[type]} text-${colorMap[type]} me-2"></i>
                <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;

        document.body.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast, {
            autohide: autoHide,
            delay: delay
        });
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    async showConfirmation(title, message, type = 'warning') {
        return new Promise((resolve) => {
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

            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();

            const confirmBtn = modal.querySelector('#confirm-btn');
            confirmBtn.addEventListener('click', () => {
                bsModal.hide();
                resolve(true);
            });

            modal.addEventListener('hidden.bs.modal', () => {
                modal.remove();
                resolve(false);
            });
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.advancedFeatures = new GreytHRAdvancedFeatures();
    window.advancedFeatures.init();
});
