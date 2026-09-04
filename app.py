import base64
import html
from pathlib import Path
import os

import requests
import streamlit as st

from src.research.web_search import search_web


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AROHA AI",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

HOME_BG_FILE = BASE_DIR / "assets" / "aroha_trend_background.png"
RESEARCH_BG_FILE = BASE_DIR / "assets" / "aroha_research_background.png"
BG_FILE = RESEARCH_BG_FILE if st.session_state.get("page", "Home") != "Home" and RESEARCH_BG_FILE.exists() else HOME_BG_FILE

API_URL = "http://127.0.0.1:5000/api/research"


# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

if "research_results" not in st.session_state:
    st.session_state["research_results"] = []

if "aroha_response" not in st.session_state:
    st.session_state["aroha_response"] = {}

if "research_query" not in st.session_state:
    st.session_state["research_query"] = ""

if "selected_query" not in st.session_state:
    st.session_state["selected_query"] = ""

if "show_home_results" not in st.session_state:
    st.session_state["show_home_results"] = False

if "main_query" not in st.session_state:
    st.session_state["main_query"] = ""

if "exploration_stage" not in st.session_state:
    st.session_state["exploration_stage"] = "trends"

if "exploration_message" not in st.session_state:
    st.session_state["exploration_message"] = ""

if "selected_opportunity" not in st.session_state:
    st.session_state["selected_opportunity"] = None

if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"

if "creative_packages" not in st.session_state:
    st.session_state["creative_packages"] = {}
if "selected_opportunity_id" not in st.session_state:
    st.session_state["selected_opportunity_id"] = None


# =========================================================
# QUERY SELECTION CALLBACK
# =========================================================

def select_query(query_value):

    st.session_state["main_query"] = query_value
    st.session_state["selected_query"] = query_value


# =========================================================
# BACKGROUND IMAGE
# =========================================================

background = ""

if BG_FILE.exists():

    encoded_image = base64.b64encode(
        BG_FILE.read_bytes()
    ).decode()

    background = (
        f"data:image/png;base64,{encoded_image}"
    )


# =========================================================
# GLOBAL CSS
# =========================================================

