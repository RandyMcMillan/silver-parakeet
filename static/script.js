// Route Optimizer JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize form validation
    initializeFormValidation();
    
    // Set up date input behavior
    setupDateInput();
    
    // Add loading states to buttons
    setupLoadingStates();
    
    // Auto-dismiss alerts
    autoDismissAlerts();
});

function toggleDateInput() {
    const asapCheckbox = document.getElementById('is_asap');
    const dateGroup = document.getElementById('required_date_group');
    const dateInput = document.getElementById('required_date');
    
    if (asapCheckbox.checked) {
        dateGroup.style.display = 'none';
        dateInput.required = false;
        dateInput.value = '';
    } else {
        dateGroup.style.display = 'block';
        dateInput.required = true;
    }
}

function handleServiceTypeChange() {
    const serviceTypeSelect = document.getElementById('service_type');
    const postTypeGroup = document.getElementById('post_type_group');
    const deliverNotesGroup = document.getElementById('deliver_notes_group');
    const postTypeSelect = document.getElementById('post_type');
    const deliverNotesTextarea = document.getElementById('deliver_notes');
    
    // Hide all conditional fields first
    postTypeGroup.style.display = 'none';
    deliverNotesGroup.style.display = 'none';
    
    // Reset required attributes
    postTypeSelect.required = false;
    deliverNotesTextarea.required = false;
    
    // Show appropriate fields based on selection
    if (serviceTypeSelect.value === 'install') {
        postTypeGroup.style.display = 'block';
        postTypeSelect.required = true;
    } else if (serviceTypeSelect.value === 'deliver') {
        deliverNotesGroup.style.display = 'block';
        deliverNotesTextarea.required = true;
    }
    // For 'remove', no additional fields are shown
    
    // Trigger post type change handler in case it was already selected
    if (serviceTypeSelect.value === 'install') {
        handlePostTypeChange();
    }
}

function handlePostTypeChange() {
    const postTypeSelect = document.getElementById('post_type');
    const postTypeNotesGroup = document.getElementById('post_type_notes_group');
    const postTypeNotesTextarea = document.getElementById('post_type_notes');
    
    if (postTypeSelect.value === 'Other') {
        postTypeNotesGroup.style.display = 'block';
        postTypeNotesTextarea.required = true;
    } else {
        postTypeNotesGroup.style.display = 'none';
        postTypeNotesTextarea.required = false;
        postTypeNotesTextarea.value = '';
    }
}

function initializeFormValidation() {
    // Add custom validation for forms
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
}

function setupDateInput() {
    const dateInput = document.getElementById('required_date');
    if (dateInput) {
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        dateInput.min = today;
        
        // Add validation message
        dateInput.addEventListener('invalid', function() {
            if (this.validity.rangeUnderflow) {
                this.setCustomValidity('Please select a future date');
            } else {
                this.setCustomValidity('');
            }
        });
        
        dateInput.addEventListener('input', function() {
            this.setCustomValidity('');
        });
    }
}

function setupLoadingStates() {
    const submitButtons = document.querySelectorAll('button[type="submit"], .btn[href*="generate_routes"]');
    
    submitButtons.forEach(button => {
        button.addEventListener('click', function() {
            const originalText = this.innerHTML;
            const loadingText = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';
            
            // Add loading state
            this.innerHTML = loadingText;
            this.disabled = true;
            
            // Remove loading state after form submission
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
            }, 3000);
        });
    });
}

function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        if (alert.classList.contains('alert-success')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
}

// Address validation helper
function validateAddress(address) {
    // Basic address validation
    const addressPattern = /^[a-zA-Z0-9\s,.-]+$/;
    return addressPattern.test(address) && address.length > 5;
}

// Form enhancement for better UX
function enhanceFormInputs() {
    const addressFields = ['street_address', 'city', 'state', 'zip_code'];
    
    addressFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('blur', function() {
                if (fieldId === 'zip_code' && this.value) {
                    // Basic US ZIP code validation
                    const zipPattern = /^\d{5}(-\d{4})?$/;
                    if (!zipPattern.test(this.value)) {
                        this.setCustomValidity('Please enter a valid ZIP code (e.g., 12345 or 12345-6789)');
                    } else {
                        this.setCustomValidity('');
                    }
                } else if (fieldId === 'state' && this.value) {
                    // Basic state validation (2 letters)
                    const statePattern = /^[A-Z]{2}$/i;
                    if (!statePattern.test(this.value)) {
                        this.setCustomValidity('Please enter a valid 2-letter state code (e.g., CA, NY)');
                    } else {
                        this.setCustomValidity('');
                    }
                } else {
                    this.setCustomValidity('');
                }
            });
            
            field.addEventListener('input', function() {
                this.setCustomValidity('');
            });
        }
    });
}

// Call enhancement function
enhanceFormInputs();

// Export confirmation dialogs
function confirmDelete(itemType, itemName) {
    return confirm(`Are you sure you want to delete this ${itemType}${itemName ? `: ${itemName}` : ''}?`);
}

function confirmRouteGeneration() {
    return confirm('This will generate optimized routes for all employees. Continue?');
}

function confirmClearRoutes() {
    return confirm('This will clear all generated routes. Are you sure?');
}

// Smooth scrolling for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Alt + N: Focus on new stop form
    if (event.altKey && event.key === 'n') {
        event.preventDefault();
        const serviceTypeInput = document.getElementById('service_type');
        if (serviceTypeInput) {
            serviceTypeInput.focus();
        }
    }
    
    // Alt + A: Focus on address form
    if (event.altKey && event.key === 'a') {
        event.preventDefault();
        const streetAddressInput = document.getElementById('street_address');
        if (streetAddressInput) {
            streetAddressInput.focus();
        }
    }
    
    // Alt + E: Focus on employee form
    if (event.altKey && event.key === 'e') {
        event.preventDefault();
        const nameInput = document.getElementById('name');
        if (nameInput) {
            nameInput.focus();
        }
    }
    
    // Alt + R: Generate routes
    if (event.altKey && event.key === 'r') {
        event.preventDefault();
        const generateButton = document.querySelector('a[href*="generate_routes"]');
        if (generateButton && confirmRouteGeneration()) {
            window.location.href = generateButton.href;
        }
    }
});
