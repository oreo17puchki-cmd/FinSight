from contextlib import contextmanager
import psycopg2
from psycopg2.extras import DictCursor, RealDictCursor
import pandas as pd
from datetime import date, datetime
from decimal import Decimal
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config


def _connection_kwargs():
    return {
        "host": Config.DB_HOST,
        "database": Config.DB_NAME,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
        "port": Config.DB_PORT or 5432,
        "cursor_factory": RealDictCursor,
    }


@contextmanager
def get_connection():
    conn = psycopg2.connect(**_connection_kwargs())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()



def init_db():
    return True


def _to_float(value, default=0.0):
    if value in (None, ""):
        return default
    return float(value)


def _to_int(value, default=0):
    if value in (None, ""):
        return default
    return int(value)


def _to_bool(value):
    return value in (True, "true", "True", "1", 1, "on", "yes", "Yes")


def _clean_budget_data(data):
    budget_amount = _to_float(data.get("budget_amount"), 0.0)
    spent_amount = _to_float(data.get("spent_amount"), 0.0)

    return {
        "budget_name": data.get("budget_name", "").strip(),
        "description": data.get("description", "").strip(),
        "category": data.get("category", "").strip(),
        "budget_amount": budget_amount,
        "spent_amount": spent_amount,
        "remaining_amount": budget_amount - spent_amount,
        "currency": data.get("currency") or "USD",
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "status": data.get("status") or "Active",
        "priority": data.get("priority") or "Medium",
        "expected_income": _to_float(data.get("expected_income"), 0.0),
        "expected_expenses": _to_float(data.get("expected_expenses"), 0.0),
        "savings_goal": _to_float(data.get("savings_goal"), 0.0),
        "alert_percentage": _to_int(data.get("alert_percentage"), 80),
        "color_label": data.get("color_label") or "#0E5A4E",
        "budget_icon": data.get("budget_icon") or "fa-wallet",
        "is_recurring": _to_bool(data.get("is_recurring")),
        "notes": data.get("notes", "").strip(),
    }


def _json_ready(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def serialize_row(row):
    if not row:
        return None
    return {key: _json_ready(value) for key, value in dict(row).items()}


def serialize_rows(rows):
    return [serialize_row(row) for row in rows]


def register_user(username, email, password):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT username, email FROM users WHERE email = %s OR username = %s",
                (email, username),
            )
            existing_user = cursor.fetchone()
            if existing_user:
                if existing_user["email"] == email:
                    return False, "Email already exists."
                return False, "Username already exists."

            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, username, email
                """,
                (username, email, generate_password_hash(password)),
            )
            return True, serialize_row(cursor.fetchone())


def login_user(email, password):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return False, None

    return True, serialize_row(user)


def create_budget(user_id, data):
    payload = _clean_budget_data(data)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO budgets (
                    user_id, budget_name, description, category, budget_amount,
                    spent_amount, remaining_amount, currency, start_date, end_date,
                    status, priority, expected_income, expected_expenses, savings_goal,
                    alert_percentage, color_label, budget_icon, is_recurring, notes
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                RETURNING budget_id
                """,
                (
                    user_id,
                    payload["budget_name"],
                    payload["description"],
                    payload["category"],
                    payload["budget_amount"],
                    payload["spent_amount"],
                    payload["remaining_amount"],
                    payload["currency"],
                    payload["start_date"],
                    payload["end_date"],
                    payload["status"],
                    payload["priority"],
                    payload["expected_income"],
                    payload["expected_expenses"],
                    payload["savings_goal"],
                    payload["alert_percentage"],
                    payload["color_label"],
                    payload["budget_icon"],
                    payload["is_recurring"],
                    payload["notes"],
                ),
            )
            return serialize_row(cursor.fetchone())


