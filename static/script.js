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
    
    // Check for form reset trigger in localStorage
    checkForFormResetTrigger();
    
    // Set up form submission handler
    setupFormSubmissionHandler();
    
    // Ensure departure address is populated on page load
    ensureDepartureAddressPopulated();
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
    console.log('Checking for reset_form parameter:', urlParams.get('reset_form'));
    
    if (urlParams.get('reset_form') === 'true') {
        console.log('Form reset triggered');
        
        // Reset the form
        const form = document.querySelector('form[action*="add_stop"]');
        console.log('Form found:', form);
        
        if (form) {
            console.log('Found form, resetting...');
            
            // Force reset all form fields
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.type === 'checkbox' || input.type === 'radio') {
                    input.checked = false;
                } else {
                    input.value = '';
                }
                console.log(`Reset field: ${input.name || input.id} to: ${input.value || input.checked}`);
            });
            
            // Call form.reset() as well
            form.reset();
            
            // Reset conditional field visibility
            const fieldsToHide = ['deliver_notes_group', 'post_type_group', 'post_type_notes_group', 'agent_sign_group', 'riders_toppers_group'];
            fieldsToHide.forEach(fieldId => {
                const element = document.getElementById(fieldId);
                if (element) {
                    element.style.display = 'none';
                    console.log(`Hidden ${fieldId}`);
                }
            });
            
            // Show required date group
            const requiredDateGroup = document.getElementById('required_date_group');
            if (requiredDateGroup) {
                requiredDateGroup.style.display = 'block';
                console.log('Shown required_date_group');
            }
            
            // Reset required attributes
            const fieldsToResetRequired = [
                { id: 'post_type', required: false },
                { id: 'deliver_notes', required: false },
                { id: 'riders_toppers_description', required: false },
                { id: 'required_date', required: true }
            ];
            
            fieldsToResetRequired.forEach(field => {
                const element = document.getElementById(field.id);
                if (element) {
                    element.required = field.required;
                    console.log(`Set ${field.id} required to ${field.required}`);
                }
            });
            
            // Ensure ASAP checkbox is unchecked and date field is shown
            const asapCheckbox = document.getElementById('is_asap');
            if (asapCheckbox) {
                asapCheckbox.checked = false;
                console.log('ASAP checkbox unchecked');
            }
            
            // Hide agent sign info if visible
            hideAgentSignInfo();
            
            // Clean up URL without reloading page
            window.history.replaceState({}, document.title, window.location.pathname);
            
            // Update counters dynamically
            updateStopCounters();
            
            // Focus on first field (ASAP checkbox) after a short delay
            setTimeout(() => {
                const firstField = document.getElementById('is_asap');
                if (firstField) {
                    firstField.focus();
                    console.log('Focus set to ASAP checkbox');
                }
            }, 200);
            
            console.log('Form reset completed');
        } else {
            console.log('Form not found for reset');
        }
    } else {
        console.log('No reset_form parameter found');
    }
}

function updateStopCounters() {
    // Fetch updated counter data from server
    fetch('/api/stop_counters')
        .then(response => response.json())
        .then(data => {
            // Update next 7 days counter
            const next7DaysElement = document.querySelector('.card.bg-primary .h2');
            if (next7DaysElement) {
                next7DaysElement.textContent = data.stops_next_7_days;
            }
            
            // Update total system counter
            const totalSystemElement = document.querySelector('.card.bg-info .h2');
            if (totalSystemElement) {
                totalSystemElement.textContent = data.total_stops;
            }
            
            // Update departure address field
            const departureAddressField = document.getElementById('departure_address');
            if (departureAddressField && data.departure_address) {
                departureAddressField.value = data.departure_address;
            }
            
            console.log('Counters and departure address updated:', data);
        })
        .catch(error => {
            console.error('Error updating counters:', error);
        });
}

function ensureDepartureAddressPopulated() {
    // Check if departure address field exists and is empty
    const departureAddressField = document.getElementById('departure_address');
    if (departureAddressField && !departureAddressField.value.trim()) {
        // Fetch current departure address from API
        fetch('/api/stop_counters')
            .then(response => response.json())
            .then(data => {
                if (data.departure_address) {
                    departureAddressField.value = data.departure_address;
                    console.log('Departure address populated:', data.departure_address);
                }
            })
            .catch(error => {
                console.error('Error fetching departure address:', error);
            });
    }
}

function checkForFormResetTrigger() {
    console.log('Checking for form reset triggers...');
    
    // Check URL parameters first as they're more reliable
    const urlParams = new URLSearchParams(window.location.search);
    const urlResetParam = urlParams.get('reset_form');
    const urlTriggerParam = urlParams.get('form_reset_trigger');
    
    console.log('URL reset_form:', urlResetParam);
    console.log('URL form_reset_trigger:', urlTriggerParam);
    
    if (urlResetParam === 'true' || urlTriggerParam === 'true') {
        console.log('Form reset triggered from URL parameters');
        
        // Perform form reset
        performFormReset();
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
    }
    
    // Check localStorage as backup
    const localStorageTrigger = localStorage.getItem('formResetTrigger');
    console.log('localStorage formResetTrigger:', localStorageTrigger);
    
    if (localStorageTrigger === 'true') {
        console.log('Form reset triggered from localStorage');
        localStorage.removeItem('formResetTrigger');
        
        // Perform form reset
        performFormReset();
        return;
    }
    
    console.log('No form reset triggers found');
}

