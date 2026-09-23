import streamlit as st
import os
import base64

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="MINEGUARD AI",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# BACKGROUND IMAGE
# =========================================================

BG_FILE = "rover_bg.png"

if os.path.exists(BG_FILE):
    with open(BG_FILE, "rb") as f:
        bg_data = base64.b64encode(f.read()).decode()

    background = f"data:image/png;base64,{bg_data}"
else:
    background = ""


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    f"""
    <style>

    /* =====================================================
       MAIN APP BACKGROUND
       ===================================================== */

    .stApp {{
        background:
            linear-gradient(
                rgba(2, 15, 28, 0.90),
                rgba(2, 15, 28, 0.95)
            ),
            url("{background}");

        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}


    /* =====================================================
       STREAMLIT TOP HEADER
       ===================================================== */

    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}

    [data-testid="stAppViewContainer"] {{
        padding-top: 0 !important;
    }}


    /* =====================================================
       IMPORTANT:
       SPACE AT TOP
       ===================================================== */

    .block-container {{
        padding-top: 4rem !important;
        padding-bottom: 2rem !important;
        max-width: 1450px !important;
    }}


    /* =====================================================
       HEADER
       ===================================================== */

    .mine-title {{
        color: white;
        font-size: 28px;
        font-weight: 900;
        letter-spacing: 1.5px;
        margin-top: 0px;
        margin-bottom: 4px;
    }}

    .mine-subtitle {{
        color: #9fb5c7;
        font-size: 11px;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }}


    /* =====================================================
       SECTION TITLES
       ===================================================== */

    .section-title {{
        color: white;
        font-size: 15px;
        font-weight: 900;
        margin-top: 14px;
        margin-bottom: 8px;
    }}


    /* =====================================================
       METRIC CARDS
       ===================================================== */

    [data-testid="stMetric"] {{
        background: rgba(248, 249, 250, 0.97);
        border-radius: 13px;
        padding: 14px;
        min-height: 105px;
        border: 1px solid rgba(255,255,255,0.5);
        box-shadow: 0px 6px 18px rgba(0,0,0,0.25);
    }}

    [data-testid="stMetricLabel"] {{
        color: #60788c !important;
        font-size: 12px !important;
        font-weight: 700 !important;
    }}

    [data-testid="stMetricValue"] {{
        color: #0c2c45 !important;
        font-size: 27px !important;
        font-weight: 900 !important;
    }}

    [data-testid="stMetricDelta"] {{
        font-size: 11px !important;
    }}


    /* =====================================================
       SLIDERS
       ===================================================== */

    .stSlider {{
        background: rgba(248,249,250,0.96);
        border-radius: 12px;
        padding: 8px 15px 3px 15px;
        margin-bottom: 3px;
    }}

    .stSlider label {{
        color: #173b54 !important;
        font-weight: 700 !important;
        font-size: 11px !important;
    }}


    /* =====================================================
       BORDERED CONTAINERS
       ===================================================== */

    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(4, 24, 40, 0.70);
        border: 1px solid rgba(100,150,180,0.35);
        border-radius: 12px;
    }}


    /* =====================================================
       INFO / WARNING / SUCCESS / ERROR
       ===================================================== */

    .stAlert {{
        border-radius: 9px;
    }}


    /* =====================================================
       DIVIDER
       ===================================================== */

    hr {{
        border-color: rgba(140,170,190,0.25) !important;
    }}


    /* =====================================================
       FOOTER
       ===================================================== */

    .footer {{
        text-align: center;
        color: #7892a5;
        font-size: 9px;
        padding-top: 15px;
        padding-bottom: 10px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

header_col, status_col = st.columns([5, 1])

with header_col:

    st.markdown(
        """
        <div class="mine-title">
            ⛏️ MINEGUARD AI
        </div>

        <div class="mine-subtitle">
            UNDERGROUND MINE SAFETY • MONITORING • RESCUE ROVER
        </div>
        """,
        unsafe_allow_html=True
    )


with status_col:

    st.success("🟢 SYSTEM ONLINE")


st.divider()


# =========================================================
# VIRTUAL SENSOR INPUT
# =========================================================

st.markdown(
    """
    <div class="section-title">
        🎛️ VIRTUAL SENSOR INPUT — PROTOTYPE MODE
    </div>
    """,
    unsafe_allow_html=True
)


s1, s2, s3, s4, s5 = st.columns(5)


with s1:

    ch4 = st.slider(
        "CH₄ Gas (%)",
        0.0,
        5.0,
        0.52,
        0.01
    )


with s2:

    co = st.slider(
        "CO Level (ppm)",
        0,
        200,
        23,
        1
    )


with s3:

    temperature = st.slider(
        "Temperature (°C)",
        0.0,
        60.0,
        29.1,
        0.1
    )


with s4:

    humidity = st.slider(
        "Humidity (%)",
        0,
        100,
        75,
        1
    )


with s5:

    battery = st.slider(
        "Battery (%)",
        0,
        100,
        84,
        1
    )


# =========================================================
# SENSOR STATUS LOGIC
# =========================================================

if ch4 >= 2.0:
    ch4_status = "🔴 DANGER"
elif ch4 >= 1.0:
    ch4_status = "🟡 WARNING"
else:
    ch4_status = "🟢 SAFE"


if co >= 50:
    co_status = "🔴 DANGER"
elif co >= 25:
    co_status = "🟡 WARNING"
else:
    co_status = "🟢 SAFE"


if temperature >= 45:
    temperature_status = "🔴 DANGER"
elif temperature >= 38:
    temperature_status = "🟡 WARNING"
else:
    temperature_status = "🟢 SAFE"


if humidity >= 90:
    humidity_status = "🟡 WARNING"
else:
    humidity_status = "🟢 SAFE"


if battery <= 20:
    battery_status = "🔴 LOW"
elif battery <= 40:
    battery_status = "🟡 WARNING"
else:
    battery_status = "🟢 GOOD"


# =========================================================
# LIVE ENVIRONMENTAL MONITORING
# =========================================================

st.markdown(
    """
    <div class="section-title">
        📊 LIVE ENVIRONMENTAL MONITORING
    </div>
    """,
    unsafe_allow_html=True
)


m1, m2, m3, m4, m5 = st.columns(5)


with m1:

    st.metric(
        "CH₄ GAS",
        f"{ch4:.2f} %",
        ch4_status
    )


with m2:

    st.metric(
        "CO LEVEL",
        f"{co} ppm",
        co_status
    )


with m3:

    st.metric(
        "TEMPERATURE",
        f"{temperature:.1f} °C",
        temperature_status
    )


with m4:

    st.metric(
        "HUMIDITY",
        f"{humidity} %",
        humidity_status
    )


with m5:

    st.metric(
        "BATTERY",
        f"{battery} %",
        battery_status
    )


# =========================================================
# CAMERA + AI
# =========================================================

st.write("")

camera_col, ai_col = st.columns([1.65, 1])


# =========================================================
# LIVE CAMERA
# =========================================================

with camera_col:

    st.markdown(
        """
        <div class="section-title">
            📹 LIVE ROVER CAMERA
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.container(border=True):

        st.markdown("## 📷 LIVE CAMERA FEED")

        st.info(
            "Camera input is not connected yet."
        )

        st.caption(
            "Phase 3 → ESP32 / Raspberry Pi Camera Integration"
        )

        st.write(
            "🎥 **CAMERA STATUS:** OFFLINE"
        )


