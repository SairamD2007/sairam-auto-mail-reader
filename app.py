import streamlit as st
import base64
import requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import google.generativeai as genai
from urllib.parse import urlencode

# --- INITIAL APP SETUP WITH LIGHT REFINED THEME ---
st.set_page_config(page_title="Sairam's Auto Mail Reader", page_icon="⚡", layout="wide")

# Refined Light Premium CSS Workspace Aesthetics 
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #f3f4f6;
            color: #1f2937;
        }
        
        /* Centered Header Layout Customizations */
        .centered-container {
            text-align: center;
            padding: 35px 20px;
            margin: 0 auto;
            max-width: 800px;
        }
        
        .main-title {
            font-weight: 800;
            font-size: 2.85rem;
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -1px;
            margin-bottom: 10px;
        }
        
        .sub-title {
            font-size: 1.1rem;
            color: #4b5563;
            font-weight: 400;
            margin-bottom: 20px;
        }

        /* Authentic Identity Provider Button States */
        .google-sign-in-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background-color: #ffffff;
            color: #374151;
            font-size: 16px;
            font-weight: 600;
            font-family: 'Plus Jakarta Sans', sans-serif;
            padding: 12px 24px;
            border-radius: 8px;
            border: 1px solid #d1d5db;
            text-decoration: none;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .google-sign-in-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
        }
        .google-sign-in-btn img {
            width: 22px;
            height: 22px;
            margin-right: 12px;
        }

        /* Crisp Light Container Info Cards */
        .profile-container {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            padding: 16px 24px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            margin-bottom: 25px;
        }
        .profile-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .profile-avatar {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            border: 2px solid #3b82f6;
            background-color: #f3f4f6;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .profile-details h4 {
            margin: 0;
            font-size: 1.05rem;
            font-weight: 600;
            color: #111827;
        }
        .profile-details p {
            margin: 0;
            font-size: 0.88rem;
            color: #6b7280;
        }

        /* Bright Responsive Feed Workspace Elements */
        .workspace-card {
            background: #ffffff;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
        
        .email-feed-card {
            background: #ffffff;
            padding: 16px;
            border-radius: 8px;
            border-left: 4px solid #2563eb;
            border-top: 1px solid #e5e7eb;
            border-right: 1px solid #e5e7eb;
            border-bottom: 1px solid #e5e7eb;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
            margin-bottom: 12px;
        }

        /* Streamlit Element Overrides */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            color: white !important;
            border: none !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            padding: 0.65rem 2rem !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        }
        
        input {
            background-color: #ffffff !important;
            color: #1f2937 !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
        }
    </style>
""", unsafe_allow_html=True)

SCOPES = "https://www.googleapis.com/auth/gmail.readonly"
REDIRECT_URI = "https://sairam-mail-reader.streamlit.app/"

# --- CAPTURE GOOGLE REDIRECT TOKENS ---
query_params = st.query_params

if "code" in query_params and "credentials" not in st.session_state:
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": query_params["code"],
        "client_id": st.secrets["google"]["client_id"],
        "client_secret": st.secrets["google"]["client_secret"],
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    response = requests.post(token_url, data=payload)
    token_data = response.json()
    
    if "access_token" in token_data:
        st.session_state["credentials"] = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_url,
            client_id=st.secrets["google"]["client_id"],
            client_secret=st.secrets["google"]["client_secret"],
            scopes=[SCOPES]
        )
        st.query_params.clear()
        st.rerun()
    else:
        st.error(f"Handshake failed from Google: {token_data.get('error_description', token_data.get('error'))}")
        if st.button("Reset Sign In Screen"):
            st.query_params.clear()
            st.rerun()

# --- RENDERING THE AUTHENTICATION INTERFACE ---
if "credentials" not in st.session_state:
    st.markdown("""
        <div class="centered-container">
            <div class="main-title">Sairam's Auto Mail Reader</div>
            <div class="sub-title">An elegant AI-driven engine designed to automatically cluster, categorize, and synthesize summarized workspaces from your live email feeds.</div>
        </div>
    """, unsafe_allow_html=True)
    
    auth_params = {
        "client_id": st.secrets["google"]["client_id"],
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent select_account",
        "include_granted_scopes": "true"
    }

auth_url = (
    "https://accounts.google.com/o/oauth2/v2/auth?"
    + urlencode(auth_params)
)
    
    st.markdown(f"""
        <div style="text-align: center; margin-top: -10px;">
            <a href="{auth_url}" target="_self" class="google-sign-in-btn">
                <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" alt="Google Logo">
                Sign in with Google
            </a>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- ACTIVE DIGEST WORKSPACE ---
