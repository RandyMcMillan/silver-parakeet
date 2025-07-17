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
    
    // Set up address field listeners for agent sign lookup
    setupAddressSignLookup();
    
    // Reset form after successful submission
    resetFormAfterSuccess();
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
    const agentSignGroup = document.getElementById('agent_sign_group');
    const postTypeSelect = document.getElementById('post_type');
    const deliverNotesTextarea = document.getElementById('deliver_notes');
    
    // Hide all conditional fields first
    postTypeGroup.style.display = 'none';
    deliverNotesGroup.style.display = 'none';
    agentSignGroup.style.display = 'none';
    
    // Reset required attributes
    postTypeSelect.required = false;
    deliverNotesTextarea.required = false;
    
    // Show appropriate fields based on selection
    if (serviceTypeSelect.value === 'install') {
        postTypeGroup.style.display = 'block';
        agentSignGroup.style.display = 'block';
        postTypeSelect.required = true;
    } else if (serviceTypeSelect.value === 'deliver') {
        deliverNotesGroup.style.display = 'block';
        deliverNotesTextarea.required = true;
    } else if (serviceTypeSelect.value === 'remove') {
        // For removes, check if there's a stored agent sign for this address
        checkForStoredAgentSign();
    }
    
    // Trigger post type change handler in case it was already selected
    if (serviceTypeSelect.value === 'install') {
        handlePostTypeChange();
    }
}

function toggleRidersToppers() {
    const ridersCheckbox = document.getElementById('has_riders_toppers');
    const ridersGroup = document.getElementById('riders_toppers_group');
    const ridersTextarea = document.getElementById('riders_toppers_description');
    
    if (ridersCheckbox.checked) {
        ridersGroup.style.display = 'block';
        ridersTextarea.required = true;
    } else {
        ridersGroup.style.display = 'none';
        ridersTextarea.required = false;
        ridersTextarea.value = '';
    }
}

function checkForStoredAgentSign() {
    // This function will be called when "remove" is selected
    // Look up agent sign for current address when all address fields are filled
    const streetAddress = document.getElementById('street_address').value.trim();
    const aptUnit = document.getElementById('apt_unit').value.trim();
    const city = document.getElementById('city').value.trim();
    const state = document.getElementById('state').value.trim();
    const zipCode = document.getElementById('zip_code').value.trim();
    
    if (streetAddress && city && state && zipCode) {
        // Build full address string
        const addressParts = [streetAddress];
        if (aptUnit) {
            addressParts.push(aptUnit);
        }
        addressParts.push(city, state, zipCode);
        const fullAddress = addressParts.join(', ');
        
        // Look up agent sign for this address
        fetch(`/get_agent_sign/${encodeURIComponent(fullAddress)}`)
            .then(response => response.json())
            .then(data => {
                if (data.found) {
                    // Show the agent sign info
                    showAgentSignInfo(data.description, data.updated_at);
                } else {
                    hideAgentSignInfo();
                }
            })
            .catch(error => {
                console.error('Error looking up agent sign:', error);
                hideAgentSignInfo();
            });
    } else {
        hideAgentSignInfo();
    }
}

function showAgentSignInfo(description, updatedAt) {
    let infoDiv = document.getElementById('agent_sign_info');
    if (!infoDiv) {
        infoDiv = document.createElement('div');
        infoDiv.id = 'agent_sign_info';
        infoDiv.className = 'alert alert-info mt-2';
        document.getElementById('agent_sign_group').parentNode.insertBefore(infoDiv, document.getElementById('agent_sign_group').nextSibling);
    }
    
    infoDiv.innerHTML = `
        <strong><i data-feather="info"></i> Previous Agent Sign Found:</strong><br>
        <em>"${description}"</em><br>
        <small class="text-muted">Last updated: ${updatedAt}</small>
    `;
    infoDiv.style.display = 'block';
    
    // Re-initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

function hideAgentSignInfo() {
    const infoDiv = document.getElementById('agent_sign_info');
    if (infoDiv) {
        infoDiv.style.display = 'none';
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

function setupAddressSignLookup() {
    // Add event listeners to address fields for agent sign lookup
    const addressFields = ['street_address', 'apt_unit', 'city', 'state', 'zip_code'];
    
    addressFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('blur', function() {
                const serviceType = document.getElementById('service_type').value;
                if (serviceType === 'remove') {
                    checkForStoredAgentSign();
                }
            });
        }
    });
}

function resetFormAfterSuccess() {
    // Check if URL has reset_form parameter
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('reset_form') === 'true') {
        // Reset the form
        const form = document.querySelector('form[action*="add_stop"]');
        if (form) {
            form.reset();
            
            // Reset conditional field visibility
            document.getElementById('deliver_notes_group').style.display = 'none';
            document.getElementById('post_type_group').style.display = 'none';
            document.getElementById('post_type_notes_group').style.display = 'none';
            document.getElementById('agent_sign_group').style.display = 'none';
            document.getElementById('riders_toppers_group').style.display = 'none';
            document.getElementById('required_date_group').style.display = 'block';
            
            // Reset required attributes
            document.getElementById('post_type').required = false;
            document.getElementById('deliver_notes').required = false;
            document.getElementById('riders_toppers_description').required = false;
            document.getElementById('required_date').required = true;
            
            // Hide agent sign info if visible
            hideAgentSignInfo();
            
            // Clean up URL without reloading page
            window.history.replaceState({}, document.title, window.location.pathname);
            
            // Focus on first field (ASAP checkbox) after a short delay
            setTimeout(() => {
                document.getElementById('is_asap').focus();
            }, 100);
        }
    }
}