st.html(
    f"""
    <style>

    /* =====================================================
       GLOBAL
       ===================================================== */

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html,
    body,
    [class*="css"] {{
        font-family: Inter, sans-serif;
    }}

    .stApp {{
        background:
            linear-gradient(90deg,rgba(3,4,9,0.985) 0%,rgba(4,5,11,0.965) 35%,rgba(4,5,11,0.90) 70%,rgba(4,5,11,0.96) 100%),
            url("{background}") center top / cover fixed no-repeat;
        color:#f5f5f7;
    }}

    .aroha-theory {{ font-size:16px; line-height:1.55; }}
    .aroha-key {{ font-size:18px; line-height:1.45; font-weight:650; }}
    .aroha-meta {{ font-size:12px; color:#9995a4; }}
    .aroha-muted {{ color:#8f8f9c; }}
    @media (max-width:900px) {{ .aroha-split {{ display:block !important; }} .aroha-split > div {{ margin-bottom:14px; }} }}

    .aroha-kicker {{ color:#b979ff; font-size:9px; font-weight:800; letter-spacing:2px; margin-bottom:9px; }}
    .aroha-key {{ font-size:18px; line-height:1.45; font-weight:650; margin-bottom:14px; }}
    .aroha-body {{ font-size:16px; line-height:1.55; margin-bottom:12px; }}
    .aroha-visual-label {{ color:#b979ff; font-size:9px; font-weight:800; letter-spacing:1.6px; margin-bottom:9px; }}
    .aroha-visual-empty {{ min-height:330px; display:flex; align-items:center; justify-content:center; border:1px dashed rgba(255,255,255,.12); border-radius:16px; background:rgba(255,255,255,.025); color:#777784; font-size:12px; }}
    .aroha-why {{ padding:14px 15px; border-radius:13px; background:rgba(180,119,255,.07); border:1px solid rgba(180,119,255,.12); margin:15px 0; }}
    .aroha-next-decision {{ margin:38px 0 14px; padding:22px; border-radius:18px; border:1px solid rgba(183,119,255,.22); background:rgba(183,119,255,.055); }}
    @keyframes arohaStageIn {{ 0% {{ opacity:0; transform:translateY(20px) scale(.99); filter:blur(2px); }} 70% {{ opacity:1; }} 100% {{ opacity:1; transform:translateY(0) scale(1); filter:blur(0); }} }}
    @keyframes arohaPageIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .block-container {{ animation:arohaPageIn .55s cubic-bezier(.2,.75,.2,1) both; }}
    @keyframes arohaFadeUp {{ from {{ opacity:0; transform:translateY(12px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes arohaGlow {{ 0%,100% {{ box-shadow:0 0 0 rgba(183,119,255,0); }} 50% {{ box-shadow:0 0 30px rgba(183,119,255,.13); }} }}
    .aroha-reveal {{ animation:arohaFadeUp .46s cubic-bezier(.2,.7,.2,1) both; animation-delay:var(--delay,0ms); }}
    .aroha-stage {{ animation:arohaStageIn .58s cubic-bezier(.2,.75,.2,1) both; }}
    .aroha-decision {{ animation:arohaGlow 2.8s ease-in-out infinite; }}
    .aroha-evidence-envelope {{ transition:transform .22s ease,border-color .22s ease,background .22s ease; }}
    .aroha-evidence-envelope:hover {{ transform:translateY(-3px); border-color:rgba(183,119,255,.45) !important; background:rgba(183,119,255,.08) !important; }}
    .aroha-quiet {{ color:#aaa8b5; }}
    .aroha-rail-item {{ flex:1; min-width:92px; padding:10px 11px; border-radius:12px; border:1px solid rgba(255,255,255,.07); background:rgba(255,255,255,.025); display:flex; align-items:center; gap:8px; transition:all .25s ease; }}
    .aroha-rail-item span {{ width:20px; height:20px; display:flex; align-items:center; justify-content:center; border-radius:50%; font-size:10px; font-weight:800; color:#8e8b97; background:rgba(255,255,255,.05); }}
    .aroha-rail-item small {{ font-size:10px; font-weight:700; letter-spacing:.3px; color:#898692; }}
    .aroha-rail-item.complete {{ border-color:rgba(183,119,255,.16); }}
    .aroha-rail-item.complete span {{ color:#d0b1ff; background:rgba(183,119,255,.12); }}
    .aroha-rail-item.active {{ border-color:rgba(183,119,255,.38); background:rgba(183,119,255,.08); transform:translateY(-1px); }}
    .aroha-rail-item.active span {{ color:#fff; background:#9b65ff; box-shadow:0 0 18px rgba(155,101,255,.38); }}
    .aroha-rail-item.active small {{ color:#e6dcf4; }}
    body:has(.aroha-light-theme) .stApp {{
        background:
            linear-gradient(120deg, rgba(248,246,251,.98), rgba(255,255,255,.97)),
            url("{background}") center 18% / cover fixed no-repeat !important;
        color:#1d1a24 !important;
    }}
    body:has(.aroha-light-theme) .stApp::before {{
        content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
        background:linear-gradient(120deg,rgba(255,255,255,.80),rgba(248,244,253,.90));
    }}
    body:has(.aroha-light-theme) .block-container {{ position:relative; z-index:1; }}
    body:has(.aroha-light-theme) .aroha-card,
    body:has(.aroha-light-theme) .aroha-opportunity-card,
    body:has(.aroha-light-theme) .aroha-creative-panel,
    body:has(.aroha-light-theme) .category-card,
    body:has(.aroha-light-theme) .flow-card {{
        background:rgba(255,255,255,.94) !important;
        border-color:rgba(44,35,58,.10) !important;
        box-shadow:0 14px 36px rgba(52,39,69,.08) !important;
        color:#211d28 !important;
        backdrop-filter:blur(18px);
    }}
    body:has(.aroha-light-theme) .aroha-theory,
    body:has(.aroha-light-theme) .aroha-theory p,
    body:has(.aroha-light-theme) .aroha-theory div,
    body:has(.aroha-light-theme) .aroha-key,
    body:has(.aroha-light-theme) .aroha-body {{ color:#2b2632 !important; }}
    body:has(.aroha-light-theme) .aroha-muted,
    body:has(.aroha-light-theme) .aroha-meta,
    body:has(.aroha-light-theme) .section-description {{ color:#716a79 !important; }}
    body:has(.aroha-light-theme) .result-card {{ background:rgba(255,255,255,.96) !important; border-color:rgba(44,35,58,.09) !important; color:#2b2632 !important; }}
    body:has(.aroha-light-theme) section[data-testid="stSidebar"] {{ background:rgba(247,244,250,.97) !important; border-right:1px solid rgba(44,35,58,.09) !important; }}
    body:has(.aroha-light-theme) section[data-testid="stSidebar"] .stButton > button {{ color:#625b6a !important; }}
    body:has(.aroha-light-theme) div[data-testid="stTextInput"] input {{ background:#fff !important; color:#1d1a24 !important; border-color:rgba(44,35,58,.12) !important; }}
    body:has(.aroha-light-theme) .aroha-visual-empty {{ border-color:rgba(44,35,58,.14); background:rgba(49,37,65,.035); color:#827b89; }}
    body:has(.aroha-light-theme) .aroha-rail-item {{ background:rgba(255,255,255,.72); border-color:rgba(44,35,58,.08); }}
    body:has(.aroha-light-theme) .aroha-rail-item small {{ color:#756e7d; }}
    body:has(.aroha-light-theme) .aroha-rail-item.active {{ background:rgba(155,101,255,.09); border-color:rgba(126,77,210,.28); }}
    body:has(.aroha-light-theme) .aroha-rail-item.active small {{ color:#4d3d5d; }}

    /* Research pages use the same AROHA visual language as Home, but with a quieter background. */
    body:has(.aroha-page-research) .stApp {{
        background-position:center 18%;
        background-size:cover;
    }}
    body:has(.aroha-page-signals) .stApp, body:has(.aroha-page-trends) .stApp, body:has(.aroha-page-opportunities) .stApp, body:has(.aroha-page-creative-studio) .stApp {{
        background-position:center 28%;
    }}


    .block-container {{

        max-width:
            1450px;

        padding-top:
            90px;

        padding-bottom:
            80px;
    }}


    #MainMenu {{
        visibility:
            hidden;
    }}


    footer {{
        visibility:
            hidden;
    }}


    /* =====================================================
       SIDEBAR
       ===================================================== */

    section[data-testid="stSidebar"] {{

        background:
            rgba(5,6,12,0.97) !important;

        border-right:
            1px solid rgba(255,255,255,0.08);
    }}


    section[data-testid="stSidebar"] > div {{

        padding-top:
            1.2rem;
    }}


    section[data-testid="stSidebar"]
    .stButton > button {{

        background:
            transparent !important;

        border:
            1px solid transparent !important;

        color:
            #9f9fac !important;

        box-shadow:
            none !important;

        text-align:
            left !important;

        justify-content:
            flex-start !important;

        min-height:
            42px !important;

        font-size:
            13px !important;

        font-weight:
            500 !important;

        transition:
            all 0.2s ease;
    }}


    section[data-testid="stSidebar"]
    .stButton > button:hover {{

        background:
            rgba(164,102,255,0.10) !important;

        border:
            1px solid rgba(164,102,255,0.18) !important;

        color:
            #d19aff !important;

        transform:
            translateX(3px);
    }}


    /* =====================================================
       HERO
       ===================================================== */

    .hero-eyebrow {{

        color:
            #c28aff;

        font-size:
            11px;

        font-weight:
            800;

        letter-spacing:
            3px;

        margin-bottom:
            17px;
    }}


    .hero-title {{

        font-size:
            clamp(3.5rem, 6vw, 6.3rem);

        line-height:
            0.94;

        font-weight:
            800;

        letter-spacing:
            -4px;

        margin:
            0;
    }}


    .hero-highlight {{

        color:
            #b777ff;

        text-shadow:
            0 0 45px rgba(183,119,255,0.35);
    }}


    .hero-description {{

        max-width:
            760px;

        margin-top:
            25px;

        color:
            #c2c2ce;

        font-size:
            16px;

        line-height:
            1.75;
    }}


    /* =====================================================
       SEARCH INPUT
       ===================================================== */

    div[data-testid="stTextInput"] input {{

        background:
            rgba(255,255,255,0.97) !important;

        color:
            #22222b !important;

        border:
            1px solid rgba(255,255,255,0.65) !important;

        border-radius:
            14px !important;

        height:
            58px !important;

        font-size:
            15px !important;

        padding-left:
            18px !important;

        transition:
            all 0.2s ease;
    }}


    div[data-testid="stTextInput"] input:focus {{

        border:
            1px solid #a96cff !important;

        box-shadow:
            0 0 0 2px rgba(169,108,255,0.15) !important;
    }}


    /* =====================================================
       MAIN BUTTONS
       ===================================================== */

    .stButton > button {{

        background:
            linear-gradient(
                135deg,
                #8d5cff,
                #d05cff
            ) !important;

        color:
            white !important;

        border:
            none !important;

        border-radius:
            13px !important;

        min-height:
            48px !important;

        font-weight:
            700 !important;

        box-shadow:
            0 8px 25px rgba(143,98,255,0.24);

        transition:
            all 0.2s ease;
    }}


    .stButton > button:hover {{

        transform:
            translateY(-2px);

        box-shadow:
            0 12px 35px rgba(143,98,255,0.38);
    }}


    /* =====================================================
       LIVE BADGE
       ===================================================== */

    .live-badge {{

        display:
            inline-block;

        padding:
            9px 14px;

        border-radius:
            999px;

        background:
            rgba(62,207,138,0.09);

        border:
            1px solid rgba(62,207,138,0.20);

        color:
            #83deb0;

        font-size:
            10px;

        font-weight:
            600;

        letter-spacing:
            0.5px;
    }}


    /* =====================================================
       SECTION HEADINGS
       ===================================================== */

    .section-title {{

        font-size:
            23px;

        font-weight:
            700;

        margin-top:
            42px;

        margin-bottom:
            6px;
    }}


    .section-description {{

        color:
            #90909d;

        font-size:
            12px;

        line-height:
            1.6;

        margin-bottom:
            18px;
    }}


    /* =====================================================
       CATEGORY CARDS
       ===================================================== */

    .category-card {{

        min-height:
            132px;

        padding:
            20px;

        border-radius:
            17px;

        background:
            linear-gradient(
                145deg,
                rgba(18,19,29,0.86),
                rgba(10,11,18,0.70)
            );

        border:
            1px solid rgba(255,255,255,0.09);

        transition:
            all 0.25s ease;

        backdrop-filter:
            blur(14px);
    }}


    .category-card:hover {{

        transform:
            translateY(-5px);

        border-color:
            rgba(182,121,255,0.45);

        box-shadow:
            0 12px 30px rgba(0,0,0,0.25),
            0 0 25px rgba(153,91,255,0.08);
    }}


    .category-icon {{

        font-size:
            25px;
    }}


    .category-name {{

        margin-top:
            12px;

        font-size:
            14px;

        font-weight:
            700;
    }}


    .category-description {{

        margin-top:
            5px;

        color:
            #888895;

        font-size:
            10px;

        line-height:
            1.45;
    }}


    /* =====================================================
       HOW AROHA WORKS - GLOBAL SUPPORT
       ===================================================== */

    .flow-card {{

        position:
            relative;

        min-height:
            300px;

        padding:
            25px 21px;

        border-radius:
            20px;

        background:
            linear-gradient(
                145deg,
                rgba(22,23,35,0.88),
                rgba(9,10,18,0.72)
            );

        border:
            1px solid rgba(255,255,255,0.09);

        backdrop-filter:
            blur(18px);

        overflow:
            hidden;

        transition:
            transform 0.3s ease,
            border-color 0.3s ease,
            box-shadow 0.3s ease;
    }}


    .flow-card:hover {{

        transform:
            translateY(-8px);

        border-color:
            rgba(177,112,255,0.50);

        box-shadow:
            0 18px 45px rgba(0,0,0,0.35),
            0 0 35px rgba(153,91,255,0.12);
    }}


    .flow-number {{

        color:
            #b879ff;

        font-size:
            10px;

        font-weight:
            800;

        letter-spacing:
            2px;

        margin-bottom:
            32px;
    }}


    .flow-icon {{

        width:
            48px;

        height:
            48px;

        display:
            flex;

        align-items:
            center;

        justify-content:
            center;

        border-radius:
            14px;

        background:
            rgba(171,105,255,0.10);

        border:
            1px solid rgba(180,112,255,0.22);

        color:
            #c28aff;

        font-size:
            21px;

        margin-bottom:
            22px;

        box-shadow:
            0 0 25px rgba(168,102,255,0.10);
    }}


    .flow-title {{

        color:
            #f4f4f7;

        font-size:
            17px;

        font-weight:
            700;

        margin-bottom:
            10px;
    }}


    .flow-copy {{

        color:
            #858592;

        font-size:
            11px;

        line-height:
            1.7;
    }}


    /* =====================================================
       RADAR
       ===================================================== */

    .radar-panel {{

        padding:
            22px;

        border-radius:
            18px;

        background:
            radial-gradient(
                circle at 50% 25%,
                rgba(157,92,255,0.20),
                transparent 62%
            ),
            rgba(13,14,22,0.82);

        border:
            1px solid rgba(172,110,255,0.16);

        backdrop-filter:
            blur(14px);
    }}


    .radar-label {{

        color:
            #aaaab6;

        font-size:
            9px;

        font-weight:
            700;

        letter-spacing:
            2px;
    }}


    .radar-number {{

        color:
            #b878ff;

        font-size:
            32px;

        font-weight:
            800;

        margin-top:
            12px;
    }}


    .radar-copy {{

        color:
            #888895;

        font-size:
            10px;
    }}


    .radar-live {{

        margin-top:
            13px;

        color:
            #79dba8;

        font-size:
            8px;

        letter-spacing:
            1px;
    }}


    /* =====================================================
       RESULT CARDS
       ===================================================== */

    .result-card {{

        padding:
            20px;

        margin:
            12px 0;

        border-radius:
            16px;

        background:
            rgba(9,10,17,0.78);

        border:
            1px solid rgba(255,255,255,0.09);

        backdrop-filter:
            blur(12px);

        transition:
            all 0.2s ease;
    }}


    .result-card:hover {{

        border-color:
            rgba(177,112,255,0.30);

        transform:
            translateY(-2px);
    }}


    .result-number {{

        color:
            #b979ff;

        font-size:
            9px;

        font-weight:
            800;

        letter-spacing:
            2px;
    }}


    .result-title {{

        margin-top:
            7px;

        font-size:
            16px;

        font-weight:
            700;
    }}


    .result-url {{

        margin-top:
            5px;

        color:
            #686875;

        font-size:
            9px;

        word-break:
            break-all;
    }}


    .result-content {{

        margin-top:
            13px;

        color:
            #bcbcc7;

        font-size:
            12px;

        line-height:
            1.7;
    }}


    /* =====================================================
       EMPTY STATE
       ===================================================== */

    .empty-state {{

        margin-top:
            38px;

        padding:
            27px;

        border-radius:
            18px;

        background:
            rgba(13,14,22,0.68);

        border:
            1px solid rgba(255,255,255,0.08);

        backdrop-filter:
            blur(12px);
    }}


    .empty-title {{

        font-size:
            16px;

        font-weight:
            700;
    }}


    .empty-copy {{

        margin-top:
            7px;

        color:
            #8e8e9b;

        font-size:
            12px;

        line-height:
            1.6;
    }}


    /* =====================================================
       FOOTER
       ===================================================== */

    .footer {{

        margin-top:
            70px;

        padding-top:
            20px;

        border-top:
            1px solid rgba(255,255,255,0.07);

        text-align:
            center;

        color:
            #5f5f6b;

        font-size:
            9px;

        letter-spacing:
            1.5px;
    }}


    /* =====================================================
       MOBILE
       ===================================================== */

    @media(max-width:900px) {{

        .block-container {{

            padding-top:
                55px;

            padding-left:
                20px;

            padding-right:
                20px;
        }}


        .hero-title {{

            font-size:
                3.5rem;

            letter-spacing:
                -2px;
        }}


        .hero-description {{

            font-size:
                14px;
        }}


        .home-section {{

            margin-top:
                65px;
        }}


        .home-section-title {{

            font-size:
                2.7rem;

            letter-spacing:
                -2px;
        }}


        .flow-card {{

            min-height:
                240px;

            margin-bottom:
                14px;
        }}

    }}

    </style>
    """
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    # -----------------------------------------------------
    # BRAND
    # -----------------------------------------------------

    st.html(
        """
        <div style="
            display:flex;
            align-items:center;
            gap:11px;
            padding:5px 8px 27px;
        ">

            <div style="
                width:39px;
                height:39px;
                border:2px solid #a970ff;
                border-radius:50%;

                display:flex;
                align-items:center;
                justify-content:center;

                color:#c48aff;
                font-size:19px;

                box-shadow:
                    0 0 22px rgba(169,112,255,.30);
            ">
                △
            </div>

            <div>

                <div style="
                    font-size:20px;
                    font-weight:800;
                    letter-spacing:5px;
                ">
                    AROHA
                </div>

                <div style="
                    font-size:7px;
                    letter-spacing:2px;
                    color:#858592;
                    margin-top:4px;
                ">
                    TREND INTELLIGENCE
                </div>

            </div>

        </div>
        """
    )


    # -----------------------------------------------------
    # THEME
    # -----------------------------------------------------

    theme_label = "☀  Light Mode" if st.session_state.get("theme_mode") == "dark" else "☾  Dark Mode"
    if st.button(theme_label, use_container_width=True, key="theme_toggle"):
        st.session_state["theme_mode"] = "light" if st.session_state.get("theme_mode") == "dark" else "dark"
        st.rerun()

    # -----------------------------------------------------
    # EXPLORE
    # -----------------------------------------------------

    st.caption("NAVIGATE")

    if st.button("⌂   Home", use_container_width=True, key="nav_home"):
        st.session_state["page"] = "Home"
        st.rerun()

    if st.button("⌕   Research", use_container_width=True, key="nav_research"):
        st.session_state["page"] = "Research"
        st.rerun()

    # -----------------------------------------------------
    # YOUR SPACE
    # -----------------------------------------------------

    st.caption("WORKSPACE")


    if st.button(
        "◇   Saved Insights",
        use_container_width=True,
        key="nav_saved",
    ):

        st.session_state["page"] = "Saved Insights"
        st.rerun()


    if st.button(
        "◷   History",
        use_container_width=True,
        key="nav_history",
    ):

        st.session_state["page"] = "History"
        st.rerun()


    st.divider()


    # -----------------------------------------------------
    # TREND RADAR
    # -----------------------------------------------------

    st.html(
        """
        <div class="radar-panel">

            <div class="radar-label">
                ◉ TREND RADAR
            </div>

            <div class="radar-number">
                120+
            </div>

            <div class="radar-copy">
                countries monitored
            </div>

            <div class="radar-live">
                ● LIVE INTELLIGENCE
            </div>

        </div>
        """
    )


    # -----------------------------------------------------
    # USER
    # -----------------------------------------------------

    st.html(
        """
        <div style="
            display:flex;
            align-items:center;
            gap:10px;

            margin-top:24px;
            padding:12px;

            border-radius:12px;

            background:
                rgba(255,255,255,0.035);
        ">

            <div style="
                width:34px;
                height:34px;

                border-radius:50%;

                background:
                    linear-gradient(
                        135deg,
                        #8f62ff,
                        #d15cff
                    );

                display:flex;
                align-items:center;
                justify-content:center;

                font-size:10px;
                font-weight:800;
            ">
                KJ
            </div>

            <div>

                <div style="
                    font-size:11px;
                    font-weight:600;
                ">
                    Trend Explorer
                </div>

                <div style="
                    color:#777783;
                    font-size:9px;
                    margin-top:3px;
                ">
                    AROHA Workspace
                </div>

            </div>

        </div>
        """
    )


# =========================================================
# MAIN BRAND HEADER
# =========================================================

st.html(
    """
    <div style="
        display:flex;
        align-items:center;
        gap:12px;
        margin-bottom:62px;
    ">

        <div style="
            width:40px;
            height:40px;

            border:2px solid #a970ff;
            border-radius:50%;

            display:flex;
            align-items:center;
            justify-content:center;

            color:#c48aff;
            font-size:20px;

            box-shadow:
                0 0 25px rgba(169,112,255,.32);
        ">
            △
        </div>

        <div>

            <div style="
                font-size:23px;
                font-weight:800;
                letter-spacing:7px;
            ">
                AROHA
            </div>

            <div style="
                font-size:9px;
                letter-spacing:3px;
                color:#a1a1ad;
                margin-top:5px;
            ">
                TREND INTELLIGENCE
            </div>

        </div>

    </div>
    """
)


# =========================================================
# PAGE CONTENT
# =========================================================

current_page = st.session_state["page"]
theme_mode = st.session_state.get("theme_mode", "dark")
page_class = current_page.lower().replace(" ", "-")


# =========================================================
# HOME
# =========================================================

st.html(f'<div class="aroha-{theme_mode}-theme aroha-page-{page_class}"></div>')

if current_page == "Home":

    # =====================================================
    # HOME PAGE STYLES
    # =====================================================

    st.html(
        """
        <style>

        /* =================================================
           AROHA LANDING HERO
           ================================================= */

        .aroha-home {

            padding-top:
                25px;
        }


        .home-eyebrow {

            display:
                inline-flex;

            align-items:
                center;

            gap:
                8px;

            padding:
                8px 13px;

            border-radius:
                999px;

            background:
                rgba(171,105,255,0.08);

            border:
                1px solid rgba(171,105,255,0.20);

            color:
                #c997ff;

            font-size:
                9px;

            font-weight:
                700;

            letter-spacing:
                2px;
        }


        .home-eyebrow-dot {

            width:
                6px;

            height:
                6px;

            border-radius:
                50%;

            background:
                #b878ff;

            box-shadow:
                0 0 12px rgba(184,120,255,0.8);
        }


        .home-title {

            margin-top:
                27px;

            max-width:
                850px;

            font-size:
                clamp(4rem, 7vw, 7rem);

            line-height:
                0.92;

            font-weight:
                800;

            letter-spacing:
                -5px;
        }


        .home-title-gradient {

            background:
                linear-gradient(
                    100deg,
                    #a66cff,
                    #d75cff,
                    #b77cff
                );

            -webkit-background-clip:
                text;

            -webkit-text-fill-color:
                transparent;

            background-clip:
                text;
        }


        .home-description {

            max-width:
                780px;

            margin-top:
                30px;

            color:
                #b5b5c2;

            font-size:
                16px;

            line-height:
                1.85;
        }


        .home-description strong {

            color:
                #f1eaff;

            font-weight:
                700;
        }


        .home-description .highlight {

            color:
                #c58aff;

            font-size:
                600;

            transition:
                all 0.25s ease;
        }


        /* =================================================
           HERO CTA
           ================================================= */

        .hero-cta-space {

            margin-top:
                32px;
        }


        /* =================================================
           SECTION
           ================================================= */

        .home-section {

            margin-top:
                115px;
        }


        .home-section-label {

            color:
                #b979ff;

            font-size:
                10px;

            font-weight:
                800;

            letter-spacing:
                3px;

            margin-bottom:
                14px;
        }


        .home-section-title {

            font-size:
                38px;

            line-height:
                1.15;

            font-weight:
                750;

            letter-spacing:
                -1.5px;

            margin-bottom:
                12px;
        }


        .home-section-copy {

            max-width:
                650px;

            color:
                #858592;

            font-size:
                12px;

            line-height:
                1.7;
        }


        /* =================================================
           WHAT IS AROHA
           ================================================= */

        .about-card {

            margin-top:
                30px;

            padding:
                30px;

            border-radius:
                22px;

            background:
                linear-gradient(
                    135deg,
                    rgba(26,22,39,0.92),
                    rgba(12,13,21,0.76)
                );

            border:
                1px solid rgba(180,119,255,0.14);

            box-shadow:
                0 20px 70px rgba(0,0,0,0.20);
        }


        .about-number {

            color:
                #8f8f9c;

            font-size:
                9px;

            font-weight:
                800;

            letter-spacing:
                2px;
        }


        .about-heading {

            margin-top:
                13px;

            font-size:
                23px;

            font-weight:
                700;
        }


        .about-text {

            margin-top:
                12px;

            color:
                #9999a7;

            font-size:
                12px;

            line-height:
                1.8;

            max-width:
                900px;
        }


        /* =================================================
           HOW AROHA WORKS
           ================================================= */

        .aroha-process {

            position:
                relative;

            width:
                100%;

            margin-top:
                120px;

            padding:
                10px 0 30px;
        }


        .process-label {

            color:
                #b979ff;

            font-size:
                10px;

            font-weight:
                800;

            letter-spacing:
                3px;

            margin-bottom:
                14px;
        }


        .process-title {

            color:
                #f5f5f7;

            font-size:
                clamp(2.4rem, 4vw, 4rem);

            line-height:
                1;

            font-weight:
                800;

            letter-spacing:
                -2.5px;

            margin-bottom:
                15px;
        }


        .process-description {

            max-width:
                700px;

            color:
                #858592;

            font-size:
                13px;

            line-height:
                1.7;

            margin-bottom:
                55px;
        }


        /* =================================================
           PROCESS GROUP LABEL
           ================================================= */

        .process-group-label {

            margin:
                0 0 22px;

            color:
                #6f6f7c;

            font-size:
                9px;

            font-weight:
                800;

            letter-spacing:
                3px;
        }


        /* =================================================
           DISCOVERY ROW
           ================================================= */

        .process-row {

            width:
                100%;

            display:
                flex;

            align-items:
                stretch;

            justify-content:
                center;

            gap:
                18px;

            margin-bottom:
                18px;
        }


        /* =================================================
           PROCESS NODE
           ================================================= */

        .process-node {

            position:
                relative;

            flex:
                1;

            min-width:
                0;

            min-height:
                205px;

            padding:
                24px;

            border-radius:
                20px;

            background:
                linear-gradient(
                    145deg,
                    rgba(22,23,35,0.90),
                    rgba(9,10,18,0.76)
                );

            border:
                1px solid rgba(255,255,255,0.075);

            backdrop-filter:
                blur(18px);

            overflow:
                hidden;

            transition:
                transform .28s ease,
                border-color .28s ease,
                box-shadow .28s ease;
        }


        .process-node::before {

            content:
                "";

            position:
                absolute;

            width:
                130px;

            height:
                130px;

            right:
                -65px;

            top:
                -65px;

            border-radius:
                50%;

            background:
                radial-gradient(
                    circle,
                    rgba(178,108,255,0.20),
                    transparent 70%
                );

            pointer-events:
                none;
        }


        .process-node:hover {

            transform:
                translateY(-7px);

            border-color:
                rgba(180,119,255,0.40);

            box-shadow:
                0 20px 45px rgba(0,0,0,0.30),
                0 0 30px rgba(161,91,255,0.10);
        }


        /* =================================================
           PROCESS NUMBER
           ================================================= */

        .process-number {

            color:
                #b979ff;

            font-size:
                9px;

            font-weight:
                800;

            letter-spacing:
                2px;
        }


        /* =================================================
           PROCESS ICON
           ================================================= */

        .process-icon {

            width:
                48px;

            height:
                48px;

            margin-top:
                25px;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            border-radius:
                14px;

            background:
                rgba(171,105,255,0.09);

            border:
                1px solid rgba(180,112,255,0.20);

            color:
                #c28aff;

            font-size:
                21px;

            box-shadow:
                0 0 24px rgba(168,102,255,0.08);
        }


        /* =================================================
           PROCESS NAME
           ================================================= */

        .process-name {

            margin-top:
                18px;

            color:
                #f3f3f6;

            font-size:
                15px;

            font-weight:
                700;
        }


        /* =================================================
           PROCESS COPY
           ================================================= */

        .process-copy {

            max-width:
                260px;

            margin-top:
                8px;

            color:
                #7e7e8c;

            font-size:
                10px;

            line-height:
                1.65;
        }


        /* =================================================
           PROCESS ARROW
           ================================================= */

        .process-arrow {

            flex:
                0 0 32px;

            align-self:
                center;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            color:
                #9b66e8;

            font-size:
                19px;

            opacity:
                .8;

            text-shadow:
                0 0 15px rgba(171,105,255,.45);
        }


        /* =================================================
           CORE CONNECTOR
           ================================================= */

        .core-connector {

            width:
                100%;

            height:
                45px;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            color:
                #a76cff;

            font-size:
                22px;

            text-shadow:
                0 0 18px rgba(171,105,255,.50);
        }


        /* =================================================
           AROHA CORE
           ================================================= */

        .aroha-core {

            position:
                relative;

            width:
                min(700px, 90%);

            min-height:
                175px;

            margin:
                0 auto;

            padding:
                35px 30px;

            display:
                flex;

            flex-direction:
                column;

            align-items:
                center;

            justify-content:
                center;

            text-align:
                center;

            border-radius:
                26px;

            background:
                radial-gradient(
                    circle at center,
                    rgba(170,95,255,0.20),
                    transparent 65%
                ),
                linear-gradient(
                    145deg,
                    rgba(22,17,37,0.94),
                    rgba(9,10,18,0.88)
                );

            border:
                1px solid rgba(181,111,255,0.34);

            box-shadow:
                0 0 65px rgba(143,82,255,0.12),
                inset 0 0 45px rgba(164,91,255,0.04);

            overflow:
                hidden;
        }


        .aroha-core::before {

            content:
                "";

            position:
                absolute;

            inset:
                0;

            background:
                linear-gradient(
                    120deg,
                    transparent 15%,
                    rgba(190,130,255,0.07) 50%,
                    transparent 85%
                );

            pointer-events:
                none;
        }


        /* =================================================
           CORE ORBITS
           ================================================= */

        .core-orbit {

            position:
                absolute;

            left:
                50%;

            top:
                50%;

            border:
                1px solid rgba(180,112,255,0.10);

            border-radius:
                50%;

            transform:
                translate(-50%, -50%);

            pointer-events:
                none;
        }


        .orbit-one {

            width:
                180px;

            height:
                85px;

            transform:
                translate(-50%, -50%) rotate(15deg);
        }


        .orbit-two {

            width:
                230px;

            height:
                105px;

            transform:
                translate(-50%, -50%) rotate(-15deg);
        }


        /* =================================================
           CORE SYMBOL
           ================================================= */

        .core-symbol {

            position:
                relative;

            width:
                48px;

            height:
                48px;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            border-radius:
                50%;

            color:
                #d09aff;

            font-size:
                20px;

            border:
                1px solid rgba(192,130,255,0.60);

            box-shadow:
                0 0 30px rgba(175,105,255,0.22);

            background:
                rgba(168,91,255,0.08);

            z-index:
                2;
        }


        .core-label {

            position:
                relative;

            margin-top:
                13px;

            color:
                #b979ff;

            font-size:
                9px;

            font-weight:
                800;

            letter-spacing:
                3px;

            z-index:
                2;
        }


        .core-title {

            position:
                relative;

            margin-top:
                5px;

            color:
                #f5f5f7;

            font-size:
                18px;

            font-weight:
                800;

            z-index:
                2;
        }


        .core-copy {

            position:
                relative;

            margin-top:
                7px;

            color:
                #888895;

            font-size:
                10px;

            letter-spacing:
                1px;

            z-index:
                2;
        }


        /* =================================================
           OPPORTUNITY CARD
           ================================================= */

        .opportunity-card {

            position:
                relative;

            width:
                min(900px, 92%);

            min-height:
                135px;

            margin:
                0 auto;

            padding:
                27px 32px;

            display:
                flex;

            align-items:
                center;

            gap:
                24px;

            border-radius:
                20px;

            background:
                linear-gradient(
                    110deg,
                    rgba(24,19,39,0.92),
                    rgba(11,12,20,0.84)
                );

            border:
                1px solid rgba(180,119,255,0.20);

            box-shadow:
                0 18px 55px rgba(0,0,0,0.22);

            overflow:
                hidden;

            transition:
                all .28s ease;
        }


        .opportunity-card:hover {

            transform:
                translateY(-5px);

            border-color:
                rgba(180,119,255,0.42);

            box-shadow:
                0 22px 60px rgba(0,0,0,0.30),
                0 0 35px rgba(153,91,255,0.10);
        }


        .opportunity-glow {

            position:
                absolute;

            width:
                220px;

            height:
                220px;

            right:
                -90px;

            top:
                -90px;

            border-radius:
                50%;

            background:
                radial-gradient(
                    circle,
                    rgba(177,103,255,0.22),
                    transparent 70%
                );

            pointer-events:
                none;
        }


        .opportunity-number {

            position:
                relative;

            color:
                #b979ff;

            font-size:
                9px;

            font-weight:
                800;

            letter-spacing:
                2px;

            align-self:
                flex-start;
        }


        .opportunity-icon {

            position:
                relative;

            width:
                48px;

            height:
                48px;

            flex:
                0 0 48px;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            border-radius:
                14px;

            background:
                rgba(171,105,255,0.09);

            border:
                1px solid rgba(180,112,255,0.20);

            color:
                #c28aff;

            font-size:
                21px;
        }


        .opportunity-label {

            position:
                relative;

            color:
                #b979ff;

            font-size:
                9px;

            font-weight:
                800;

            letter-spacing:
                2px;

            margin-bottom:
                6px;
        }


        .opportunity-title {

            position:
                relative;

            color:
                #f3f3f6;

            font-size:
                16px;

            font-weight:
                700;
        }


        .opportunity-copy {

            position:
                relative;

            margin-top:
                6px;

            color:
                #81818e;

            font-size:
                10px;

            line-height:
                1.6;
        }


        /* =================================================
           CREATION ROW
           ================================================= */

        .creation-row {

            width:
                100%;

            display:
                flex;

            align-items:
                stretch;

            justify-content:
                center;

            gap:
                18px;
        }


        .creation-node {

            position:
                relative;

            flex:
                1;

            max-width:
                500px;

            min-height:
                190px;

            padding:
                24px;

            border-radius:
                20px;

            background:
                linear-gradient(
                    145deg,
                    rgba(22,23,35,0.90),
                    rgba(9,10,18,0.76)
                );

            border:
                1px solid rgba(255,255,255,0.075);

            backdrop-filter:
                blur(18px);

            overflow:
                hidden;

            transition:
                all .28s ease;
        }


        .creation-node::after {

            content:
                "";

            position:
                absolute;

            width:
                150px;

            height:
                150px;

            right:
                -70px;

            bottom:
                -70px;

            border-radius:
                50%;

            background:
                radial-gradient(
                    circle,
                    rgba(171,105,255,0.15),
                    transparent 70%
                );

            pointer-events:
                none;
        }


        .creation-node:hover {

            transform:
                translateY(-6px);

            border-color:
                rgba(180,119,255,0.38);

            box-shadow:
                0 18px 45px rgba(0,0,0,0.28);
        }


        /* =================================================
           HOW IT WORKS RESPONSIVE
           ================================================= */

        @media(max-width:900px) {

            .aroha-process {

                margin-top:
                    80px;
            }


            .process-title {

                font-size:
                    2.8rem;
            }


            .process-description {

                margin-bottom:
                    40px;
            }


            .process-row {

                flex-direction:
                    column;

                gap:
                    12px;
            }


            .process-node {

                width:
                    100%;

                min-height:
                    175px;
            }


            .process-arrow {

                height:
                    28px;

                flex:
                    0 0 28px;

                transform:
                    rotate(90deg);
            }


            .core-connector {

                height:
                    35px;
            }


            .aroha-core {

                width:
                    100%;

                min-height:
                    165px;

                padding:
                    28px 20px;
            }


            .opportunity-card {

                width:
                    100%;

                flex-wrap:
                    wrap;

                gap:
                    14px;

                padding:
                    24px;
            }


            .opportunity-number {

                width:
                    100%;
            }


            .creation-row {

                flex-direction:
                    column;

                gap:
                    12px;
            }


            .creation-node {

                width:
                    100%;

                max-width:
                    none;
            }

        }


        /* =================================================
           CAPABILITIES
           ================================================= */

        .capability-card {

            padding:
                22px;

            min-height:
                145px;

            border-radius:
                18px;

            background:
                rgba(12,13,20,0.68);

            border:
                1px solid rgba(255,255,255,0.075);
        }


        .capability-icon {

            font-size:
                22px;
        }


        .capability-title {

            margin-top:
                13px;

            font-size:
                13px;

            font-weight:
                700;
        }


        .capability-copy {

            margin-top:
                6px;

            color:
                #777784;

            font-size:
                10px;

            line-height:
                1.55;
        }


        /* =================================================
           FINAL CTA
           ================================================= */

        .final-cta {

            margin-top:
                110px;

            padding:
                55px 35px;

            text-align:
                center;

            border-radius:
                25px;

            background:
                radial-gradient(
                    circle at 50% 0%,
                    rgba(168,94,255,0.20),
                    transparent 65%
                ),
                rgba(14,15,24,0.82);

            border:
                1px solid rgba(180,119,255,0.16);
        }


        .final-cta-title {

            font-size:
                32px;

            font-weight:
                750;

            letter-spacing:
                -1px;
        }


        .final-cta-copy {

            max-width:
                560px;

            margin:
                12px auto 25px;

            color:
                #858592;

            font-size:
                12px;

            line-height:
                1.7;
        }


        /* =================================================
           CATEGORY CHIPS
           ================================================= */

        .category-chip {

            padding:
                15px 18px;

            border-radius:
                14px;

            text-align:
                center;

            background:
                rgba(255,255,255,0.035);

            border:
                1px solid rgba(255,255,255,0.07);

            color:
                #b9b9c4;

            font-size:
                11px;

            font-weight:
                600;

            transition:
                all .2s ease;
        }


        .category-chip:hover {

            border-color:
                rgba(180,119,255,0.30);

            background:
                rgba(180,119,255,0.07);

            color:
                #d2aaff;
        }

        </style>
        """
    )


    # =====================================================
    # HERO
    # =====================================================

    st.html(
        """
        <div class="aroha-home">

            <div class="home-eyebrow">

                <span class="home-eyebrow-dot"></span>

                AI-POWERED TREND INTELLIGENCE

            </div>


            <div class="home-title">

                Discover

                <br>

                <span class="home-title-gradient">
                    What's Next.
                </span>

            </div>


            <div class="home-description">

                <strong>AROHA</strong> watches what is happening
                across the web, connects the signals, and helps
                you see <span class="highlight">what could happen next.</span>

                <br><br>

                Explore emerging behaviors, cultural shifts,
                market movements and creative possibilities —
                then turn that intelligence into something you
                can actually <span class="highlight">use.</span>

            </div>

        </div>
        """
    )


    # =====================================================
    # HERO CTA
    # =====================================================

    st.html(
        '<div class="hero-cta-space"></div>'
    )


    hero_col1, hero_col2, hero_col3 = st.columns(
        [1.2, 2.4, 1.2]
    )


    with hero_col2:

        if st.button(
            "◈   Explore Research  →",
            use_container_width=True,
            key="home_start_research",
        ):

            st.session_state["page"] = "Research"

            st.rerun()


    # =====================================================
    # POPULAR EXPLORATIONS
    # =====================================================

    st.html(
        """
        <div style="
            margin-top:20px;
            margin-bottom:12px;

            color:#777783;
            font-size:9px;
            font-weight:700;
            letter-spacing:2px;
        ">
            POPULAR EXPLORATIONS
        </div>
        """
    )


    popular_queries = [
        "Minimalist Home Decor",
        "AI Lifestyle",
        "Gen Z Fashion",
        "Functional Beverages",
    ]


    popular_columns = st.columns(4)


    for i, popular_query in enumerate(popular_queries):

        with popular_columns[i]:

            if st.button(
                popular_query,
                use_container_width=True,
                key=f"home_popular_{i}",
            ):

                st.session_state["selected_query"] = (
                    popular_query
                )

                st.session_state["research_query"] = (
                    popular_query
                )

                st.session_state["page"] = "Research"

                st.rerun()


    # =====================================================
    # WHAT IS AROHA
    # =====================================================

    st.html(
        """
        <div class="home-section">

            <div class="home-section-label">
                WHAT IS AROHA?
            </div>

            <div class="home-section-title">
                Intelligence for what comes next.
            </div>

            <div class="home-section-copy">
                AROHA is an AI-powered trend intelligence
                system designed to move from information
                to insight — and from insight to action.
            </div>


            <div class="about-card">

                <div class="about-number">
                    AROHA / INTELLIGENCE ENGINE
                </div>

                <div class="about-heading">
                    From the noise of the web to signals
                    you can actually use.
                </div>

                <div class="about-text">

                    AROHA researches live information across
                    the web, identifies meaningful patterns,
                    interprets emerging signals and transforms
                    them into trends and opportunities.

                    From there, the intelligence can become
                    creative directions, visual concepts and
                    new possibilities to explore.

                </div>

            </div>

        </div>
        """
    )


    # =====================================================
    # HOW IT WORKS — AROHA INTELLIGENCE JOURNEY
    # =====================================================

    st.html(
        """
        <div class="aroha-process">

            <!-- ============================================
                 SECTION INTRO
            ============================================= -->

            <div class="process-label">
                HOW IT WORKS
            </div>

            <div class="process-title">
                One intelligence pipeline.
            </div>

            <div class="process-description">
                AROHA connects research, reasoning and creative
                generation into one continuous intelligence cycle.
            </div>


            <!-- ============================================
                 DISCOVERY
            ============================================= -->

            <div class="process-group-label">
                DISCOVER
            </div>


            <div class="process-row">

                <!-- RESEARCH -->

                <div class="process-node">

                    <div class="process-number">
                        01
                    </div>

                    <div class="process-icon">
                        ◌
                    </div>

                    <div class="process-name">
                        Research
                    </div>

                    <div class="process-copy">
                        Scan the live web and collect
                        relevant evidence.
                    </div>

                </div>


                <div class="process-arrow">
                    →
                </div>


                <!-- SIGNALS -->

                <div class="process-node">

                    <div class="process-number">
                        02
                    </div>

                    <div class="process-icon">
                        ≋
                    </div>

                    <div class="process-name">
                        Signals
                    </div>

                    <div class="process-copy">
                        Extract meaningful patterns
                        from the research.
                    </div>

                </div>


                <div class="process-arrow">
                    →
                </div>


                <!-- TRENDS -->

                <div class="process-node">

                    <div class="process-number">
                        03
                    </div>

                    <div class="process-icon">
                        ↗
                    </div>

                    <div class="process-name">
                        Trends
                    </div>

                    <div class="process-copy">
                        Identify emerging movements,
                        behaviors and patterns.
                    </div>

                </div>

            </div>


            <!-- ============================================
                 AROHA CORE
            ============================================= -->

            <div class="core-connector">
                ↓
            </div>


            <div class="aroha-core">

                <div class="core-orbit orbit-one"></div>

                <div class="core-orbit orbit-two"></div>

                <div class="core-symbol">
                    △
                </div>

                <div class="core-label">
                    AROHA
                </div>

                <div class="core-title">
                    Intelligence Engine
                </div>

                <div class="core-copy">
                    Connect · Reason · Discover
                </div>

            </div>


            <div class="core-connector">
                ↓
            </div>


            <!-- ============================================
                 OPPORTUNITY
            ============================================= -->

            <div class="opportunity-card">

                <div class="opportunity-glow"></div>

                <div class="opportunity-number">
                    04
                </div>

                <div class="opportunity-icon">
                    ◇
                </div>

                <div>

                    <div class="opportunity-label">
                        OPPORTUNITY
                    </div>

                    <div class="opportunity-title">
                        From signal to possibility.
                    </div>

                    <div class="opportunity-copy">
                        AROHA identifies where emerging trends
                        can create value, action and innovation.
                    </div>

                </div>

            </div>


            <!-- ============================================
                 CREATION
            ============================================= -->

            <div class="core-connector">
                ↓
            </div>


            <div class="process-group-label">
                CREATE
            </div>


            <div class="creation-row">

                <!-- CREATIVE -->

                <div class="creation-node">

                    <div class="process-number">
                        05
                    </div>

                    <div class="process-icon">
                        ✦
                    </div>

                    <div class="process-name">
                        Creative Directions
                    </div>

                    <div class="process-copy">
                        Turn intelligence into ideas,
                        concepts and creative directions.
                    </div>

                </div>


                <div class="process-arrow">
                    →
                </div>


                <!-- VISUALIZE -->

                <div class="creation-node">

                    <div class="process-number">
                        06
                    </div>

                    <div class="process-icon">
                        ◈
                    </div>

                    <div class="process-name">
                        Visualize
                    </div>

                    <div class="process-copy">
                        Transform concepts into
                        visual possibilities.
                    </div>

                </div>

            </div>

        </div>
        """
    )


    # =====================================================
    # EXPLORE DOMAINS
    # =====================================================

    st.html(
        """
        <div class="home-section">

            <div class="home-section-label">
                EXPLORE
            </div>

            <div class="home-section-title">
                Intelligence across domains.
            </div>

            <div class="home-section-copy">
                Explore emerging behavior, ideas and
                opportunities across different areas of
                culture and industry.
            </div>

        </div>
        """
    )


    category_columns = st.columns(6)


    categories = [

        ("Fashion", "Style, consumer behavior and aesthetics."),

        ("Technology", "Emerging technology and digital behavior."),

        ("Design", "Visual culture, spaces and product thinking."),

        ("Culture", "Ideas, communities and changing behavior."),

        ("Food", "Food culture, products and consumption."),

        ("Lifestyle", "New habits, experiences and everyday life."),

    ]


    for i, (
        category,
        description
    ) in enumerate(categories):

        with category_columns[i]:

            st.html(
                f"""
                <div class="capability-card">

                    <div class="capability-icon">
                        {"✦" if i % 2 == 0 else "◇"}
                    </div>

                    <div class="capability-title">
                        {category}
                    </div>

                    <div class="capability-copy">
                        {description}
                    </div>

                </div>
                """
            )

    # =========================================================
    # WHAT YOU CAN DISCOVER
    # =========================================================

    st.html(
        """
        <div class="home-section">

            <div class="home-section-label">
                WHAT YOU CAN DISCOVER
            </div>

            <div class="home-section-title">
                Intelligence that leads somewhere.
            </div>

            <div class="home-section-copy">
                AROHA turns emerging information into
                perspectives you can understand, opportunities
                you can explore and ideas you can act on.
            </div>

        </div>
        """
    )


    discovery_columns = st.columns(4)


    discoveries = [

        (
            "↗",
            "Emerging Trends",
            "See what is gaining momentum before it becomes obvious."
        ),

        (
            "◇",
            "Market Opportunities",
            "Discover spaces where changing behavior can create value."
        ),

        (
            "◎",
            "Consumer Behavior",
            "Understand how people, culture and preferences are shifting."
        ),

        (
            "✦",
            "Creative Possibilities",
            "Turn emerging intelligence into concepts and visual directions."
        ),

    ]


    for i, (
        icon,
        title,
        description
    ) in enumerate(discoveries):

        with discovery_columns[i]:

            st.html(
                f"""
                <div class="capability-card">

                    <div class="capability-icon">
                        {icon}
                    </div>

                    <div class="capability-title">
                        {title}
                    </div>

                    <div class="capability-copy">
                        {description}
                    </div>

                </div>
                """
            )

    # =====================================================
    # FINAL CTA
    # =====================================================

    st.html(
        """
        <div class="final-cta">

            <div class="home-section-label">
                BEGIN EXPLORING
            </div>

            <div class="final-cta-title">
                What will you discover next?
            </div>

            <div class="final-cta-copy">

                Ask AROHA a question about a market,
                behavior, culture, product or emerging trend
                and start an intelligence cycle.

            </div>

        </div>
        """
    )


    final_col1, final_col2, final_col3 = st.columns(
        [1.2, 2.4, 1.2]
    )


    with final_col2:

        if st.button(
            "◈   Explore Research  →",
            use_container_width=True,
            key="home_final_research",
        ):

            st.session_state["page"] = "Research"

            st.rerun()


# =========================================================
# RESEARCH PAGE

elif current_page == "Research":

    # =====================================================
    # AROHA RESEARCH → SIGNAL → TREND → OPPORTUNITY →
    # FINAL CONTEXT → VISUAL → IMAGE
    #
    # The backend already executes the complete pipeline.
    # This page renders the complete response in the SAME
    # PAGE and in the SAME ORDER.
    # =====================================================

    st.html(
        """
        <div class="section-title" style="margin-top:10px;">
            🔎 AROHA Research Intelligence
        </div>

        <div class="section-description">
            Research the live web, extract signals, connect them
            into emerging trends, identify opportunities and
            turn the intelligence into creative and visual concepts.
        </div>
        """
    )

    # -----------------------------------------------------
    # UI normalization helpers
    # -----------------------------------------------------

    import json
    import re

    def _as_list(value, key_candidates=None):
        """Accept lists, nested response dictionaries and JSON strings."""
        if value is None:
            return []

        if isinstance(value, list):
            return value

        if isinstance(value, dict):
            for key in (key_candidates or []):
                nested = value.get(key)
                if isinstance(nested, list):
                    return nested
            return []

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict):
                    for key in (key_candidates or []):
                        nested = parsed.get(key)
                        if isinstance(nested, list):
                            return nested
            except Exception:
                pass

        return []


    def _text(value, default=""):
        if value is None:
            return default
        if isinstance(value, (dict, list)):
            return str(value)
        return str(value).strip() or default


    def _is_source_label(value):
        return bool(
            value
            and re.match(
                r"^\s*source\s*[-_#]?\s*\d+\s*$",
                str(value),
                re.IGNORECASE,
            )
        )


    def _resolve_signal_source(signal, research_results):
        """Resolve a signal to the real research source without using 'Source 1' as a title."""
        source_url = _text(signal.get("source_url", ""))
        source_title = _text(signal.get("source_title", ""))
        source_index = signal.get(
            "source_index",
            signal.get(
                "source_number",
                signal.get("source_id", None),
            ),
        )

        if source_url:
            for idx, result in enumerate(research_results, start=1):
                if not isinstance(result, dict):
                    continue
                result_url = _text(result.get("url", ""))
                if result_url and result_url == source_url:
                    return (
                        idx,
                        _text(result.get("title", source_title or "Research source")),
                        result_url,
                    )

        try:
            if source_index is not None:
                numeric_index = int(source_index)
                if 1 <= numeric_index <= len(research_results):
                    result = research_results[numeric_index - 1]
                    if isinstance(result, dict):
                        return (
                            numeric_index,
                            _text(result.get("title", source_title or "Research source")),
                            _text(result.get("url", source_url)),
                        )
        except Exception:
            pass

        if source_title and not _is_source_label(source_title):
            return None, source_title, source_url

        return None, "Research evidence", source_url


    def _render_section_header(number, label, title, description):
        st.html(
            f"""
            <div style="
                margin-top:52px;
                margin-bottom:20px;
                padding:18px 20px;
                border-radius:16px;
                border:1px solid rgba(177,112,255,0.18);
                background:rgba(177,112,255,0.045);
            ">
                <div style="
                    color:#b979ff;
                    font-size:9px;
                    font-weight:800;
                    letter-spacing:2px;
                    margin-bottom:7px;
                ">
                    {number} · {html.escape(label.upper())}
                </div>
                <div style="
                    font-size:24px;
                    font-weight:750;
                    margin-bottom:6px;
                ">
                    {html.escape(title)}
                </div>
                <div style="
                    color:#8f8f9c;
                    font-size:11px;
                    line-height:1.6;
                ">
                    {html.escape(description)}
                </div>
            </div>
            """
        )


    # -----------------------------------------------------
    # Read the COMPLETE backend response
    # -----------------------------------------------------

    aroha_response = st.session_state.get("aroha_response", {})
    if not isinstance(aroha_response, dict):
        aroha_response = {}

    results = _as_list(
        aroha_response.get("results", []),
        ["results", "sources", "research_results"],
    )

    signals = _as_list(
        aroha_response.get("signals", []),
        ["signals", "trend_signals"],
    )

    trends = _as_list(
        aroha_response.get("trends", []),
        ["trends", "emerging_trends"],
    )

    opportunities = _as_list(
        aroha_response.get("opportunities", []),
        ["opportunities", "opportunity_intelligence"],
    )

    creative_directions = _as_list(
        aroha_response.get("creative_directions", []),
        ["creative_directions", "creative", "directions"],
    )

    visual_prompts = _as_list(
        aroha_response.get("visual_prompts", []),
        ["visual_prompts", "prompts", "visuals"],
    )

    generated_images = _as_list(
        aroha_response.get("generated_images", []),
        ["generated_images", "images"],
    )

    trend_images = _as_list(
        aroha_response.get("trend_images", []),
        ["trend_images", "images"],
    )


    # -----------------------------------------------------
    # =====================================================
    # STEP 01 — RESEARCH
    # The research workspace is deliberately decision-first:
    # raw evidence stays available behind compact evidence envelopes,
    # while the visible journey progressively compresses information.

    aroha_response = st.session_state.get("aroha_response", {})
    if not isinstance(aroha_response, dict):
        aroha_response = {}

    results = _as_list(aroha_response.get("results", []), ["results", "sources", "research_results"])
    signals = _as_list(aroha_response.get("signals", []), ["signals", "trend_signals"])
    trends = _as_list(aroha_response.get("trends", []), ["trends", "emerging_trends"])
    opportunities = _as_list(aroha_response.get("opportunities", []), ["opportunities", "opportunity_intelligence"])

    # -----------------------------------------------------
    # QUERY
    # -----------------------------------------------------
    research_query = st.text_input(
        "Research query",
        value=st.session_state.get("selected_query", st.session_state.get("research_query", "")),
        placeholder="What should AROHA investigate?",
        label_visibility="collapsed",
        key="research_page_query_v6",
    )

    if st.button("◈  Start Intelligence Cycle", use_container_width=True, key="research_page_button_v6"):
        if not research_query.strip():
            st.warning("Enter a research topic first.")
        else:
            try:
                with st.spinner("AROHA is reading the landscape and connecting the first patterns..."):
                    response = requests.post(
                        API_URL,
                        json={"query": research_query.strip(), "pipeline_mode": "trends_only", "generate_images": False},
                        timeout=900,
                    )
                    response.raise_for_status()
                    data = response.json()
                if not isinstance(data, dict) or data.get("status") != "success":
                    raise ValueError(data.get("message", "AROHA backend returned an invalid response."))
                st.session_state["aroha_response"] = data
                st.session_state["research_results"] = _as_list(data.get("results", []), ["results", "sources", "research_results"])
                st.session_state["research_query"] = research_query.strip()
                st.session_state["selected_query"] = research_query.strip()
                st.session_state["exploration_stage"] = "trends"
                st.session_state["selected_opportunity"] = None
                st.session_state["selected_opportunity_id"] = None
                st.session_state["creative_packages"] = {}
                st.session_state["exploration_message"] = ""
                st.rerun()
            except requests.exceptions.RequestException as error:
                st.error(f"Could not connect to AROHA backend: {error}")
            except Exception as error:
                st.error(f"AROHA research failed: {error}")

    # Refresh local references after a possible rerun/state update.
    aroha_response = st.session_state.get("aroha_response", {})
    results = _as_list(aroha_response.get("results", []), ["results", "sources", "research_results"])
    signals = _as_list(aroha_response.get("signals", []), ["signals", "trend_signals"])
    trends = _as_list(aroha_response.get("trends", []), ["trends", "emerging_trends"])
    opportunities = _as_list(aroha_response.get("opportunities", []), ["opportunities", "opportunity_intelligence"])
    trend_images = _as_list(aroha_response.get("trend_images", []), ["trend_images", "images"])

    # -----------------------------------------------------
    # DECISION RAIL
    # -----------------------------------------------------
    if aroha_response:
        stage = st.session_state.get("exploration_stage", "trends")
        active_index = {"trends": 3, "opportunities": 4, "creative": 5, "visuals": 5}.get(stage, 3)
        stages = [(1, "Research"), (2, "Signals"), (3, "Patterns"), (4, "Opportunities"), (5, "Creative"), (6, "Visual")]
        rail = []
        for number, name in stages:
            state = "complete" if number < active_index else ("active" if number == active_index else "future")
            icon = "✓" if state == "complete" else ("●" if state == "active" else "○")
            rail.append(f'<div class="aroha-rail-item {state}"><span>{icon}</span><small>{html.escape(name)}</small></div>')
        st.html(f'<div class="aroha-stage" style="display:flex;gap:8px;flex-wrap:wrap;margin:20px 0 28px;padding:8px 4px;">{"".join(rail)}</div>')

    def _source_meta(signal):
        source_url = _text(signal.get("source_url", ""))
        source_title = _text(signal.get("source_title", ""))
        source_image = _text(signal.get("source_image_url", ""))
        if not source_image and source_url:
            for result in results:
                if isinstance(result, dict) and _text(result.get("url", "")) == source_url:
                    source_image = _text(result.get("source_image_url", ""))
                    if not source_title:
                        source_title = _text(result.get("title", ""))
                    break
        return source_title or "Research evidence", source_url, source_image

    def _evidence_envelope(title, url, image_url, label="EVIDENCE"):
        title = title or "Research evidence"
        if image_url:
            media = f'<img src="{html.escape(image_url, quote=True)}" alt="Research evidence" style="width:100%;height:155px;object-fit:cover;border-radius:13px;display:block;">'
        else:
            media = '<div class="aroha-visual-empty" style="min-height:155px;height:155px;">No reference visual</div>'
        link = f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer" style="color:#b979ff;text-decoration:none;font-weight:700;">Open original ↗</a>' if url else '<span class="aroha-quiet">Original source unavailable</span>'
        return f'''<div class="aroha-evidence-envelope" style="border:1px solid rgba(183,119,255,.18);border-radius:16px;padding:12px;background:rgba(255,255,255,.025);">{media}<div style="margin-top:10px;color:#b979ff;font-size:8px;font-weight:800;letter-spacing:1.5px;">{html.escape(label)}</div><div style="font-size:13px;font-weight:700;margin-top:4px;line-height:1.4;">{html.escape(title[:110])}</div><div style="margin-top:8px;font-size:10px;">{link}</div></div>'''

    # -----------------------------------------------------
    # SIGNALS
    # -----------------------------------------------------
    if aroha_response:
        _render_section_header("02", "Decode", "Signals that matter", "AROHA compresses the web into the strongest observable shifts. The evidence stays one click away.")
        if signals:
            for index, signal in enumerate(signals, start=1):
                if not isinstance(signal, dict):
                    continue
                theme = _text(signal.get("theme", ""))
                title = _text(signal.get("subject", signal.get("title", "")))
                key_signal = _text(signal.get("key_signal", signal.get("signal", "")))
                observation = _text(signal.get("observation", ""))
                concepts = signal.get("recurring_concepts", [])
                if not isinstance(concepts, list): concepts = [concepts]
                title = title if title and not _is_source_label(title) else (theme or key_signal[:80] or "Signal")
                source_title, source_url, source_image = _source_meta(signal)
                evidence_card = _evidence_envelope(source_title, source_url, source_image, "VISUAL EVIDENCE")
                bullets = [x for x in concepts[:3] if _text(x)]
                bullet_html = "".join(f'<li>{html.escape(_text(x))}</li>' for x in bullets)
                st.html(f'''<div class="aroha-card aroha-reveal" style="--delay:{min(index-1,7)*70}ms;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:22px;border:1px solid rgba(183,119,255,.18);border-radius:20px;padding:22px;margin:18px 0;background:rgba(13,14,22,.52);"><div class="aroha-theory"><div class="aroha-kicker">SIGNAL DISCOVERY</div><div style="font-size:28px;font-weight:760;line-height:1.14;margin-bottom:13px;">{html.escape(title)}</div><div class="aroha-key">{html.escape(key_signal)}</div>{f'<div class="aroha-body"><b>What changed</b><br>{html.escape(observation)}</div>' if observation else ''}{f'<div style="margin-top:12px;font-size:12px;color:#aaa8b5;"><b>Patterns:</b> {html.escape(" · ".join(_text(x) for x in bullets))}</div>' if bullets else ''}</div><div>{evidence_card}</div></div>''')
        else:
            st.warning("AROHA could not establish reliable signals from this research cycle.")

    # -----------------------------------------------------
    # EMERGING TRENDS
    # -----------------------------------------------------
    if aroha_response:
        _render_section_header("03", "Connect", "Emerging patterns", "Signals become trends only when AROHA can connect them into an evidence-backed change worth watching.")
        if trends:
            signal_lookup = {i + 1: s for i, s in enumerate(signals) if isinstance(s, dict)}
            for index, trend in enumerate(trends, start=1):
                if not isinstance(trend, dict): continue
                title = _text(trend.get("trend", trend.get("title", trend.get("name", ""))))
                description = _text(trend.get("description", trend.get("summary", "")))
                why = _text(trend.get("why_it_matters", trend.get("rationale", "")))
                confidence = trend.get("confidence", None)
                ids = trend.get("supporting_signal_ids", trend.get("signal_ids", []))
                if not isinstance(ids, list): ids = [ids]
                source_cards=[]
                seen_urls=set()
                for sid in ids:
                    try: sig = signal_lookup.get(int(sid))
                    except (TypeError,ValueError): sig=None
                    if not isinstance(sig,dict): continue
                    stitle,surl,simage=_source_meta(sig)
                    if surl in seen_urls: continue
                    seen_urls.add(surl)
                    source_cards.append(_evidence_envelope(stitle,surl,simage,"SUPPORTING EVIDENCE"))
                    if len(source_cards)>=2: break
                generated = trend_images[index-1] if index-1 < len(trend_images) and isinstance(trend_images[index-1],dict) else {}
                generated_path = _text(generated.get("image_path", generated.get("path", "")))
                if generated_path and not Path(generated_path).is_file():
                    candidate=BASE_DIR/generated_path
                    generated_path=str(candidate) if candidate.is_file() else generated_path
                if generated_path and Path(generated_path).is_file():
                    visual = f'<div class="aroha-visual-label">AI TREND VISUALIZATION</div><img src="data:image/webp;base64,{base64.b64encode(Path(generated_path).read_bytes()).decode()}" alt="AI visualization of trend" style="width:100%;height:330px;object-fit:cover;border-radius:16px;display:block;"><div class="aroha-meta" style="margin-top:8px;">AI visualization — designed to make the pattern tangible, not to serve as evidence.</div>'
                else:
                    visual = '<div class="aroha-visual-empty">Trend visualization unavailable</div>'
                evidence_row = ''.join(source_cards)
                if evidence_row:
                    evidence_row = f'<div style="margin-top:12px;display:grid;grid-template-columns:1fr 1fr;gap:10px;">{evidence_row}</div>'
                st.html(f'''<div class="aroha-card aroha-reveal" style="--delay:{min(index-1,7)*80}ms;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:22px;border:1px solid rgba(183,119,255,.20);border-radius:20px;padding:22px;margin:20px 0;background:rgba(16,14,25,.56);"><div class="aroha-theory"><div class="aroha-kicker">EMERGING PATTERN</div><div style="font-size:30px;font-weight:760;line-height:1.14;margin-bottom:14px;">{html.escape(title)}</div>{f'<div class="aroha-key">{html.escape(description)}</div>' if description else ''}{f'<div class="aroha-why"><div style="color:#b979ff;font-size:9px;font-weight:800;letter-spacing:1.4px;margin-bottom:7px;">WHY IT MATTERS</div><div style="font-size:14px;line-height:1.55;">{html.escape(why)}</div></div>' if why else ''}<div class="aroha-meta">{f'Confidence · {html.escape(str(confidence))}/10' if confidence is not None else 'Evidence-backed pattern'} </div>{evidence_row}</div><div>{visual}</div></div>''')
        else:
            st.warning("AROHA did not find enough validated convergence to call an emerging trend.")

        st.html('''<div class="aroha-next-decision aroha-decision"><div style="color:#b979ff;font-size:9px;font-weight:800;letter-spacing:1.8px;margin-bottom:7px;">NEXT MOVE</div><div style="font-size:23px;font-weight:740;">Turn the patterns into opportunity spaces.</div><div class="aroha-muted" style="font-size:12px;margin-top:7px;">AROHA will now separate the trend from the possible action — no premature product ideas.</div></div>''')
        if st.button("💡  Discover Opportunity Spaces", use_container_width=True, key="explore_opportunities_v6"):
            try:
                with st.spinner("AROHA is asking where the strongest unmet potential sits..."):
                    response=requests.post("http://127.0.0.1:5000/api/opportunities",json={"trends":trends},timeout=300)
                    response.raise_for_status(); data=response.json()
                if data.get("status")!="success": raise ValueError(data.get("message","Opportunity exploration failed."))
                st.session_state["aroha_response"]["opportunities"]=data.get("opportunities",[])
                st.session_state["selected_opportunity"]=None
                st.session_state["selected_opportunity_id"]=None
                st.session_state["creative_packages"]={}
                st.session_state["exploration_stage"]="opportunities"
                st.session_state["exploration_message"]=""
                st.rerun()
            except Exception as error:
                st.error(f"Opportunity exploration failed: {error}")

    # -----------------------------------------------------
    # OPPORTUNITIES
    # -----------------------------------------------------
    if aroha_response and st.session_state.get("exploration_stage") in {"opportunities","creative","visuals"}:
        _render_section_header("04", "Act", "Opportunity spaces", "These are the gaps worth acting on — not finished products. Choose one to move into creative strategy.")
        if opportunities:
            for index, opportunity in enumerate(opportunities, start=1):
                if not isinstance(opportunity,dict): continue
                title=_text(opportunity.get("title",opportunity.get("name",f"Opportunity {index}")))
                description=_text(opportunity.get("description",opportunity.get("opportunity", "")))
                rationale=_text(opportunity.get("rationale",opportunity.get("reason", "")))
                score=opportunity.get("overall_score",opportunity.get("opportunity_score",opportunity.get("score",None)))
                unmet=_text(opportunity.get("unmet_need",opportunity.get("opportunity_space", "")))
                score_html=f'<span style="padding:7px 10px;border-radius:999px;background:rgba(183,119,255,.10);color:#c999ff;font-weight:800;">{html.escape(str(score))}/10</span>' if score is not None else ''
                st.html(f'''<div class="aroha-opportunity-card aroha-reveal" style="--delay:{min(index-1,7)*80}ms;border:1px solid rgba(183,119,255,.20);border-radius:20px;padding:22px;margin:18px 0;background:rgba(13,14,22,.45);"><div style="display:flex;justify-content:space-between;gap:15px;align-items:flex-start;"><div><div class="aroha-kicker">OPPORTUNITY SPACE</div><div style="font-size:27px;font-weight:760;line-height:1.15;">{html.escape(title)}</div></div>{score_html}</div><div style="font-size:16px;line-height:1.58;margin-top:13px;color:#c4c2cc;">{html.escape(description)}</div>{f'<div style="margin-top:12px;font-size:12px;color:#aaa8b5;"><b>Unmet potential:</b> {html.escape(unmet)}</div>' if unmet else ''}{f'<div style="margin-top:12px;font-size:12px;color:#aaa8b5;"><b>Why now:</b> {html.escape(rationale)}</div>' if rationale else ''}</div>''')
                if st.button("✦  Explore this opportunity", use_container_width=True, key=f"opportunity_creative_v6_{index}"):
                    try:
                        with st.spinner("AROHA is turning this opportunity into a creative direction and visual concept..."):
                            response=requests.post("http://127.0.0.1:5000/api/creative",json={"selected_opportunity":opportunity},timeout=900)
                            response.raise_for_status(); data=response.json()
                        if data.get("status")!="success": raise ValueError(data.get("message","Creative generation failed."))
                        opportunity_id=data.get("opportunity_id")
                        if not opportunity_id: raise ValueError("Creative package did not return an opportunity ID.")
                        st.session_state["selected_opportunity"]=opportunity
                        st.session_state["selected_opportunity_id"]=opportunity_id
                        st.session_state["creative_packages"][opportunity_id]={"creative_directions":data.get("creative_directions",[]),"visual_prompts":data.get("visual_prompts",[]),"generated_images":data.get("generated_images",[]),"image_errors":data.get("image_errors",[])}
                        st.session_state["exploration_stage"]="visuals"
                        st.session_state["exploration_message"]=""
                        st.rerun()
                    except Exception as error:
                        st.error(f"Creative research failed: {error}")
        else:
            st.warning("No opportunity spaces were returned.")

    # -----------------------------------------------------
    # CREATIVE + VISUAL
    # -----------------------------------------------------
    if aroha_response and st.session_state.get("exploration_stage") in {"creative","visuals"}:
        _render_section_header("05", "Create", "Creative direction", "A selected opportunity becomes a small set of distinct creative territories. The strongest visual concept sits beside the strategy.")
        selected=st.session_state.get("selected_opportunity") or {}
        selected_id=st.session_state.get("selected_opportunity_id")
        package=st.session_state.get("creative_packages",{}).get(selected_id,{})
        directions=package.get("creative_directions",[]) if isinstance(package,dict) else []
        prompts=package.get("visual_prompts",[]) if isinstance(package,dict) else []
        images=package.get("generated_images",[]) if isinstance(package,dict) else []
        selected_title=_text(selected.get("title",selected.get("name","Selected opportunity"))) if isinstance(selected,dict) else "Selected opportunity"
        st.html(f'''<div class="aroha-stage" style="padding:14px 18px;margin:8px 0 18px;border-radius:15px;border:1px solid rgba(183,119,255,.20);background:rgba(183,119,255,.06);"><span style="color:#b979ff;font-size:9px;font-weight:800;letter-spacing:1.5px;">SELECTED OPPORTUNITY</span><span style="margin-left:10px;font-size:15px;font-weight:700;">{html.escape(selected_title)}</span></div>''')
        if directions:
            for index,direction in enumerate(directions,start=1):
                if not isinstance(direction,dict): direction={"name":f"Creative direction {index}","concept":_text(direction)}
                title=_text(direction.get("title",direction.get("name",f"Creative direction {index}")))
                concept=_text(direction.get("concept",direction.get("description", "")))
                direction_text=_text(direction.get("creative_direction",direction.get("direction", "")))
                target=_text(direction.get("target_audience", ""))
                rationale=_text(direction.get("rationale",direction.get("reason", "")))
                visual=prompts[index-1] if index-1<len(prompts) and isinstance(prompts[index-1],dict) else {}
                visual_name=_text(visual.get("name",title))
                visual_prompt=_text(visual.get("visual_prompt",visual.get("prompt", "")))
                image=images[index-1] if index-1<len(images) and isinstance(images[index-1],dict) else {}
                image_path=_text(image.get("image_path",image.get("path", "")))
                image_file=Path(image_path) if image_path else None
                if image_file and not image_file.is_file():
                    candidate=BASE_DIR/image_path
                    image_file=candidate if candidate.is_file() else image_file
                left,right=st.columns([1,1],gap="large")
                with left:
                    parts=[f'<div class="aroha-kicker">CREATIVE TERRITORY {index:02d}</div>',f'<div style="font-size:27px;font-weight:760;line-height:1.15;margin-bottom:14px;">{html.escape(title)}</div>']
                    for label,value in [("The idea",concept),("Audience",target),("Why it works",rationale),("Creative move",direction_text)]:
                        if value: parts.append(f'<div style="margin:0 0 12px;font-size:15px;line-height:1.55;"><b>{label}</b><br>{html.escape(value)}</div>')
                    st.html(f'<div class="aroha-creative-panel aroha-reveal" style="--delay:{min(index-1,7)*90}ms;min-height:390px;border:1px solid rgba(183,119,255,.20);border-radius:18px;padding:23px;background:rgba(18,15,28,.64);">{"".join(parts)}</div>')
                with right:
                    st.html(f'<div class="aroha-creative-panel aroha-reveal" style="--delay:{min(index-1,7)*90+60}ms;border:1px solid rgba(183,119,255,.20);border-radius:18px 18px 0 0;padding:17px 18px;background:rgba(18,15,28,.64);"><div class="aroha-kicker">GENERATED CONCEPT</div><div style="font-size:17px;font-weight:700;">{html.escape(visual_name)}</div></div>')
                    if image_file and image_file.is_file():
                        st.image(str(image_file),use_container_width=True)
                    elif image_path.startswith(("http://","https://")):
                        st.image(image_path,use_container_width=True)
                    else:
                        st.html('<div class="aroha-visual-empty">Visual concept unavailable</div>')
                    if visual_prompt:
                        with st.expander("View visual prompt"):
                            st.write(visual_prompt)
                    if index==len(directions) and package.get("image_errors"):
                        errors=package.get("image_errors",[])
                        st.caption(f"{len(errors)} visual generation issue{'s' if len(errors)!=1 else ''} recorded. AROHA kept the strategy available while the visual step was incomplete.")
        else:
            st.warning("No creative directions were returned for this opportunity.")

        # -------------------------------------------------
        # AROHA SIGNATURE ENDING
        # -------------------------------------------------
        st.html(f'''<div class="aroha-stage" style="margin:52px 0 20px;padding:42px 28px;border-radius:26px;border:1px solid rgba(183,119,255,.24);background:radial-gradient(circle at 75% 20%,rgba(183,119,255,.16),transparent 38%),linear-gradient(145deg,rgba(25,19,36,.92),rgba(9,9,16,.96));text-align:center;overflow:hidden;"><div style="color:#b979ff;font-size:9px;font-weight:800;letter-spacing:2.5px;margin-bottom:12px;">AROHA / THE NEXT MOVE</div><div style="font-size:clamp(32px,5vw,54px);font-weight:820;letter-spacing:-2px;line-height:1.02;">Make it good, KJ.</div><div style="max-width:620px;margin:14px auto 0;color:#b9b5c2;font-size:15px;line-height:1.65;">The research is only the beginning. You now have a signal, a pattern, an opportunity and a visual direction worth turning into something real.</div><div style="margin-top:18px;color:#d8c4ff;font-size:12px;font-weight:700;letter-spacing:.8px;">DISCOVER → DECIDE → CREATE → MAKE IT REAL</div><div style="margin-top:12px;color:#8f899b;font-size:10px;">Your strategy is ready. Visual generation status is shown above; AROHA never reuses an old image silently.</div></div>''')

    if not aroha_response:
        st.html('''<div class="empty-state aroha-stage"><div class="empty-title">AROHA is ready.</div><div class="empty-copy">Start with a question. AROHA will turn live research into signals, patterns, opportunity spaces and visual concepts.</div></div>''')