creds = st.session_state["credentials"]
gmail_service = build('gmail', 'v1', credentials=creds)

if "user_profile" not in st.session_state:
    try:
        prof = gmail_service.users().getProfile(userId='me').execute()
        st.session_state["user_profile"] = prof
    except Exception:
        st.session_state["user_profile"] = {"emailAddress": "Authorized User"}

user_email = st.session_state["user_profile"].get("emailAddress", "Connected Account")

# Premium Header Panel with Profile Identity and Logout Actions
p_col1, p_col2 = st.columns([4, 1])
with p_col1:
    st.markdown(f"""
        <div class="profile-container">
            <div class="profile-info">
                <div class="profile-avatar">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" style="width:18px; height:18px;">
                </div>
                <div class="profile-details">
                    <h4>Connected Identity</h4>
                    <p>{user_email}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

with p_col2:
    st.write("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Log Out", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.query_params.clear()
        st.rerun()

st.markdown("""
    <div style="margin-top: -10px; margin-bottom: 25px;">
        <h2 style="font-weight:700; font-size:1.65rem; margin:0; color:#111827;">📬 Analytics Dashboard</h2>
        <p style="color:#4b5563; margin:0; font-size:0.95rem;">Provide an email search keyword to target matching threads for prompt synthesis.</p>
    </div>
""", unsafe_allow_html=True)

search_query = st.text_input("🔍 Enter Subject Line / Keyword to Summarize:", placeholder="e.g., Registration, AWS, Interview")

def get_email_body(payload):
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                body = get_email_body(part)
                if body: return body
    elif 'body' in payload and 'data' in payload['body']:
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    return ""

if st.button("Generate AI Summary", type="primary"):
    if not search_query:
        st.warning("Please type a subject keyword first.")
    else:
        with st.spinner("Scanning your mailbox for matching entries..."):
            try:
                results = gmail_service.users().messages().list(userId='me', q=search_query, maxResults=6).execute()
                messages = results.get('messages', [])
                
                if not messages:
                    st.info(f"No recent emails found matching: '{search_query}'")
                else:
                    st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                    m_col1, m_col2 = st.columns(2)
                    with m_col1:
                        st.metric(label="Threads Found", value=len(messages))
                    with m_col2:
                        st.metric(label="Target Pipeline Status", value="Ready to Parse")
                        
                    compiled_email_data = ""
                    layout_left, layout_right = st.columns([1.1, 1.3], gap="large")
                    
                    with layout_left:
                        st.markdown("<h3 style='font-size:1.25rem; font-weight:600; color:#111827; margin-bottom:15px;'>📥 Matching Mail Pipeline</h3>", unsafe_allow_html=True)
                        
                        for index, msg in enumerate(messages, start=1):
                            msg_detail = gmail_service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                            headers = msg_detail['payload']['headers']
                            
                            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
                            body_content = get_email_body(msg_detail['payload'])
                            
                            compiled_email_data += f"--- EMAIL #{index} ---\nFROM: {sender}\nSUBJECT: {subject}\nCONTENT:\n{body_content[:1200]}\n\n"
                            
                            st.markdown(f"""
                                <div class="email-feed-card">
                                    <div style="font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#2563eb; margin-bottom:3px;">Thread #{index}</div>
                                    <div style="font-weight:600; color:#111827; font-size:0.98rem;">{subject}</div>
                                    <div style="font-size:0.85rem; color:#4b5563; margin-top:2px;">From: {sender}</div>
                                </div>
                            """, unsafe_allow_html=True)
                    
                    with layout_right:
                        with st.spinner("Analyzing text layout via Gemini..."):
                            genai.configure(api_key=st.secrets["gemini"]["api_key"])
                            model = genai.GenerativeModel("gemini-2.5-flash")
                            
                            ai_prompt = (
                                f"The user filtered their inbox looking for content matching: '{search_query}'.\n"
                                f"Review the live emails down below and compile them into a single unified summary context.\n"
                                f"Group common themes, point out deadlines or specific action items, and keep the output concise using clean bullet points.\n\n"
                                f"{compiled_email_data}"
                            )
                            
                            response = model.generate_content(ai_prompt)
                            
                            st.markdown("<h3 style='font-size:1.25rem; font-weight:600; color:#111827; margin-bottom:15px;'>📋 Executive Summary Digest</h3>", unsafe_allow_html=True)
                            
                            # Isolated Markdown and HTML elements to fix trailing formatting outputs
                            st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
                            st.markdown(f'*Generated by Gemini for query: "{search_query}"*')
                            st.write(response.text)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
            except Exception as err:
                st.error(f"Inbox execution error occurred: {err}")
