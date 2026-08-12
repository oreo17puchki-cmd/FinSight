"""
=============================================================================
FinSight Financial Goal Planning Module - Flask Blueprint Routes (backend/goal.py)
=============================================================================
This file defines all Flask routes for Goal Planning:
- GET  /goals             : Main Goal Planning Dashboard view
- GET  /goals/create      : Form view for creating a new goal
- POST /goals/create      : Process creation with strict backend validation
- GET  /goals/edit/<id>   : Form view populated with existing goal data
- POST /goals/edit/<id>   : Process goal update with strict backend validation
- POST /goals/delete/<id> : Process goal deletion
- GET  /goals/view/<id>   : API endpoint returning single goal JSON for modal
- GET  /goals/search      : Real-time search/filter/sort API endpoint returning JSON
"""

import datetime
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
import goal_db as db

# Create Blueprint named 'goal'
goal_bp = Blueprint('goal', __name__, url_prefix='/goals')

VALID_CATEGORIES = ['Education', 'Travel', 'Emergency', 'Personal', 'Shopping', 'Health', 'Family', 'Other']
VALID_TYPES = ['Short Term', 'Medium Term', 'Long Term']
VALID_PRIORITIES = ['Low', 'Medium', 'High']


# =============================================================================
# BACKEND VALIDATION HELPER
# =============================================================================

def validate_goal_input(form_data):
    """
    Strict server-side validation for goal creation and updates.
    Never trusts client-side validation alone.
    
    Returns:
        tuple: (errors_list, cleaned_data_dict)
    """
    errors = []
    cleaned = {}
    
    # 1. Validate Goal Name
    goal_name = form_data.get('goal_name', '').strip()
    if not goal_name:
        errors.append("Goal name is required.")
    elif len(goal_name) > 150:
        errors.append("Goal name cannot exceed 150 characters.")
    cleaned['goal_name'] = goal_name

    # 2. Validate Description / Notes
    cleaned['description'] = form_data.get('description', '').strip()
    cleaned['notes'] = form_data.get('notes', '').strip()

    # 3. Validate Goal Type
    goal_type = form_data.get('goal_type', '').strip()
    if goal_type not in VALID_TYPES:
        errors.append(f"Invalid goal type. Must be one of: {', '.join(VALID_TYPES)}")
    cleaned['goal_type'] = goal_type

    # 4. Validate Target Amount
    target_str = form_data.get('target_amount', '').strip()
    try:
        target_amount = float(target_str)
        if target_amount <= 0:
            errors.append("Target amount must be greater than ₹0.")
        cleaned['target_amount'] = target_amount
    except (ValueError, TypeError):
        errors.append("Target amount must be a valid numeric amount.")

    # 5. Validate Current Amount
    current_str = form_data.get('current_amount', '0').strip()
    if not current_str:
        current_str = '0'
    try:
        current_amount = float(current_str)
        if current_amount < 0:
            errors.append("Current saved amount cannot be negative.")
        cleaned['current_amount'] = current_amount
    except (ValueError, TypeError):
        errors.append("Current saved amount must be a valid numeric amount.")

    # 6. Validate Target Date
    target_date_str = form_data.get('target_date', '').strip()
    if not target_date_str:
        errors.append("Please select a target date.")
    else:
        try:
            target_date_obj = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
            cleaned['target_date'] = target_date_str
        except ValueError:
            errors.append("Target date must be a valid date in YYYY-MM-DD format.")

    # 7. Validate Category
    category = form_data.get('category', '').strip()
    if category not in VALID_CATEGORIES:
        errors.append(f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}")
    cleaned['category'] = category

    # 8. Validate Priority
    priority = form_data.get('priority', '').strip()
    if priority not in VALID_PRIORITIES:
        errors.append(f"Invalid priority. Must be one of: {', '.join(VALID_PRIORITIES)}")
    cleaned['priority'] = priority

    return errors, cleaned


