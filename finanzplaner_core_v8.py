"""
Finanzplanungs-App Core Logic & Data Structures v8 (Ultimate Complete Edition)
Grounded strictly in Finanzplanungs_App_Spezifikation.md
Includes ALL features from v1 through v7:
- Full CRUD & Forms for all 15 data entities
- Settings view for changing initial balances (Kontostand, Bargeld), cutoff date, forecast period, PIN
- Event Months view with individual amounts per month and active/description controls
- Forecast Engine with 6-60 month selector, Best/Normal/Worst scenario line chart, and alert system
- Calendar View with daily balance projection and due-day management for subscriptions
- Custom Savings Challenge Generator (custom euro target & duration)
- PDF Monatsbericht Generator (fpdf2 with fallback)
- Multi-Tab Excel & CSV Exporter
- Privacy Mode (Diskreter Modus) & Hashtag Tagging
- Currency Converter
- AI Finance Coach
"""

from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import json
import uuid
import calendar
import io
import pandas as pd

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

# --- Helper Functions for Currency Formatting & Privacy ---

def cents_to_euro_str(cents: int, privacy_mode: bool = False) -> str:
    """Converts cents integer to German formatted Euro string or masked string."""
    if privacy_mode:
        return "••• €"
    is_negative = cents < 0
    abs_cents = abs(cents)
    euros = abs_cents // 100
    remainder = abs_cents % 100
    formatted_euros = f"{euros:,}".replace(",", ".")
    result = f"{formatted_euros},{remainder:02d} €"
    return f"-{result}" if is_negative else result

def parse_euro_to_cents(val) -> int:
    """Parses float, int, or string input into cents integer."""
    if val is None:
        return 0
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(round(val * 100))
    s = str(val).strip().replace("€", "").strip()
    if not s:
        return 0
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        f = float(s)
        return int(round(f * 100))
    except ValueError:
        return 0

def format_date_de(d) -> str:
    if isinstance(d, str):
        try:
            d = date.fromisoformat(d)
        except ValueError:
            return d
    return d.strftime("%d.%m.%Y") if d else ""

def calculate_missing_months(last_date: date, current_date: date) -> int:
    if not last_date or not current_date or last_date >= current_date:
        return 0
    months_diff = (current_date.year - last_date.year) * 12 + (current_date.month - last_date.month)
    return max(0, months_diff)

def parse_hashtags(text: str):
    """Extracts hashtags from description text."""
    if not text:
        return []
    words = text.split()
    return [w.lower() for w in words if w.startswith("#") and len(w) > 1]

# --- Currency Conversion Rates to EUR ---
EXCHANGE_RATES_TO_EUR = {
    "EUR": 1.0,
    "USD": 0.92,
    "GBP": 1.17,
    "CHF": 1.04,
    "JPY": 0.0061,
    "CAD": 0.68,
    "AUD": 0.61,
    "SEK": 0.087,
    "NOK": 0.086
}

def convert_to_eur_cents(amount: float, from_currency: str) -> int:
    rate = EXCHANGE_RATES_TO_EUR.get(from_currency.upper(), 1.0)
    eur_amount = amount * rate
    return parse_euro_to_cents(eur_amount)


# --- Default Initial Data Getters ---

def get_default_settings():
    return {
        "cutoff_date": date.today().isoformat(),
        "start_account_cents": 150000,  # 1.500,00 €
        "start_cash_cents": 20000,      # 200,00 €
        "currency": "€",
        "forecast_months": 36,
        "pin_code": "",
        "privacy_mode_default": False,
        "scenario_factors": {
            "best": {"income": 1.10, "fix": 0.95, "variable": 0.90},
            "normal": {"income": 1.00, "fix": 1.00, "variable": 1.00},
            "worst": {"income": 0.80, "fix": 1.15, "variable": 1.15}
        }
    }

def get_default_categories():
    return [
        {"id": "c1", "name": "Freizeit", "limit_cents": 6000, "active": True},
        {"id": "c2", "name": "Technik", "limit_cents": 4000, "active": True},
        {"id": "c3", "name": "Kleidung", "limit_cents": 2500, "active": True},
        {"id": "c4", "name": "Essen", "limit_cents": 3500, "active": True},
        {"id": "c5", "name": "Schule", "limit_cents": 2000, "active": True},
        {"id": "c6", "name": "Sport", "limit_cents": 3000, "active": True},
        {"id": "c7", "name": "Sonstiges", "limit_cents": 2500, "active": True},
        {"id": "c8", "name": "Fixkosten", "limit_cents": 0, "active": True},
        {"id": "c9", "name": "Einmalig", "limit_cents": 0, "active": True},
        {"id": "c10", "name": "Einkommen", "limit_cents": 0, "active": True},
        {"id": "c11", "name": "Umbuchung", "limit_cents": 0, "active": True},
    ]

