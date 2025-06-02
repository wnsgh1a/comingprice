// ComImg Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-important)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation and submission handling
    initializeFormHandlers();
    
    // Price comparison features
    initializePriceComparison();
    
    // Search functionality
    initializeSearch();
    
    // Notification management
    initializeNotifications();
});

function initializeFormHandlers() {
    // Product search form
    const searchForm = document.getElementById('product-search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const url = document.getElementById('product_url').value.trim();
            if (!isValidUrl(url)) {
                e.preventDefault();
                showAlert('올바른 URL을 입력해주세요.', 'error');
                return;
            }
            
            showLoadingSpinner('상품 정보를 분석하고 있습니다...');
        });
    }

    // Card management form
    const cardForm = document.getElementById('card-form');
    if (cardForm) {
        const addCardBtn = document.getElementById('add-card-btn');
        if (addCardBtn) {
            addCardBtn.addEventListener('click', addCardRow);
        }
        
        // Remove card buttons
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-card-btn')) {
                removeCardRow(e.target);
            }
        });
    }

    // Notification settings form
    const notificationForm = document.getElementById('notification-form');
    if (notificationForm) {
        notificationForm.addEventListener('submit', function(e) {
            const targetPrice = document.getElementById('target_price').value;
            if (!targetPrice || parseInt(targetPrice) <= 0) {
                e.preventDefault();
                showAlert('올바른 목표 가격을 입력해주세요.', 'error');
                return;
            }
        });
    }
}

function initializePriceComparison() {
    // Price update animations
    const priceElements = document.querySelectorAll('.price-display');
    priceElements.forEach(function(element) {
        element.classList.add('fade-in');
    });

    // Discount breakdown toggle
    const discountToggle = document.getElementById('discount-breakdown-toggle');
    if (discountToggle) {
        discountToggle.addEventListener('click', function() {
            const breakdown = document.getElementById('discount-breakdown');
            if (breakdown) {
                breakdown.classList.toggle('d-none');
                this.textContent = breakdown.classList.contains('d-none') ? 
                    '할인 내역 보기' : '할인 내역 숨기기';
            }
        });
    }

    // Copy product URL
    const copyButtons = document.querySelectorAll('.copy-url-btn');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const url = this.getAttribute('data-url');
            navigator.clipboard.writeText(url).then(function() {
                showAlert('URL이 복사되었습니다.', 'success');
            }).catch(function() {
                showAlert('URL 복사에 실패했습니다.', 'error');
            });
        });
    });
}

function initializeSearch() {
    // URL validation as user types
    const urlInput = document.getElementById('product_url');
    if (urlInput) {
        urlInput.addEventListener('input', function() {
            const url = this.value.trim();
            const isValid = !url || isValidUrl(url);
            
            this.classList.toggle('is-invalid', !isValid);
            this.classList.toggle('is-valid', isValid && url.length > 0);
        });
    }

    // Search history filtering
    const searchFilter = document.getElementById('search-filter');
    if (searchFilter) {
        searchFilter.addEventListener('input', function() {
            const filter = this.value.toLowerCase();
            const searchItems = document.querySelectorAll('.search-history-item');
            
            searchItems.forEach(function(item) {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(filter) ? '' : 'none';
            });
        });
    }

    // Auto-refresh price data
    const refreshBtn = document.getElementById('refresh-prices-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> 업데이트 중...';
            
            // Simulate refresh (in real app, this would make an AJAX call)
            setTimeout(() => {
                location.reload();
            }, 2000);
        });
    }
}

function initializeNotifications() {
    // Toggle notification switches
    const notificationSwitches = document.querySelectorAll('.notification-toggle');
    notificationSwitches.forEach(function(toggle) {
        toggle.addEventListener('change', function() {
            const notificationId = this.getAttribute('data-notification-id');
            const isActive = this.checked;
            
            // Show loading state
            this.disabled = true;
            
            // In a real app, this would make an AJAX call
            setTimeout(() => {
                this.disabled = false;
                const message = isActive ? '알림이 활성화되었습니다.' : '알림이 비활성화되었습니다.';
                showAlert(message, 'success');
            }, 500);
        });
    });

    // Delete notification confirmations
    const deleteButtons = document.querySelectorAll('.delete-notification-btn');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('정말로 이 알림을 삭제하시겠습니까?')) {
                e.preventDefault();
            }
        });
    });

    // Check prices manually
    const checkPricesBtn = document.getElementById('check-prices-btn');
    if (checkPricesBtn) {
        checkPricesBtn.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> 확인 중...';
            
            // This would typically be an AJAX call
            setTimeout(() => {
                location.reload();
            }, 3000);
        });
    }
}

// Utility functions
function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
        return false;
    }
}

function showAlert(message, type) {
    const alertContainer = document.getElementById('alert-container') || document.body;
    const alertClass = type === 'error' ? 'alert-danger' : `alert-${type}`;
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert ${alertClass} alert-dismissible fade show`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.insertBefore(alertElement, alertContainer.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertElement.parentNode) {
            alertElement.remove();
        }
    }, 5000);
}

function showLoadingSpinner(message = '처리 중...') {
    const spinner = document.createElement('div');
    spinner.id = 'loading-spinner';
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = `
        <div class="text-center text-white">
            <div class="spinner-border spinner-border-custom" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <div class="mt-3">${message}</div>
        </div>
    `;
    
    document.body.appendChild(spinner);
}

function hideLoadingSpinner() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.remove();
    }
}

function addCardRow() {
    const container = document.getElementById('cards-container');
    const cardCount = container.children.length;
    
    const cardRow = document.createElement('div');
    cardRow.className = 'row mb-3 card-row';
    cardRow.innerHTML = `
        <div class="col-md-6">
            <input type="text" class="form-control" name="card_name[]" 
                   placeholder="카드명 (예: 삼성카드 taptap O)" required>
        </div>
        <div class="col-md-4">
            <input type="number" class="form-control" name="card_rate[]" 
                   placeholder="할인율 (%)" min="0" max="100" step="0.1" required>
        </div>
        <div class="col-md-2">
            <button type="button" class="btn btn-outline-danger remove-card-btn">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    
    container.appendChild(cardRow);
    cardRow.classList.add('slide-in');
}

function removeCardRow(button) {
    const row = button.closest('.card-row');
    if (row) {
        row.style.opacity = '0';
        row.style.transform = 'translateX(-20px)';
        setTimeout(() => {
            row.remove();
        }, 300);
    }
}

// Chart initialization (if Chart.js is available)
function initializeCharts() {
    // Price history chart
    const priceChart = document.getElementById('price-history-chart');
    if (priceChart && typeof Chart !== 'undefined') {
        const ctx = priceChart.getContext('2d');
        
        // This would be populated with real data
        const priceData = {
            labels: [],
            datasets: [{
                label: '가격',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        };
        
        new Chart(ctx, {
            type: 'line',
            data: priceData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString() + '원';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + 
                                       context.parsed.y.toLocaleString() + '원';
                            }
                        }
                    }
                }
            }
        });
    }
}

// Initialize charts when DOM is ready
document.addEventListener('DOMContentLoaded', initializeCharts);

// Export functions for external use
window.ComImg = {
    showAlert,
    showLoadingSpinner,
    hideLoadingSpinner,
    isValidUrl,
    addCardRow,
    removeCardRow
};
