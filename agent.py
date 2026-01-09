import streamlit as st
import json
import time
import requests
import os
from datetime import datetime

# Try importing FPDF for PDF generation (Optional)
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- CONFIGURATION ---
ST_PAGE_TITLE = "GenAI SOW Architect"
ST_PAGE_ICON = "📄"
# GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025" 
# Note: Use a standard stable model name if the preview model is unavailable in your region.
GEMINI_MODEL = "gemini-2.0-flash-exp" 

# --- CONSTANTS & DROPDOWNS ---
SOLUTION_TYPES = [
    "Multi Agent Store Advisor", "Intelligent Search", "Recommendation", 
    "AI Agents Demand Forecasting", "Banner Audit using LLM", "Image Enhancement", 
    "Virtual Try-On", "Agentic AI L1 Support", "Product Listing Standardization", 
    "AI Agents Based Pricing Module", "Cost, Margin Visibility & Insights using LLM", 
    "AI Trend Simulator", "Virtual Data Analyst (Text to SQL)", "Multilingual Call Analysis", 
    "Customer Review Analysis", "Sales Co-Pilot", "Research Co-Pilot", 
    "Product Copy Generator", "Multi-agent e-KYC & Onboarding", "Document / Report Audit", 
    "RBI Circular Scraping & Insights Bot", "Visual Inspection", "AIoT based CCTV Surveillance", 
    "Multilingual Voice Bot", "SOP Creation", "Other"
]

INDUSTRIES = [
    "Retail / E-commerce", "BFSI", "Manufacturing", "Telecom", "Healthcare", 
    "Energy / Utilities", "Logistics", "Media", "Government", "Other"
]

ENGAGEMENT_TYPES = ["Proof of Concept (PoC)", "Pilot", "MVP", "Production Rollout", "Assessment / Discovery"]

# --- PDF CLASS ---
if FPDF:
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Statement of Work (SOW)', 0, 1, 'C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

        def chapter_title(self, title):
            self.set_font('Arial', 'B', 12)
            self.set_fill_color(230, 230, 230)
            self.cell(0, 10, title, 0, 1, 'L', 1)
            self.ln(4)
else:
    class PDF: pass

def clean_text_pdf(text):
    """Helper for PDF encoding."""
    if not isinstance(text, str): return str(text)
    replacements = {'\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"', '●': '-', '•': '-'}
    for k, v in replacements.items(): text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