def get_all_budgets(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM budgets
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            return serialize_rows(cursor.fetchall())


def filter_budgets(
    user_id,
    search_query="",
    category_filter="All",
    status_filter="All",
    priority_filter="All",
    sort_by="newest",
):
    clauses = ["user_id = %s"]
    params = [user_id]

    if search_query:
        clauses.append(
            "(budget_name ILIKE %s OR category ILIKE %s OR description ILIKE %s OR notes ILIKE %s)"
        )
        term = f"%{search_query}%"
        params.extend([term, term, term, term])

    if category_filter and category_filter != "All":
        clauses.append("category = %s")
        params.append(category_filter)

    if status_filter and status_filter != "All":
        clauses.append("status = %s")
        params.append(status_filter)

    if priority_filter and priority_filter != "All":
        clauses.append("priority = %s")
        params.append(priority_filter)

    order_by = {
        "oldest": "created_at ASC",
        "amount_desc": "budget_amount DESC",
        "amount_asc": "budget_amount ASC",
    }.get(sort_by, "created_at DESC")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM budgets
                WHERE {" AND ".join(clauses)}
                ORDER BY {order_by}
                """,
                tuple(params),
            )
            return serialize_rows(cursor.fetchall())


def get_budget(budget_id, user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM budgets
                WHERE budget_id = %s AND user_id = %s
                """,
                (budget_id, user_id),
            )
            return serialize_row(cursor.fetchone())


def update_budget(budget_id, user_id, data):
    payload = _clean_budget_data(data)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE budgets
                SET
                    budget_name = %s,
                    description = %s,
                    category = %s,
                    budget_amount = %s,
                    spent_amount = %s,
                    remaining_amount = %s,
                    currency = %s,
                    start_date = %s,
                    end_date = %s,
                    status = %s,
                    priority = %s,
                    expected_income = %s,
                    expected_expenses = %s,
                    savings_goal = %s,
                    alert_percentage = %s,
                    color_label = %s,
                    budget_icon = %s,
                    is_recurring = %s,
                    notes = %s,
                    updated_at = NOW()
                WHERE budget_id = %s AND user_id = %s
                """,
                (
                    payload["budget_name"],
                    payload["description"],
                    payload["category"],
                    payload["budget_amount"],
                    payload["spent_amount"],
                    payload["remaining_amount"],
                    payload["currency"],
                    payload["start_date"],
                    payload["end_date"],
                    payload["status"],
                    payload["priority"],
                    payload["expected_income"],
                    payload["expected_expenses"],
                    payload["savings_goal"],
                    payload["alert_percentage"],
                    payload["color_label"],
                    payload["budget_icon"],
                    payload["is_recurring"],
                    payload["notes"],
                    budget_id,
                    user_id,
                ),
            )
            return cursor.rowcount > 0


def delete_budget(budget_id, user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM budgets
                WHERE budget_id=%s
                AND user_id=%s
                """,
                (budget_id, user_id),
            )

            return cursor.rowcount > 0


def get_summary_stats(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_budgets,
                    COUNT(*) FILTER (WHERE status = 'Active') AS active_budgets,
                    COUNT(*) FILTER (WHERE status = 'Completed') AS completed_budgets,
                    COALESCE(SUM(budget_amount), 0) AS total_allocated,
                    COALESCE(SUM(spent_amount), 0) AS total_spent,
                    COALESCE(SUM(remaining_amount), 0) AS total_remaining
                FROM budgets
                WHERE user_id = %s
                """,
                (user_id,),
            )
            stats = serialize_row(cursor.fetchone())

    return {
        "total_budgets": stats.get("total_budgets", 0),
        "active_budgets": stats.get("active_budgets", 0),
        "completed_budgets": stats.get("completed_budgets", 0),
        "total_allocated": stats.get("total_allocated", 0.0),
        "total_spent": stats.get("total_spent", 0.0),
        "total_remaining": stats.get("total_remaining", 0.0),
    }


def ensure_transactions_table():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
                    type VARCHAR(20) NOT NULL DEFAULT 'Expense',
                    category VARCHAR(80) NOT NULL,
                    date DATE NOT NULL,
                    description TEXT,
                    payment_mode VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_transactions_user_id
                ON transactions(user_id)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_transactions_user_type
                ON transactions(user_id, type)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_transactions_user_date
                ON transactions(user_id, date DESC)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_transactions_user_category
                ON transactions(user_id, category)
                """
            )