function performFormReset() {
    console.log('Performing form reset');
    
    // Reset the form
    const form = document.querySelector('form[action*="add_stop"]');
    console.log('Form found:', form);
    
    if (form) {
        console.log('Found form, resetting...');
        
        // Force reset all form fields except departure address
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            // Skip departure address field
            if (input.id === 'departure_address') {
                console.log('Skipping departure_address field');
                return;
            }
            
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = false;
                console.log(`Reset checkbox: ${input.name || input.id} to: ${input.checked}`);
            } else {
                input.value = '';
                console.log(`Reset field: ${input.name || input.id} to: "${input.value}"`);
            }
        });
        
        // Call form.reset() but then restore departure address
        const departureAddressValue = document.getElementById('departure_address')?.value || '';
        form.reset();
        if (departureAddressValue) {
            const departureField = document.getElementById('departure_address');
            if (departureField) {
                departureField.value = departureAddressValue;
                console.log('Restored departure address:', departureAddressValue);
            }
        }
        
        // Reset conditional field visibility
        const fieldsToHide = ['deliver_notes_group', 'post_type_group', 'post_type_notes_group', 'agent_sign_group', 'riders_toppers_group'];
        fieldsToHide.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element) {
                element.style.display = 'none';
                console.log(`Hidden ${fieldId}`);
            }
        });
        
        // Show required date group
        const requiredDateGroup = document.getElementById('required_date_group');
        if (requiredDateGroup) {
            requiredDateGroup.style.display = 'block';
            console.log('Shown required_date_group');
        }
        
        // Reset required attributes
        const fieldsToResetRequired = [
            { id: 'post_type', required: false },
            { id: 'deliver_notes', required: false },
            { id: 'riders_toppers_description', required: false },
            { id: 'required_date', required: true }
        ];
        
        fieldsToResetRequired.forEach(field => {
            const element = document.getElementById(field.id);
            if (element) {
                element.required = field.required;
                console.log(`Set ${field.id} required to ${field.required}`);
            }
        });
        
        // Ensure ASAP checkbox is unchecked and date field is shown
        const asapCheckbox = document.getElementById('is_asap');
        if (asapCheckbox) {
            asapCheckbox.checked = false;
            console.log('ASAP checkbox unchecked');
        }
        
        // Hide agent sign info if visible
        hideAgentSignInfo();
        
        // Update counters dynamically
        updateStopCounters();
        
        // Focus on first field (ASAP checkbox) after a short delay
        setTimeout(() => {
            const firstField = document.getElementById('is_asap');
            if (firstField) {
                firstField.focus();
                console.log('Focus set to ASAP checkbox');
            }
        }, 200);
        
        // Verify the reset actually worked by checking field values
        setTimeout(() => {
            console.log('=== FORM RESET VERIFICATION ===');
            const verifyInputs = form.querySelectorAll('input, select, textarea');
            verifyInputs.forEach(input => {
                if (input.type === 'checkbox') {
                    console.log(`${input.id || input.name}: ${input.checked}`);
                } else {
                    console.log(`${input.id || input.name}: "${input.value}"`);
                }
            });
            console.log('=== END VERIFICATION ===');
            
            // Force clear any autofilled values after verification
            setTimeout(() => {
                console.log('=== FORCING CLEAR AUTOFILL ===');
                const addressFields = ['street_address', 'apt_unit', 'city', 'state', 'zip_code'];
                addressFields.forEach(fieldId => {
                    const field = document.getElementById(fieldId);
                    if (field && field.value) {
                        console.log(`Autofill detected in ${fieldId}: "${field.value}" - clearing it`);
                        field.value = '';
                    }
                });
                console.log('=== AUTOFILL CLEAR COMPLETE ===');
            }, 500);
        }, 300);
        
        console.log('Form reset completed');
    } else {
        console.log('Form not found for reset');
    }
}

function setFormResetTrigger() {
    // Set localStorage flag to trigger form reset after successful submission
    localStorage.setItem('formResetTrigger', 'true');
    console.log('Form reset trigger set in localStorage');
    console.log('Current localStorage formResetTrigger:', localStorage.getItem('formResetTrigger'));
    
    // Also log that form is being submitted
    console.log('Form is being submitted...');
    
    // Return true to allow form submission to continue
    return true;
}

function setupFormSubmissionHandler() {
    // Set up both onsubmit and button click handlers for maximum reliability
    const form = document.querySelector('form[action*="add_stop"]');
    const submitButton = document.getElementById('add-stop-btn');
    
    if (form) {
        console.log('Setting up form submission handlers');
        
        // Form submit handler
        form.addEventListener('submit', function(e) {
            console.log('Form submit event triggered');
            setFormResetTrigger();
        });
        
        // Button click handler as backup
        if (submitButton) {
            submitButton.addEventListener('click', function(e) {
                console.log('Submit button clicked');
                // Check if form is valid before setting trigger
                if (form.checkValidity()) {
                    console.log('Form is valid, setting reset trigger');
                    setFormResetTrigger();
                } else {
                    console.log('Form is invalid, not setting reset trigger');
                }
            });
        }
    } else {
        console.log('Form not found for submission handler setup');
    }
}
