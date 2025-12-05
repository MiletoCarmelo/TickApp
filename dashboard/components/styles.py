"""
Styles CSS pour le dashboard
"""
import streamlit as st


def load_styles():
    """Charge les styles CSS du dashboard"""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * { 
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, sans-serif !important;
        }
        
        /* Background gradient */
        .stApp {
            background: linear-gradient(135deg, #1e1e2e 0%, #16161f 100%);
        }
        
        .main .block-container {
            padding: 1.25rem 1.5rem !important;
        }
        
        /* ===== SIDEBAR PREMIUM ===== */
        [data-testid="stSidebar"] {
            background: #25252d;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            padding: 0 !important;
        }
        
        [data-testid="stSidebar"] > div:first-child {
            padding: 1rem 0.75rem !important;
        }
        
        /* Profile section en haut - COMPACT */
        .profile-section {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 0.625rem 0.75rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.625rem;
        }
        
        .profile-avatar {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.125rem;
            flex-shrink: 0;
        }
        
        .profile-info {
            flex: 1;
            min-width: 0;
        }
        
        .profile-name {
            font-size: 0.8125rem;
            font-weight: 600;
            color: #E5E7EB;
            line-height: 1.2;
            margin-bottom: 0.05rem;
        }
        
        .profile-email {
            font-size: 0.6875rem;
            color: #9CA3AF;
            font-weight: 400;
        }
        
        .profile-toggle {
            color: #9CA3AF;
            font-size: 0.625rem;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 0.05rem;
        }
        
        /* Navigation items - COMPACT */
        [data-testid="stSidebar"] .stRadio > label {
            display: none !important;
        }
        
        [data-testid="stSidebar"] [role="radiogroup"] {
            gap: 0.15rem;
            display: flex;
            flex-direction: column;
        }
        
        [data-testid="stSidebar"] [role="radiogroup"] label {
            color: #D1D5DB !important;
            background: transparent;
            padding: 0.5rem 0.625rem !important;
            margin: 0 !important;
            border-radius: 6px;
            font-size: 0.8125rem !important;
            font-weight: 500 !important;
            transition: all 0.2s ease;
            cursor: pointer;
            position: relative;
            border-left: 2px solid transparent;
        }
        
        /* Hover state */
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: rgba(255, 255, 255, 0.04);
            color: #F3F4F6 !important;
        }
        
        /* Active state avec border-left coloré */
        [data-testid="stSidebar"] [role="radiogroup"] label[aria-checked="true"] {
            background: rgba(99, 102, 241, 0.12);
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border-left-color: #6366F1;
        }
        
        /* Cacher le radio button */
        [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
            display: none !important;
        }
        
        /* Divider */
        [data-testid="stSidebar"] hr {
            margin: 1rem 0 !important;
            border: none !important;
            border-top: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        
        /* Stats card - COMPACT */
        .sidebar-stats {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 8px;
            padding: 0.875rem;
            margin-top: 1rem;
        }
        
        .stat-label {
            font-size: 0.625rem;
            color: #9CA3AF;
            margin-bottom: 0.375rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .stat-value {
            font-size: 1.5rem;
            color: #FFFFFF;
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1;
        }
        
        .stat-secondary {
            font-size: 0.6875rem;
            color: #D1D5DB;
            margin-top: 0.375rem;
        }
        
        /* Main content - COMPACT */
        h1 { 
            font-size: 1.5rem !important; 
            font-weight: 700 !important; 
            margin: 0 0 0.25rem 0 !important;
            color: #F3F4F6 !important;
            letter-spacing: -0.03em !important;
        }
        
        .stCaption {
            font-size: 0.8125rem !important;
            color: #9CA3AF !important;
            margin-bottom: 1.25rem !important;
        }
        
        /* Metric cards - COMPACT */
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            color: #F9FAFB !important;
            letter-spacing: -0.03em !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.6875rem !important;
            font-weight: 500 !important;
            color: #9CA3AF !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        [data-testid="metric-container"] {
            background: rgba(37, 37, 45, 0.6);
            backdrop-filter: blur(10px);
            padding: 1rem 1.25rem !important;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.3s ease;
        }
        
        [data-testid="metric-container"]:hover {
            background: rgba(37, 37, 45, 0.8);
            border-color: rgba(99, 102, 241, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.3);
        }
        
        /* Filtres - COMPACT */
        .stDateInput input, .stMultiSelect div, .stSelectbox div {
            background: rgba(37, 37, 45, 0.6) !important;
            color: #F3F4F6 !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 8px;
            font-size: 0.8125rem !important;
            padding: 0.5rem 0.75rem !important;
            min-height: 36px !important;
        }
        
        .stDateInput label, .stMultiSelect label, .stSelectbox label {
            font-size: 0.6875rem !important;
            font-weight: 500 !important;
            color: #9CA3AF !important;
        }
        
        /* Buttons - COMPACT */
        .stButton button {
            background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-size: 0.8125rem;
            font-weight: 600;
            transition: all 0.2s;
            min-height: 36px !important;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px -4px rgba(99, 102, 241, 0.5);
        }
    </style>
    """, unsafe_allow_html=True)