def _clean_transaction_data(data):
    return {
        "amount": _to_float(data.get("amount"), 0.0),
        "category": data.get("category", "").strip(),
        "date": data.get("date"),
        "description": data.get("description", "").strip(),
        "payment_mode": data.get("payment_mode", "").strip(),
    }


def create_transaction(user_id, data):
    ensure_transactions_table()
    payload = _clean_transaction_data(data)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO transactions (
                    user_id, amount, type, category, date, description, payment_mode
                )
                VALUES (%s, %s, 'Expense', %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user_id,
                    payload["amount"],
                    payload["category"],
                    payload["date"],
                    payload["description"],
                    payload["payment_mode"],
                ),
            )
            return serialize_row(cursor.fetchone())


def get_transactions(
    user_id,
    search_query="",
    category_filter="All",
    payment_filter="All",
    sort_by="newest",
):
    ensure_transactions_table()
    clauses = ["user_id = %s", "type = 'Expense'"]
    params = [user_id]

    if search_query:
        clauses.append("(description ILIKE %s OR category ILIKE %s OR payment_mode ILIKE %s)")
        term = f"%{search_query}%"
        params.extend([term, term, term])

    if category_filter and category_filter != "All":
        clauses.append("category = %s")
        params.append(category_filter)

    if payment_filter and payment_filter != "All":
        clauses.append("payment_mode = %s")
        params.append(payment_filter)

    order_by = {
        "oldest": "date ASC, created_at ASC",
        "amount_desc": "amount DESC",
        "amount_asc": "amount ASC",
    }.get(sort_by, "date DESC, created_at DESC")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM transactions
                WHERE {" AND ".join(clauses)}
                ORDER BY {order_by}
                """,
                tuple(params),
            )
            return serialize_rows(cursor.fetchall())


def get_transaction(transaction_id, user_id):
    ensure_transactions_table()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM transactions
                WHERE id = %s
                AND user_id = %s
                AND type = 'Expense'
                """,
                (transaction_id, user_id),
            )
            return serialize_row(cursor.fetchone())


def update_transaction(transaction_id, user_id, data):
    ensure_transactions_table()
    payload = _clean_transaction_data(data)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE transactions
                SET
                    amount = %s,
                    category = %s,
                    date = %s,
                    description = %s,
                    payment_mode = %s,
                    updated_at = NOW()
                WHERE id = %s
                AND user_id = %s
                AND type = 'Expense'
                """,
                (
                    payload["amount"],
                    payload["category"],
                    payload["date"],
                    payload["description"],
                    payload["payment_mode"],
                    transaction_id,
                    user_id,
                ),
            )
            return cursor.rowcount > 0


def delete_transaction(transaction_id, user_id):
    ensure_transactions_table()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM transactions
                WHERE id = %s
                AND user_id = %s
                AND type = 'Expense'
                """,
                (transaction_id, user_id),
            )
            return cursor.rowcount > 0


