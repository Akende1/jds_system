/**
 * School Management System - Main JavaScript File
 * Modern UI with Dark Mode & Enhanced Features
 */

(function($) {
    'use strict';

    // ============================================
    // DARK MODE FUNCTIONALITY
    // ============================================
    
    // Initialize dark mode from localStorage
    function initDarkMode() {
        const darkMode = localStorage.getItem('darkMode');
        const darkModeToggle = document.getElementById('darkModeToggle');
        
        if (darkMode === 'enabled') {
            document.documentElement.setAttribute('data-theme', 'dark');
            if (darkModeToggle) {
                darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            }
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            if (darkModeToggle) {
                darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            }
        }
    }

    // Toggle dark mode
    function toggleDarkMode() {
        const darkModeToggle = document.getElementById('darkModeToggle');
        const currentTheme = document.documentElement.getAttribute('data-theme');
        
        if (currentTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('darkMode', 'disabled');
            if (darkModeToggle) {
                darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            }
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('darkMode', 'enabled');
            if (darkModeToggle) {
                darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            }
        }
    }

    // ============================================
    // OFFLINE/ONLINE STATUS DETECTION
    // ============================================
    
    function updateOnlineStatus() {
        const indicator = document.getElementById('connectionStatus');
        if (!indicator) return;
        
        if (navigator.onLine) {
            indicator.className = 'online-indicator';
            indicator.innerHTML = '<i class="fas fa-wifi"></i> Online';
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 3000);
        } else {
            indicator.className = 'offline-indicator';
            indicator.innerHTML = '<i class="fas fa-wifi-slash"></i> Offline Mode';
            indicator.style.display = 'block';
        }
    }

    // ============================================
    // LOADING OVERLAY
    // ============================================
    
    function showLoading(message = 'Loading...') {
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay active';
        overlay.innerHTML = `
            <div class="text-center">
                <div class="spinner mb-3"></div>
                <h4 class="text-white">${message}</h4>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    function hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(() => overlay.remove(), 300);
        }
    }

    // ============================================
    // SMOOTH ANIMATIONS
    // ============================================
    
    function animateOnScroll() {
        const elements = document.querySelectorAll('.card, .stats-card');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, {
            threshold: 0.1
        });

        elements.forEach(el => observer.observe(el));
    }

    // ============================================
    // DOCUMENT READY
    // ============================================
    
    $(document).ready(function() {
        
        // Initialize dark mode
        initDarkMode();
        
        // Dark mode toggle event
        $(document).on('click', '#darkModeToggle', toggleDarkMode);
        
        // Initialize connection status
        updateOnlineStatus();
        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
        
        // Initialize scroll animations
        animateOnScroll();
        
        // Initialize tooltips
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Initialize popovers
        var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });

        // Smooth scrolling for anchor links
        $('a[href*="#"]:not([href="#"])').click(function() {
            if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && 
                location.hostname == this.hostname) {
                var target = $(this.hash);
                target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
                if (target.length) {
                    $('html, body').animate({
                        scrollTop: target.offset().top - 70
                    }, 800);
                    return false;
                }
            }
        });

        // Auto-dismiss alerts after 5 seconds
        setTimeout(function() {
            $('.alert').fadeOut('slow');
        }, 5000);

        // Confirm delete actions
        $('.delete-confirm').on('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
                return false;
            }
        });

        // Form validation
        (function() {
            'use strict';
            var forms = document.querySelectorAll('.needs-validation');
            Array.prototype.slice.call(forms).forEach(function(form) {
                form.addEventListener('submit', function(event) {
                    if (!form.checkValidity()) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                    form.classList.add('was-validated');
                }, false);
            });
        })();

        // Sidebar active link
        var currentPath = window.location.pathname;
        $('.sidebar .nav-link, .navbar .nav-link').each(function() {
            if ($(this).attr('href') === currentPath) {
                $(this).addClass('active');
            }
        });

        // Page back button: show when there is history or a referrer
        function initBackButtons() {
            var backBtn = document.getElementById('pageBackBtn');
            var backBtnFrontend = document.getElementById('pageBackBtnFrontend');
            var canGoBack = (window.history && window.history.length > 1) || (document.referrer && document.referrer !== '');
            if (backBtn && canGoBack) backBtn.classList.remove('d-none');
            if (backBtnFrontend && canGoBack) backBtnFrontend.classList.remove('d-none');

            if (backBtn) backBtn.addEventListener('click', function(e) {
                e.preventDefault();
                window.history.back();
            });
            if (backBtnFrontend) backBtnFrontend.addEventListener('click', function(e) {
                e.preventDefault();
                window.history.back();
            });

            // Keyboard shortcut: Alt + Left for back
            document.addEventListener('keydown', function(e) {
                if (e.altKey && e.key === 'ArrowLeft') {
                    window.history.back();
                }
            });
        }

        initBackButtons();

        // Data tables (if using DataTables plugin)
        if ($.fn.DataTable) {
            $('.data-table').DataTable({
                responsive: true,
                pageLength: 25,
                order: [[0, 'desc']],
                language: {
                    search: "_INPUT_",
                    searchPlaceholder: "Search records..."
                }
            });
        }

        // Print functionality
        $('.print-btn').on('click', function(e) {
            e.preventDefault();
            window.print();
        });

        // Export functionality
        $('.export-btn').on('click', function(e) {
            e.preventDefault();
            var format = $(this).data('format');
            showLoading('Preparing ' + format.toUpperCase() + ' export...');
            
            // Simulate export delay
            setTimeout(function() {
                hideLoading();
                alert('Export to ' + format.toUpperCase() + ' functionality coming soon!');
            }, 1500);
        });

        // Toggle sidebar on mobile
        $('.sidebar-toggle').on('click', function() {
            $('.sidebar').toggleClass('show');
        });
        
        // ============================================
        // AJAX FORM SUBMISSIONS
        // ============================================
        
        $('.ajax-form').on('submit', function(e) {
            e.preventDefault();
            const form = $(this);
            const url = form.attr('action');
            const data = form.serialize();
            
            showLoading('Saving...');
            
            $.ajax({
                type: 'POST',
                url: url,
                data: data,
                success: function(response) {
                    hideLoading();
                    if (response.success) {
                        showNotification('Success', response.message, 'success');
                        form[0].reset();
                    } else {
                        showNotification('Error', response.message, 'danger');
                    }
                },
                error: function() {
                    hideLoading();
                    showNotification('Error', 'Something went wrong. Please try again.', 'danger');
                }
            });
        });
        
        // ============================================
        // NOTIFICATION SYSTEM
        // ============================================
        
        window.showNotification = function(title, message, type = 'info') {
            const notification = $(`
                <div class="alert alert-${type} alert-dismissible fade show position-fixed" 
                     role="alert" 
                     style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
                    <strong>${title}:</strong> ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `);
            
            $('body').append(notification);
            
            setTimeout(function() {
                notification.fadeOut('slow', function() {
                    $(this).remove();
                });
            }, 5000);
        };
        
        // ============================================
        // SEARCH ENHANCEMENT
        // ============================================
        
        $('.search-input').on('keyup', function() {
            const value = $(this).val().toLowerCase();
            const target = $(this).data('target');
            
            $(target).filter(function() {
                $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
            });
        });
        
        // ============================================
        // NUMBER ANIMATION (COUNT UP)
        // ============================================
        
        function animateValue(element, start, end, duration) {
            let startTimestamp = null;
            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                element.textContent = Math.floor(progress * (end - start) + start).toLocaleString();
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                }
            };
            window.requestAnimationFrame(step);
        }
        
        // Animate stats numbers on page load
        $('.stats-card h3').each(function() {
            const text = $(this).text();
            const number = parseInt(text.replace(/[^0-9]/g, ''));
            if (!isNaN(number) && number > 0) {
                animateValue(this, 0, number, 1500);
            }
        });
        
        // ============================================
        // AUTO-SAVE DRAFTS
        // ============================================
        
        let autoSaveTimeout;
        $('.auto-save').on('input', function() {
            clearTimeout(autoSaveTimeout);
            const field = $(this);
            const key = 'draft_' + field.attr('name');
            
            autoSaveTimeout = setTimeout(function() {
                localStorage.setItem(key, field.val());
                showNotification('Draft Saved', 'Your changes have been saved', 'info');
            }, 2000);
        });
        
        // Restore drafts on page load
        $('.auto-save').each(function() {
            const field = $(this);
            const key = 'draft_' + field.attr('name');
            const saved = localStorage.getItem(key);
            
            if (saved && field.val() === '') {
                field.val(saved);
            }
        });
        
        // ============================================
        // KEYBOARD SHORTCUTS
        // ============================================
        
        $(document).on('keydown', function(e) {
            // Ctrl/Cmd + K: Focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                $('.search-input').first().focus();
            }
            
            // Ctrl/Cmd + D: Toggle dark mode
            if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
                e.preventDefault();
                toggleDarkMode();
            }
        });
        
        // ============================================
        // COPY TO CLIPBOARD
        // ============================================
        
        $('.copy-btn').on('click', function() {
            const text = $(this).data('copy');
            navigator.clipboard.writeText(text).then(function() {
                showNotification('Copied', 'Text copied to clipboard', 'success');
            });
        });
        
    }); // End Document Ready

    // ============================================
    // WINDOW LOAD EVENT
    // ============================================
    
    $(window).on('load', function() {
        // Hide preloader if exists
        $('.preloader').fadeOut('slow');
        
        // Add loaded class to body
        $('body').addClass('loaded');
    });

})(jQuery);


        // Number formatting
        $('.currency').each(function() {
            var value = parseFloat($(this).text());
            if (!isNaN(value)) {
                $(this).text('₦' + value.toLocaleString('en-NG', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }));
            }
        });

        // Date picker initialization
        if ($.fn.datepicker) {
            $('.datepicker').datepicker({
                format: 'yyyy-mm-dd',
                autoclose: true,
                todayHighlight: true
            });
        }

        // Character counter for textareas
        $('textarea[maxlength]').each(function() {
            var maxLength = $(this).attr('maxlength');
            var currentLength = $(this).val().length;
            var counter = $('<small class="text-muted float-end">' + currentLength + '/' + maxLength + '</small>');
            $(this).after(counter);
            
            $(this).on('input', function() {
                currentLength = $(this).val().length;
                counter.text(currentLength + '/' + maxLength);
            });
        });
        
    }); // End Document Ready

    // ============================================
    // WINDOW LOAD EVENT
    // ============================================
    
    $(window).on('load', function() {
        // Hide preloader if exists
        $('.preloader').fadeOut('slow');
        
        // Add loaded class to body
        $('body').addClass('loaded');
    });

})(jQuery);

