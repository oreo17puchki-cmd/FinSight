/* ============================================================
   FinSight Financial Goal Planning Module - Goal Dashboard JS
   File: static/js/goal.js
   ============================================================ */

let searchDebounceTimer = null;

/**
 * Handles live input change for search, category, goal_type, priority, status, and sort.
 */
function handleSearchFilterChange() {
    const searchInput = document.getElementById('goal-search-input');
    const clearBtn = document.getElementById('search-clear-btn');
    
    if (searchInput && clearBtn) {
        clearBtn.style.display = searchInput.value.trim().length > 0 ? 'block' : 'none';
    }

    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        fetchFilteredGoals();
    }, 250);
}

/**
 * Clears the search input field.
 */
function clearSearchInput() {
    const searchInput = document.getElementById('goal-search-input');
    const clearBtn = document.getElementById('search-clear-btn');
    if (searchInput) {
        searchInput.value = '';
    }
    if (clearBtn) {
        clearBtn.style.display = 'none';
    }
    fetchFilteredGoals();
}

/**
 * Resets all filter dropdowns and search input to default states.
 */
function resetAllFilters() {
    const searchInput = document.getElementById('goal-search-input');
    const catSelect = document.getElementById('filter-category');
    const typeSelect = document.getElementById('filter-type');
    const priSelect = document.getElementById('filter-priority');
    const statSelect = document.getElementById('filter-status');
    const sortSelect = document.getElementById('sort-by');
    const clearBtn = document.getElementById('search-clear-btn');

    if (searchInput) searchInput.value = '';
    if (catSelect) catSelect.value = 'All';
    if (typeSelect) typeSelect.value = 'All';
    if (priSelect) priSelect.value = 'All';
    if (statSelect) statSelect.value = 'All';
    if (sortSelect) sortSelect.value = 'newest';
    if (clearBtn) clearBtn.style.display = 'none';

    fetchFilteredGoals();
}

/**
 * Fetches goals asynchronously from backend route GET /goals/search
 */
