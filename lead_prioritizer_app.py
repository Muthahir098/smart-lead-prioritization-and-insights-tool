# lead_prioritizer_app.py
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Smart Lead Prioritizer", layout="wide")

st.title("🚀 Smart Lead Prioritization & Insights Tool")
st.markdown(
    "Upload a leads CSV and get scored, enriched, and prioritized leads for sales outreach. "
    "Columns expected (minimum): company, website, industry, employees, region, hiring, funding_stage, tech_stack, email_present, linkedin."
)

# --- Sidebar: ICP & weights ---
st.sidebar.header("Settings — ICP & Weights")
default_icp = ["SaaS", "Fintech", "HealthTech", "AI", "EdTech"]
icp_input = st.sidebar.text_area("Target industries (comma-separated)", value=",".join(default_icp))
TARGET_INDUSTRIES = [i.strip() for i in icp_input.split(",") if i.strip()]

preferred_regions_input = st.sidebar.text_input("Preferred regions (comma-separated)", value="US,EU")
PREFERRED_REGIONS = [r.strip() for r in preferred_regions_input.split(",") if r.strip()]

st.sidebar.markdown("*Weights (total not required to sum — normalized implicitly)*")
w_industry = st.sidebar.slider("Industry match weight", 0.0, 1.0, 0.30, 0.05)
w_growth = st.sidebar.slider("Growth signals (hiring/funding) weight", 0.0, 1.0, 0.25, 0.05)
w_tech = st.sidebar.slider("Tech fit weight", 0.0, 1.0, 0.20, 0.05)
w_region = st.sidebar.slider("Region priority weight", 0.0, 1.0, 0.10, 0.05)
w_contact = st.sidebar.slider("Contact availability weight", 0.0, 1.0, 0.15, 0.05)

# Normalize to a 0-100 scale by dividing by sum_of_maxes later in the scoring functions

# --- Helper functions (same logic as demo but parameterized) ---
def industry_score(industry):
    if pd.isna(industry) or str(industry).strip() == "":
        return 0
    return 1.0 if industry in TARGET_INDUSTRIES else 0.33  # full or partial match

def growth_signal_score(row):
    score = 0.0
    if str(row.get("hiring", False)).strip().lower() in ["true", "yes", "1"]:
        score += 1.0
    funding = str(row.get("funding_stage", "")).strip().lower()
    if funding:
        # rough ordinal mapping
        if "seed" in funding:
            score += 0.5
        elif "series a" in funding:
            score += 0.8
        elif "series b" in funding:
            score += 1.0
        elif "series c" in funding or "series d" in funding:
            score += 1.2
    return min(score, 2.0)  # cap

def tech_fit_score(tech_stack):
    if pd.isna(tech_stack) or str(tech_stack).strip() == "":
        return 0.0
    techs = [t.strip().lower() for t in str(tech_stack).split(";") if t.strip()]
    score = 0.0
    if any(t in techs for t in ["aws", "gcp", "azure", "kubernetes", "docker"]):
        score += 1.0
    if any(t in techs for t in ["python", "java", "nodejs", "react", "tensorflow", "pytorch"]):
        score += 0.8
    if any(t in techs for t in ["salesforce", "oracle", "sap"]):
        score += 0.2
    return min(score, 2.0)

def region_score(region):
    if pd.isna(region) or str(region).strip() == "":
        return 0.0
    return 1.0 if region in PREFERRED_REGIONS else 0.3

def contact_info_score(email_present):
    return 1.0 if str(email_present).strip().lower() in ["yes","y","true","1"] else 0.0

def compute_score_row(row):
    # compute sub-scores in their natural small ranges then scale by weights and a normalization factor
    i_s = industry_score(row.get("industry", ""))
    g_s = growth_signal_score(row)
    t_s = tech_fit_score(row.get("tech_stack", ""))
    r_s = region_score(row.get("region", ""))
    c_s = contact_info_score(row.get("email_present", ""))

    # maximum possible raw score given our sub-score caps:
    # industry max = 1.0, growth max = 2.0, tech max = 2.0, region max = 1.0, contact max = 1.0
    max_raw = 1.0 * 1 + 2.0 * 1 + 2.0 * 1 + 1.0 * 1 + 1.0 * 1  # =7.0
    raw = (i_s * w_industry) + (g_s * w_growth) + (t_s * w_tech) + (r_s * w_region) + (c_s * w_contact)

    # To map to 0-100: divide by max_possible_weighted_raw then *100
    # compute max_possible_weighted_raw given weights and sub-score caps
    max_possible_weighted_raw = (1.0 * w_industry) + (2.0 * w_growth) + (2.0 * w_tech) + (1.0 * w_region) + (1.0 * w_contact)
    score_pct = (raw / max_possible_weighted_raw) * 100 if max_possible_weighted_raw > 0 else 0
    return int(round(max(0, min(100, score_pct))))