# SIGNALS PAGE

# =========================================================

elif current_page == "Signals":


    st.html(
        """
        <div class="section-title"
            style="margin-top:10px;">

            📈 Trend Signals

        </div>

        <div class="section-description">

            Structured signals extracted from AROHA's
            web research evidence.

        </div>
        """
    )


    # ---------------------------------------------------------
    # Get signals from the latest AROHA research response
    # ---------------------------------------------------------

    aroha_response = st.session_state.get(
        "aroha_response",
        {}
    )

    signals = aroha_response.get(
        "signals",
        []
    )


    # ---------------------------------------------------------
    # Display signals
    # ---------------------------------------------------------

    if signals:

        st.success(
            f"AROHA extracted {len(signals)} trend signal"
            f"{'s' if len(signals) != 1 else ''}."
        )


        for index, signal in enumerate(
            signals,
            start=1
        ):

            if not isinstance(signal, dict):
                continue


            subject = signal.get(
                "subject",
                "Untitled Signal"
            )

            theme = signal.get(
                "theme",
                "Not available"
            )

            style = signal.get(
                "style",
                "Not available"
            )

            key_signal = signal.get(
                "key_signal",
                "No key signal available."
            )

            source_title = signal.get(
                "source_title",
                "Source unavailable"
            )

            source_url = signal.get(
                "source_url",
                ""
            )

            source_image_url = signal.get(
                "source_image_url",
                ""
            )

            if not source_image_url and source_url:
                for result in aroha_response.get("results", []):
                    if isinstance(result, dict) and result.get("url") == source_url:
                        source_image_url = result.get("source_image_url", "")
                        break

            recurring_concepts = signal.get(
                "recurring_concepts",
                []
            )


            # -------------------------------------------------
            # Signal Card
            # -------------------------------------------------

            st.html(
                f"""
                <div style="
                    border:1px solid rgba(128,128,128,0.25);
                    border-radius:16px;
                    padding:22px;
                    margin:18px 0;
                ">

                    <div style="
                        font-size:13px;
                        opacity:0.65;
                        margin-bottom:8px;
                    ">
                        SIGNAL {index}
                    </div>

                    <div style="
                        font-size:22px;
                        font-weight:700;
                        margin-bottom:14px;
                    ">
                        {subject}
                    </div>

                    <div style="
                        margin-bottom:10px;
                    ">
                        <b>Theme:</b> {theme}
                    </div>

                    <div style="
                        margin-bottom:10px;
                    ">
                        <b>Style:</b> {style}
                    </div>

                    <div style="
                        margin-top:16px;
                        margin-bottom:16px;
                    ">
                        <b>Key Signal</b>

                        <div style="
                            margin-top:7px;
                            padding:12px;
                            border-radius:10px;
                            background:rgba(128,128,128,0.08);
                        ">
                            {key_signal}
                        </div>

                    </div>

                """
                +
                (
                    f"""
                    <div style="
                        margin-top:12px;
                    ">
                        <b>Recurring Concepts:</b>

                        <div style="
                            margin-top:7px;
                            line-height:1.8;
                        ">
                            {" • ".join(str(x) for x in recurring_concepts)}
                        </div>

                    </div>
                    """
                    if recurring_concepts
                    else ""
                )
                +
                (
                    f"""
                    <div style="margin-top:18px;">
                        <div style="
                            font-size:9px;
                            font-weight:800;
                            letter-spacing:1.5px;
                            color:#b979ff;
                            margin-bottom:8px;
                        ">SOURCE VISUAL</div>
                        <img
                            src="{html.escape(str(source_image_url), quote=True)}"
                            alt="Original visual from source webpage"
                            style="
                                width:100%;
                                max-height:360px;
                                object-fit:cover;
                                border-radius:12px;
                                display:block;
                            "
                        >
                        <div style="margin-top:6px;font-size:9px;opacity:0.55;">Original reference visual from the supporting webpage.</div>
                    </div>
                    """
                    if source_image_url
                    else
                    """
                    <div style="
                        margin-top:18px;
                        padding:16px;
                        border-radius:12px;
                        border:1px dashed rgba(255,255,255,0.10);
                        color:#777784;
                        font-size:11px;
                    >
                        No reference image available for this source.
                    </div>
                    """
                )
                +
                (
                    f"""
                    <div style="
                        margin-top:16px;
                        font-size:13px;
                        opacity:0.7;
                    ">

                        <b>Source:</b> {source_title}

                        <br>

                        <a
                            href="{source_url}"
                            target="_blank"
                            style="
                                word-break:break-all;
                            "
                        >
                            {source_url}
                        </a>

                    </div>
                    """
                    if source_url
                    else
                    f"""
                    <div style="
                        margin-top:16px;
                        font-size:13px;
                        opacity:0.7;
                    ">
                        <b>Source:</b> {source_title}
                    </div>
                    """
                )
                +
                """
                </div>
                """
            )

    else:

        st.html(
            """
            <div class="empty-state">

                <div class="empty-title">
                    Signal engine is waiting.
                </div>

                <div class="empty-copy">

                    Run web research first. AROHA will then
                    convert collected evidence into structured
                    trend signals.

                </div>

            </div>
            """
        )