function fetchFilteredGoals() {
    const searchVal = document.getElementById('goal-search-input')?.value.trim() || '';
    const catVal = document.getElementById('filter-category')?.value || 'All';
    const typeVal = document.getElementById('filter-type')?.value || 'All';
    const priVal = document.getElementById('filter-priority')?.value || 'All';
    const statVal = document.getElementById('filter-status')?.value || 'All';
    const sortVal = document.getElementById('sort-by')?.value || 'newest';

    const spinner = document.getElementById('goals-loading-spinner');
    const gridContainer = document.getElementById('goals-grid-container');

    if (spinner) spinner.style.display = 'block';

    const queryParams = new URLSearchParams({
        q: searchVal,
        category: catVal,
        goal_type: typeVal,
        priority: priVal,
        status: statVal,
        sort_by: sortVal
    });

    fetch(`/goals/search?${queryParams.toString()}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Search request failed.');
        return response.json();
    })
    .then(data => {
        if (spinner) spinner.style.display = 'none';
        if (data.status === 'success') {
            renderGoalsGrid(data.goals);
            updateSummaryCards(data.summary);
        }
    })
    .catch(err => {
        if (spinner) spinner.style.display = 'none';
        console.error('Error fetching filtered goals:', err);
    });
}

/**
 * Dynamically renders the goals grid DOM elements.
 * 
 * @param {Array} goals - List of goal objects.
 */
function renderGoalsGrid(goals) {
    const gridContainer = document.getElementById('goals-grid-container');
    if (!gridContainer) return;

    if (!goals || goals.length === 0) {
        gridContainer.innerHTML = `
            <div class="empty-state-card" id="empty-state-card">
                <div class="empty-state-icon">
                    <i class="fa-solid fa-bullseye"></i>
                </div>
                <h2 class="empty-state-title">No matching goals found</h2>
                <p class="empty-state-description">Try adjusting your search terms or filter criteria.</p>
                <button type="button" class="btn btn-gold btn-lg" onclick="resetAllFilters()">
                    <i class="fa-solid fa-rotate-left"></i> Reset All Filters
                </button>
            </div>
        `;
        return;
    }

    let cardsHtml = '<div class="goals-grid" id="goals-grid">';
    goals.forEach(goal => {
        const catLower = (goal.category || 'other').toLowerCase();
        let iconClass = 'fa-bullseye';
        if (goal.category === 'Education') iconClass = 'fa-graduation-cap';
        else if (goal.category === 'Travel') iconClass = 'fa-plane';
        else if (goal.category === 'Emergency') iconClass = 'fa-shield-halved';
        else if (goal.category === 'Personal') iconClass = 'fa-user';
        else if (goal.category === 'Shopping') iconClass = 'fa-bag-shopping';
        else if (goal.category === 'Health') iconClass = 'fa-heart-pulse';
        else if (goal.category === 'Family') iconClass = 'fa-users';

        let statusClass = 'status-in-progress';
        let statusIcon = 'fa-clock';
        if (goal.status === 'Completed') {
            statusClass = 'status-completed';
            statusIcon = 'fa-circle-check';
        } else if (goal.status === 'Overdue') {
            statusClass = 'status-overdue';
            statusIcon = 'fa-circle-exclamation';
        }

        let progressClass = '';
        if (goal.status === 'Completed') progressClass = 'fill-completed';
        else if (goal.status === 'Overdue') progressClass = 'fill-overdue';

        cardsHtml += `
            <article class="goal-card" id="goal-card-${goal.goal_id}">
                <div class="goal-card-header">
                    <div class="goal-category-icon icon-cat-${catLower}">
                        <i class="fa-solid ${iconClass}"></i>
                    </div>

                    <div class="goal-card-title-group">
                        <h2 class="goal-title">${escapeHtml(goal.goal_name)}</h2>
                        <div class="goal-meta-badges">
                            <span class="badge badge-type">${escapeHtml(goal.goal_type)}</span>
                            <span class="badge badge-category">${escapeHtml(goal.category)}</span>
                            <span class="badge badge-priority priority-${(goal.priority || '').toLowerCase()}">${escapeHtml(goal.priority)} Priority</span>
                        </div>
                    </div>

                    <div class="goal-status-badge ${statusClass}">
                        <i class="fa-solid ${statusIcon}"></i> ${escapeHtml(goal.status)}
                    </div>
                </div>

                <div class="goal-financials">
                    <div class="fin-item">
                        <span class="fin-label">Target</span>
                        <span class="fin-amount fin-target">${formatCurrency(goal.target_amount)}</span>
                    </div>
                    <div class="fin-item">
                        <span class="fin-label">Saved</span>
                        <span class="fin-amount fin-saved">${formatCurrency(goal.current_amount)}</span>
                    </div>
                    <div class="fin-item">
                        <span class="fin-label">Remaining</span>
                        <span class="fin-amount fin-remaining">${formatCurrency(goal.remaining_amount)}</span>
                    </div>
                </div>

                <div class="goal-progress-wrapper">
                    <div class="progress-info-row">
                        <span class="progress-label">Progress</span>
                        <span class="progress-percentage">${goal.progress_percentage}%</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill ${progressClass}" style="width: ${goal.progress_percentage}%;"></div>
                    </div>
                </div>

                <div class="goal-date-row">
                    <span class="date-item"><i class="fa-regular fa-calendar"></i> Target: ${formatDateReadable(goal.target_date)}</span>
                    <span class="remaining-days-pill"><i class="fa-solid fa-hourglass-start"></i> ${escapeHtml(goal.remaining_days_label || '')}</span>
                </div>

                <div class="goal-card-actions">
                    <button type="button" class="btn btn-outline btn-sm" onclick="openViewModal(${goal.goal_id})" id="view-btn-${goal.goal_id}">
                        <i class="fa-regular fa-eye"></i> View
                    </button>
                    <a href="/goals/edit/${goal.goal_id}" class="btn btn-outline btn-sm" id="edit-btn-${goal.goal_id}">
                        <i class="fa-regular fa-pen-to-square"></i> Edit
                    </a>
                    <button type="button" class="btn btn-danger-soft btn-sm" onclick="openDeleteConfirmModal(${goal.goal_id}, '${escapeHtml(goal.goal_name).replace(/'/g, "\\'")}')" id="delete-btn-${goal.goal_id}">
                        <i class="fa-regular fa-trash-can"></i> Delete
                    </button>
                </div>
            </article>
        `;
    });

    cardsHtml += '</div>';
    gridContainer.innerHTML = cardsHtml;
}

/**
 * Updates summary card numerical metrics in the DOM.
 * 
 * @param {Object} summary - Calculated summary metrics object.
 */
function updateSummaryCards(summary) {
    if (!summary) return;
    const totalGoals = document.getElementById('summary-total-goals');
    const activeGoals = document.getElementById('summary-active-goals');
    const completedGoals = document.getElementById('summary-completed-goals');
    const totalTarget = document.getElementById('summary-total-target');
    const totalSaved = document.getElementById('summary-total-saved');
    const totalRemaining = document.getElementById('summary-total-remaining');

    if (totalGoals) totalGoals.textContent = summary.total_goals || 0;
    if (activeGoals) activeGoals.textContent = summary.active_goals || 0;
    if (completedGoals) completedGoals.textContent = summary.completed_goals || 0;
    if (totalTarget) totalTarget.textContent = formatCurrency(summary.total_target_amount || 0);
    if (totalSaved) totalSaved.textContent = formatCurrency(summary.total_saved_amount || 0);
    if (totalRemaining) totalRemaining.textContent = formatCurrency(summary.total_remaining_amount || 0);
}

/**
 * Opens the View Goal Modal and fetches single goal JSON data via GET /goals/view/<id>
 * 
 * @param {number} goalId - Unique Goal ID.
 */
function openViewModal(goalId) {
    const modal = document.getElementById('view-goal-modal');
    if (!modal) return;

    fetch(`/goals/view/${goalId}`)
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success' && data.goal) {
                const goal = data.goal;

                document.getElementById('modal-goal-title').textContent = goal.goal_name;
                document.getElementById('modal-goal-category-type').textContent = `${goal.category} • ${goal.goal_type}`;
                
                // Icon
                let iconClass = 'fa-bullseye';
                if (goal.category === 'Education') iconClass = 'fa-graduation-cap';
                else if (goal.category === 'Travel') iconClass = 'fa-plane';
                else if (goal.category === 'Emergency') iconClass = 'fa-shield-halved';
                else if (goal.category === 'Personal') iconClass = 'fa-user';
                else if (goal.category === 'Shopping') iconClass = 'fa-bag-shopping';
                else if (goal.category === 'Health') iconClass = 'fa-heart-pulse';
                else if (goal.category === 'Family') iconClass = 'fa-users';
                document.getElementById('modal-category-icon').innerHTML = `<i class="fa-solid ${iconClass}"></i>`;

                // Badges
                const statBadge = document.getElementById('modal-status-badge');
                statBadge.className = `badge status-${(goal.status || '').toLowerCase().replace(/ /g, '-')}`;
                statBadge.textContent = goal.status;

                const priBadge = document.getElementById('modal-priority-badge');
                priBadge.className = `badge priority-${(goal.priority || '').toLowerCase()}`;
                priBadge.textContent = `${goal.priority} Priority`;

                // Financials
                document.getElementById('modal-target-amount').textContent = formatCurrency(goal.target_amount);
                document.getElementById('modal-current-amount').textContent = formatCurrency(goal.current_amount);
                document.getElementById('modal-remaining-amount').textContent = formatCurrency(goal.remaining_amount);

                // Progress Bar
                document.getElementById('modal-progress-percentage').textContent = `${goal.progress_percentage}%`;
                const progressFill = document.getElementById('modal-progress-fill');
                progressFill.style.width = `${goal.progress_percentage}%`;
                progressFill.className = `progress-fill ${goal.status === 'Completed' ? 'fill-completed' : (goal.status === 'Overdue' ? 'fill-overdue' : '')}`;

                // Timeline & text
                document.getElementById('modal-target-date').textContent = formatDateReadable(goal.target_date);
                document.getElementById('modal-remaining-days').textContent = goal.remaining_days_label || '-';
                document.getElementById('modal-description').textContent = goal.description || 'No description provided.';
                document.getElementById('modal-notes').textContent = goal.notes || 'No strategic notes added.';

                document.getElementById('modal-created-at').textContent = `Created: ${goal.created_at || '-'}`;
                document.getElementById('modal-updated-at').textContent = `Updated: ${goal.updated_at || '-'}`;

                // Edit Button Link
                document.getElementById('modal-edit-btn').href = `/goals/edit/${goal.goal_id}`;

                modal.style.display = 'flex';
                modal.setAttribute('aria-hidden', 'false');
            } else {
                showToast('Unable to load goal details.', 'error');
            }
        })
        .catch(err => {
            console.error('Error fetching goal details:', err);
            showToast('Something went wrong while fetching goal data.', 'error');
        });
}

/**
 * Closes the View Goal Modal.
 */
function closeViewModal() {
    const modal = document.getElementById('view-goal-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
    }
}

/**
 * Opens the Delete Confirmation Modal for a given goal.
 * 
 * @param {number} goalId - ID of goal to delete.
 * @param {string} goalName - Name of goal to confirm.
 */
function openDeleteConfirmModal(goalId, goalName) {
    const modal = document.getElementById('delete-confirm-modal');
    const placeholder = document.getElementById('delete-goal-name-placeholder');
    const form = document.getElementById('delete-goal-form');

    if (!modal || !placeholder || !form) return;

    placeholder.textContent = `"${goalName}"`;
    form.action = `/goals/delete/${goalId}`;

    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
}

/**
 * Closes the Delete Confirmation Modal.
 */
function closeDeleteConfirmModal() {
    const modal = document.getElementById('delete-confirm-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
    }
}

// Close modals on Escape key press or backdrop click
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeViewModal();
        closeDeleteConfirmModal();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const viewModal = document.getElementById('view-goal-modal');
    const deleteModal = document.getElementById('delete-confirm-modal');

    if (viewModal) {
        viewModal.addEventListener('click', (e) => {
            if (e.target === viewModal) closeViewModal();
        });
    }

    if (deleteModal) {
        deleteModal.addEventListener('click', (e) => {
            if (e.target === deleteModal) closeDeleteConfirmModal();
        });
    }
});