# =========================================================
# AI DETECTION
# =========================================================

with ai_col:

    st.markdown(
        """
        <div class="section-title">
            🤖 AI DETECTION
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.container(border=True):

        st.markdown("## 🤖 AI ANALYSIS")

        detection = st.selectbox(
            "Detection Simulation",
            [
                "No Person Detected",
                "Person Detected",
                "Possible Worker in Distress"
            ]
        )


        if detection == "No Person Detected":

            st.success(
                "🟢 AREA CLEAR"
            )


        elif detection == "Person Detected":

            st.warning(
                "👷 PERSON DETECTED"
            )

            st.metric(
                "AI Confidence",
                "91%"
            )


        else:

            st.error(
                "🚨 WORKER DISTRESS DETECTED"
            )

            st.metric(
                "AI Confidence",
                "87%"
            )


# =========================================================
# LIDAR MAP
# =========================================================

st.write("")

st.markdown(
    """
    <div class="section-title">
        🗺️ LiDAR LIVE MAP & OBSTACLE DETECTION
    </div>
    """,
    unsafe_allow_html=True
)


with st.container(border=True):

    map_col, lidar_col = st.columns([4, 1])


    # -----------------------------------------------------
    # MAP
    # -----------------------------------------------------

    with map_col:

        st.markdown("### 🗺️ Underground Tunnel Map")

        st.code(
r"""
                 UNDERGROUND MINE

        ┌────────────────────────────────────┐
        │                                    │
        │       • • • • • •                  │
        │     ╱             ╲                │
        │    ╱               ╲               │
        │   ╱                 ╲              │
        │  │       🚙          │       🔴     │
        │  │      ROVER        │    OBSTACLE │
        │  │                   │              │
        │   ╲                 ╱               │
        │    ╲_______________╱                │
        │                                    │
        └────────────────────────────────────┘

        • = LiDAR scan points
        🚙 = Rescue Rover
        🔴 = Detected obstacle
""",
            language="text"
        )


    # -----------------------------------------------------
    # LIDAR DATA
    # -----------------------------------------------------

    with lidar_col:

        st.metric(
            "LiDAR",
            "ACTIVE"
        )

        st.metric(
            "Range",
            "10 m"
        )

        st.metric(
            "Obstacles",
            "1"
        )


# =========================================================
# ROVER STATUS + ALERT CENTER
# =========================================================

st.write("")

status_col, alert_col = st.columns(2)


# =========================================================
# ROVER STATUS
# =========================================================

with status_col:

    st.markdown(
        """
        <div class="section-title">
            🚙 ROVER STATUS
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.container(border=True):

        st.write("🟢 **Connection:** Connected")

        st.write("⚙️ **Control Mode:** Manual")

        st.write(f"🔋 **Battery:** {battery}%")

        st.write("📍 **Mine Zone:** Zone A")

        st.write("🗺️ **LiDAR:** Active")


# =========================================================
# ALERT CENTER
# =========================================================

with alert_col:

    st.markdown(
        """
        <div class="section-title">
            🚨 ALERT CENTER
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.container(border=True):

        # CH4 ALERT

        if ch4 >= 2.0:

            st.error(
                f"🚨 CRITICAL CH₄ LEVEL: {ch4:.2f}%"
            )

        elif ch4 >= 1.0:

            st.warning(
                f"⚠️ CH₄ LEVEL WARNING: {ch4:.2f}%"
            )

        else:

            st.success(
                f"✓ CH₄ LEVEL NORMAL: {ch4:.2f}%"
            )


        # CO ALERT

        if co >= 50:

            st.error(
                f"🚨 CRITICAL CO LEVEL: {co} ppm"
            )

        elif co >= 25:

            st.warning(
                f"⚠️ CO LEVEL WARNING: {co} ppm"
            )


        # TEMPERATURE ALERT

        if temperature >= 45:

            st.error(
                f"🔥 CRITICAL TEMPERATURE: "
                f"{temperature:.1f} °C"
            )

        elif temperature >= 38:

            st.warning(
                f"⚠️ HIGH TEMPERATURE: "
                f"{temperature:.1f} °C"
            )


        # BATTERY ALERT

        if battery <= 20:

            st.error(
                f"🔋 CRITICAL BATTERY: {battery}%"
            )

        elif battery <= 40:

            st.warning(
                f"🔋 LOW BATTERY: {battery}%"
            )


        # AI ALERT

        if detection == "Person Detected":

            st.warning(
                "👷 POSSIBLE HUMAN DETECTED"
            )

        elif detection == "Possible Worker in Distress":

            st.error(
                "🚨 WORKER DISTRESS DETECTED"
            )


# =========================================================
# PROTOTYPE NOTICE
# =========================================================

st.write("")

st.warning(
    "⚠️ PROTOTYPE MODE: Sensor values are currently simulated. "
    "Real ESP32 sensor data will replace these inputs."
)


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">

        ⛏️ MINEGUARD AI

        <br>

        INTELLIGENT UNDERGROUND MINE SAFETY & RESCUE SYSTEM

        <br>

        Prototype Dashboard • Environmental Sensors • AI • LiDAR

    </div>
    """,
    unsafe_allow_html=True
)