# =========================================================
# TRENDS PAGE
# =========================================================

elif current_page == "Trends":

    st.html(
        """
        <div class="section-title"
             style="margin-top:10px;">

            ↗ Emerging Trends

        </div>

        <div class="section-description">

            Trends detected by AROHA by connecting
            multiple signals from the research evidence.

        </div>
        """
    )

    # -----------------------------------------------------
    # GET TRENDS FROM AROHA RESPONSE
    # -----------------------------------------------------

    aroha_response = st.session_state.get(
        "aroha_response",
        {}
    )

    trends = aroha_response.get(
        "trends",
        []
    )

    # -----------------------------------------------------
    # DISPLAY TRENDS
    # -----------------------------------------------------

    if trends:

        st.success(
            f"AROHA detected {len(trends)} "
            f"emerging trend{'s' if len(trends) != 1 else ''}."
        )

        for index, trend in enumerate(
            trends,
            start=1
        ):

            if not isinstance(trend, dict):
                continue

            title = trend.get(
                "title",
                trend.get(
                    "name",
                    f"Emerging Trend {index}"
                )
            )

            description = trend.get(
                "description",
                trend.get(
                    "trend",
                    trend.get(
                        "summary",
                        "No trend description available."
                    )
                )
            )

            rationale = trend.get(
                "rationale",
                trend.get(
                    "reason",
                    trend.get(
                        "why",
                        ""
                    )
                )
            )

            signals_used = trend.get(
                "signals",
                trend.get(
                    "supporting_signals",
                    []
                )
            )

            confidence = trend.get(
                "confidence",
                trend.get(
                    "score",
                    None
                )
            )

            # -------------------------------------------------
            # TREND CARD
            # -------------------------------------------------

            st.html(
                f"""
                <div style="
                    position:relative;
                    overflow:hidden;

                    border:1px solid rgba(180,119,255,0.24);
                    border-radius:20px;

                    padding:28px;

                    margin:20px 0;

                    background:
                        linear-gradient(
                            135deg,
                            rgba(24,19,39,0.94),
                            rgba(10,11,18,0.82)
                        );

                    box-shadow:
                        0 18px 50px rgba(0,0,0,0.20);
                ">

                    <div style="
                        color:#b979ff;
                        font-size:9px;
                        font-weight:800;
                        letter-spacing:2px;
                        margin-bottom:10px;
                    ">
                        EMERGING TREND {index:02d}
                    </div>

                    <div style="
                        font-size:25px;
                        font-weight:750;
                        margin-bottom:15px;
                    ">
                        {html.escape(str(title))}
                    </div>

                    <div style="
                        color:#bdbdc8;
                        font-size:13px;
                        line-height:1.75;
                        margin-bottom:20px;
                    ">
                        {html.escape(str(description))}
                    </div>

                    {
                        f'''
                        <div style="
                            padding:15px;
                            border-radius:12px;
                            background:rgba(180,119,255,0.07);
                            border:1px solid rgba(180,119,255,0.12);
                            margin-bottom:15px;
                        ">

                            <div style="
                                color:#b979ff;
                                font-size:9px;
                                font-weight:800;
                                letter-spacing:1.5px;
                                margin-bottom:7px;
                            ">
                                WHY THIS IS A TREND
                            </div>

                            <div style="
                                color:#9999a7;
                                font-size:11px;
                                line-height:1.65;
                            ">
                                {html.escape(str(rationale))}
                            </div>

                        </div>
                        '''
                        if rationale
                        else ""
                    }

                    {
                        f'''
                        <div style="
                            margin-top:12px;
                            color:#8e8e9b;
                            font-size:11px;
                        ">
                            <b>Supporting Signals:</b>
                            {len(signals_used)
                             if isinstance(signals_used, list)
                             else signals_used}
                        </div>
                        '''
                        if signals_used
                        else ""
                    }

                    {
                        f'''
                        <div style="
                            margin-top:10px;
                            color:#8e8e9b;
                            font-size:11px;
                        ">
                            <b>Confidence:</b> {confidence}
                        </div>
                        '''
                        if confidence is not None
                        else ""
                    }

                </div>
                """
            )

    else:

        st.html(
            """
            <div class="empty-state">

                <div class="empty-title">
                    Trend engine is waiting.
                </div>

                <div class="empty-copy">

                    Run web research first. Once signals are
                    extracted, AROHA will connect those signals
                    into emerging trends.

                </div>

            </div>
            """
        )


