"""
Finanzplanungs-App - Streamlit UI v8 (Ultimate Complete Edition)
Grounded strictly in Finanzplanungs_App_Spezifikation.md
Includes ALL features & forms from v1 through v7:
- Apple Glassmorphism Design
- Full Standartwerte Adjustments (Start-Kontostand, Start-Bargeld, Stichtag, PIN, Reset) in Settings
- Full Event-Monate Management (Checkbox, Description, Individual Euro Bonus Amount)
- Full Forecast Engine with 6-60 Month Slider & Interactive Line Chart (Best, Normal, Worst)
- All Add/Edit/Delete Forms for Transactions, Transfers, Categories, Wishlists, Savings Goals, Debts, Subscriptions, Incomes
- Interactive Calendar with Daily Projected Balance & Due-day Assignment
- Custom Savings Challenge Generator
- PDF, Excel & CSV Exporters
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
import json
import calendar

from finanzplaner_core_v8 import (
    FinanceEngine,
    cents_to_euro_str,
    parse_euro_to_cents,
    format_date_de,
    calculate_missing_months,
    convert_to_eur_cents,
    create_challenge_weeks,
    EXCHANGE_RATES_TO_EUR,
    HAS_FPDF
)

# Page Config
st.set_page_config(
    page_title="PersoFinanz Apple v8",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "engine" not in st.session_state:
    st.session_state.engine = FinanceEngine()

engine: FinanceEngine = st.session_state.engine

if "cal_selected_day" not in st.session_state:
    st.session_state.cal_selected_day = date.today().day

# Custom CSS for Apple Glassmorphism Design
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #172033 50%, #0b0f19 100%);
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
    }
    
    .apple-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 10px 30px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 14px 18px;
        box-shadow: inset 0 0 12px rgba(255, 255, 255, 0.03);
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-weight: 500;
        font-size: 0.9rem;
    }
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-weight: 700;
        font-size: 1.5rem;
    }

    section[data-testid="stSidebar"] {
        background: rgba(11, 15, 25, 0.85) !important;
        backdrop-filter: blur(25px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.25), rgba(59, 130, 246, 0.35)) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        color: #f8fafc !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.45), rgba(59, 130, 246, 0.55)) !important;
        border: 1px solid rgba(255, 255, 255, 0.45) !important;
        box-shadow: 0 0 18px rgba(56, 189, 248, 0.4) !important;
    }

    div[data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# Privacy Mode State
if "privacy_mode" not in st.session_state:
    st.session_state.privacy_mode = engine.settings.get("privacy_mode_default", False)

# PIN Lock State
pin_code = engine.settings.get("pin_code", "")
if "unlocked" not in st.session_state:
    st.session_state.unlocked = True if not pin_code else False

# PIN Verification Screen
if pin_code and not st.session_state.unlocked:
    st.title("🔒 PersoFinanz - PIN Eingabe")
    st.caption("Eingabe erforderlich, um deine Finanzdaten zu schützen.")
    entered_pin = st.text_input("Gib deinen 4-stelligen PIN ein", type="password")
    if st.button("Entsperren"):
        if entered_pin == pin_code:
            st.session_state.unlocked = True
            st.success("Erfolgreich entsperrt!")
            st.rerun()
        else:
            st.error("Falscher PIN! Bitte versuche es erneut.")
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("💎 PersoFinanz v8")
st.sidebar.caption("Ultimate Glass Edition")

# Privacy Mode Toggle
st.sidebar.markdown("---")
privacy = st.sidebar.checkbox("👁️ Diskreter Modus (••• €)", value=st.session_state.privacy_mode)
st.session_state.privacy_mode = privacy

nav_options = [
    "1. 📊 Dashboard",
    "2. 📝 Buchungsregister",
    "3. 🎯 Monatsbudget",
    "4. 🐖 Sparziele & Challenges",
    "5. 💵 Bargeld-Rechner",
    "6. 🎁 Wunschlisten",
    "7. 🤝 Schulden & Forderungen",
    "8. 📅 Kalender & Fixkosten",
    "9. 📈 Prognose & Berichte",
    "10. 💱 Währungsrechner",
    "11. ⚙️ Einstellungen & Daten"
]

selected_page = st.sidebar.radio("Navigation", nav_options)

# Quick Sidebar Summary
balances = engine.calculate_current_balances()
st.sidebar.markdown("---")
st.sidebar.subheader("Schnellübersicht")
st.sidebar.metric("Liquides Vermögen", cents_to_euro_str(balances["liquid_assets_cents"], privacy))
st.sidebar.metric("Offene Forderungen", cents_to_euro_str(balances["receivables_cents"], privacy))
st.sidebar.caption(f"Stichtag: {format_date_de(engine.settings.get('cutoff_date'))}")

fc_m = engine.settings.get("forecast_months", 36)

# ==========================================
# 1. DASHBOARD
# ==========================================
if selected_page.startswith("1."):
    st.title("📊 Finanz-Dashboard")
    
    # Smart Reminders Banner
    reminders = []
    for d in engine.debts:
        open_amt = max(0, d.get("total_cents", 0) - d.get("paid_cents", 0))
        if open_amt > 0:
            if d.get("direction") == "Ich schulde":
                reminders.append(f"⚠️ Offene Schuld an **{d['person']}**: {cents_to_euro_str(open_amt, privacy)} (Fällig: {format_date_de(d.get('due_date'))})")
            else:
                reminders.append(f"💡 Offene Forderung an **{d['person']}**: {cents_to_euro_str(open_amt, privacy)}")
    
    for sg in engine.savings_goals:
        rest = sg.get("target_cents", 0) - sg.get("saved_cents", 0)
        if 0 < rest <= 5000:
            reminders.append(f"🎯 Sparziel **'{sg['name']}'** steht kurz vor dem Ziel! Nur noch {cents_to_euro_str(rest, privacy)} fehlen.")

    if reminders:
        with st.expander("🔔 **Smart Reminders & Fristen-Erinnerungen**", expanded=True):
            for rem in reminders:
                st.write(rem)

    # Key Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Bargeld aktuell", cents_to_euro_str(balances["cash_cents"], privacy))
    c2.metric("Girokonto aktuell", cents_to_euro_str(balances["account_cents"], privacy))
    c3.metric("Liquides Vermögen", cents_to_euro_str(balances["liquid_assets_cents"], privacy))
    c4.metric("Offene Forderungen", cents_to_euro_str(balances["receivables_cents"], privacy))
    c5.metric("Erwartete Mittel Gesamt", cents_to_euro_str(balances["expected_funds_cents"], privacy))

    st.markdown("---")

    # Current Month Flow
    cur_month = date.today().strftime("%Y-%m")
    cur_inc = sum(t["amountCents"] for t in engine.transactions if t.get("status")=="Ist" and t.get("type")=="Einnahme" and t.get("date","").startswith(cur_month))
    cur_exp = sum(t["amountCents"] for t in engine.transactions if t.get("status")=="Ist" and t.get("type")=="Ausgabe" and t.get("date","").startswith(cur_month))
    cur_net = cur_inc - cur_exp

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Einnahmen ({cur_month})", cents_to_euro_str(cur_inc, privacy))
    m2.metric(f"Ausgaben ({cur_month})", cents_to_euro_str(cur_exp, privacy))
    m3.metric(f"Nettofluss ({cur_month})", cents_to_euro_str(cur_net, privacy), delta=cents_to_euro_str(cur_net, privacy))
    
    exceeded_cats = 0
    for cat in engine.categories:
        if cat.get("limit_cents", 0) > 0 and cat["name"] not in ["Fixkosten", "Einmalig", "Einkommen", "Umbuchung"]:
            bm = engine.calculate_monthly_budget(cur_month, cat["name"])
            if bm["status"] == "Überschritten":
                exceeded_cats += 1
    m4.metric("Überschrittene Budgets", f"{exceeded_cats} Kategorie(n)")

    st.markdown("---")

    # Quick Actions
    with st.expander("⚡ **Schnellaktionen: Neue Buchung / Ziel / Schuld / Wunsch erfassen**"):
        qa_tab1, qa_tab2, qa_tab3, qa_tab4 = st.tabs(["Neue Buchung", "Neues Sparziel", "Neue Schuld/Forderung", "Neue Wunschliste"])
        
        with qa_tab1:
            with st.form("qa_trans_form"):
                qa_date = st.date_input("Datum", date.today())
                qa_type = st.selectbox("Typ", ["Ausgabe", "Einnahme"])
                qa_cat_names = [c["name"] for c in engine.categories if c["name"] not in ["Einkommen", "Umbuchung"]]
                qa_cat = st.selectbox("Kategorie", qa_cat_names)
                qa_desc = st.text_input("Beschreibung (z. B. Supermarkt #Essen)", placeholder="z. B. #Essen")
                qa_acc = st.selectbox("Konto/Bargeld", ["Konto", "Bargeld"])
                qa_amt = st.number_input("Betrag in €", min_value=0.01, value=15.00, step=1.00)
                qa_status = st.radio("Status", ["Ist", "Geplant"], horizontal=True)
                if st.form_submit_button("Buchung speichern"):
                    engine.add_transaction(
                        qa_date.isoformat(), qa_status, qa_type, qa_cat, qa_desc, qa_acc, parse_euro_to_cents(qa_amt)
                    )
                    st.success("Buchung gespeichert!")
                    st.rerun()

        with qa_tab2:
            with st.form("qa_sg_form"):
                sg_name = st.text_input("Zielname", placeholder="z. B. Urlaub")
                sg_target = st.number_input("Zielbetrag (€)", min_value=1.0, value=500.0)
                sg_saved = st.number_input("Bereits gespart (€)", min_value=0.0, value=50.0)
                sg_rate = st.number_input("Monatliche Sparrate (€)", min_value=0.0, value=50.0)
                if st.form_submit_button("Sparziel erstellen"):
                    engine.savings_goals.append({
                        "id": str(datetime.now().timestamp()),
                        "name": sg_name,
                        "target_cents": parse_euro_to_cents(sg_target),
                        "saved_cents": parse_euro_to_cents(sg_saved),
                        "monthly_rate_cents": parse_euro_to_cents(sg_rate),
                        "priority": "Mittel",
                        "desired_date": ""
                    })
                    st.success("Sparziel erstellt!")
                    st.rerun()

        with qa_tab3:
            with st.form("qa_debt_form"):
                d_person = st.text_input("Person", placeholder="z. B. Alex")
                d_reason = st.text_input("Grund", placeholder="z. B. Geschenk")
                d_dir = st.selectbox("Richtung", ["Mir geschuldet", "Ich schulde"])
                d_total = st.number_input("Gesamtbetrag (€)", min_value=1.0, value=30.0)
                d_due = st.date_input("Fälligkeitsdatum", date.today())
                if st.form_submit_button("Schuld/Forderung speichern"):
                    engine.debts.append({
                        "id": str(datetime.now().timestamp()),
                        "person": d_person,
                        "reason": d_reason,
                        "direction": d_dir,
                        "total_cents": parse_euro_to_cents(d_total),
                        "paid_cents": 0,
                        "due_date": d_due.isoformat(),
                        "notes": "",
                        "payments": []
                    })
                    st.success("Schuld/Forderung gespeichert!")
                    st.rerun()

        with qa_tab4:
            with st.form("qa_wl_form"):
                wl_name = st.text_input("Name der Wunschliste", placeholder="z. B. Geschenke 2026")
                if st.form_submit_button("Wunschliste anlegen"):
                    if wl_name:
                        engine.wishlists.append({
                            "id": str(datetime.now().timestamp()),
                            "name": wl_name,
                            "items": []
                        })
                        st.success("Wunschliste angelegt!")
                        st.rerun()

    # Forecast & Visualizations Section
    st.subheader(f"📈 {fc_m}-Monats-Entwicklung der Liquiden Mittel")
    fc_data = engine.calculate_forecast(num_months=fc_m)
    
    df_fc_rows = []
    for m in fc_data["months"]:
        m_key = m["month"]
        df_fc_rows.append({"Monat": m_key, "Szenario": "Best Case", "Liquide Mittel (€)": m["best_balance_cents"] / 100})
        df_fc_rows.append({"Monat": m_key, "Szenario": "Normal Case", "Liquide Mittel (€)": m["normal_balance_cents"] / 100})
        df_fc_rows.append({"Monat": m_key, "Szenario": "Worst Case", "Liquide Mittel (€)": m["worst_balance_cents"] / 100})
    
    df_fc = pd.DataFrame(df_fc_rows)
    fig_fc = px.line(
        df_fc, x="Monat", y="Liquide Mittel (€)", color="Szenario",
        title=f"Prognoseverlauf über {fc_m} Monate",
        color_discrete_map={"Best Case": "#4ade80", "Normal Case": "#38bdf8", "Worst Case": "#f87171"}
    )
    fig_fc.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="0 € Grenze")
    fig_fc.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#f8fafc")
    st.plotly_chart(fig_fc, use_container_width=True)

    # Secondary Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader(f"📊 Budgetverbrauch ({cur_month})")
        b_data = []
        for cat in engine.categories:
            if cat.get("limit_cents", 0) > 0 and cat["name"] not in ["Fixkosten", "Einmalig", "Einkommen", "Umbuchung"]:
                bm = engine.calculate_monthly_budget(cur_month, cat["name"])
                b_data.append({
                    "Kategorie": cat["name"],
                    "Ist-Ausgaben (€)": bm["spent_cents"] / 100,
                    "Limit (€)": bm["limit_cents"] / 100
                })
        if b_data:
            df_b = pd.DataFrame(b_data)
            fig_b = px.bar(
                df_b, x="Kategorie", y=["Ist-Ausgaben (€)", "Limit (€)"], barmode="group",
                title="Monatsausgaben vs. Budget-Limits"
            )
            fig_b.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#f8fafc")
            st.plotly_chart(fig_b, use_container_width=True)
        else:
            st.info("Keine aktiven Kategorie-Limits konfiguriert.")

    with chart_col2:
        st.subheader(f"🍰 Ausgaben nach Kategorie ({cur_month})")
        exp_by_cat = {}
        for t in engine.transactions:
            if t.get("status") == "Ist" and t.get("type") == "Ausgabe" and t.get("date","").startswith(cur_month):
                c = t.get("category", "Sonstiges")
                exp_by_cat[c] = exp_by_cat.get(c, 0) + (t.get("amountCents", 0) / 100)
        if exp_by_cat:
            df_pie = pd.DataFrame([{"Kategorie": k, "Ausgaben (€)": v} for k, v in exp_by_cat.items()])
            fig_pie = px.pie(df_pie, values="Ausgaben (€)", names="Kategorie", title="Verteilung der Ausgaben", hole=0.4)
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#f8fafc")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Noch keine Ausgaben in diesem Monat gebucht.")

    # AI Coach Banner
    st.subheader("💡 **Dein KI-Finanz-Coach**")
    ai_tips = engine.generate_ai_financial_tips(cur_month)
    for tip in ai_tips:
        st.info(tip)

# ==========================================
# 2. BUCHUNGSREGISTER
# ==========================================
elif selected_page.startswith("2."):
    st.title("📝 Buchungsregister")
    st.caption("Filterung nach Status, Typ, Hashtags (#Tags) und Verwaltung aller Buchungen.")

    with st.expander("➕ **Neue Buchung manuell anlegen**", expanded=False):
        with st.form("add_trans_form"):
            t_col1, t_col2, t_col3 = st.columns(3)
            with t_col1:
                new_t_date = st.date_input("Datum", date.today())
                new_t_status = st.selectbox("Status", ["Ist", "Geplant"])
            with t_col2:
                new_t_type = st.selectbox("Typ", ["Ausgabe", "Einnahme"])
                new_t_cat_names = [c["name"] for c in engine.categories if c["name"] not in ["Einkommen", "Umbuchung"]]
                new_t_cat = st.selectbox("Kategorie", new_t_cat_names)
            with t_col3:
                new_t_acc = st.selectbox("Konto/Bargeld", ["Konto", "Bargeld"])
                new_t_amt = st.number_input("Betrag in €", min_value=0.01, value=20.00, step=1.00)
            
            new_t_desc = st.text_input("Beschreibung (z. B. #Urlaub2026 Geschenk für Alex)")
            if st.form_submit_button("Buchung anlegen"):
                engine.add_transaction(
                    new_t_date.isoformat(), new_t_status, new_t_type, new_t_cat,
                    new_t_desc, new_t_acc, parse_euro_to_cents(new_t_amt)
                )
                st.success("Buchung erfolgreich angelegt!")
                st.rerun()

    with st.expander("🔄 **Neue Umbuchung tätigen (Konto ↔ Bargeld)**", expanded=False):
        with st.form("add_transfer_form"):
            tr_col1, tr_col2, tr_col3 = st.columns(3)
            with tr_col1:
                tr_from = st.selectbox("Von Konto", ["Konto", "Bargeld"])
                tr_to = st.selectbox("Zu Konto", ["Bargeld", "Konto"])
            with tr_col2:
                tr_amt = st.number_input("Betrag in €", min_value=1.0, value=50.0, step=5.0)
                tr_date = st.date_input("Umbuchungsdatum", date.today())
            with tr_col3:
                tr_desc = st.text_input("Beschreibung", value="Bargeld-Abhebung")
            if st.form_submit_button("Umbuchung durchführen"):
                if tr_from == tr_to:
                    st.error("Quell- und Zielkonto dürfen nicht identisch sein!")
                else:
                    engine.add_transfer(
                        tr_date.isoformat(), "Ist", tr_from, tr_to, tr_desc, parse_euro_to_cents(tr_amt)
                    )
                    st.success("Umbuchung gebucht!")
                    st.rerun()

    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        f_status = st.multiselect("Status Filter", ["Ist", "Geplant"])
    with f_col2:
        f_type = st.multiselect("Typ Filter", ["Ausgabe", "Einnahme", "Umbuchung Ausgang", "Umbuchung Eingang"])
    with f_col3:
        f_acc = st.multiselect("Konto Filter", ["Konto", "Bargeld"])
    with f_col4:
        f_search = st.text_input("Freitext / Tag-Suche", placeholder="z. B. #Urlaub")

    filtered_t = []
    for t in engine.transactions:
        if f_status and t.get("status") not in f_status:
            continue
        if f_type and t.get("type") not in f_type:
            continue
        if f_acc and t.get("account") not in f_acc:
            continue
        if f_search:
            q = f_search.lower()
            desc_match = q in t.get("description", "").lower()
            tag_match = any(q in tg.lower() for tg in t.get("tags", []))
            if not (desc_match or tag_match):
                continue
        filtered_t.append(t)

    if filtered_t:
        t_rows = []
        for t in filtered_t:
            amt_str = cents_to_euro_str(t.get("amountCents", 0), privacy)
            if t.get("type") in ["Ausgabe", "Umbuchung Ausgang"]:
                amt_str = f"-{amt_str}"
            t_rows.append({
                "ID": t["id"][:8],
                "Datum": format_date_de(t.get("date")),
                "Status": t.get("status"),
                "Typ": t.get("type"),
                "Kategorie": t.get("category"),
                "Beschreibung": t.get("description"),
                "Tags": " ".join(t.get("tags", [])),
                "Konto/Bargeld": t.get("account"),
                "Betrag": amt_str
            })
        st.dataframe(pd.DataFrame(t_rows), use_container_width=True)

        st.markdown("---")
        st.subheader("Aktionen für gewählte Buchung")
        del_id = st.selectbox("Buchung auswählen (nach ID)", [t["id"] for t in filtered_t], format_func=lambda x: f"{x[:8]} - {next((t['description'] for t in filtered_t if t['id']==x), '')}")
        
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            if st.button("🗑️ Ausgewählte Buchung löschen"):
                engine.transactions = [t for t in engine.transactions if t["id"] != del_id]
                st.success("Buchung gelöscht.")
                st.rerun()
        with act_col2:
            if st.button("📋 Ausgewählte Buchung duplizieren"):
                orig = next(t for t in engine.transactions if t["id"] == del_id)
                engine.add_transaction(
                    date.today().isoformat(), orig["status"], orig["type"], orig["category"],
                    f"{orig['description']} (Kopie)", orig["account"], orig["amountCents"]
                )
                st.success("Buchung dupliziert!")
                st.rerun()
    else:
        st.info("Keine Buchungen für die gewählten Filter gefunden.")

# ==========================================
# 3. MONATSBUDGET
# ==========================================
elif selected_page.startswith("3."):
    st.title("🎯 Monatsbudget & Limits")
    st.caption("Überwachung der variablen Ausgaben je Kategorie.")

    sel_month = st.date_input("Monat auswählen", date.today()).strftime("%Y-%m")
    
    st.subheader(f"Budgetauslastung für {sel_month}")
    
    budget_summary = []
    for cat in engine.categories:
        if cat["name"] in ["Fixkosten", "Einmalig", "Einkommen", "Umbuchung"]:
            continue
        bm = engine.calculate_monthly_budget(sel_month, cat["name"])
        budget_summary.append(bm)

    if budget_summary:
        cols = st.columns(3)
        for idx, bm in enumerate(budget_summary):
            with cols[idx % 3]:
                st.markdown(f"### {bm['category']}")
                st.write(f"**Limit:** {cents_to_euro_str(bm['limit_cents'], privacy)}")
                st.write(f"**Ausgegeben:** {cents_to_euro_str(bm['spent_cents'], privacy)}")
                st.write(f"**Verbleibend:** {cents_to_euro_str(bm['rest_cents'], privacy)}")
                
                pct = min(1.0, bm["utilization_pct"] / 100.0)
                st.progress(pct)
                
                if bm["status"] == "Überschritten":
                    st.error("⚠️ Überschritten!")
                elif bm["status"] == "Fast aufgebraucht":
                    st.warning(f"⚡ Fast aufgebraucht ({bm['utilization_pct']:.1f}%)")
                else:
                    st.success("✅ Im Rahmen")
                st.markdown("---")

    # Category Management
    with st.expander("➕ **Neue Kategorie anlegen**", expanded=False):
        with st.form("add_cat_form"):
            c_name = st.text_input("Kategoriename (z. B. Hobbys)")
            c_limit = st.number_input("Monatliches Limit (€)", min_value=0.0, value=50.0, step=10.0)
            if st.form_submit_button("Kategorie anlegen"):
                if c_name:
                    engine.categories.append({
                        "id": str(datetime.now().timestamp()),
                        "name": c_name,
                        "limit_cents": parse_euro_to_cents(c_limit),
                        "active": True
                    })
                    st.success(f"Kategorie '{c_name}' angelegt!")
                    st.rerun()

    with st.expander("⚙️ **Kategorien verwalten (Limits anpassen & löschen)**", expanded=False):
        st.subheader("Bestehende Kategorien bearbeiten oder löschen")
        for cat in engine.categories[:]:
            if cat["name"] not in ["Fixkosten", "Einmalig", "Einkommen", "Umbuchung"]:
                c_col1, c_col2, c_col3 = st.columns([3, 2, 1])
                with c_col1:
                    cat["name"] = st.text_input("Name", value=cat["name"], key=f"cat_n_{cat['id']}")
                with c_col2:
                    new_lim = st.number_input(
                        "Limit (€)", min_value=0.0, value=float(cat["limit_cents"]/100), step=5.0, key=f"cat_l_{cat['id']}"
                    )
                    cat["limit_cents"] = parse_euro_to_cents(new_lim)
                with c_col3:
                    st.write("")
                    st.write("")
                    if st.button("🗑️", key=f"del_cat_{cat['id']}", help="Kategorie löschen"):
                        engine.categories = [c for c in engine.categories if c["id"] != cat["id"]]
                        st.success("Kategorie gelöscht!")
                        st.rerun()

# ==========================================
# 4. SPARZIELE & CHALLENGES
# ==========================================
elif selected_page.startswith("4."):
    st.title("🐖 Sparziele & Spar-Challenges")
    st.caption("Sparfortschritt, individuelle Spar-Challenges, 0-Euro-Tage Streak & Badge-Galerie.")

    tab_sg, tab_ch, tab_badges = st.tabs(["🎯 Meine Sparziele", "📅 Spar-Challenge Generator", "🏆 Abzeichen & Badges"])

    with tab_sg:
        goals_summary = engine.calculate_savings_goals_forecast(num_months=fc_m)

        with st.expander("➕ **Neues Sparziel anlegen**"):
            with st.form("add_sg_tab_form"):
                new_sg_n = st.text_input("Zielname (z. B. Führerschein)")
                new_sg_t = st.number_input("Zielbetrag (€)", min_value=1.0, value=1000.0)
                new_sg_s = st.number_input("Bereits gespart (€)", min_value=0.0, value=100.0)
                new_sg_r = st.number_input("Monatliche Sparrate (€)", min_value=0.0, value=50.0)
                if st.form_submit_button("Sparziel anlegen"):
                    if new_sg_n:
                        engine.savings_goals.append({
                            "id": str(datetime.now().timestamp()),
                            "name": new_sg_n,
                            "target_cents": parse_euro_to_cents(new_sg_t),
                            "saved_cents": parse_euro_to_cents(new_sg_s),
                            "monthly_rate_cents": parse_euro_to_cents(new_sg_r),
                            "priority": "Mittel",
                            "desired_date": ""
                        })
                        st.success("Sparziel angelegt!")
                        st.rerun()

        if goals_summary:
            for sg in goals_summary:
                with st.container():
                    st.subheader(f"🎯 {sg['name']}")
                    g_col1, g_col2, g_col3, g_col4 = st.columns([3, 3, 3, 1])
                    with g_col1:
                        st.write(f"**Zielbetrag:** {cents_to_euro_str(sg['target_cents'], privacy)}")
                        st.write(f"**Bereits gespart:** {cents_to_euro_str(sg['saved_cents'], privacy)}")
                        st.write(f"**Offener Restbetrag:** {cents_to_euro_str(sg['rest_cents'], privacy)}")
                    with g_col2:
                        st.write(f"**Monatliche Sparrate:** {cents_to_euro_str(sg['monthly_rate_cents'], privacy)}")
                        st.write(f"**Rechnerisches Zieldatum:** {sg['calc_target_date']}")
                    with g_col3:
                        st.info(f"💡 **Machbar ab:** {sg['forecast_buy_month']}")
                    with g_col4:
                        if st.button("🗑️", key=f"del_sg_{sg['id']}"):
                            engine.savings_goals = [s for s in engine.savings_goals if s["id"] != sg["id"]]
                            st.success("Sparziel entfernt.")
                            st.rerun()

                    # Quick Deposit Form directly on Goal Card
                    with st.expander(f"💵 Geld auf '{sg['name']}' einzahlen / anpassen"):
                        with st.form(f"deposit_sg_form_{sg['id']}"):
                            dep_amt = st.number_input("Betrag zum Einzahlen (€)", min_value=1.0, value=25.0)
                            if st.form_submit_button("Betrag einzahlen"):
                                real_sg = next((s for s in engine.savings_goals if s["id"] == sg["id"]), None)
                                if real_sg:
                                    real_sg["saved_cents"] += parse_euro_to_cents(dep_amt)
                                    st.success(f"{dep_amt} € eingezahlt!")
                                    st.rerun()

                    pct = min(1.0, sg["saved_cents"] / sg["target_cents"]) if sg["target_cents"] > 0 else 1.0
                    st.progress(pct)
                    st.caption(f"Fortschritt: {cents_to_euro_str(sg['saved_cents'], privacy)} / {cents_to_euro_str(sg['target_cents'], privacy)} ({pct*100:.1f}%)")
                    st.markdown("---")

    with tab_ch:
        st.subheader("⚙️ **Individuelle Spar-Challenge konfigurieren**")
        
        ch_target_cents = engine.challenges.get("target_cents", 137800)
        ch_num_weeks = engine.challenges.get("num_weeks", 52)
        ch_mode = engine.challenges.get("mode", "Progressiv")

        with st.expander("🛠️ **Challenge-Parameter anpassen (Zielbetrag & Dauer)**", expanded=True):
            with st.form("custom_challenge_form"):
                col_ch1, col_ch2, col_ch3 = st.columns(3)
                with col_ch1:
                    user_target = st.number_input("Sparziel der Challenge (€)", min_value=10.0, value=float(ch_target_cents/100), step=50.0)
                with col_ch2:
                    user_weeks = st.number_input("Laufzeit in Wochen", min_value=1, max_value=104, value=int(ch_num_weeks), step=1)
                with col_ch3:
                    user_mode = st.selectbox("Challenge-Typ", ["Progressiv", "Gleichmäßig"], index=0 if ch_mode=="Progressiv" else 1)

                if st.form_submit_button("🚀 Neue Challenge generieren"):
                    t_cents = parse_euro_to_cents(user_target)
                    w_list = create_challenge_weeks(t_cents, int(user_weeks), user_mode)
                    engine.challenges = {
                        "target_cents": t_cents,
                        "num_weeks": int(user_weeks),
                        "mode": user_mode,
                        "weeks": w_list
                    }
                    st.success(f"Spar-Challenge über {cents_to_euro_str(t_cents, privacy)} in {user_weeks} Wochen generiert!")
                    st.rerun()

        weeks = engine.challenges.get("weeks", [])
        saved_challenge_cents = sum(w["amount_cents"] for w in weeks if w.get("completed", False))
        total_target = engine.challenges.get("target_cents", 137800)
        
        c_pct = min(1.0, saved_challenge_cents / total_target) if total_target > 0 else 0.0

        st.markdown("---")
        m_ch1, m_ch2, m_ch3 = st.columns(3)
        m_ch1.metric("Gesamtziel der Challenge", cents_to_euro_str(total_target, privacy))
        m_ch2.metric("Bereits in Challenge gespart", cents_to_euro_str(saved_challenge_cents, privacy))
        m_ch3.metric("Verbleibender Rest", cents_to_euro_str(max(0, total_target - saved_challenge_cents), privacy))

        st.progress(c_pct)
        st.caption(f"Fortschritt: {c_pct*100:.1f}% des Challenge-Ziels erreicht.")

        st.markdown("---")
        st.subheader("📅 **Wochen-Checkliste**")
        ch_cols = st.columns(4)
        for idx, w in enumerate(weeks):
            with ch_cols[idx % 4]:
                w_amt = cents_to_euro_str(w["amount_cents"], privacy)
                chk = st.checkbox(f"Woche {w['week']} ({w_amt})", value=w.get("completed", False), key=f"ch_w_{w['week']}")
                w["completed"] = chk

    with tab_badges:
        st.subheader("🏆 **Erfolge & Abzeichen**")
        
        cur_m = date.today().strftime("%Y-%m")
        z_days, eval_d = engine.calculate_zero_euro_days(cur_m)
        
        st.markdown('<div class="apple-card">', unsafe_allow_html=True)
        st.write(f"### 🔥 **0-Euro-Tage Streak in {cur_m}: {z_days} von {eval_d} Tagen!**")
        st.caption("An diesen Tagen hast du kein Geld für variable Ausgaben ausgegeben. Weiter so!")
        st.markdown('</div>', unsafe_allow_html=True)

        badges = engine.get_earned_badges()
        if badges:
            b_cols = st.columns(3)
            for idx, b in enumerate(badges):
                with b_cols[idx % 3]:
                    st.markdown(f"""
                    <div class="apple-card" style="text-align: center;">
                        <div style="font-size: 2.5rem;">{b['icon']}</div>
                        <div style="font-weight: bold; font-size: 1.1rem;">{b['title']}</div>
                        <div style="color: #8e8e93; font-size: 0.85rem;">{b['desc']}</div>
                    </div>
                    """, unsafe_allow_html=True)

# ==========================================
# 5. BARGELD-RECHNER
# ==========================================
elif selected_page.startswith("5."):
    st.title("💵 Bargeld-Stückelungsrechner")
    st.caption("Erfassung aller Scheine und Münzen bis 1 Cent.")

    st.subheader("Stückelung erfassen")
    total_denom_cents = 0
    
    c_cols = st.columns(3)
    for idx, denom in enumerate(engine.cash_denominations):
        with c_cols[idx % 3]:
            count = st.number_input(
                f"{denom['name']} ({cents_to_euro_str(denom['value_cents'], privacy)})",
                min_value=0,
                value=denom["count"],
                step=1,
                key=f"denom_{idx}"
            )
            denom["count"] = count
            subtotal = count * denom["value_cents"]
            total_denom_cents += subtotal
            st.caption(f"Gesamt: {cents_to_euro_str(subtotal, privacy)}")

    st.markdown("---")
    st.subheader(f"💰 Gesamtbargeld: {cents_to_euro_str(total_denom_cents, privacy)}")
    
    if st.button("Als Bargeld-Startbestand übernehmen"):
        engine.settings["start_cash_cents"] = total_denom_cents
        st.success("Startbestand aktualisiert!")
        st.rerun()

# ==========================================
# 6. WUNSCHLISTEN
# ==========================================
elif selected_page.startswith("6."):
    st.title("🎁 Wunschlisten")
    st.caption("Simulation von Wünschen und Berechnung des Machbarkeits-Monats.")

    wl_summary = engine.calculate_wishlist_summary(num_months=fc_m)

    w_m1, w_m2, w_m3, w_m4 = st.columns(4)
    w_m1.metric("Aktivierte Wünsche", cents_to_euro_str(wl_summary["total_active_cents"], privacy))
    w_m2.metric("Liquides Vermögen", cents_to_euro_str(balances["liquid_assets_cents"], privacy))
    w_m3.metric("Offener Betrag", cents_to_euro_str(wl_summary["overall_missing_cents"], privacy))
    
    if wl_summary["overall_machbar"]:
        w_m4.success("✅ Jetzt machbar!")
    else:
        w_m4.info(f"💡 Machbar ab: **{wl_summary['overall_reachability_month']}**")

    st.markdown("---")

    with st.expander("➕ **Neue Wunschliste (Oberkategorie) anlegen**", expanded=False):
        with st.form("add_new_wl_cat_form"):
            new_wl_title = st.text_input("Name der neuen Wunschliste (z. B. Urlaub 2026, Wohnung, Geschenke)")
            if st.form_submit_button("Wunschliste anlegen"):
                if new_wl_title:
                    engine.wishlists.append({
                        "id": str(datetime.now().timestamp()),
                        "name": new_wl_title,
                        "items": []
                    })
                    st.success(f"Wunschliste '{new_wl_title}' angelegt!")
                    st.rerun()

    st.markdown("---")

    for wl in engine.wishlists[:]:
        st.subheader(f"📜 {wl['name']}")
        
        wl_active_price = sum(item.get("price_cents", 0) for item in wl.get("items", []) if item.get("active", False))
        wl_reach_month = engine.calculate_wishlist_reachability(wl_active_price, num_months=fc_m)
        st.caption(f"Aktiviert: **{cents_to_euro_str(wl_active_price, privacy)}** | Machbar ab: **{wl_reach_month}**")

        wl_c1, wl_c2 = st.columns([4, 1])
        with wl_c1:
            with st.expander(f"➕ Neuen Wunsch zu '{wl['name']}' hinzufügen"):
                with st.form(f"add_wish_form_{wl['id']}"):
                    w_name = st.text_input("Wunschname")
                    w_price = st.number_input("Preis (€)", min_value=1.0, value=50.0, step=5.0)
                    w_url = st.text_input("Shop Link (optional)")
                    w_active = st.checkbox("Aktivieren (in Simulation einrechnen)", value=True)
                    if st.form_submit_button("Wunsch speichern"):
                        if w_name:
                            wl["items"].append({
                                "id": str(datetime.now().timestamp()),
                                "name": w_name,
                                "url": w_url,
                                "price_cents": parse_euro_to_cents(w_price),
                                "active": w_active,
                                "notes": ""
                            })
                            st.success("Wunsch hinzugefügt!")
                            st.rerun()
        with wl_c2:
            if st.button(f"🗑️ Liste löschen", key=f"del_wl_{wl['id']}", help="Gesamte Ober-Wunschliste löschen"):
                engine.wishlists = [w for w in engine.wishlists if w["id"] != wl["id"]]
                st.success(f"Wunschliste '{wl['name']}' gelöscht!")
                st.rerun()

        if wl["items"]:
            for item in wl["items"][:]:
                wi_col1, wi_col2, wi_col3, wi_col4, wi_col5 = st.columns([3, 2, 2, 2, 1])
                with wi_col1:
                    st.write(f"**{item['name']}**")
                    if item.get("url"):
                        st.caption(f"[Shop Link]({item['url']})")
                with wi_col2:
                    st.write(cents_to_euro_str(item["price_cents"], privacy))
                    item_reach = engine.calculate_wishlist_reachability(item["price_cents"], num_months=fc_m)
                    st.caption(f"Machbar: **{item_reach}**")
                with wi_col3:
                    item["active"] = st.checkbox("Aktiv", value=item.get("active", True), key=f"wi_act_{item['id']}")
                with wi_col4:
                    if st.button("🛒 Kaufen", key=f"buy_wi_{item['id']}", help="Erzeugt echte Ist-Ausgabe"):
                        engine.add_transaction(
                            date.today().isoformat(), "Ist", "Ausgabe", "Einmalig",
                            f"Kauf Wunsch: {item['name']}", "Konto", item["price_cents"]
                        )
                        st.success(f"Kauf gebucht für {item['name']}!")
                        st.rerun()
                with wi_col5:
                    if st.button("🗑️", key=f"del_item_{item['id']}"):
                        wl["items"] = [i for i in wl["items"] if i["id"] != item["id"]]
                        st.success("Entfernt!")
                        st.rerun()
        else:
            st.info("Diese Wunschliste ist leer.")
        st.markdown("---")

# ==========================================
# 7. SCHULDEN & FORDERUNGEN
# ==========================================
elif selected_page.startswith("7."):
    st.title("🤝 Schulden & Forderungen")
    st.caption("Verwaltung von Außenständen mit Teilzahlungshistorie.")

    rec_cents = balances["receivables_cents"]
    debt_cents = balances["debts_cents"]

    s_c1, s_c2 = st.columns(2)
    s_c1.metric("Mir geschuldet (Forderungen)", cents_to_euro_str(rec_cents, privacy))
    s_c2.metric("Ich schulde (Schulden)", cents_to_euro_str(debt_cents, privacy))

    st.markdown("---")

    with st.expander("➕ **Neue Schuld / Forderung erfassen**", expanded=False):
        with st.form("add_debt_main_form"):
            d_p = st.text_input("Person / Kontakt (z. B. Max)")
            d_r = st.text_input("Grund (z. B. Konzertkarte)")
            d_d = st.selectbox("Richtung", ["Mir geschuldet", "Ich schulde"])
            d_tot = st.number_input("Gesamtbetrag (€)", min_value=1.0, value=50.0, step=5.0)
            d_due_d = st.date_input("Fälligkeitsdatum", date.today())
            d_notes = st.text_input("Notizen (optional)")
            if st.form_submit_button("Schuld/Forderung speichern"):
                if d_p and d_r:
                    engine.debts.append({
                        "id": str(datetime.now().timestamp()),
                        "person": d_p,
                        "reason": d_r,
                        "direction": d_d,
                        "total_cents": parse_euro_to_cents(d_tot),
                        "paid_cents": 0,
                        "due_date": d_due_d.isoformat(),
                        "notes": d_notes,
                        "payments": []
                    })
                    st.success("Schuld/Forderung erfasst!")
                    st.rerun()

    st.markdown("---")

    if engine.debts:
        for d in engine.debts[:]:
            open_amt = max(0, d.get("total_cents", 0) - d.get("paid_cents", 0))
            with st.expander(f"{d['direction']}: {d['person']} ({cents_to_euro_str(open_amt, privacy)} offen)"):
                d_col1, d_col2 = st.columns([1, 1])
                with d_col1:
                    st.write(f"**Grund:** {d['reason']}")
                    st.write(f"**Gesamtbetrag:** {cents_to_euro_str(d['total_cents'], privacy)}")
                    st.write(f"**Bereits bezahlt:** {cents_to_euro_str(d['paid_cents'], privacy)}")
                    st.write(f"**Offener Rest:** {cents_to_euro_str(open_amt, privacy)}")
                    st.write(f"**Fälligkeit:** {format_date_de(d.get('due_date'))}")
                    if st.button("🗑️ Eintrag löschen", key=f"del_debt_{d['id']}"):
                        engine.debts = [debt for debt in engine.debts if debt["id"] != d["id"]]
                        st.success("Eintrag gelöscht!")
                        st.rerun()

                with d_col2:
                    st.subheader("Teilzahlung erfassen")
                    with st.form(f"payment_form_{d['id']}"):
                        pay_amt = st.number_input("Teilzahlung in €", min_value=0.01, value=float(open_amt/100) if open_amt > 0 else 10.0)
                        pay_date = st.date_input("Zahlungsdatum", date.today())
                        auto_t = st.checkbox("Automatisch passende Ist-Buchung erstellen", value=True)
                        if st.form_submit_button("Zahlung verbuchen"):
                            engine.add_debt_payment(d["id"], pay_date.isoformat(), parse_euro_to_cents(pay_amt), auto_create_transaction=auto_t)
                            st.success("Teilzahlung verbucht!")
                            st.rerun()

                if d.get("payments"):
                    st.write("**Zahlungshistorie:**")
                    for p in d["payments"]:
                        st.caption(f"• {format_date_de(p['date'])}: {cents_to_euro_str(p['amount_cents'], privacy)}")
    else:
        st.info("Keine Schulden oder Forderungen erfasst.")

# ==========================================
# 8. KALENDER & FIXKOSTEN
# ==========================================
elif selected_page.startswith("8."):
    st.title("📅 Kalender & Fixkosten")
    st.caption("Interaktiver Finanz-Kalender, Taschengeld-Rechner, Abos und Event-Monate.")

    tab_cal, tab_inc, tab_fix, tab_events = st.tabs([
        "📅 Interaktiver Kalender", "💵 Taschengeld & Einnahmen", "🔒 Fixkosten & Abos", "🎉 Event-Monate"
    ])

    with tab_cal:
        st.subheader("Interaktiver Monats-Kalender")
        cal_col1, cal_col2 = st.columns([1, 3])
        with cal_col1:
            sel_y = st.number_input("Jahr", min_value=2024, max_value=2030, value=date.today().year)
            sel_m = st.number_input("Monat", min_value=1, max_value=12, value=date.today().month)
        
        cal_grid, days_data = engine.generate_calendar_month_data(sel_y, sel_m)
        
        st.markdown(f"### Kalenderansicht für {sel_m:02d}/{sel_y}")
        
        day_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        header_cols = st.columns(7)
        for idx, name in enumerate(day_names):
            header_cols[idx].markdown(f"**{name}**")

        for week in cal_grid:
            w_cols = st.columns(7)
            for idx, day in enumerate(week):
                if day == 0:
                    w_cols[idx].write("")
                else:
                    items = days_data.get(day, [])
                    btn_label = f"{day} 📌" if items else f"{day}"
                    if w_cols[idx].button(btn_label, key=f"btn_cal_{sel_y}_{sel_m}_{day}"):
                        st.session_state.cal_selected_day = day

        selected_d = st.session_state.cal_selected_day
        max_d = calendar.monthrange(sel_y, sel_m)[1]
        if selected_d > max_d:
            selected_d = max_d

        st.markdown("---")
        st.markdown('<div class="apple-card">', unsafe_allow_html=True)
        st.subheader(f"📌 Details & Kontostand für den {selected_d:02d}.{sel_m:02d}.{sel_y}")

        proj = engine.calculate_projected_balance_for_day(sel_y, sel_m, selected_d)
        proj_str = cents_to_euro_str(proj["projected_liquid_cents"], privacy)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.metric(f"Prognostizierter Kontostand am {selected_d:02d}.{sel_m:02d}.{sel_y}", proj_str)
            if proj["is_future"]:
                st.caption("ℹ️ Berechnet basierend auf bisherigen Buchungen, Fixkosten und Einnahmen bis zu diesem Tag.")
            else:
                st.caption("ℹ️ Aktueller Ist-Bestand.")

        with col_d2:
            st.write("**Einnahmen, Ausgaben & Abos an diesem Tag:**")
            day_items = days_data.get(selected_d, [])
            if day_items:
                for it in day_items:
                    amt_str = cents_to_euro_str(it["amount_cents"], privacy)
                    icon = "🟢" if it["direction"]=="in" else "🔴"
                    st.write(f"{icon} **{it['title']}**: {amt_str} ({it['status']})")
            else:
                st.info("Keine besonderen Abbuchungen oder Einnahmen an diesem Tag.")

        st.markdown("---")
        st.write("⚡ **Abbuchungstag von Fixkosten auf diesen Tag anpassen:**")
        
        fix_options = {exp["id"]: f"{exp['name']} ({cents_to_euro_str(exp['amount_cents'], privacy)}) - aktuell Tag {exp.get('due_day', 1)}" for exp in engine.recurring_expenses}
        if fix_options:
            c_f1, c_f2 = st.columns([3, 1])
            with c_f1:
                sel_fix_id = st.selectbox("Abo / Fixkosten auswählen", list(fix_options.keys()), format_func=lambda x: fix_options[x])
            with c_f2:
                st.write("")
                st.write("")
                if st.button(f"Abbuchung auf Tag {selected_d} legen"):
                    exp_item = next((e for e in engine.recurring_expenses if e["id"] == sel_fix_id), None)
                    if exp_item:
                        exp_item["due_day"] = selected_d
                        st.success(f"Abbuchungstag für '{exp_item['name']}' auf den {selected_d}. gelegt!")
                        st.rerun()
        else:
            st.caption("Keine Abos vorhanden.")

        st.markdown('</div>', unsafe_allow_html=True)

    with tab_inc:
        st.subheader("Monatliche Einnahmen & Taschengeld-Rechner")
        
        with st.expander("➕ **Neue wiederkehrende Einnahme hinzufügen**"):
            with st.form("add_inc_form"):
                inc_n = st.text_input("Name der Einnahme (z. B. Nebenjob, Taschengeld)")
                inc_a = st.number_input("Betrag (€/Monat)", min_value=1.0, value=100.0, step=10.0)
                inc_d = st.number_input("Eingangstag im Monat (1-31)", min_value=1, max_value=31, value=1)
                if st.form_submit_button("Einnahme speichern"):
                    if inc_n:
                        engine.recurring_incomes.append({
                            "id": str(datetime.now().timestamp()),
                            "name": inc_n,
                            "amount_cents": parse_euro_to_cents(inc_a),
                            "due_day": int(inc_d),
                            "received_current_month": False,
                            "last_received_date": date.today().isoformat()
                        })
                        st.success("Einnahme hinzugefügt!")
                        st.rerun()

        for inc in engine.recurring_incomes[:]:
            st.markdown(f"### 💰 {inc['name']}")
            i_col1, i_col2, i_col3, i_col4 = st.columns([3, 2, 2, 1])
            with i_col1:
                inc["amount_cents"] = parse_euro_to_cents(st.number_input(f"Betrag (€/Monat)", value=float(inc["amount_cents"]/100), key=f"inc_{inc['id']}"))
            with i_col2:
                inc["due_day"] = st.number_input(f"Eingangstag (1-31)", min_value=1, max_value=31, value=int(inc.get("due_day", 1)), key=f"inc_day_{inc['id']}")
            with i_col3:
                inc["received_current_month"] = st.checkbox("Im aktuellen Monat bereits erhalten", value=inc.get("received_current_month", False), key=f"inc_rec_{inc['id']}")
            with i_col4:
                st.write("")
                st.write("")
                if st.button("🗑️", key=f"del_inc_{inc['id']}"):
                    engine.recurring_incomes = [i for i in engine.recurring_incomes if i["id"] != inc["id"]]
                    st.success("Einnahme gelöscht!")
                    st.rerun()

            # Special Taschengeld Backlog Calculator
            if "taschengeld" in inc["name"].lower():
                st.write("**Kalender: Letzte Auszahlung**")
                last_date_val = date.fromisoformat(inc.get("last_received_date", date.today().isoformat()))
                new_last_date = st.date_input("Zuletzt erhalten am", value=last_date_val, key=f"tg_date_{inc['id']}")
                inc["last_received_date"] = new_last_date.isoformat()
                
                missing_m = calculate_missing_months(new_last_date, date.today())
                backlog_cents = missing_m * inc["amount_cents"]
                
                st.warning(f"⏳ Offener Rückstand: **{missing_m} Monat(e)** = **{cents_to_euro_str(backlog_cents, privacy)}**")
                if missing_m > 0:
                    if st.button("💵 Rückstand jetzt verbuchen", key=f"book_tg_{inc['id']}"):
                        engine.add_transaction(
                            date.today().isoformat(), "Ist", "Einnahme", "Einkommen",
                            f"Taschengeld Rückstand ({missing_m} Monate)", "Konto", backlog_cents
                        )
                        inc["last_received_date"] = date.today().isoformat()
                        inc["received_current_month"] = True
                        st.success("Taschengeld-Rückstand verbucht!")
                        st.rerun()
            st.markdown("---")

    with tab_fix:
        st.subheader("Regelmäßige Fixkosten & Abos")
        
        with st.expander("➕ **Neues Abo / Fixkosten hinzufügen**"):
            with st.form("add_fix_tab_form"):
                f_name = st.text_input("Name (z. B. Netflix, Gym)")
                f_amt = st.number_input("Betrag (€)", min_value=0.5, value=10.0, step=1.0)
                f_day = st.number_input("Abbuchungstag im Monat (1-31)", min_value=1, max_value=31, value=1)
                f_freq = st.selectbox("Rhythmus", ["monatlich", "jährlich"])
                f_ann_m = st.number_input("Abbuchungsmonat bei jährlich (1-12)", min_value=1, max_value=12, value=1)
                if st.form_submit_button("Abo speichern"):
                    if f_name:
                        engine.recurring_expenses.append({
                            "id": str(datetime.now().timestamp()),
                            "name": f_name,
                            "amount_cents": parse_euro_to_cents(f_amt),
                            "frequency": f_freq,
                            "annual_month": f_ann_m,
                            "due_day": int(f_day),
                            "debited_current_month": False
                        })
                        st.success("Abo gespeichert!")
                        st.rerun()

        for exp in engine.recurring_expenses[:]:
            e_col1, e_col2, e_col3, e_col4, e_col5 = st.columns([3, 2, 2, 2, 1])
            with e_col1:
                st.write(f"**{exp['name']}**")
            with e_col2:
                exp["amount_cents"] = parse_euro_to_cents(st.number_input("Betrag (€)", value=float(exp["amount_cents"]/100), key=f"exp_{exp['id']}"))
            with e_col3:
                exp["due_day"] = st.number_input("Abbuchungstag", min_value=1, max_value=31, value=int(exp.get("due_day", 1)), key=f"exp_day_{exp['id']}")
            with e_col4:
                exp["debited_current_month"] = st.checkbox("Im aktuellen Monat abgebucht", value=exp.get("debited_current_month", False), key=f"exp_deb_{exp['id']}")
            with e_col5:
                if st.button("🗑️", key=f"del_exp_{exp['id']}"):
                    engine.recurring_expenses = [e for e in engine.recurring_expenses if e["id"] != exp["id"]]
                    st.success("Abo gelöscht!")
                    st.rerun()

    with tab_events:
        st.subheader("🎉 **Event-Monate & Boni (z. B. Geburtstage, Boni, Weihnachten)**")
        st.caption("Aktiviere bestimmte Monate im Jahr und trage die individuellen Bonus-Beträge in Euro ein.")
        
        cur_y = date.today().year
        for m_idx in range(1, 13):
            m_key = f"{cur_y}-{m_idx:02d}"
            evt = engine.event_months.get(m_key, {"active": False, "description": "", "amount_cents": 10000})
            
            ev_col1, ev_col2, ev_col3 = st.columns([2, 4, 3])
            with ev_col1:
                act = st.checkbox(f"Event im Monat {m_key}", value=evt.get("active", False), key=f"evt_act_{m_key}")
            with ev_col2:
                desc = st.text_input("Beschreibung / Bonus-Grund", value=evt.get("description", ""), key=f"evt_desc_{m_key}")
            with ev_col3:
                amt_val = float(evt.get("amount_cents", 10000) / 100)
                new_amt = st.number_input(f"Bonus-Betrag in € ({m_key})", min_value=0.0, value=amt_val, step=10.0, key=f"evt_amt_{m_key}")
                
            engine.event_months[m_key] = {
                "active": act,
                "description": desc,
                "amount_cents": parse_euro_to_cents(new_amt)
            }

# ==========================================
# 9. PROGNOSE & BERICHTE
# ==========================================
elif selected_page.startswith("9."):
    st.title("📈 Prognose & Export-Berichte")
    st.caption("Konfigurierbare Monatsprognose nach Best, Normal und Worst Case Szenarien sowie Exporte.")

    col_p1, col_p2 = st.columns([2, 2])
    with col_p1:
        fc_months_sel = st.selectbox(
            "Prognosezeitraum (Monate)", [6, 12, 24, 36, 48, 60],
            index=[6, 12, 24, 36, 48, 60].index(engine.settings.get("forecast_months", 36)),
            help="Wähle wie viele Monate in die Zukunft gerechnet werden soll."
        )
        engine.settings["forecast_months"] = fc_months_sel
    with col_p2:
        st.write("")
        st.write("")
        hide_alerts = st.checkbox("🙈 Systemwarnungen ausblenden", value=False)

    fc = engine.calculate_forecast(num_months=fc_months_sel)

    if fc["alerts"] and not hide_alerts:
        st.error("🚨 **Systemwarnungen aus der Prognose:**")
        for alt in fc["alerts"]:
            st.write(f"• {alt}")

    st.markdown("---")

    st.subheader("Szenario-Annahmen")
    fac_cols = st.columns(3)
    fac_cols[0].info("🟢 **Best Case:** Einnahmen × 1.10 | Fixkosten × 0.95 | Var. Budget × 0.90")
    fac_cols[1].info("🔵 **Normal Case:** Planwerte ohne Anpassung (1.00)")
    fac_cols[2].info("🔴 **Worst Case:** Einnahmen × 0.80 | Fixkosten × 1.15 | Var. Budget × 1.15")

    # Prognose Diagramm
    df_fc_rows = []
    for m in fc["months"]:
        m_key = m["month"]
        df_fc_rows.append({"Monat": m_key, "Szenario": "Best Case", "Liquide Mittel (€)": m["best_balance_cents"] / 100})
        df_fc_rows.append({"Monat": m_key, "Szenario": "Normal Case", "Liquide Mittel (€)": m["normal_balance_cents"] / 100})
        df_fc_rows.append({"Monat": m_key, "Szenario": "Worst Case", "Liquide Mittel (€)": m["worst_balance_cents"] / 100})
    
    df_fc = pd.DataFrame(df_fc_rows)
    fig_fc = px.line(
        df_fc, x="Monat", y="Liquide Mittel (€)", color="Szenario",
        title=f"Detaillierter Prognoseverlauf über {fc_months_sel} Monate",
        color_discrete_map={"Best Case": "#4ade80", "Normal Case": "#38bdf8", "Worst Case": "#f87171"}
    )
    fig_fc.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="0 € Grenze")
    fig_fc.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#f8fafc")
    st.plotly_chart(fig_fc, use_container_width=True)

    st.markdown("---")
    st.subheader("📄 Monatsbericht als PDF & Excel exportieren")
    p_col1, p_col2, p_col3 = st.columns(3)
    
    with p_col1:
        rep_m_str = st.date_input("Monat für PDF-Bericht", date.today()).strftime("%Y-%m")
        pdf_bytes = engine.generate_monthly_pdf_report_bytes(rep_m_str)
        if HAS_FPDF:
            st.download_button(
                label="📄 PDF-Monatsbericht herunterladen",
                data=pdf_bytes,
                file_name=f"Finanzbericht_{rep_m_str}.pdf",
                mime="application/pdf"
            )
        else:
            st.info("ℹ️ PDF-Export lokal deaktiviert (fpdf2 Modul fehlt). In der Cloud voll verfügbar.")

    with p_col2:
        st.write("")
        st.write("")
        excel_bytes = engine.export_transactions_to_excel_bytes()
        st.download_button(
            label="📊 Excel-Arbeitsmappe (.xlsx) herunterladen",
            data=excel_bytes,
            file_name="Finanzplaner_Daten.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with p_col3:
        st.write("")
        st.write("")
        csv_bytes = engine.export_transactions_to_csv_bytes()
        st.download_button(
            label="📋 CSV-Datei (.csv) herunterladen",
            data=csv_bytes,
            file_name="Finanzplaner_Buchungen.csv",
            mime="text/csv"
        )

# ==========================================
# 10. WÄHRUNGSRECHNER
# ==========================================
elif selected_page.startswith("10."):
    st.title("💱 Währungsrechner & Urlaubs-Modus")
    st.caption("Umrechnung von Fremdwährungen in Euro für Shopping und Reisen.")

    col_curr1, col_curr2 = st.columns(2)
    with col_curr1:
        f_amt = st.number_input("Betrag in Fremdwährung", min_value=0.01, value=50.0)
        f_curr = st.selectbox("Währung auswählen", list(EXCHANGE_RATES_TO_EUR.keys()), index=1)
    
    eur_cents = convert_to_eur_cents(f_amt, f_curr)
    eur_str = cents_to_euro_str(eur_cents, privacy)

    with col_curr2:
        st.markdown('<div class="apple-card">', unsafe_allow_html=True)
        st.markdown("### Umgerechnet in Euro:")
        st.markdown(f"# **{eur_str}**")
        st.caption(f"Wechselkurs: 1 {f_curr} = {EXCHANGE_RATES_TO_EUR[f_curr]} EUR")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🛒 Direkt als Ausgabe in 'Einmalig' verbuchen"):
        engine.add_transaction(
            date.today().isoformat(), "Ist", "Ausgabe", "Einmalig",
            f"Urlaubskauf ({f_amt} {f_curr})", "Konto", eur_cents
        )
        st.success(f"Ausgabe über {eur_str} verbucht!")
        st.rerun()

# ==========================================
# 11. EINSTELLUNGEN & DATEN
# ==========================================
elif selected_page.startswith("11."):
    st.title("⚙️ Einstellungen & Daten")
    st.caption("Startwerte anpassen (Kontostand, Bargeld, Stichtag), PIN-Code, JSON Backup & Reset.")

    st.subheader("🔑 **Startwerte & Standardwerte anpassen**")
    st.caption("Hier kannst du deine ursprünglichen Kontostände und Parameter festlegen:")
    
    with st.form("settings_start_form"):
        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            cur_acc_euro = float(engine.settings.get("start_account_cents", 150000) / 100)
            new_start_acc = st.number_input("Girokonto Startbestand (€)", min_value=-100000.0, value=cur_acc_euro, step=50.0)
        with s_col2:
            cur_cash_euro = float(engine.settings.get("start_cash_cents", 20000) / 100)
            new_start_cash = st.number_input("Bargeld Startbestand (€)", min_value=0.0, value=cur_cash_euro, step=10.0)
        with s_col3:
            cur_cutoff = engine.settings.get("cutoff_date", date.today().isoformat())
            new_cutoff = st.date_input("Stichtag (Cutoff-Datum)", date.fromisoformat(cur_cutoff))
        
        if st.form_submit_button("Startwerte speichern"):
            engine.settings["start_account_cents"] = parse_euro_to_cents(new_start_acc)
            engine.settings["start_cash_cents"] = parse_euro_to_cents(new_start_cash)
            engine.settings["cutoff_date"] = new_cutoff.isoformat()
            st.success("Startwerte erfolgreich gespeichert!")
            st.rerun()

    st.markdown("---")
    st.subheader("🔒 **PIN-Code Sicherheit**")
    curr_pin = engine.settings.get("pin_code", "")
    new_pin = st.text_input("4-stelligen PIN-Code festlegen (leer lassen für keinen Schutz)", value=curr_pin, type="password")
    if st.button("PIN speichern"):
        engine.settings["pin_code"] = new_pin
        st.success("PIN-Einstellung gespeichert!")
        st.rerun()

    st.markdown("---")
    st.subheader("💾 **JSON Backup Export & Import**")
    json_str = json.dumps(engine.to_dict(), indent=2)
    st.download_button("💾 JSON-Sicherung herunterladen", data=json_str, file_name="finanzplanung_v8_backup.json", mime="application/json")

    st.markdown("---")
    uploaded_file = st.file_uploader("Daten aus JSON-Sicherungsdatei wiederherstellen", type=["json"])
    if uploaded_file is not None:
        if st.button("Import von JSON jetzt durchführen"):
            try:
                data = json.load(uploaded_file)
                engine.load_from_dict(data)
                st.success("Daten erfolgreich importiert!")
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Importieren der Datei: {e}")

    st.markdown("---")
    st.subheader("⚠️ **System zurücksetzen**")
    if st.button("⚠️ Alle Daten auf Standardwerte zurücksetzen"):
        engine.reset_to_defaults()
        st.warning("App wurde auf Werkszustand zurückgesetzt.")
        st.rerun()
