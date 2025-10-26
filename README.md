# smart-lead-prioritization-and-insights-tool
Build a lightweight web-based tool that takes a list of business leads and automatically scores, enriches, and ranks them based on how valuable they are for sales outreach.
A sales team often gets hundreds of raw leads from scraping tools like SaaSQuatchLeads — but not all are useful.
This project filters and scores the leads to highlight the most promising ones, giving the sales team:

Lead quality scores

Company insights

Recommended next steps



---

🧠 Core Features

Feature	Description	Purpose

Lead Upload	Upload a CSV or paste scraped leads	Input
Data Enrichment	Adds missing data (industry, size, domain, etc.) using APIs or mock data	Makes leads more informative
AI Scoring System	Gives each lead a score (0–100) based on match with target customer	Prioritizes high-value leads
Insights Generator	Adds notes like “Hiring fast” or “Recently funded”	Gives context for outreach
Dashboard + Export	View ranked list and export as CSV	Easy for sales use



---

⚙ Technical Stack

Component	Suggested Tools

Frontend/UI	Streamlit (fast & simple Python UI)
Backend/Logic	Python (Pandas, Scikit-learn, Regex)
Data Enrichment	Mock data + optional Clearbit/Crunchbase API
Output	Downloadable CSV or Excel



---

🧩 How It Works (Workflow)

1. User uploads a leads CSV file.


2. Script extracts domains (like example.com).


3. Fetches or simulates company data:

        Industry, size, country, hiring keywords, tech stack.



4. Calculates Lead Score using weighted formula:

        score = 0.3 * industry_match + 0.25 * growth_signal + 
        0.2 * tech_fit + 0.15 * region_match + 
        0.1 * contact_info


5. Displays sorted leads with tags:

           🔥 Hot (score > 80)

           🌡 Warm (50–80)

            ❄ Cold (<50)



6. Generates short insights for top leads:

        “Recently expanded operations”

        “Uses competitor’s tech — switch potential”