# =========================================================
# OPPORTUNITIES PAGE
# =========================================================

elif current_page == "Opportunities":

    st.html(
        """
        <div class="section-title"
             style="margin-top:10px;">

            🎯 Opportunity Intelligence

        </div>

        <div class="section-description">

            Actionable opportunities identified from
            AROHA's detected trends and signals.

        </div>
        """
    )


    # ---------------------------------------------------------
    # Get opportunities from the latest AROHA response
    # ---------------------------------------------------------

    aroha_response = st.session_state.get(
        "aroha_response",
        {}
    )

    opportunities = aroha_response.get(
        "opportunities",
        []
    )


    # ---------------------------------------------------------
    # Display opportunities
    # ---------------------------------------------------------

    if opportunities:

        st.success(
            f"AROHA identified {len(opportunities)} "
            f"opportunit{'y' if len(opportunities) == 1 else 'ies'}."
        )


        for index, opportunity in enumerate(
            opportunities,
            start=1
        ):

            if not isinstance(
                opportunity,
                dict
            ):
                continue


            title = opportunity.get(
                "title",
                opportunity.get(
                    "name",
                    f"Opportunity {index}"
                )
            )

            description = opportunity.get(
                "description",
                opportunity.get(
                    "opportunity",
                    "No description available."
                )
            )

            score = opportunity.get(
                "score",
                opportunity.get(
                    "opportunity_score",
                    None
                )
            )

            rationale = opportunity.get(
                "rationale",
                opportunity.get(
                    "reason",
                    ""
                )
            )


            # -------------------------------------------------
            # Opportunity Card
            # -------------------------------------------------

            st.html(
                f"""
                <div style="
                    border:1px solid rgba(128,128,128,0.25);
                    border-radius:16px;
                    padding:22px;
                    margin:18px 0;
                ">

                    <div style="
                        font-size:13px;
                        opacity:0.65;
                        margin-bottom:8px;
                    ">
                        OPPORTUNITY {index}
                    </div>

                    <div style="
                        font-size:22px;
                        font-weight:700;
                        margin-bottom:14px;
                    ">
                        {title}
                    </div>

                    <div style="
                        margin-bottom:14px;
                        line-height:1.6;
                    ">
                        {description}
                    </div>

                    {
                        f'''
                        <div style="
                            margin-top:12px;
                            margin-bottom:12px;
                        ">
                            <b>Opportunity Score:</b> {score}
                        </div>
                        '''
                        if score is not None
                        else ""
                    }

                    {
                        f'''
                        <div style="
                            margin-top:12px;
                            line-height:1.6;
                        ">

                            <b>Why it matters:</b>

                            <div style="
                                margin-top:6px;
                            ">
                                {rationale}
                            </div>

                        </div>
                        '''
                        if rationale
                        else ""
                    }

                </div>
                """
            )


    else:

        st.html(
            """
            <div class="empty-state">

                <div class="empty-title">
                    Opportunity engine is waiting.
                </div>

                <div class="empty-copy">

                    Complete web research first, then AROHA
                    can identify actionable opportunities.

                </div>

            </div>
            """
        )