def get_expense_summary(user_id):
    ensure_transactions_table()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_expenses,
                    COALESCE(SUM(amount), 0) AS total_spent,
                    COALESCE(AVG(amount), 0) AS average_expense,
                    COALESCE(MAX(amount), 0) AS largest_expense,
                    COUNT(*) FILTER (
                        WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
                        AND date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                    ) AS month_expenses,
                    COALESCE(SUM(amount) FILTER (
                        WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
                        AND date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                    ), 0) AS month_spent
                FROM transactions
                WHERE user_id = %s
                AND type = 'Expense'
                """,
                (user_id,),
            )
            summary = serialize_row(cursor.fetchone())

            cursor.execute(
                """
                SELECT category, COALESCE(SUM(amount), 0) AS total
                FROM transactions
                WHERE user_id = %s
                AND type = 'Expense'
                GROUP BY category
                ORDER BY total DESC
                LIMIT 1
                """,
                (user_id,),
            )
            top_category = serialize_row(cursor.fetchone())

    return {
        "total_expenses": summary.get("total_expenses", 0),
        "total_spent": summary.get("total_spent", 0.0),
        "average_expense": summary.get("average_expense", 0.0),
        "largest_expense": summary.get("largest_expense", 0.0),
        "month_expenses": summary.get("month_expenses", 0),
        "month_spent": summary.get("month_spent", 0.0),
        "top_category": top_category.get("category", "No data") if top_category else "No data",
    }


def calculate_burn_rate_metrics(df):
    if df is None or df.empty:
        # Default benchmark — ₹60,000/month employee, 60% expenses (₹36,000), 40% savings (₹24,000)
        return {
            "phases": [
                {
                    "phase_id": 1,
                    "phase_name": "Phase 1 (Days 1-10)",
                    "subtitle": "Post-Payday Surge",
                    "total_amount": 18500.0,
                    "daily_avg": 1850.0,
                    "days": 10,
                    "percentage": 51.4,
                    "color": "#941334"
                },
                {
                    "phase_id": 2,
                    "phase_name": "Phase 2 (Days 11-20)",
                    "subtitle": "Mid-Month Baseline",
                    "total_amount": 11000.0,
                    "daily_avg": 1100.0,
                    "days": 10,
                    "percentage": 30.6,
                    "color": "#E5A93C"
                },
                {
                    "phase_id": 3,
                    "phase_name": "Phase 3 (Days 21-End)",
                    "subtitle": "Month-End Frugality",
                    "total_amount": 6500.0,
                    "daily_avg": 650.0,
                    "days": 10,
                    "percentage": 18.1,
                    "color": "#3E8299"
                }
            ],
            "max_daily_avg": 1850.0,
            "total_monthly_spending": 36000.0,
            "multiplier": 2.85,
            "phase_1_percentage": 51.4,
            "status": "surge",
            "alert_theme": "warning",
            "alert_icon": "fa-solid fa-triangle-exclamation",
            "alert_title": "Post-Payday Surge Detected:",
            "alert_line_1": "Your daily spending in Days 1-10 is 2.85x higher than Month-End.",
            "alert_line_2": "51.4% of total monthly expenses occurred in the first 10 days."
        }
    
    df_burn = df.copy()
    df_burn["amount"] = pd.to_numeric(df_burn["amount"], errors="coerce").fillna(0.0)
    df_burn["date"] = pd.to_datetime(df_burn["date"], errors="coerce")
    df_burn = df_burn.dropna(subset=["date"])
    
    if df_burn.empty:
        return calculate_burn_rate_metrics(None)
        
    df_burn["day"] = df_burn["date"].dt.day
    
    # Phase 1: Days 1-10
    p1 = df_burn[(df_burn["day"] >= 1) & (df_burn["day"] <= 10)]
    p1_total = float(p1["amount"].sum())
    p1_days = 10
    p1_avg = p1_total / p1_days
    
    # Phase 2: Days 11-20
    p2 = df_burn[(df_burn["day"] >= 11) & (df_burn["day"] <= 20)]
    p2_total = float(p2["amount"].sum())
    p2_days = 10
    p2_avg = p2_total / p2_days
    
    # Phase 3: Days 21-End
    p3 = df_burn[df_burn["day"] >= 21]
    p3_total = float(p3["amount"].sum())
    p3_days = 10
    p3_avg = p3_total / p3_days
    
    total_monthly = p1_total + p2_total + p3_total
    
    if total_monthly <= 0:
        return calculate_burn_rate_metrics(None)

    p1_pct = round((p1_total / total_monthly) * 100, 1)
    p2_pct = round((p2_total / total_monthly) * 100, 1)
    p3_pct = round((p3_total / total_monthly) * 100, 1)
    
    max_avg = max(p1_avg, p2_avg, p3_avg, 1.0)
    
    if p3_avg > 0:
        multiplier = round(p1_avg / p3_avg, 1)
        line_1 = f"Your daily spending in Days 1-10 is {multiplier:.1f}x higher than Month-End."
    elif p2_avg > 0:
        multiplier = round(p1_avg / p2_avg, 1)
        line_1 = f"Your daily spending in Days 1-10 is {multiplier:.1f}x higher than Mid-Month Baseline."
    else:
        multiplier = 1.0
        line_1 = "Spending in Days 1-10 represents the dominant portion of your monthly expenses."
        
    line_2 = f"{p1_pct:.1f}% of total monthly expenses occurred in the first 10 days."
    
    if multiplier >= 1.5 or p1_pct >= 45.0:
        status = "surge"
        alert_theme = "warning"
        alert_icon = "fa-solid fa-triangle-exclamation"
        alert_title = "Post-Payday Surge Detected:"
    elif p2_avg > p1_avg and p2_avg > p3_avg:
        status = "mid_surge"
        alert_theme = "info"
        alert_icon = "fa-solid fa-circle-info"
        alert_title = "Mid-Month Spike Detected:"
        line_1 = f"Your daily spending peaked in Days 11-20 at ₹{p2_avg:,.0f}/day."
        line_2 = f"Mid-month spending accounted for {p2_pct:.1f}% of monthly expenses."
    else:
        status = "balanced"
        alert_theme = "success"
        alert_icon = "fa-solid fa-circle-check"
        alert_title = "Balanced Monthly Burn Rate:"
        line_1 = "Your daily spending is evenly distributed throughout the month."
        line_2 = f"First 10 days accounted for {p1_pct:.1f}% of total monthly expenses."
        
    return {
        "phases": [
            {
                "phase_id": 1,
                "phase_name": "Phase 1 (Days 1-10)",
                "subtitle": "Post-Payday Surge",
                "total_amount": round(p1_total, 2),
                "daily_avg": round(p1_avg, 2),
                "days": p1_days,
                "percentage": p1_pct,
                "color": "#8b1538"
            },
            {
                "phase_id": 2,
                "phase_name": "Phase 2 (Days 11-20)",
                "subtitle": "Mid-Month Baseline",
                "total_amount": round(p2_total, 2),
                "daily_avg": round(p2_avg, 2),
                "days": p2_days,
                "percentage": p2_pct,
                "color": "#d99b38"
            },
            {
                "phase_id": 3,
                "phase_name": "Phase 3 (Days 21-End)",
                "subtitle": "Month-End Frugality",
                "total_amount": round(p3_total, 2),
                "daily_avg": round(p3_avg, 2),
                "days": p3_days,
                "percentage": p3_pct,
                "color": "#388299"
            }
        ],
        "max_daily_avg": round(max_avg, 2),
        "total_monthly_spending": round(total_monthly, 2),
        "multiplier": multiplier,
        "phase_1_percentage": p1_pct,
        "status": status,
        "alert_theme": alert_theme,
        "alert_icon": alert_icon,
        "alert_title": alert_title,
        "alert_line_1": line_1,
        "alert_line_2": line_2
    }



def calculate_labor_equivalency(df, monthly_salary=60000.0):
    """
    Translates discretionary spending into work hours and work days.
    Standard: 160 working hours/month (20 days × 8 hrs/day).
    """
    WORK_HOURS_PER_MONTH = 160.0
    WORK_HOURS_PER_DAY   = 8.0

    # Hourly wage
    hourly_rate = monthly_salary / WORK_HOURS_PER_MONTH

    # Discretionary category aliases (flexible matching)
    CATEGORY_MAP = {
        "shopping":     ["Shopping", "Clothing", "Lifestyle"],
        "dining":       ["Meals (clients or travel)", "Dining", "Food & Dining", "Restaurants", "Meals"],
        "entertainment": ["Entertainment", "Recreation", "Leisure", "Movies", "Sports"],
    }

    def _sum_categories(df_inner, aliases):
        if df_inner is None or df_inner.empty:
            return 0.0
        mask = df_inner["category"].str.lower().apply(
            lambda c: any(a.lower() in c or c in a.lower() for a in aliases)
        )
        return float(df_inner.loc[mask, "amount"].sum())

    # Fallback mock amounts (match new ₹60k salary discretionary target values)
    if df is None or df.empty:
        shop_amt = 6000.0
        dine_amt = 4500.0
        ent_amt  = 1875.0
    else:
        shop_amt = _sum_categories(df, CATEGORY_MAP["shopping"])
        dine_amt = _sum_categories(df, CATEGORY_MAP["dining"])
        ent_amt  = _sum_categories(df, CATEGORY_MAP["entertainment"])

    def _hrs(amt):
        return round(amt / hourly_rate, 1) if hourly_rate > 0 else 0.0

    def _days(hrs):
        return round(hrs / WORK_HOURS_PER_DAY, 1)

    shop_hrs  = _hrs(shop_amt);  shop_days  = _days(shop_hrs)
    dine_hrs  = _hrs(dine_amt);  dine_days  = _days(dine_hrs)
    ent_hrs   = _hrs(ent_amt);   ent_days   = _days(ent_hrs)
    total_hrs  = round(shop_hrs + dine_hrs + ent_hrs, 1)
    total_days = _days(total_hrs)

    return {
        "hourly_rate": round(hourly_rate, 0),
        "monthly_salary": monthly_salary,
        "work_hours_per_month": WORK_HOURS_PER_MONTH,
        "categories": [
            {
                "key": "shopping",
                "label": "Shopping",
                "icon": "🛍️",
                "amount": shop_amt,
                "hours": shop_hrs,
                "days": shop_days,
            },
            {
                "key": "dining",
                "label": "Dining / Meals",
                "icon": "🍽️",
                "amount": dine_amt,
                "hours": dine_hrs,
                "days": dine_days,
            },
            {
                "key": "entertainment",
                "label": "Entertainment",
                "icon": "🎬",
                "amount": ent_amt,
                "hours": ent_hrs,
                "days": ent_days,
            },
        ],
        "total_hours": total_hrs,
        "total_days": total_days,
        "callout": (
            f"You worked {total_hrs} hours (~{total_days} working days) "
            f"this month solely to fund discretionary lifestyle purchases."
        ),
    }


def get_spending_analysis_data(user_id, time_window="MTD"):
    ensure_transactions_table()
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Fetch all expenses for the user
            cursor.execute(
                """
                SELECT id, category, amount, date
                FROM transactions
                WHERE user_id = %s AND type = 'Expense'
                ORDER BY date ASC
                """, (user_id,)
            )
            rows = cursor.fetchall()
            
            # Query user's monthly salary from Income transactions (e.g. Current Month or Fallback)
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0.0) as salary
                FROM transactions
                WHERE user_id = %s AND type = 'Income' AND date >= DATE_TRUNC('month', CURRENT_DATE)
                """, (user_id,)
            )
            salary_row = cursor.fetchone()
            monthly_salary = float(salary_row["salary"]) if salary_row and salary_row["salary"] else 0.0
            
            # If no income found in the current month, fallback to the latest income transaction
            if monthly_salary <= 0.0:
                cursor.execute(
                    """
                    SELECT amount
                    FROM transactions
                    WHERE user_id = %s AND type = 'Income'
                    ORDER BY date DESC, id DESC
                    LIMIT 1
                    """ , (user_id,)
                )
                latest_salary_row = cursor.fetchone()
                monthly_salary = float(latest_salary_row["amount"]) if latest_salary_row else 60000.0

    is_mock = False
    if not rows:
        is_mock = True
        import datetime as _dt
        today_date = _dt.datetime.today().date()
        
        # Spread mock transactions across 30 days so each time window shows different data
        DEFAULT_MOCK_TRANSACTIONS = [
            # Recent (within last 7 days) — visible in all filters
            {"category": "Home", "amount": 21450.00, "days_ago": 1},
            {"category": "Shopping", "amount": 6000.00, "days_ago": 3},
            {"category": "Entertainment", "amount": 1875.00, "days_ago": 5},
            # Mid-range (8-20 days ago) — visible in MTD and L30D only
            {"category": "Home", "amount": 14200.00, "days_ago": 10},
            {"category": "Meals (clients or travel)", "amount": 4500.00, "days_ago": 12},
            {"category": "Car & Truck", "amount": 8450.00, "days_ago": 15},
            # Older (21-30 days ago) — visible in L30D only
            {"category": "Personal Care", "amount": 3592.00, "days_ago": 22},
            {"category": "Uncategorized", "amount": 1476.00, "days_ago": 28},
        ]
        rows = []
        for i, m in enumerate(DEFAULT_MOCK_TRANSACTIONS):
            dt = today_date - _dt.timedelta(days=m["days_ago"])
            rows.append({"id": i, "category": m["category"], "amount": m["amount"], "date": dt})

    # Convert DictRows to dictionaries
    full_df = pd.DataFrame([dict(row) for row in rows])
    
    # Ensure amount is numeric
    full_df["amount"] = pd.to_numeric(full_df["amount"])
    full_df["date"] = pd.to_datetime(full_df["date"])
    
    # Apply Time Window Filter
    today = pd.Timestamp.today().normalize()
    if time_window == "MTD":
        start_date = today.replace(day=1)
    elif time_window == "L7D":
        start_date = today - pd.Timedelta(days=6)
    elif time_window == "L30D":
        start_date = today - pd.Timedelta(days=29)
    else:
        start_date = today.replace(day=1)
        
    df = full_df[(full_df["date"] >= start_date) & (full_df["date"] <= today)]
    
    # Calculate burn rate metrics and labor equivalency dynamically on the filtered df
    if is_mock or df.empty:
        burn_rate_data = calculate_burn_rate_metrics(None)
        labor_data = calculate_labor_equivalency(None, monthly_salary=monthly_salary)
    else:
        burn_rate_data = calculate_burn_rate_metrics(df)
        labor_data = calculate_labor_equivalency(df, monthly_salary=monthly_salary)
    
    if df.empty:
        return {
            "total_expenses": 0.0,
            "date_range": f"{start_date.strftime('%b %d, %Y')} - {today.strftime('%b %d, %Y')}",
            "spend_by_category": [],
            "assist_insights": {
                "summary": "No spending data available in this time window.",
                "top_spending": []
            },
            "burn_rate": burn_rate_data,
            "labor_equivalency": labor_data
        }
    df["amount"] = pd.to_numeric(df["amount"])
    
    total_spend = float(df["amount"].sum())
    
    # Calculate Date Range
    min_date = df["date"].min().strftime("%b %d, %Y")
    max_date = df["date"].max().strftime("%b %d, %Y")
    date_range = f"{min_date} - {max_date}"

    # Category Breakdown
    cat_df = df.groupby("category")["amount"].sum().reset_index().sort_values(by="amount", ascending=False)
    
    spend_by_category = []
    for _, row in cat_df.iterrows():
        spend_by_category.append({
            "category": row["category"],
            "amount": float(row["amount"]),
            "percentage": round((row["amount"] / total_spend) * 100, 2)
        })

    # Assist Insights Generation
    summary_text = (f"In the period from {min_date} to {max_date}, total spending was "
                    f"₹{total_spend:,.2f} across all available categories. ")
    
    if len(cat_df) > 0:
        top_cat = cat_df.iloc[0]
        summary_text += f"The largest share of expenses went to {top_cat['category']}, accounting for ₹{top_cat['amount']:,.2f}."
        
    top_spending = [f"• {c['category']}: ₹{c['amount']:,.2f}" for c in spend_by_category[:5]]
    
    return {
        "total_expenses": total_spend,
        "date_range": date_range,
        "spend_by_category": spend_by_category,
        "assist_insights": {
            "summary": summary_text,
            "top_spending": top_spending
        },
        "burn_rate": burn_rate_data,
        "labor_equivalency": labor_data
    }