# --- API UTILITIES ---
def clean_json_string(text):
    """Removes markdown formatting from JSON strings."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def call_gemini_json(prompt, schema, system_instruction="You are a professional solution architect.", api_key=None):
    """Calls Gemini with a structured JSON output requirement."""
    if not api_key:
        return None
        
    # --- URL FIX ---
    # Strictly cleaned URL string to prevent connection adapters error
    url = f"[https://generativelanguage.googleapis.com/v1beta/models/](https://generativelanguage.googleapis.com/v1beta/models/){GEMINI_MODEL}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    for i in range(3): # Reduced retries for faster feedback
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                try:
                    text_content = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "{}")
                    cleaned_text = clean_json_string(text_content)
                    return json.loads(cleaned_text)
                except (IndexError, json.JSONDecodeError):
                    # Fallback if structure is unexpected
                    return None
            else:
                # Log error for debugging if needed (but keep UI clean)
                print(f"API Error {response.status_code}: {response.text}")
                time.sleep(1)
        except Exception as e:
            time.sleep(1)
            
    return None

# --- PAGE SETUP ---
st.set_page_config(page_title=ST_PAGE_TITLE, page_icon=ST_PAGE_ICON, layout="wide")

# --- SESSION STATE INITIALIZATION ---
if "autofill_data" not in st.session_state:
    st.session_state.autofill_data = {}
if "autofill_done" not in st.session_state:
    st.session_state.autofill_done = False

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_input = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API Key here.")
    
    # Check environment variable if input is empty
    # Checks for both GEMINI_API_KEY and GOOGLE_API_KEY
    if not api_key_input:
        api_key_input = os.environ.get("GEMINI_API_KEY", "")
    if not api_key_input:
        api_key_input = os.environ.get("GOOGLE_API_KEY", "")
    
    if not api_key_input:
        st.warning("⚠️ Please enter an API Key to generate content.")
        st.markdown("[Get a Gemini API Key](https://aistudio.google.com/app/apikey)")
    else:
        st.success("API Key detected.")

st.title(f"{ST_PAGE_ICON} {ST_PAGE_TITLE}")
st.markdown("Create end-to-end professional SOWs tailored to specific AWS GenAI solutions.")

# --- TABS ---
tabs = st.tabs([
    "1. High-Level Context", 
    "2. Project Overview", 
    "3. Details & Success Criteria", 
    "4. Architecture", 
    "5. Timeline & Costs",
    "6. Review & Export"
])

# --- TAB 1: CONTEXT ---
with tabs[0]:
    col1, col2 = st.columns(2)
    with col1:
        sol_type_select = st.selectbox("1.1 Solution Type", SOLUTION_TYPES)
        sol_type = st.text_input("Specify Solution Type", value="") if sol_type_select == "Other" else sol_type_select
            
        engagement = st.selectbox("1.2 Engagement Type", ENGAGEMENT_TYPES)
        
    with col2:
        industry_select = st.selectbox("1.3 Industry / Domain", INDUSTRIES)
        industry = st.text_input("Specify Industry", value="") if industry_select == "Other" else industry_select
            
        customer_name = st.text_input("Customer Name", "Acme Global")

    st.divider()
    
    if st.button("✨ GENERATE COMPLETE SOW DRAFT (SECTION-BY-SECTION)", use_container_width=True, type="primary"):
        if not api_key_input:
            st.error("Please provide a Gemini API Key in the sidebar to proceed.")
        else:
            # We initialize with existing data to allow partial updates without wiping everything
            generated_sow = st.session_state.autofill_data.copy()
            sys_instruct = f"You are a specialized Solution Architect for the {industry} industry. Writing SOW for '{sol_type}'."
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 1. Objective
                status_text.text(f"1/6 Generating Specific Objective for {sol_type}...")
                obj_schema = {"type": "OBJECT", "properties": {"objective": {"type": "STRING"}}}
                res = call_gemini_json(f"Generate a concise, 1-2 sentence formal business objective specifically for a '{sol_type}' solution. Focus on accuracy, automation, speed. Do not use generic goals.", obj_schema, sys_instruct, api_key_input)
                if res: 
                    generated_sow.update(res)
                    st.session_state.autofill_data = generated_sow # Save progress immediately
                progress_bar.progress(20)

                # 2. Stakeholders
                status_text.text("2/6 Generating Stakeholder information...")
                # Removed 'Role' from schema
                stk_schema = {
                    "type": "OBJECT", "properties": {
                        "stakeholders": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "title": {"type": "STRING"}, "email": {"type": "STRING"}}}}
                    }
                }
                prompt_stakeholders = f"""Generate project stakeholders for {sol_type} at {customer_name}. 
                Required Contacts:
                1. Partner Executive Sponsor: Name "Partner Exec", Title "Head of Analytics & ML".
                2. Customer Executive Sponsor: Realistic name/title.
                3. AWS Executive Sponsor: Realistic name, Title "AWS Account Executive".
                4. Project Escalation Contacts: Generate TWO distinct people."""
                res = call_gemini_json(prompt_stakeholders, stk_schema, sys_instruct, api_key_input)
                if res: 
                    generated_sow.update(res)
                    st.session_state.autofill_data = generated_sow # Save progress immediately
                progress_bar.progress(40)

                # 3. Dependencies
                status_text.text(f"3/6 Generating Dependencies...")
                deps_schema = {
                     "type": "OBJECT", "properties": {
                          "dependencies": {"type": "ARRAY", "items": {"type": "STRING"}},
                          "assumptions": {"type": "ARRAY", "items": {"type": "STRING"}}
                     }
                }
                res = call_gemini_json(f"List 6 Assumptions and 6 Dependencies SPECIFIC to a '{sol_type}' project.", deps_schema, sys_instruct, api_key_input)
                if res: 
                    generated_sow.update(res)
                    st.session_state.autofill_data = generated_sow # Save progress immediately
                progress_bar.progress(60)

                # 4. Success Criteria
                status_text.text("4/6 Defining Success Criteria...")
                success_schema = {
                    "type": "OBJECT", "properties": {
                        "success_criteria": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"heading": {"type": "STRING"}, "points": {"type": "ARRAY", "items": {"type": "STRING"}}}}}
                    }
                }
                res = call_gemini_json(f"Generate detailed PoC Success Criteria for '{sol_type}'. Sections: Demonstrations, Results, Usability.", success_schema, sys_instruct, api_key_input)
                if res: 
                    generated_sow.update(res)
                    st.session_state.autofill_data = generated_sow # Save progress immediately
                progress_bar.progress(80)

                # Skipped Technical Scope generation as per request (handled in Timeline)

                # 5. Architecture
                status_text.text("5/6 Selecting AWS Services...")
                arch_schema = {
                    "type": "OBJECT", "properties": {
                        "architecture": {"type": "OBJECT", "properties": {
                            "compute": {"type": "STRING"}, "storage": {"type": "STRING"}, "ml_services": {"type": "STRING"}, "ui": {"type": "STRING"}
                        }}
                    }
                }
                res = call_gemini_json(f"Design AWS architecture for '{sol_type}'. Suggest text for Compute, Storage, ML Services, UI.", arch_schema, sys_instruct, api_key_input)
                if res: 
                    generated_sow.update(res)
                    st.session_state.autofill_data = generated_sow # Save progress immediately
                progress_bar.progress(90)

                # 6. Timeline
                status_text.text("6/6 Finalizing Timeline...")
                time_schema = {
                    "type": "OBJECT", "properties": {
                        "timeline": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"phase": {"type": "STRING"}, "task": {"type": "STRING"}, "weeks": {"type": "STRING"}}}},
                        "usage_users": {"type": "NUMBER"}, "usage_requests": {"type": "NUMBER"}
                    }
                }
                res = call_gemini_json(f"Create high-level timeline for '{sol_type}'. Include Phase, Task, Weeks.", time_schema, sys_instruct, api_key_input)
                if res: 
                    generated_sow.update(res)
                    st.session_state.autofill_data = generated_sow # Save progress immediately
                progress_bar.progress(100)
                
                st.session_state.autofill_done = True
                status_text.success("Complete SOW Draft Generated Successfully!")
                st.toast("Check Tab 6 for the Final Report.")

            except Exception as e:
                st.error(f"Error during generation: {str(e)}")
                status_text.text("Generation paused.")

# --- UI LOGIC ---
data = st.session_state.autofill_data

# --- TAB 2: OVERVIEW ---
with tabs[1]:
    st.header("2. PROJECT OVERVIEW")
    st.subheader("2.1 OBJECTIVE")
    default_obj = data.get("objective", "Click 'Generate' in Tab 1 to populate this objective.")
    final_objective = st.text_area("Edit Objective", value=default_obj, height=100)
    data["objective"] = final_objective

    st.subheader("2.2 STAKEHOLDERS")
    # Default without Role
    default_stakeholders = [{"name": "", "title": "", "email": ""}]
    current_stakeholders = data.get("stakeholders", default_stakeholders)
    
    updated_stakeholders = []
    # Removed Role Input
    for i, s in enumerate(current_stakeholders):
        c1, c2, c3 = st.columns([1.5, 1.5, 2])
        n = c1.text_input("Name", s.get('name', ''), key=f"s_n_{i}")
        t = c2.text_input("Title", s.get('title', ''), key=f"s_t_{i}")
        e = c3.text_input("Contact/Email", s.get('email', ''), key=f"s_e_{i}")
        updated_stakeholders.append({"name": n, "title": t, "email": e})
    
    if st.button("+ Add Stakeholder"):
        updated_stakeholders.append({"name": "", "title": "", "email": ""})
        data["stakeholders"] = updated_stakeholders
        st.rerun()
    data["stakeholders"] = updated_stakeholders

# --- TAB 3: DETAILS ---
with tabs[2]:
    # Renamed Tab, Removed 'Scope of Work - Technical Project Plan' section
    st.header("2.3 ASSUMPTIONS & DEPENDENCIES")
    col_d, col_a = st.columns(2)
    with col_d:
        st.subheader("Dependencies")
        deps_list = data.get("dependencies", [])
        deps_val = "\n".join(deps_list) if isinstance(deps_list, list) else str(deps_list)
        deps_text = st.text_area("One per line", value=deps_val, height=200, key="deps")
    with col_a:
        st.subheader("Assumptions")
        assump_list = data.get("assumptions", [])
        assump_val = "\n".join(assump_list) if isinstance(assump_list, list) else str(assump_list)
        assump_text = st.text_area("One per line", value=assump_val, height=200, key="assump")

    st.divider()
    st.header("2.4 PoC SUCCESS CRITERIA")
    sc_data = data.get("success_criteria", [])
    sc_text_build = ""
    for item in sc_data:
        sc_text_build += f"**{item.get('heading', '')}**\n" + "\n".join([f"- {p}" for p in item.get('points', [])]) + "\n\n"
    final_sc_text = st.text_area("Edit Success Criteria", value=sc_text_build, height=300)

# --- TAB 4: ARCHITECTURE ---
with tabs[3]:
    st.header("4 SOLUTION ARCHITECTURE")
    st.info("Edit the architecture components below.")
    arch = data.get("architecture", {})
    
    compute = st.text_input("Compute", value=arch.get("compute", "AWS Lambda, Step Functions"))
    storage = st.text_input("Storage", value=arch.get("storage", "Amazon S3, DynamoDB"))
    ml_services = st.text_input("ML Services", value=arch.get("ml_services", "Amazon Bedrock"))
    ui_layer = st.text_input("UI Layer", value=arch.get("ui", "Streamlit on S3"))

# --- TAB 5: TIMELINE ---
with tabs[4]:
    st.header("Development Timelines")
    st.caption("This section serves as the main Technical Project Plan.")
    raw_timeline = data.get("timeline", [{"phase": "Setup", "task": "Init", "weeks": "Wk1"}])
    
    final_timeline = []
    for i, step in enumerate(raw_timeline):
        c1, c2, c3 = st.columns([1, 3, 1])
        p = c1.text_input("Phase", step.get("phase", ""), key=f"t_p_{i}")
        t = c2.text_input("Task", step.get("task", ""), key=f"t_t_{i}")
        w = c3.text_input("Weeks", step.get("weeks", ""), key=f"t_w_{i}")
        final_timeline.append({"Phase": p, "Task": t, "Weeks": w})
    
    if st.button("+ Add Timeline Phase"):
        final_timeline.append({"Phase": "New Phase", "Task": "", "Weeks": ""})
        data["timeline"] = final_timeline
        st.rerun()
    data["timeline"] = final_timeline

    st.divider()
    st.header("5 RESOURCES & COST ESTIMATES")
    c1, c2, c3 = st.columns(3)
    n_users = c1.number_input("Est. Daily Users", value=int(data.get("usage_users", 100)))
    n_reqs = c2.number_input("Requests/User/Day", value=int(data.get("usage_requests", 5)))
    ownership = c3.selectbox("Cost Ownership", ["Funded by AWS", "Funded by Partner", "Funded by Customer", "Shared"])

# --- TAB 6: EXPORT ---
with tabs[5]:
    st.header("Final SOW Export")
    
    # 1. GENERATE WORD DOC (HTML-based)
    html_content = f"""
    <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='[http://www.w3.org/TR/REC-html40](http://www.w3.org/TR/REC-html40)'>
    <head><title>Statement of Work</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; line-height: 1.6; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #000; padding: 10px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        h1 {{ font-size: 24pt; color: #232f3e; border-bottom: 2px solid #232f3e; padding-bottom: 10px; }}
        h2 {{ font-size: 18pt; color: #232f3e; margin-top: 30px; }}
        h3 {{ font-size: 14pt; color: #444; margin-top: 20px; }}
        ul {{ margin-bottom: 15px; }}
        li {{ margin-bottom: 5px; }}
    </style>
    </head>
    <body>
    
    <h1>Statement of Work: {sol_type}</h1>
    <p><strong>Customer:</strong> {customer_name}</p>
    <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
    <hr>
    
    <h2>1. PROJECT OVERVIEW</h2>
    <h3>1.1 OBJECTIVE</h3>
    <p>{final_objective}</p>
    
    <h3>1.2 STAKEHOLDERS</h3>
    <table>
        <tr><th>Name</th><th>Title</th><th>Contact/Email</th></tr>
        {"".join([f"<tr><td>{s['name']}</td><td>{s['title']}</td><td>{s['email']}</td></tr>" for s in updated_stakeholders])}
    </table>
    
    <h3>1.3 ASSUMPTIONS & DEPENDENCIES</h3>
    <table style="border: none;">
    <tr>
    <td style="border: none; vertical-align: top; width: 50%;">
        <h4>Dependencies</h4>
        <ul>{"".join([f"<li>{d}</li>" for d in deps_text.splitlines() if d.strip()])}</ul>
    </td>
    <td style="border: none; vertical-align: top; width: 50%;">
        <h4>Assumptions</h4>
        <ul>{"".join([f"<li>{a}</li>" for a in assump_text.splitlines() if a.strip()])}</ul>
    </td>
    </tr>
    </table>
    
    <h3>1.4 PoC SUCCESS CRITERIA</h3>
    <div style="white-space: pre-wrap;">{final_sc_text.replace(chr(10), '<br>')}</div>
    
    <h2>2. SCOPE OF WORK & TIMELINES</h2>
    
    <h3>Development Timelines</h3>
    <table>
        <tr><th>Phase</th><th>Task</th><th>Weeks</th></tr>
        {"".join([f"<tr><td>{t['Phase']}</td><td>{t['Task']}</td><td>{t['Weeks']}</td></tr>" for t in final_timeline])}
    </table>
    
    <h2>3. ARCHITECTURE</h2>
    <ul>
        <li><strong>Compute:</strong> {compute}</li>
        <li><strong>Storage:</strong> {storage}</li>
        <li><strong>ML Services:</strong> {ml_services}</li>
        <li><strong>UI Layer:</strong> {ui_layer}</li>
    </ul>
    
    <h2>4. RESOURCES</h2>
    <p><strong>Ownership:</strong> {ownership}</p>
    <p><strong>Estimates:</strong> {n_users} users, {n_reqs} requests/day</p>
    
    </body></html>
    """
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            label="📥 Download as Word Doc",
            data=html_content,
            file_name=f"{customer_name.replace(' ', '_')}_SOW.doc",
            mime="application/msword",
            use_container_width=True,
            type="primary"
        )
        st.caption("ℹ️ This downloads a .doc file. If Word shows a warning, click 'Yes' to open it.")

    with col_d2:
        # 2. GENERATE PDF (If FPDF available)
        if FPDF:
            def create_pdf():
                pdf = PDF()
                pdf.add_page()
                pdf.chapter_title("1. PROJECT OVERVIEW")
                
                pdf.set_font('Arial', 'B', 11); pdf.cell(0, 8, "1.1 OBJECTIVE", 0, 1)
                pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 5, clean_text_pdf(final_objective)); pdf.ln(5)
                
                pdf.set_font('Arial', 'B', 11); pdf.cell(0, 8, "1.2 STAKEHOLDERS", 0, 1)
                pdf.set_font('Arial', 'B', 9)
                # Adjusted columns for 3 fields
                col_w = [60, 60, 60]
                pdf.cell(col_w[0], 7, "Name", 1); pdf.cell(col_w[1], 7, "Title", 1); pdf.cell(col_w[2], 7, "Contact/Email", 1, 1)
                pdf.set_font('Arial', '', 9)
                for s in updated_stakeholders:
                    pdf.cell(col_w[0], 7, clean_text_pdf(s['name'][:35]), 1)
                    pdf.cell(col_w[1], 7, clean_text_pdf(s['title'][:35]), 1)
                    pdf.cell(col_w[2], 7, clean_text_pdf(s['email'][:35]), 1, 1)
                pdf.ln(5)
                
                pdf.chapter_title("2. SCOPE OF WORK")
                # Removed detailed phase text blocks, relying on timeline logic if needed, 
                # but for PDF simplistic export, let's just show Architecture and Timeline
                
                pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, "2.1 ARCHITECTURE", 0, 1)
                pdf.set_font('Arial', '', 10)
                pdf.multi_cell(0, 5, clean_text_pdf(f"Compute: {compute}\nStorage: {storage}\nML: {ml_services}\nUI: {ui_layer}"))
                pdf.ln(5)

                pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, "2.2 TIMELINES", 0, 1)
                pdf.set_font('Arial', 'B', 9)
                t_cols = [30, 130, 20]
                pdf.cell(t_cols[0], 7, "Phase", 1); pdf.cell(t_cols[1], 7, "Task", 1); pdf.cell(t_cols[2], 7, "Wks", 1, 1)
                pdf.set_font('Arial', '', 9)
                for t in final_timeline:
                    pdf.cell(t_cols[0], 7, clean_text_pdf(t['Phase'][:15]), 1)
                    pdf.cell(t_cols[1], 7, clean_text_pdf(t['Task'][:70]), 1)
                    pdf.cell(t_cols[2], 7, clean_text_pdf(t['Weeks'][:5]), 1, 1)
                
                return pdf.output(dest='S').encode('latin-1')

            try:
                pdf_data = create_pdf()
                st.download_button(
                    label="📥 Download as PDF",
                    data=pdf_data,
                    file_name=f"{customer_name.replace(' ', '_')}_SOW.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF Gen Error: {e}")
        else:
            st.warning("PDF export unavailable (requires fpdf).")