#==========================================================
# CREATIVE STUDIO
# =========================================================

elif current_page == "Creative Studio":

    st.html(
        """
        <div class="section-title"
             style="margin-top:10px;">

            ✦ Creative Studio

        </div>

        <div class="section-description">

            Transform trend intelligence into creative
            directions, concepts and visual opportunities.

        </div>
        """
    )


    if st.session_state["research_results"]:

        st.success(
            "Trend research is ready for creative generation."
        )

        st.info(
            "Next integration: Creative Direction → "
            "Visual Prompt Generator → FLUX."
        )

    else:

        st.html(
            """
            <div class="empty-state">

                <div class="empty-title">
                    Creative Studio is ready.
                </div>

                <div class="empty-copy">

                    Start by researching a trend. AROHA will
                    then turn the intelligence into creative
                    directions and visual concepts.

                </div>

            </div>
            """
        )


# =========================================================
# SAVED INSIGHTS
# =========================================================

elif current_page == "Saved Insights":

    st.html(
        """
        <div class="section-title"
             style="margin-top:10px;">

            ◇ Saved Insights

        </div>

        <div class="section-description">

            Your important trend discoveries will appear here.

        </div>

        <div class="empty-state">

            <div class="empty-title">
                Nothing saved yet.
            </div>

            <div class="empty-copy">

                Saved trend intelligence will eventually
                be available here.

            </div>

        </div>
        """
    )


