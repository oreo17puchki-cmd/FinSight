/* ============================================================
   FinSight Financial Goal Planning Module - Goal Form JS
   File: static/js/goal_form.js
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
    const goalForm = document.getElementById('goal-form');
    if (goalForm) {
        calculateLivePreview();
        goalForm.addEventListener('submit', handleFormSubmit);
    }
});

/**
 * Calculates remaining amount and progress percentage live as the user types amounts.
 */
function calculateLivePreview() {
    const targetInput = document.getElementById('target_amount');
    const currentInput = document.getElementById('current_amount');
    const dateInput = document.getElementById('target_date');

    const prevRemaining = document.getElementById('preview-remaining-amount');
    const prevProgress = document.getElementById('preview-progress-percentage');
    const prevStatus = document.getElementById('preview-status');

    if (!targetInput || !currentInput) return;

    const target = parseFloat(targetInput.value) || 0;
    const current = parseFloat(currentInput.value) || 0;

    // Remaining Calculation
    const remaining = Math.max(0, target - current);
    if (prevRemaining) {
        prevRemaining.textContent = formatCurrency(remaining);
    }

    // Progress Calculation
    let progress = 0;
    if (target > 0) {
        progress = Math.min(100, Math.max(0, (current / target) * 100));
    }
    if (prevProgress) {
        prevProgress.textContent = `${progress.toFixed(1)}%`;
    }

    // Status Calculation
    let statusText = 'In Progress';
    if (current >= target && target > 0) {
        statusText = 'Completed';
    } else if (dateInput && dateInput.value) {
        const targetDate = new Date(dateInput.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        if (targetDate < today) {
            statusText = 'Overdue';
        }
    }

    if (prevStatus) {
        prevStatus.textContent = statusText;
        if (statusText === 'Completed') prevStatus.style.color = '#059669';
        else if (statusText === 'Overdue') prevStatus.style.color = '#DC2626';
        else prevStatus.style.color = '#0E5A4E';
    }

    // Live Field Validations
    validateTargetAmountField();
    validateCurrentAmountField();
}

/**
 * Validates Goal Name field
 */
function validateGoalNameField() {
    const field = document.getElementById('goal_name');
    const errSpan = document.getElementById('error-goal_name');
    if (!field) return true;

    const val = field.value.trim();
    if (!val) {
        showFieldError(field, errSpan, 'Goal name is required.');
        return false;
    } else if (val.length > 150) {
        showFieldError(field, errSpan, 'Goal name cannot exceed 150 characters.');
        return false;
    } else {
        clearFieldError(field, errSpan);
        return true;
    }
}

/**
 * Validates Category field
 */
function validateCategoryField() {
    const field = document.getElementById('category');
    const errSpan = document.getElementById('error-category');
    if (!field) return true;

    if (!field.value) {
        showFieldError(field, errSpan, 'Please select a category.');
        return false;
    } else {
        clearFieldError(field, errSpan);
        return true;
    }
}

/**
 * Validates Goal Type / Horizon field
 */
function validateGoalTypeField() {
    const field = document.getElementById('goal_type');
    const errSpan = document.getElementById('error-goal_type');
    if (!field) return true;

    if (!field.value) {
        showFieldError(field, errSpan, 'Please select a goal horizon.');
        return false;
    } else {
        clearFieldError(field, errSpan);
        return true;
    }
}

/**
 * Validates Target Amount field
 */
function validateTargetAmountField() {
    const field = document.getElementById('target_amount');
    const errSpan = document.getElementById('error-target_amount');
    if (!field) return true;

    const val = parseFloat(field.value);
    if (isNaN(val) || val <= 0) {
        showFieldError(field, errSpan, 'Target amount must be greater than ₹0.');
        return false;
    } else {
        clearFieldError(field, errSpan);
        return true;
    }
}

/**
 * Validates Current Amount field
 */
function validateCurrentAmountField() {
    const field = document.getElementById('current_amount');
    const targetField = document.getElementById('target_amount');
    const errSpan = document.getElementById('error-current_amount');
    if (!field) return true;

    const val = parseFloat(field.value);
    const targetVal = parseFloat(targetField?.value || 0);

    if (isNaN(val) || val < 0) {
        showFieldError(field, errSpan, 'Current saved amount cannot be negative.');
        return false;
    } else if (targetVal > 0 && val > targetVal) {
        showFieldError(field, errSpan, 'Note: Current saved amount exceeds target amount.');
        return true;
    } else {
        clearFieldError(field, errSpan);
        return true;
    }
}

/**
 * Validates Target Date field
 */
function validateTargetDateField() {
    const field = document.getElementById('target_date');
    const errSpan = document.getElementById('error-target_date');
    if (!field) return true;

    if (!field.value) {
        showFieldError(field, errSpan, 'Please select a target completion date.');
        return false;
    } else {
        clearFieldError(field, errSpan);
        return true;
    }
}

/**
 * Validates Priority field
 */
function validatePriorityField() {
    const field = document.getElementById('priority');
    const errSpan = document.getElementById('error-priority');
    if (!field) return true;

    if (!field.value) {
        showFieldError(field, errSpan, 'Please select a priority level.');
        return false;
    } else {
        clearFieldError(field, errSpan);
        return true;
    }
}

/**
 * Helper to display inline field validation error
 */
function showFieldError(field, errSpan, message) {
    if (field) field.classList.add('input-error');
    if (errSpan) errSpan.textContent = message;
}

/**
 * Helper to clear inline field validation error
 */
function clearFieldError(field, errSpan) {
    if (field) field.classList.remove('input-error');
    if (errSpan) errSpan.textContent = '';
}

/**
 * Resets the goal form and re-evaluates live calculation preview
 */
function resetGoalForm() {
    const form = document.getElementById('goal-form');
    if (form) {
        form.reset();
        document.querySelectorAll('.inline-error').forEach(span => span.textContent = '');
        document.querySelectorAll('.input-error').forEach(input => input.classList.remove('input-error'));
        calculateLivePreview();
        showToast('Form reset to default values.', 'success', 2000);
    }
}

/**
 * Form Submit Handler via Fetch API with server validation handling
 */
function handleFormSubmit(e) {
    e.preventDefault();

    const isNameValid = validateGoalNameField();
    const isCategoryValid = validateCategoryField();
    const isTypeValid = validateGoalTypeField();
    const isTargetValid = validateTargetAmountField();
    const isCurrentValid = validateCurrentAmountField();
    const isDateValid = validateTargetDateField();
    const isPriorityValid = validatePriorityField();

    if (!isNameValid || !isCategoryValid || !isTypeValid || !isTargetValid || !isCurrentValid || !isDateValid || !isPriorityValid) {
        showToast('Please fix the validation errors in the form before submitting.', 'error');
        return;
    }

    const form = e.target;
    const submitBtn = document.getElementById('form-submit-btn');
    const spinner = document.getElementById('submit-btn-spinner');
    const btnText = document.getElementById('submit-btn-text');

    if (submitBtn) submitBtn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';

    const formData = new FormData(form);
    const formJson = {};
    formData.forEach((value, key) => {
        formJson[key] = value;
    });

    fetch(form.action, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        },
        body: JSON.stringify(formJson)
    })
    .then(response => response.json().then(data => ({ status: response.status, body: data })))
    .then(res => {
        if (submitBtn) submitBtn.disabled = false;
        if (spinner) spinner.style.display = 'none';

        if (res.status === 200 || res.status === 201) {
            showToast(res.body.message || 'Goal saved successfully!', 'success');
            setTimeout(() => {
                window.location.href = res.body.redirect_url || '/goals';
            }, 800);
        } else {
            showToast(res.body.message || 'Unable to save goal.', 'error');
        }
    })
    .catch(err => {
        if (submitBtn) submitBtn.disabled = false;
        if (spinner) spinner.style.display = 'none';
        console.error('Submission error:', err);
        showToast('Network error occurred while saving goal.', 'error');
    });
}