def generate_insight(row):
    insights = []
    funding = str(row.get('funding_stage', "")).strip()
    if funding:
        insights.append(f"Funding: {funding}")
    if str(row.get('hiring', False)).strip().lower() in ["true","yes","1"]:
        insights.append("Active hiring")
    techs = [t.strip().lower() for t in str(row.get('tech_stack', "")).split(";") if t.strip()]
    if any("aws" in t for t in techs):
        insights.append("Cloud-based (AWS)")
    if any(t in techs for t in ["tensorflow","pytorch","ai","tensor"]):
        insights.append("AI/ML capabilities")
    employees = row.get('employees', None)
    try:
        if employees and int(employees) >= 200:
            insights.append("Enterprise-sized (>=200 employees)")
    except Exception:
        pass
    if str(row.get('email_present', "")).strip().lower() not in ["yes","y","true","1"]:
        insights.append("No public email — harder to reach")
    return " | ".join(insights) if insights else "No strong signals"

# --- File upload / sample data loader ---
uploaded_file = st.file_uploader("Upload leads CSV", type=["csv"])
use_sample = st.checkbox("Use sample dataset (provided)", value=True if uploaded_file is None else False)

if use_sample and uploaded_file is None:
    # small built-in sample dataset
    sample_data = [
        {"company":"DataZoom","website":"datazoom.com","industry":"SaaS","employees":120,"region":"US","hiring":True,"funding_stage":"Series A","tech_stack":"Python;AWS;Postgres","email_present":"yes","linkedin":"https://www.linkedin.com/company/datazoom"},
        {"company":"AgroMart","website":"agromart.in","industry":"Retail","employees":18,"region":"IN","hiring":False,"funding_stage":"","tech_stack":"PHP;MySQL","email_present":"no","linkedin":""},
        {"company":"FinServe","website":"finserve.io","industry":"Fintech","employees":250,"region":"UK","hiring":True,"funding_stage":"Series B","tech_stack":"Java;AWS;Kafka","email_present":"yes","linkedin":"https://www.linkedin.com/company/finserve"},
        {"company":"EduSpark","website":"eduspark.edu","industry":"EdTech","employees":40,"region":"US","hiring":True,"funding_stage":"","tech_stack":"Python;GCP","email_present":"yes","linkedin":"https://www.linkedin.com/company/eduspark"},
        {"company":"MarketGaze","website":"marketgaze.io","industry":"SaaS","employees":85,"region":"US","hiring":True,"funding_stage":"Series A","tech_stack":"Python;React;AWS","email_present":"yes","linkedin":"https://www.linkedin.com/company/marketgaze"}
    ]
    df = pd.DataFrame(sample_data)
else:
    if uploaded_file is None:
        st.info("Please upload a CSV or choose the sample dataset.")
        st.stop()
    df = pd.read_csv(uploaded_file)

# Ensure consistent column names (lower-case)
df.columns = [c.strip() for c in df.columns]
# Compute scores
df['Score'] = df.apply(compute_score_row, axis=1)
df['Category'] = pd.cut(df['Score'], bins=[-1,49,79,100], labels=['Cold','Warm','Hot'])
df['Insight'] = df.apply(generate_insight, axis=1)

# --- Main display ---
st.subheader("Scored & Enriched Leads")
col1, col2 = st.columns([3,1])
with col2:
    st.metric("Total leads", len(df))
    st.metric("Hot", int((df['Category']=='Hot').sum()), delta=None)
    st.metric("Warm", int((df['Category']=='Warm').sum()), delta=None)
    st.metric("Cold", int((df['Category']=='Cold').sum()), delta=None)

# Filters
filter_cols = st.multiselect("Columns to show (extras will be visible in table)", list(df.columns), default=['company','website','industry','employees','region','Score','Category','Insight'])
category_filter = st.multiselect("Filter by category", options=['Hot','Warm','Cold'], default=['Hot','Warm','Cold'])

df_display = df[df['Category'].isin(category_filter)].sort_values(by='Score', ascending=False).reset_index(drop=True)
st.dataframe(df_display[filter_cols], use_container_width=True)

# Quick outreach suggestion for selected lead
st.subheader("Quick Outreach Helper")
selected_idx = st.number_input("Select row index (as shown in table) to generate a short outreach line", min_value=0, max_value=max(0,len(df_display)-1), value=0, step=1)
if len(df_display)>0:
    lead = df_display.iloc[selected_idx]
    # template-based outreach (no external LLM)
    template = (
        "Hi {name},\n\n"
        "Noticed {company} is {insight_short}. We help {industry_lower} teams scale with faster onboarding and lower operational cost. "
        "Would you be open to a short 15-min call next week to explore if this is relevant?\n\nThanks,\n[Your name]"
    )
    insight_short = lead['Insight'].split("|")[0].strip() if lead['Insight'] else ""
    outreach = template.format(
        name=lead.get('company', 'there'),
        company=lead.get('company', ''),
        insight_short=insight_short or "showing growth signals",
        industry_lower=str(lead.get('industry','')).lower()
    )
    st.code(outreach)

# Export scored CSV
st.subheader("Export")
buf = BytesIO()
df_sorted = df.sort_values(by='Score', ascending=False).reset_index(drop=True)
df_sorted.to_csv(buf, index=False)
buf.seek(0)
st.download_button("Download scored leads (CSV)", data=buf, file_name="sales_ready_leads.csv", mime="text/csv")

st.markdown("---")
st.caption("Tip: Swap the sample dataset with your scraped CSV (ensure columns roughly match). To enrich further, integrate Clearbit/Crunchbase/BuiltWith APIs where noted.")