# =========================================================
# HISTORY
# =========================================================

elif current_page == "History":

    st.html(
        """
        <div class="section-title"
             style="margin-top:10px;">

            ◷ Research History

        </div>

        <div class="section-description">

            Previously explored trend topics will appear here.

        </div>
        """
    )


    if st.session_state.get(
        "research_query"
    ):

        st.html(
            f"""
            <div class="result-card">

                <div class="result-number">
                    RECENT RESEARCH
                </div>

                <div class="result-title">

                    {html.escape(
                        st.session_state["research_query"]
                    )}

                </div>

            </div>
            """
        )


    else:

        st.html(
            """
            <div class="empty-state">

                <div class="empty-title">
                    No research history yet.
                </div>

                <div class="empty-copy">

                    Your explored trends will appear here
                    after you start researching.

                </div>

            </div>
            """
        )


# =========================================================
# CONSTANT FOOTER — PRESENT ON EVERY AROHA PAGE
# =========================================================

st.html(
    """
    <div class="aroha-footer-wrap">
        <div class="aroha-footer-brand">AROHA · TREND INTELLIGENCE</div>
        <div class="aroha-footer-copy">
            From live research to meaningful signals, opportunity spaces and creative possibilities.
        </div>
        <div style="margin-top:15px;color:#777482;font-size:10px;line-height:1.6;">
            About AROHA · Evidence & Sources · Contact & Info are available through the footer controls below.
        </div>
        <div class="aroha-footer-note">
            AROHA is an intelligence workspace — evidence first, action next.
        </div>
    </div>
    """
)

# Small functional navigation row: keeps the footer useful without competing with the main workspace.
footer_cols = st.columns(5)
with footer_cols[0]:
    if st.button("⌂  Home", key="footer_home", use_container_width=True):
        st.session_state["page"] = "Home"
        st.rerun()
with footer_cols[1]:
    if st.button("⌕  Research", key="footer_research", use_container_width=True):
        st.session_state["page"] = "Research"
        st.rerun()
with footer_cols[2]:
    if st.button("✦  Opportunities", key="footer_opportunities", use_container_width=True):
        st.session_state["page"] = "Opportunities"
        st.rerun()
with footer_cols[3]:
    if st.button("◌  Creative Studio", key="footer_creative", use_container_width=True):
        st.session_state["page"] = "Creative Studio"
        st.rerun()
with footer_cols[4]:
    with st.popover("ⓘ  Contact & Info", use_container_width=True):
        st.markdown("### AROHA")
        st.caption("Trend Intelligence · Opportunity Discovery · Creative Visualization")
        st.markdown("**Evidence:** source URLs remain available from evidence cards.  \n**Visuals:** current-session FLUX output is never silently replaced with an older image.  \n**Version:** v7 · Intelligence & Experience Polish")