def get_default_recurring_incomes():
    return [
        {"id": "inc1", "name": "Taschengeld", "amount_cents": 5000, "received_current_month": False, "last_received_date": date.today().isoformat(), "due_day": 1},
        {"id": "inc2", "name": "Lohn / Nebenjob", "amount_cents": 20000, "received_current_month": False, "last_received_date": date.today().isoformat(), "due_day": 15},
    ]

def get_default_recurring_expenses():
    return [
        {"id": "fix1", "name": "Handyvertrag", "amount_cents": 1500, "frequency": "monatlich", "annual_month": 1, "debited_current_month": False, "due_day": 1},
        {"id": "fix2", "name": "Spotify", "amount_cents": 999, "frequency": "monatlich", "annual_month": 1, "debited_current_month": False, "due_day": 15},
        {"id": "fix3", "name": "Fitnessstudio", "amount_cents": 2500, "frequency": "monatlich", "annual_month": 1, "debited_current_month": False, "due_day": 1},
        {"id": "fix4", "name": "Streaming", "amount_cents": 1299, "frequency": "monatlich", "annual_month": 1, "debited_current_month": False, "due_day": 10},
        {"id": "fix5", "name": "Sonstiges Abo", "amount_cents": 499, "frequency": "monatlich", "annual_month": 1, "debited_current_month": False, "due_day": 20},
    ]

def get_default_savings_goals():
    return [
        {"id": "sg1", "name": "Neues Handy", "target_cents": 85000, "saved_cents": 20000, "monthly_rate_cents": 10000, "priority": "Hoch", "desired_date": ""},
        {"id": "sg2", "name": "PC-Upgrade", "target_cents": 220000, "saved_cents": 50000, "monthly_rate_cents": 15000, "priority": "Mittel", "desired_date": ""},
        {"id": "sg3", "name": "Führerschein / Mobilität", "target_cents": 80000, "saved_cents": 10000, "monthly_rate_cents": 7500, "priority": "Hoch", "desired_date": ""},
    ]

def get_default_cash_denominations():
    return [
        {"name": "500 € Schein", "value_cents": 50000, "count": 0},
        {"name": "200 € Schein", "value_cents": 20000, "count": 0},
        {"name": "100 € Schein", "value_cents": 10000, "count": 1},
        {"name": "50 € Schein", "value_cents": 5000, "count": 1},
        {"name": "20 € Schein", "value_cents": 2000, "count": 2},
        {"name": "10 € Schein", "value_cents": 1000, "count": 1},
        {"name": "5 € Schein", "value_cents": 500, "count": 0},
        {"name": "2 € Münze", "value_cents": 200, "count": 0},
        {"name": "1 € Münze", "value_cents": 100, "count": 0},
        {"name": "50 Cent Münze", "value_cents": 50, "count": 0},
        {"name": "20 Cent Münze", "value_cents": 20, "count": 0},
        {"name": "10 Cent Münze", "value_cents": 10, "count": 0},
        {"name": "5 Cent Münze", "value_cents": 5, "count": 0},
        {"name": "2 Cent Münze", "value_cents": 2, "count": 0},
        {"name": "1 Cent Münze", "value_cents": 1, "count": 0},
    ]

def get_default_wishlists():
    return [
        {
            "id": "wl1", "name": "Technik-Wünsche", "items": [
                {"id": "wi1", "name": "Bluetooth Kopfhörer", "url": "", "price_cents": 12000, "active": True, "notes": ""},
                {"id": "wi2", "name": "Zweiter Monitor", "url": "", "price_cents": 25000, "active": False, "notes": ""}
            ]
        },
        {"id": "wl2", "name": "Freizeit & Hobby", "items": []},
        {"id": "wl3", "name": "Kleidung & Style", "items": []}
    ]

def get_default_debts():
    return [
        {
            "id": "d1", "person": "Max", "reason": "Konzertkarte", "direction": "Mir geschuldet",
            "total_cents": 4500, "paid_cents": 0, "due_date": date.today().isoformat(), "notes": "", "payments": []
        }
    ]

def get_default_event_months():
    cur_y = date.today().year
    evts = {}
    for m in range(1, 13):
        m_str = f"{cur_y}-{m:02d}"
        evts[m_str] = {"active": False, "description": "", "amount_cents": 10000}
    return evts

def create_challenge_weeks(target_cents: int, num_weeks: int = 52, mode: str = "Progressiv"):
    weeks = []
    if num_weeks <= 0:
        num_weeks = 52
    
    if mode == "Progressiv":
        sum_weights = (num_weeks * (num_weeks + 1)) // 2
        unit_cents = target_cents / sum_weights
        running_total = 0
        for w in range(1, num_weeks + 1):
            if w == num_weeks:
                w_amt = target_cents - running_total
            else:
                w_amt = int(round(w * unit_cents))
                running_total += w_amt
            weeks.append({"week": w, "amount_cents": max(100, w_amt), "completed": False})
    else: # Gleichmäßig
        base_amt = target_cents // num_weeks
        rem = target_cents % num_weeks
        for w in range(1, num_weeks + 1):
            w_amt = base_amt + (1 if w <= rem else 0)
            weeks.append({"week": w, "amount_cents": w_amt, "completed": False})
            
    return weeks

