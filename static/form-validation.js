/**
 * Client-side form validation and UI enhancements
 * Provides immediate feedback and prevents common errors
 */

// Form validation rules
const validationRules = {
    street_address: {
        required: true,
        minLength: 3,
        message: 'Street address must be at least 3 characters'
    },
    city: {
        required: true,
        minLength: 2,
        message: 'City must be at least 2 characters'
    },
    state: {
        required: true,
        pattern: /^[A-Z]{2}$/,
        message: 'State must be 2 uppercase letters (e.g., GA)'
    },
    zip_code: {
        required: true,
        pattern: /^\d{5}(-\d{4})?$/,
        message: 'ZIP code must be 5 digits or 5+4 format'
    },
    service_type: {
        required: true,
        message: 'Please select a service type'
    }
};

// Initialize form validation when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('addStopForm');
    const submitBtn = document.getElementById('addStopBtn');
    const errorContainer = document.getElementById('form-errors');
    
    if (!form || !submitBtn) return;
    
    // Add input event listeners for real-time validation
    Object.keys(validationRules).forEach(fieldName => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.addEventListener('input', () => validateField(field, fieldName));
            field.addEventListener('blur', () => validateField(field, fieldName));
        }
    });
    
    // Form submission handler
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return false;
        }
        
        // Show loading state
        showLoadingState();
    });
    
    // Field validation function
    function validateField(field, fieldName) {
        const rule = validationRules[fieldName];
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';
        
        // Required field check
        if (rule.required && !value) {
            isValid = false;
            errorMessage = `${getFieldLabel(fieldName)} is required`;
        }
        
        // Minimum length check
        if (isValid && rule.minLength && value.length < rule.minLength) {
            isValid = false;
            errorMessage = rule.message;
        }
        
        // Pattern check
        if (isValid && rule.pattern && !rule.pattern.test(value)) {
            isValid = false;
            errorMessage = rule.message;
        }
        
        // Update field styling
        updateFieldValidation(field, isValid, errorMessage);
        
        return isValid;
    }
    
    // Full form validation
    function validateForm() {
        let isFormValid = true;
        const errors = [];
        
        Object.keys(validationRules).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field && !validateField(field, fieldName)) {
                isFormValid = false;
                errors.push(validationRules[fieldName].message || `${getFieldLabel(fieldName)} is invalid`);
            }
        });
        
        // Show/hide error container
        if (errors.length > 0) {
            showFormErrors(errors);
        } else {
            hideFormErrors();
        }
        
        return isFormValid;
    }
    
    // Update field validation styling
    function updateFieldValidation(field, isValid, errorMessage) {
        const fieldGroup = field.closest('.mb-3') || field.closest('.form-group');
        let feedback = fieldGroup.querySelector('.invalid-feedback');
        
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
            if (feedback) feedback.remove();
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                field.parentNode.appendChild(feedback);
            }
            feedback.textContent = errorMessage;
        }
    }
    
    // Show form errors
    function showFormErrors(errors) {
        errorContainer.innerHTML = errors.map(error => `<div>${error}</div>`).join('');
        errorContainer.classList.remove('d-none');
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    // Hide form errors
    function hideFormErrors() {
        errorContainer.classList.add('d-none');
    }
    
    // Show loading state
    function showLoadingState() {
        const btnText = submitBtn.querySelector('.btn-text');
        const spinner = submitBtn.querySelector('.spinner-border');
        
        if (btnText) btnText.textContent = 'Adding Stop...';
        if (spinner) spinner.classList.remove('d-none');
        submitBtn.disabled = true;
    }
    
    // Get human-readable field label
    function getFieldLabel(fieldName) {
        const labels = {
            street_address: 'Street Address',
            city: 'City',
            state: 'State',
            zip_code: 'ZIP Code',
            service_type: 'Service Type'
        };
        return labels[fieldName] || fieldName;
    }
});

// Auto-format state field to uppercase
document.addEventListener('DOMContentLoaded', function() {
    const stateField = document.querySelector('[name="state"]');
    if (stateField) {
        stateField.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    }
});