# =============================================================================
# FLASK ROUTES IMPLEMENTATION
# =============================================================================

@goal_bp.route('', methods=['GET'])
def dashboard():
    """
    GET /goals
    Renders the Financial Goal Planning Dashboard with summary metrics & goals.
    """
    try:
        goals = db.get_all_goals()
        summary = db.get_goal_summary()
        today_date = datetime.date.today().strftime("%B %d, %Y")
        return render_template(
            'goal_dashboard.html',
            goals=goals,
            summary=summary,
            today_date=today_date,
            categories=VALID_CATEGORIES,
            types=VALID_TYPES,
            priorities=VALID_PRIORITIES
        )
    except Exception as e:
        print(f"[Route Error /goals]: {e}")
        # Return fallback empty state if database is loading/initializing
        return render_template(
            'goal_dashboard.html',
            goals=[],
            summary={
                "total_goals": 0, "active_goals": 0, "completed_goals": 0,
                "total_target_amount": 0, "total_saved_amount": 0, "total_remaining_amount": 0
            },
            today_date=datetime.date.today().strftime("%B %d, %Y"),
            categories=VALID_CATEGORIES,
            types=VALID_TYPES,
            priorities=VALID_PRIORITIES,
            db_error="Database is initializing or not connected. Please create/check PostgreSQL database."
        )


@goal_bp.route('/create', methods=['GET'])
def create_form():
    """
    GET /goals/create
    Renders the Create Financial Goal form page.
    """
    return render_template(
        'goal_form.html',
        mode='create',
        goal=None,
        categories=VALID_CATEGORIES,
        types=VALID_TYPES,
        priorities=VALID_PRIORITIES
    )


@goal_bp.route('/create', methods=['POST'])
def create_action():
    """
    POST /goals/create
    Validates form data and creates a new financial goal record.
    Supports both traditional HTML form submission and asynchronous JSON fetch requests.
    """
    is_json = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    data_source = request.get_json() if request.is_json else request.form
    
    errors, cleaned_data = validate_goal_input(data_source)
    
    if errors:
        if is_json:
            return jsonify({"status": "error", "message": errors[0], "errors": errors}), 400
        for err in errors:
            flash(err, "error")
        return render_template(
            'goal_form.html',
            mode='create',
            goal=data_source,
            errors=errors,
            categories=VALID_CATEGORIES,
            types=VALID_TYPES,
            priorities=VALID_PRIORITIES
        ), 400

    try:
        new_goal = db.create_goal(cleaned_data)
        if is_json:
            return jsonify({
                "status": "success",
                "message": "Goal created successfully.",
                "goal": new_goal,
                "redirect_url": url_for('goal.dashboard')
            }), 201
            
        flash("Goal created successfully.", "success")
        return redirect(url_for('goal.dashboard'))
    except Exception as e:
        error_msg = "Unable to save goal. Database error occurred."
        if is_json:
            return jsonify({"status": "error", "message": error_msg, "detail": str(e)}), 500
        flash(error_msg, "error")
        return render_template(
            'goal_form.html',
            mode='create',
            goal=cleaned_data,
            errors=[error_msg],
            categories=VALID_CATEGORIES,
            types=VALID_TYPES,
            priorities=VALID_PRIORITIES
        ), 500


@goal_bp.route('/edit/<int:goal_id>', methods=['GET'])
def edit_form(goal_id):
    """
    GET /goals/edit/<id>
    Fetches existing goal data and renders the Edit Financial Goal page.
    """
    goal = db.get_goal(goal_id)
    if not goal:
        flash("Goal not found.", "error")
        return redirect(url_for('goal.dashboard'))
        
    return render_template(
        'goal_form.html',
        mode='edit',
        goal=goal,
        goal_id=goal_id,
        categories=VALID_CATEGORIES,
        types=VALID_TYPES,
        priorities=VALID_PRIORITIES
    )