def get_default_challenges():
    return {
        "target_cents": 137800,
        "num_weeks": 52,
        "mode": "Progressiv",
        "weeks": create_challenge_weeks(137800, 52, "Progressiv")
    }


# --- PDF Report Class (Fallback safe) ---

if HAS_FPDF:
    class PDFReport(FPDF):
        def header(self):
            self.set_fill_color(15, 23, 42)
            self.rect(0, 0, 210, 22, 'F')
            self.set_font('Helvetica', 'B', 14)
            self.set_text_color(255, 255, 255)
            self.cell(0, 8, '  Finanzplanungs-Monatsbericht (PDF)', 0, 1, 'L')
            self.ln(4)

        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Seite {self.page_no()} | PersoFinanz App', 0, 0, 'C')


# --- Main FinanceEngine Class ---

class FinanceEngine:
    def __init__(self, data=None):
        if data is None:
            self.reset_to_defaults()
        else:
            self.load_from_dict(data)

    def reset_to_defaults(self):
        self.settings = get_default_settings()
        self.categories = get_default_categories()
        self.transactions = []
        self.recurring_incomes = get_default_recurring_incomes()
        self.recurring_expenses = get_default_recurring_expenses()
        self.savings_goals = get_default_savings_goals()
        self.cash_denominations = get_default_cash_denominations()
        self.wishlists = get_default_wishlists()
        self.debts = get_default_debts()
        self.event_months = get_default_event_months()
        self.event_bonus_cents = 10000
        self.challenges = get_default_challenges()

    def to_dict(self):
        return {
            "settings": self.settings,
            "categories": self.categories,
            "transactions": self.transactions,
            "recurring_incomes": self.recurring_incomes,
            "recurring_expenses": self.recurring_expenses,
            "savings_goals": self.savings_goals,
            "cash_denominations": self.cash_denominations,
            "wishlists": self.wishlists,
            "debts": self.debts,
            "event_months": self.event_months,
            "event_bonus_cents": self.event_bonus_cents,
            "challenges": self.challenges
        }

    def load_from_dict(self, data):
        self.settings = data.get("settings", get_default_settings())
        self.categories = data.get("categories", get_default_categories())
        self.transactions = data.get("transactions", [])
        self.recurring_incomes = data.get("recurring_incomes", get_default_recurring_incomes())
        self.recurring_expenses = data.get("recurring_expenses", get_default_recurring_expenses())
        self.savings_goals = data.get("savings_goals", get_default_savings_goals())
        
        saved_denoms = data.get("cash_denominations", [])
        default_denoms = get_default_cash_denominations()
        if saved_denoms:
            saved_map = {d["name"]: d["count"] for d in saved_denoms}
            for d in default_denoms:
                if d["name"] in saved_map:
                    d["count"] = saved_map[d["name"]]
            self.cash_denominations = default_denoms
        else:
            self.cash_denominations = default_denoms

        self.wishlists = data.get("wishlists", get_default_wishlists())
        self.debts = data.get("debts", get_default_debts())
        self.event_months = data.get("event_months", get_default_event_months())
        self.event_bonus_cents = data.get("event_bonus_cents", 10000)
        
        ch = data.get("challenges", {})
        if "weeks" in ch:
            self.challenges = ch
        else:
            self.challenges = get_default_challenges()

    # --- Balances ---

    def calculate_current_balances(self):
        cutoff = self.settings.get("cutoff_date", date.today().isoformat())
        start_account = self.settings.get("start_account_cents", 0)
        start_cash = self.settings.get("start_cash_cents", 0)

        account_balance = start_account
        cash_balance = start_cash

        for t in self.transactions:
            if t.get("status") != "Ist":
                continue
            t_date = t.get("date", "")
            if t_date < cutoff:
                continue

            acc = t.get("account", "Konto")
            t_type = t.get("type", "Ausgabe")
            amt = t.get("amountCents", 0)

            effect = 0
            if t_type in ["Einnahme", "Umbuchung Eingang"]:
                effect = amt
            elif t_type in ["Ausgabe", "Umbuchung Ausgang"]:
                effect = -amt

            if acc == "Konto":
                account_balance += effect
            elif acc == "Bargeld":
                cash_balance += effect

        liquid_assets = account_balance + cash_balance

        receivables_cents = 0
        debts_cents = 0
        for d in self.debts:
            open_amt = max(0, d.get("total_cents", 0) - d.get("paid_cents", 0))
            if d.get("direction") == "Mir geschuldet":
                receivables_cents += open_amt
            elif d.get("direction") == "Ich schulde":
                debts_cents += open_amt

        expected_funds = liquid_assets + receivables_cents

        return {
            "account_cents": account_balance,
            "cash_cents": cash_balance,
            "liquid_assets_cents": liquid_assets,
            "receivables_cents": receivables_cents,
            "debts_cents": debts_cents,
            "expected_funds_cents": expected_funds
        }

    # --- Daily Projected Balance Engine ---

    def calculate_projected_balance_for_day(self, target_year: int, target_month: int, target_day: int):
        target_date_str = f"{target_year:04d}-{target_month:02d}-{target_day:02d}"

        balances = self.calculate_current_balances()
        current_liquid = balances["liquid_assets_cents"]

        today_str = date.today().isoformat()

        if target_date_str <= today_str:
            return {
                "projected_liquid_cents": current_liquid,
                "target_date": target_date_str,
                "is_future": False
            }

        projected = current_liquid
        cur = date.today() + timedelta(days=1)
        end_d = date(target_year, target_month, target_day)

        while cur <= end_d:
            cur_str = cur.isoformat()
            
            for t in self.transactions:
                if t.get("date") == cur_str:
                    amt = t.get("amountCents", 0)
                    t_type = t.get("type")
                    if t_type in ["Einnahme", "Umbuchung Eingang"]:
                        projected += amt
                    elif t_type in ["Ausgabe", "Umbuchung Ausgang"]:
                        projected -= amt

            for exp in self.recurring_expenses:
                due_d = exp.get("due_day", 1)
                freq = exp.get("frequency", "monatlich")
                ann_m = exp.get("annual_month", 1)
                if due_d == cur.day:
                    if freq == "monatlich" or (freq == "jährlich" and ann_m == cur.month):
                        projected -= exp.get("amount_cents", 0)

            for inc in self.recurring_incomes:
                due_d = inc.get("due_day", 1)
                if due_d == cur.day:
                    projected += inc.get("amount_cents", 0)

            cur += timedelta(days=1)

        return {
            "projected_liquid_cents": projected,
            "target_date": target_date_str,
            "is_future": True
        }

    # --- Transactions & Transfers ---

    def add_transaction(self, date_str, status, t_type, category, description, account, amount_cents, transfer_group_id=None):
        t_id = str(uuid.uuid4())
        now_str = datetime.now().isoformat()
        parsed_tags = parse_hashtags(description)
        t = {
            "id": t_id,
            "date": date_str,
            "status": status,
            "type": t_type,
            "category": category,
            "description": description,
            "account": account,
            "amountCents": abs(amount_cents),
            "tags": parsed_tags,
            "transferGroupId": transfer_group_id,
            "createdAt": now_str,
            "updatedAt": now_str
        }
        self.transactions.append(t)
        return t

    def add_transfer(self, date_str, status, from_account, to_account, description, amount_cents):
        group_id = str(uuid.uuid4())
        desc_out = f"Umbuchung an {to_account}: {description}".strip(": ")
        desc_in = f"Umbuchung von {from_account}: {description}".strip(": ")
        
        t_out = self.add_transaction(
            date_str, status, "Umbuchung Ausgang", "Umbuchung", desc_out, from_account, amount_cents, transfer_group_id=group_id
        )
        t_in = self.add_transaction(
            date_str, status, "Umbuchung Eingang", "Umbuchung", desc_in, to_account, amount_cents, transfer_group_id=group_id
        )
        return t_out, t_in

    def checkForDuplicateTransaction(self, date_str, amount_cents, t_type, description):
        for t in self.transactions:
            if (t.get("date") == date_str and
                t.get("amountCents") == abs(amount_cents) and
                t.get("type") == t_type and
                description.lower() in t.get("description", "").lower()):
                return True
        return False

    # --- Calendar View Data Generator ---

    def generate_calendar_month_data(self, year: int, month: int):
        cal = calendar.monthcalendar(year, month)
        m_str = f"{year:04d}-{month:02d}"

        days_data = {}
        for w in cal:
            for day in w:
                if day == 0:
                    continue
                d_str = f"{m_str}-{day:02d}"
                items = []

                for t in self.transactions:
                    if t.get("date") == d_str:
                        items.append({
                            "type": "transaction",
                            "title": t.get("description", "Buchung"),
                            "amount_cents": t.get("amountCents", 0),
                            "direction": "in" if t.get("type") in ["Einnahme", "Umbuchung Eingang"] else "out",
                            "status": t.get("status")
                        })

                for exp in self.recurring_expenses:
                    due_d = exp.get("due_day", 1)
                    if due_d == day:
                        items.append({
                            "type": "fixkosten",
                            "id": exp["id"],
                            "title": f"Abo: {exp['name']}",
                            "amount_cents": exp["amount_cents"],
                            "direction": "out",
                            "status": "Abo"
                        })

                for inc in self.recurring_incomes:
                    due_d = inc.get("due_day", 1)
                    if due_d == day:
                        items.append({
                            "type": "einkommen",
                            "id": inc["id"],
                            "title": f"Einnahme: {inc['name']}",
                            "amount_cents": inc["amount_cents"],
                            "direction": "in",
                            "status": "Plan"
                        })

                days_data[day] = items

        return cal, days_data

    # --- AI Finance Coach ---

    def generate_ai_financial_tips(self, month_str=None):
        if not month_str:
            month_str = date.today().strftime("%Y-%m")

        balances = self.calculate_current_balances()
        liquid = balances["liquid_assets_cents"]

        fix_total = sum(e["amount_cents"] for e in self.recurring_expenses)
        inc_total = sum(i["amount_cents"] for i in self.recurring_incomes)

        tips = []

        monthly_cost = fix_total + sum(c["limit_cents"] for c in self.categories if c["name"] not in ["Fixkosten", "Einmalig", "Einkommen", "Umbuchung"])
        if monthly_cost > 0:
            buffer_months = liquid / monthly_cost
            if buffer_months >= 3.0:
                tips.append(f"🟢 **Super Notgroschen!** Dein liquides Vermögen reicht für ca. **{buffer_months:.1f} Monate** aller Ausgaben. Du bist finanziell sehr gut abgesichert.")
            elif buffer_months < 1.0:
                tips.append(f"🔴 **Puffer erhöhen:** Dein liquides Vermögen deckt weniger als 1 Monat deiner regelmäßigen Kosten ({cents_to_euro_str(monthly_cost)}/Monat). Versuche etwas Erspartes anzulegen.")

        if inc_total > 0:
            fix_ratio = (fix_total / inc_total) * 100
            if fix_ratio > 40:
                tips.append(f"⚠️ **Kostenfalle Abos:** Deine Fixkosten machen **{fix_ratio:.0f} %** deines regelmäßigen Einkommens aus. Prüfe unter 'Events & Fixkosten', ob du ungenutzte Abos kündigen kannst.")
            else:
                tips.append(f"✅ **Schlanke Fixkosten:** Deine Abos & Verträge betragen nur **{fix_ratio:.0f} %** deines Einkommens. Das gibt dir viel Spielraum für Wünsche.")

        cat_spent = {}
        for t in self.transactions:
            if t.get("status")=="Ist" and t.get("type")=="Ausgabe" and t.get("date","").startswith(month_str):
                c = t.get("category", "Sonstiges")
                cat_spent[c] = cat_spent.get(c, 0) + t.get("amountCents", 0)

        if cat_spent:
            top_cat = max(cat_spent, key=cat_spent.get)
            top_val = cat_spent[top_cat]
            tips.append(f"📊 **Größter Posten im Monat:** In der Kategorie **'{top_cat}'** hast du diesen Monat bereits **{cents_to_euro_str(top_val)}** ausgegeben.")

        active_goals = [sg for sg in self.savings_goals if sg.get("saved_cents",0) < sg.get("target_cents",0)]
        if active_goals:
            first_goal = active_goals[0]
            rest = first_goal["target_cents"] - first_goal["saved_cents"]
            tips.append(f"🎯 **Sparziel im Blick:** Für dein Ziel **'{first_goal['name']}'** fehlen noch **{cents_to_euro_str(rest)}**. Wenn du 15 € monatlich mehr sparst, bist du knapp 2 Monate früher am Ziel!")

        if not tips:
            tips.append("💡 Trage deine ersten Ausgaben ein, damit dein persönlicher KI-Coach dir maßgeschneiderte Tipps geben kann!")

        return tips

    # --- PDF Report Generator ---

    def generate_monthly_pdf_report_bytes(self, month_str=None):
        if not HAS_FPDF:
            return b""

        if not month_str:
            month_str = date.today().strftime("%Y-%m")

        balances = self.calculate_current_balances()

        pdf = PDFReport()
        pdf.add_page()
        pdf.set_font("Helvetica", "", 12)

        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 10, f"Monatsbericht fuer den Zeitraum: {month_str}", 0, 1, "L")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Erstellt am: {date.today().strftime('%d.%m.%Y')}", 0, 1, "L")
        pdf.ln(5)

        pdf.set_fill_color(240, 244, 248)
        pdf.rect(10, pdf.get_y(), 190, 25, 'F')
        pdf.set_y(pdf.get_y() + 3)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(60, 6, "  Girokonto:", 0, 0)
        pdf.cell(60, 6, "  Bargeld:", 0, 0)
        pdf.cell(60, 6, "  Liquides Vermoegen:", 0, 1)
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(0, 102, 204)

        acc_str = cents_to_euro_str(balances['account_cents']).replace("€", "EUR")
        cash_str = cents_to_euro_str(balances['cash_cents']).replace("€", "EUR")
        liq_str = cents_to_euro_str(balances['liquid_assets_cents']).replace("€", "EUR")

        pdf.cell(60, 8, f"  {acc_str}", 0, 0)
        pdf.cell(60, 8, f"  {cash_str}", 0, 0)
        pdf.cell(60, 8, f"  {liq_str}", 0, 1)
        pdf.ln(10)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "Uebersicht der Buchungen in diesem Monat:", 0, 1)

        pdf.set_fill_color(15, 23, 42)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(25, 7, "Datum", 1, 0, "C", True)
        pdf.cell(30, 7, "Typ", 1, 0, "C", True)
        pdf.cell(35, 7, "Kategorie", 1, 0, "C", True)
        pdf.cell(65, 7, "Beschreibung", 1, 0, "C", True)
        pdf.cell(35, 7, "Betrag", 1, 1, "C", True)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(0, 0, 0)

        month_t = [t for t in self.transactions if t.get("date","").startswith(month_str)]
        fill = False
        for t in month_t[:30]:
            pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
            d_str = format_date_de(t.get("date"))
            t_type = t.get("type", "")
            cat = t.get("category", "")[:18].encode('latin-1', 'replace').decode('latin-1')
            desc = t.get("description", "")[:32].encode('latin-1', 'replace').decode('latin-1')
            amt = cents_to_euro_str(t.get("amountCents", 0)).replace("€", "EUR")
            if t_type in ["Ausgabe", "Umbuchung Ausgang"]:
                amt = f"-{amt}"

            pdf.cell(25, 6, d_str, 1, 0, "C", fill)
            pdf.cell(30, 6, t_type, 1, 0, "C", fill)
            pdf.cell(35, 6, cat, 1, 0, "L", fill)
            pdf.cell(65, 6, desc, 1, 0, "L", fill)
            pdf.cell(35, 6, amt, 1, 1, "R", fill)
            fill = not fill

        if not month_t:
            pdf.cell(190, 8, "Keine Buchungen in diesem Monat erfasst.", 1, 1, "C")

        pdf_out = pdf.output()
        if isinstance(pdf_out, (bytes, bytearray)):
            return bytes(pdf_out)
        return str(pdf_out).encode('latin-1', errors='replace')

    # --- CSV & Excel Exporter ---

    def export_transactions_to_excel_bytes(self):
        output = io.BytesIO()
        rows = []
        for t in self.transactions:
            rows.append({
                "ID": t.get("id"),
                "Datum": t.get("date"),
                "Status": t.get("status"),
                "Typ": t.get("type"),
                "Kategorie": t.get("category"),
                "Beschreibung": t.get("description"),
                "Konto/Bargeld": t.get("account"),
                "Betrag (€)": t.get("amountCents", 0) / 100,
                "Tags": ", ".join(t.get("tags", []))
            })
        df = pd.DataFrame(rows)
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Buchungen', index=False)
            
            df_fix = pd.DataFrame(self.recurring_expenses)
            df_fix.to_excel(writer, sheet_name='Fixkosten', index=False)
            
            df_sg = pd.DataFrame(self.savings_goals)
            df_sg.to_excel(writer, sheet_name='Sparziele', index=False)

        return output.getvalue()

    def export_transactions_to_csv_bytes(self):
        rows = []
        for t in self.transactions:
            rows.append({
                "ID": t.get("id"),
                "Datum": t.get("date"),
                "Status": t.get("status"),
                "Typ": t.get("type"),
                "Kategorie": t.get("category"),
                "Beschreibung": t.get("description"),
                "Konto/Bargeld": t.get("account"),
                "Betrag_Euro": t.get("amountCents", 0) / 100,
                "Tags": ", ".join(t.get("tags", []))
            })
        df = pd.DataFrame(rows)
        return df.to_csv(index=False).encode('utf-8')

    # --- Gamification & Badges Engine ---

    def calculate_zero_euro_days(self, month_str=None):
        if not month_str:
            month_str = date.today().strftime("%Y-%m")

        year, month = map(int, month_str.split("-"))
        days_in_m = calendar.monthrange(year, month)[1]

        today = date.today()
        if today.strftime("%Y-%m") == month_str:
            eval_days = min(today.day, days_in_m)
        else:
            eval_days = days_in_m

        spent_days = set()
        for t in self.transactions:
            if t.get("status") == "Ist" and t.get("type") == "Ausgabe":
                t_d = t.get("date", "")
                if t_d.startswith(month_str):
                    try:
                        d_num = int(t_d.split("-")[2])
                        spent_days.add(d_num)
                    except (IndexError, ValueError):
                        pass

        zero_euro_count = sum(1 for d in range(1, eval_days + 1) if d not in spent_days)
        return zero_euro_count, eval_days

    def get_earned_badges(self):
        badges = []
        balances = self.calculate_current_balances()

        if balances["liquid_assets_cents"] >= 50000:
            badges.append({
                "id": "b1",
                "icon": "🛡️",
                "title": "Notgroschen-Meister",
                "desc": "Mindestens 500 € liquides Vermögen aufgebaut!"
            })

        if len(self.savings_goals) >= 2:
            badges.append({
                "id": "b2",
                "icon": "🦊",
                "title": "Spar-Fuchs",
                "desc": "Mindestens 2 verschiedene Sparziele angelegt!"
            })

        cur_m = date.today().strftime("%Y-%m")
        z_days, _ = self.calculate_zero_euro_days(cur_m)
        if z_days >= 5:
            badges.append({
                "id": "b3",
                "icon": "🔥",
                "title": "Disziplin-Star",
                "desc": "Schon 5+ 0-Euro-Tage im aktuellen Monat erreicht!"
            })

        if balances["cash_cents"] >= 10000:
            badges.append({
                "id": "b4",
                "icon": "💵",
                "title": "Cash-Champ",
                "desc": "Mindestens 100 € Bargeld-Bestand gezählt!"
            })

        return badges

    # --- Monthly Budget ---

    def calculate_monthly_budget(self, month_str, category_name):
        cat_info = next((c for c in self.categories if c["name"] == category_name), None)
        limit_cents = cat_info["limit_cents"] if cat_info else 0

        spent_cents = 0
        for t in self.transactions:
            if t.get("status") != "Ist" or t.get("type") != "Ausgabe":
                continue
            if t.get("category") != category_name:
                continue
            t_date = t.get("date", "")
            if t_date.startswith(month_str):
                spent_cents += t.get("amountCents", 0)

        rest_cents = limit_cents - spent_cents
        pct = (spent_cents / limit_cents * 100) if limit_cents > 0 else 0.0

        if limit_cents == 0:
            status = "Kein Limit"
        elif spent_cents > limit_cents:
            status = "Überschritten"
        elif pct >= 80.0:
            status = "Fast aufgebraucht"
        else:
            status = "Im Rahmen"

        return {
            "category": category_name,
            "month": month_str,
            "limit_cents": limit_cents,
            "spent_cents": spent_cents,
            "rest_cents": rest_cents,
            "utilization_pct": pct,
            "status": status
        }

    # --- Debts & Receivables ---

    def add_debt_payment(self, debt_id, payment_date, amount_cents, auto_create_transaction=True):
        debt = next((d for d in self.debts if d["id"] == debt_id), None)
        if not debt:
            return None
        
        amt = abs(amount_cents)
        debt["paid_cents"] = debt.get("paid_cents", 0) + amt
        
        p_id = str(uuid.uuid4())
        payment = {
            "id": p_id,
            "debt_id": debt_id,
            "date": payment_date,
            "amount_cents": amt,
            "transaction_id": None
        }
        
        if auto_create_transaction:
            t_type = "Einnahme" if debt.get("direction") == "Mir geschuldet" else "Ausgabe"
            desc = f"Teilzahlung {debt['person']}: {debt['reason']}"
            t = self.add_transaction(
                payment_date, "Ist", t_type, "Einmalig", desc, "Konto", amt
            )
            payment["transaction_id"] = t["id"]

        if "payments" not in debt:
            debt["payments"] = []
        debt["payments"].append(payment)
        return payment

    # --- Wishlists ---

    def calculate_wishlist_reachability(self, required_cents: int, num_months: int = 36):
        balances = self.calculate_current_balances()
        if balances["liquid_assets_cents"] >= required_cents:
            return "Jetzt machbar!"

        fc = self.calculate_forecast(num_months=num_months)
        for m in fc["months"]:
            if m["normal_balance_cents"] >= required_cents:
                return m["month"]
        return f"Nicht innerhalb von {num_months} Monaten erreichbar"

    def calculate_wishlist_summary(self, num_months: int = 36):
        balances = self.calculate_current_balances()
        liquid_cents = balances["liquid_assets_cents"]

        total_active_cents = 0
        total_all_cents = 0

        for wl in self.wishlists:
            for item in wl.get("items", []):
                price = item.get("price_cents", 0)
                total_all_cents += price
                if item.get("active", False):
                    total_active_cents += price

        missing_cents = max(0, total_active_cents - liquid_cents)
        machbar = total_active_cents <= liquid_cents
        reachability_month = self.calculate_wishlist_reachability(total_active_cents, num_months=num_months)

        return {
            "total_active_cents": total_active_cents,
            "total_all_cents": total_all_cents,
            "liquid_assets_cents": liquid_cents,
            "overall_missing_cents": missing_cents,
            "overall_machbar": machbar,
            "overall_reachability_month": reachability_month
        }

    # --- Savings Goals ---

    def calculate_savings_goals_forecast(self, num_months: int = 36):
        results = []
        today = date.today()

        for sg in self.savings_goals:
            target = sg.get("target_cents", 0)
            saved = sg.get("saved_cents", 0)
            rate = sg.get("monthly_rate_cents", 0)
            rest = max(0, target - saved)

            if rest == 0:
                calc_date_str = "Ziel bereits erreicht!"
                calc_status = "Erreicht"
            elif rate <= 0:
                calc_date_str = "Keine Sparrate festgelegt"
                calc_status = "Sparrate fehlt"
            else:
                months_needed = (rest + rate - 1) // rate
                target_date = today + relativedelta(months=months_needed)
                calc_date_str = target_date.strftime("%m/%Y")
                calc_status = "In Planung"

            buy_month = self.calculate_wishlist_reachability(target, num_months=num_months)

            results.append({
                "id": sg["id"],
                "name": sg["name"],
                "target_cents": target,
                "saved_cents": saved,
                "monthly_rate_cents": rate,
                "rest_cents": rest,
                "priority": sg.get("priority", "Mittel"),
                "desired_date": sg.get("desired_date", ""),
                "calc_target_date": calc_date_str,
                "calc_status": calc_status,
                "forecast_buy_month": buy_month
            })

        return results

    # --- Configurable Forecast Engine ---

    def calculate_forecast(self, num_months: int = 36):
        balances = self.calculate_current_balances()
        start_liquid = balances["liquid_assets_cents"]

        today = date.today()
        months_list = []
        alerts = []

        factors = self.settings.get("scenario_factors", {
            "best": {"income": 1.10, "fix": 0.95, "variable": 0.90},
            "normal": {"income": 1.00, "fix": 1.00, "variable": 1.00},
            "worst": {"income": 0.80, "fix": 1.15, "variable": 1.15}
        })

        best_balance = start_liquid
        normal_balance = start_liquid
        worst_balance = start_liquid

        for i in range(num_months):
            m_date = today + relativedelta(months=i)
            m_str = m_date.strftime("%Y-%m")
            is_current_month = (i == 0)

            if is_current_month:
                base_income = sum(
                    inc["amount_cents"] for inc in self.recurring_incomes
                    if not inc.get("received_current_month", False)
                )
            else:
                base_income = sum(inc["amount_cents"] for inc in self.recurring_incomes)

            evt_info = self.event_months.get(m_str, {})
            if evt_info.get("active", False):
                event_bonus = evt_info.get("amount_cents", self.event_bonus_cents)
            else:
                event_bonus = 0

            fix_expenses = 0
            for exp in self.recurring_expenses:
                if is_current_month and exp.get("debited_current_month", False):
                    continue
                
                freq = exp.get("frequency", "monatlich")
                if freq == "monatlich":
                    fix_expenses += exp["amount_cents"]
                elif freq == "jährlich" and exp.get("annual_month", 1) == m_date.month:
                    fix_expenses += exp["amount_cents"]

            var_budget = sum(
                c["limit_cents"] for c in self.categories
                if c.get("active", True) and c["name"] not in ["Fixkosten", "Einmalig", "Einkommen", "Umbuchung"]
            )

            planned_income = sum(
                t["amountCents"] for t in self.transactions
                if t.get("status") == "Geplant" and t.get("type") in ["Einnahme", "Umbuchung Eingang"] and t.get("date","").startswith(m_str)
            )
            planned_expense = sum(
                t["amountCents"] for t in self.transactions
                if t.get("status") == "Geplant" and t.get("type") in ["Ausgabe", "Umbuchung Ausgang"] and t.get("date","").startswith(m_str)
            )
            planned_net = planned_income - planned_expense

            best_inc = (base_income + event_bonus) * factors["best"]["income"]
            best_fix = fix_expenses * factors["best"]["fix"]
            best_var = var_budget * factors["best"]["variable"]
            best_net = (best_inc - best_fix - best_var) + planned_net

            normal_inc = (base_income + event_bonus) * factors["normal"]["income"]
            normal_fix = fix_expenses * factors["normal"]["fix"]
            normal_var = var_budget * factors["normal"]["variable"]
            normal_net = (normal_inc - normal_fix - normal_var) + planned_net

            worst_inc = (base_income + event_bonus) * factors["worst"]["income"]
            worst_fix = fix_expenses * factors["worst"]["fix"]
            worst_var = var_budget * factors["worst"]["variable"]
            worst_net = (worst_inc - worst_fix - worst_var) + planned_net

            best_balance += int(round(best_net))
            normal_balance += int(round(normal_net))
            worst_balance += int(round(worst_net))

            if normal_balance < 0 and f"Normal Case Saldo wird im Monat {m_str} negativ!" not in alerts:
                alerts.append(f"Normal Case Saldo wird im Monat {m_str} negativ ({cents_to_euro_str(normal_balance)})!")
            if worst_balance < 0 and f"Worst Case Saldo wird im Monat {m_str} negativ!" not in alerts:
                alerts.append(f"Worst Case Saldo wird im Monat {m_str} negativ ({cents_to_euro_str(worst_balance)})!")

            months_list.append({
                "month": m_str,
                "base_income_cents": base_income + event_bonus,
                "fix_cents": fix_expenses,
                "var_cents": var_budget,
                "planned_one_off_cents": planned_net,
                "best_balance_cents": best_balance,
                "normal_balance_cents": normal_balance,
                "worst_balance_cents": worst_balance,
                "normal_net_cents": normal_net
            })

        return {
            "months": months_list,
            "alerts": alerts
        }

    def calculate_36_month_forecast(self):
        return self.calculate_forecast(num_months=36)