@goal_bp.route('/edit/<int:goal_id>', methods=['POST'])
def edit_action(goal_id):
    """
    POST /goals/edit/<id>
    Validates updated values and modifies the target financial goal in PostgreSQL.
    """
    is_json = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    data_source = request.get_json() if request.is_json else request.form
    
    existing_goal = db.get_goal(goal_id)
    if not existing_goal:
        msg = "Goal not found for editing."
        if is_json:
            return jsonify({"status": "error", "message": msg}), 404
        flash(msg, "error")
        return redirect(url_for('goal.dashboard'))

    errors, cleaned_data = validate_goal_input(data_source)
    
    if errors:
        if is_json:
            return jsonify({"status": "error", "message": errors[0], "errors": errors}), 400
        for err in errors:
            flash(err, "error")
        return render_template(
            'goal_form.html',
            mode='edit',
            goal=data_source,
            goal_id=goal_id,
            errors=errors,
            categories=VALID_CATEGORIES,
            types=VALID_TYPES,
            priorities=VALID_PRIORITIES
        ), 400

    try:
        updated_goal = db.update_goal(goal_id, cleaned_data)
        if is_json:
            return jsonify({
                "status": "success",
                "message": "Goal updated successfully.",
                "goal": updated_goal,
                "redirect_url": url_for('goal.dashboard')
            }), 200
            
        flash("Goal updated successfully.", "success")
        return redirect(url_for('goal.dashboard'))
    except Exception as e:
        error_msg = "Unable to update goal. Database error occurred."
        if is_json:
            return jsonify({"status": "error", "message": error_msg, "detail": str(e)}), 500
        flash(error_msg, "error")
        return render_template(
            'goal_form.html',
            mode='edit',
            goal=cleaned_data,
            goal_id=goal_id,
            errors=[error_msg],
            categories=VALID_CATEGORIES,
            types=VALID_TYPES,
            priorities=VALID_PRIORITIES
        ), 500


@goal_bp.route('/delete/<int:goal_id>', methods=['POST'])
def delete_action(goal_id):
    """
    POST /goals/delete/<id>
    Deletes the financial goal from the database.
    """
    is_json = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    success = db.delete_goal(goal_id)
    
    if success:
        msg = "Goal deleted successfully."
        if is_json:
            return jsonify({"status": "success", "message": msg, "goal_id": goal_id}), 200
        flash(msg, "success")
    else:
        msg = "Goal not found or could not be deleted."
        if is_json:
            return jsonify({"status": "error", "message": msg}), 404
        flash(msg, "error")
        
    return redirect(url_for('goal.dashboard'))


@goal_bp.route('/view/<int:goal_id>', methods=['GET'])
def view_goal_json(goal_id):
    """
    GET /goals/view/<id>
    API endpoint returning individual goal details in JSON format for the View Modal.
    """
    goal = db.get_goal(goal_id)
    if not goal:
        return jsonify({"status": "error", "message": "Goal not found."}), 404
    return jsonify({"status": "success", "goal": goal}), 200


@goal_bp.route('/search', methods=['GET'])
def search_and_filter():
    """
    GET /goals/search
    API endpoint for real-time search, filter, and sort on the Goal Dashboard.
    Parameters: q (query), category, goal_type, priority, status, sort_by
    """
    search_q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    goal_type = request.args.get('goal_type', '').strip()
    priority = request.args.get('priority', '').strip()
    status = request.args.get('status', '').strip()
    sort_by = request.args.get('sort_by', 'newest').strip()
    
    goals = db.get_all_goals(
        category=category,
        goal_type=goal_type,
        priority=priority,
        status=status,
        search=search_q,
        sort_by=sort_by
    )
    summary = db.get_goal_summary()
    
    return jsonify({
        "status": "success",
        "count": len(goals),
        "goals": goals,
        "summary": summary
    }), 200
