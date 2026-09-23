import streamlit as st
import os
import base64
import cv2
import av
import threading
import time
import requests

from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer


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
# FILE PATHS
# =========================================================

BG_FILE = "rover_bg.png"

# Your trained Fire + Smoke model
HAZARD_MODEL_PATH = "models/best.pt"
PERSON_MODEL_PATH = "AI/yolo11n.pt"

# =========================================================
# ESP32 SENSOR CONNECTION
# =========================================================

# Change this IP to the IP address shown by your ESP32.
ESP32_URL = "http://192.168.4.1/sensors"
SENSOR_TIMEOUT = 1.5

sensor_lock = threading.Lock()

sensor_state = {
    "connected": False,
    "ch4": None,
    "co": None,
    "temperature": None,
    "humidity": None,
    "battery": None,
    "front_distance": None,
    "left_distance": None,
    "right_distance": None,
    "last_update": 0.0
}


def read_esp32_sensors():

    try:

        response = requests.get(
            ESP32_URL,
            timeout=SENSOR_TIMEOUT
        )

        if response.status_code != 200:
            raise RuntimeError("ESP32 returned invalid response")

        data = response.json()

        with sensor_lock:

            sensor_state["connected"] = True
            sensor_state["ch4"] = data.get("ch4")
            sensor_state["co"] = data.get("co")
            sensor_state["temperature"] = data.get("temperature")
            sensor_state["humidity"] = data.get("humidity")
            sensor_state["battery"] = data.get("battery")
            sensor_state["front_distance"] = data.get("front_distance")
            sensor_state["left_distance"] = data.get("left_distance")
            sensor_state["right_distance"] = data.get("right_distance")
            sensor_state["last_update"] = time.time()

    except Exception:

        with sensor_lock:

            sensor_state["connected"] = False
            sensor_state["ch4"] = None
            sensor_state["co"] = None
            sensor_state["temperature"] = None
            sensor_state["humidity"] = None
            sensor_state["battery"] = None
            sensor_state["front_distance"] = None
            sensor_state["left_distance"] = None
            sensor_state["right_distance"] = None
            sensor_state["last_update"] = 0.0


def sensor_value(value, unit=""):

    if value is None:
        return "NO INPUT GIVEN"

    try:

        if unit == "%":
            return f"{float(value):.2f} %"

        if unit == "ppm":
            return f"{float(value):.0f} ppm"

        if unit == "°C":
            return f"{float(value):.1f} °C"

        if unit == "cm":
            return f"{float(value):.0f} cm"

        return str(value)

    except Exception:

        return "NO INPUT GIVEN"


# =========================================================
# BACKGROUND IMAGE
# =========================================================

if os.path.exists(BG_FILE):

    with open(BG_FILE, "rb") as f:
        bg_data = base64.b64encode(f.read()).decode()

    background_url = f"data:image/png;base64,{bg_data}"

else:

    background_url = ""


# =========================================================
# LOAD MODELS
# =========================================================

@st.cache_resource
def load_hazard_model():

    if os.path.exists(HAZARD_MODEL_PATH):
        return YOLO(HAZARD_MODEL_PATH)

    return None


@st.cache_resource
def load_person_model():

    if os.path.exists(PERSON_MODEL_PATH):
        return YOLO(PERSON_MODEL_PATH)

    return None


hazard_model = load_hazard_model()
person_model = load_person_model()


# =========================================================
# SHARED AI STATE
# =========================================================

ai_lock = threading.Lock()

ai_state = {
    "person": False,
    "person_count": 0,
    "person_conf": 0.0,

    "fire": False,
    "fire_conf": 0.0,

    "smoke": False,
    "smoke_conf": 0.0,

    "last_update": 0.0
}


# =========================================================
# AI CAMERA PROCESSING
# =========================================================

def ai_camera(frame):

    img = frame.to_ndarray(format="bgr24")

    output = img.copy()


    # -----------------------------------------------------
    # RESET CURRENT FRAME VALUES
    # -----------------------------------------------------

    person_detected = False
    person_count = 0
    person_conf = 0.0

    fire_detected = False
    fire_conf = 0.0

    smoke_detected = False
    smoke_conf = 0.0


    # =====================================================
    # FIRE + SMOKE MODEL
    # =====================================================

    if hazard_model is not None:

        try:

            results = hazard_model(
                img,
                conf=0.35,
                verbose=False
            )

            result = results[0]


            if result.boxes is not None:

                for box in result.boxes:

                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])

                    class_name = str(
                        hazard_model.names[class_id]
                    )

                    name = class_name.lower()


                    # -------------------------------
                    # FIRE
                    # -------------------------------

                    if "fire" in name:

                        fire_detected = True

                        fire_conf = max(
                            fire_conf,
                            confidence
                        )


                    # -------------------------------
                    # SMOKE
                    # -------------------------------

                    if "smoke" in name:

                        smoke_detected = True

                        smoke_conf = max(
                            smoke_conf,
                            confidence
                        )


            # Draw fire/smoke detections
            output = result.plot(
                img=output
            )

        except Exception:
            pass


    # =====================================================
    # PERSON MODEL
    # =====================================================

    if person_model is not None:

        try:

            person_results = person_model(
                img,
                conf=0.40,
                classes=[0],
                verbose=False
            )

            person_result = person_results[0]


            if person_result.boxes is not None:

                for box in person_result.boxes:

                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])


                    # COCO class 0 = person
                    if class_id != 0:
                        continue


                    person_detected = True

                    person_count += 1

                    person_conf = max(
                        person_conf,
                        confidence
                    )


                    # ---------------------------------
                    # PERSON BOUNDING BOX
                    # ---------------------------------

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0]
                    )


                    cv2.rectangle(
                        output,
                        (x1, y1),
                        (x2, y2),
                        (255, 180, 0),
                        3
                    )


                    cv2.putText(
                        output,
                        f"PERSON {confidence * 100:.1f}%",
                        (x1, max(y1 - 12, 25)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 180, 0),
                        2
                    )

        except Exception:
            pass


    # =====================================================
    # DETECTION STATUS
    # =====================================================

    if fire_detected and smoke_detected:

        status_text = "FIRE + SMOKE DETECTED"
        status_color = (0, 0, 255)

    elif fire_detected:

        status_text = "FIRE DETECTED"
        status_color = (0, 0, 255)

    elif smoke_detected:

        status_text = "SMOKE DETECTED"
        status_color = (0, 165, 255)

    elif person_detected:

        status_text = "PERSON DETECTED"
        status_color = (255, 180, 0)

    else:

        status_text = "AREA CLEAR"
        status_color = (0, 255, 0)


    # =====================================================
    # UPDATE SHARED STATE
    # =====================================================

    with ai_lock:

        ai_state["person"] = person_detected
        ai_state["person_count"] = person_count
        ai_state["person_conf"] = person_conf

        ai_state["fire"] = fire_detected
        ai_state["fire_conf"] = fire_conf

        ai_state["smoke"] = smoke_detected
        ai_state["smoke_conf"] = smoke_conf

        ai_state["last_update"] = time.time()


    # =====================================================
    # CAMERA HEADER
    # =====================================================

    cv2.rectangle(
        output,
        (0, 0),
        (output.shape[1], 78),
        (12, 18, 25),
        -1
    )


    cv2.putText(
        output,
        "MINEGUARD AI",
        (20, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2
    )


    cv2.putText(
        output,
        status_text,
        (20, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        status_color,
        2
    )


    # =====================================================
    # RETURN FRAME
    # =====================================================

    return av.VideoFrame.from_ndarray(
        output,
        format="bgr24"
    )


# =========================================================
# CSS
# =========================================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background:
            linear-gradient(
                rgba(2, 15, 28, 0.88),
                rgba(2, 15, 28, 0.95)
            ),
            url("{background_url}");

        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}


    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}


    .block-container {{
        padding-top: 4rem !important;
        padding-bottom: 2rem !important;
        max-width: 1450px !important;
    }}


    .mine-title {{
        color: white;
        font-size: 30px;
        font-weight: 900;
        letter-spacing: 1.5px;
    }}


    .mine-subtitle {{
        color: #9db3c5;
        font-size: 11px;
        letter-spacing: 0.6px;
    }}


    .section-title {{
        color: white;
        font-size: 16px;
        font-weight: 900;
        margin-top: 14px;
        margin-bottom: 10px;
    }}


    [data-testid="stMetric"] {{
        background: rgba(248, 249, 250, 0.97);
        border-radius: 14px;
        padding: 15px;
        min-height: 105px;
        box-shadow: 0 5px 18px rgba(0,0,0,0.25);
    }}


    [data-testid="stMetricLabel"] {{
        color: #557086 !important;
        font-weight: 700 !important;
    }}


    [data-testid="stMetricValue"] {{
        color: #0b2d47 !important;
        font-weight: 900 !important;
    }}


    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(3, 24, 40, 0.70);
        border: 1px solid rgba(120,160,190,0.35);
        border-radius: 14px;
    }}


    .footer {{
        text-align: center;
        color: #718b9e;
        font-size: 9px;
        padding-top: 15px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

header, connection = st.columns([5, 1])


with header:

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


with connection:

    if person_model is not None and hazard_model is not None:

        st.success("🟢 AI ONLINE")

    elif person_model is not None:

        st.warning("🟡 PERSON AI")

    elif hazard_model is not None:

        st.warning("🟡 HAZARD AI")

    else:

        st.error("🔴 AI OFFLINE")


st.divider()


# =========================================================
# LIVE ESP32 SENSOR INPUT
# =========================================================

read_esp32_sensors()

with sensor_lock:

    sensors_connected = sensor_state["connected"]

    ch4 = sensor_state["ch4"]
    co = sensor_state["co"]
    temperature = sensor_state["temperature"]
    humidity = sensor_state["humidity"]
    battery = sensor_state["battery"]

    front_distance = sensor_state["front_distance"]
    left_distance = sensor_state["left_distance"]
    right_distance = sensor_state["right_distance"]


st.markdown(
    """
    <div class="section-title">
        📡 LIVE ROVER SENSOR INPUT
    </div>
    """,
    unsafe_allow_html=True
)


if sensors_connected:

    st.success(
        "🟢 ESP32 CONNECTED — Live sensor data received"
    )

else:

    st.warning(
        "⚪ ESP32 NOT CONNECTED — NO INPUT GIVEN"
    )


# =========================================================
# SENSOR STATUS
# =========================================================

def status_text(value, warning_limit=None, danger_limit=None):

    if value is None:
        return "NO INPUT GIVEN"

    if danger_limit is not None and value >= danger_limit:
        return "🔴 DANGER"

    if warning_limit is not None and value >= warning_limit:
        return "🟡 WARNING"

    return "🟢 SAFE"


ch4_status = status_text(ch4, 1, 2)
co_status = status_text(co, 25, 50)
temp_status = status_text(temperature, 38, 45)
humidity_status = status_text(humidity, 90)

battery_status = (
    "NO INPUT GIVEN"
    if battery is None
    else (
        "🔴 LOW" if battery <= 20
        else "🟡 WARNING" if battery <= 40
        else "🟢 GOOD"
    )
)


# =========================================================
# ENVIRONMENTAL MONITORING
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
    st.metric("CH₄ GAS", sensor_value(ch4, "%"), ch4_status)

with m2:
    st.metric("CO LEVEL", sensor_value(co, "ppm"), co_status)

with m3:
    st.metric(
        "TEMPERATURE",
        sensor_value(temperature, "°C"),
        temp_status
    )

with m4:
    st.metric(
        "HUMIDITY",
        sensor_value(humidity, "%"),
        humidity_status
    )

with m5:
    st.metric(
        "BATTERY",
        sensor_value(battery, "%"),
        battery_status
    )


# =========================================================
# ULTRASONIC NAVIGATION
# =========================================================

st.write("")

st.markdown(
    """
    <div class="section-title">
        📡 ULTRASONIC OBSTACLE DETECTION & NAVIGATION
    </div>
    """,
    unsafe_allow_html=True
)


with st.container(border=True):

    nav_col, distance_col = st.columns([3, 2])


    with nav_col:

        st.markdown("### 🚙 Rover Navigation")

        front_blocked = (
            front_distance is not None
            and front_distance < 30
        )

        left_blocked = (
            left_distance is not None
            and left_distance < 30
        )

        right_blocked = (
            right_distance is not None
            and right_distance < 30
        )


        if front_distance is None:

            navigation_status = "⚪ NO INPUT GIVEN"
            navigation_action = "WAITING FOR FRONT SENSOR"

        elif not front_blocked:

            navigation_status = "🟢 PATH CLEAR"
            navigation_action = "MOVE FORWARD"

        elif (
            left_distance is not None
            and right_distance is not None
            and left_blocked
            and right_blocked
        ):

            navigation_status = "🔴 ALL SIDES BLOCKED"
            navigation_action = "ROTATE 180°"

        elif (
            left_distance is not None
            and right_distance is not None
            and left_distance > right_distance
        ):

            navigation_status = "🟡 FRONT OBSTACLE"
            navigation_action = "ROTATE LEFT"

        elif right_distance is not None:

            navigation_status = "🟡 FRONT OBSTACLE"
            navigation_action = "ROTATE RIGHT"

        else:

            navigation_status = "🟡 FRONT OBSTACLE"
            navigation_action = "WAITING FOR SIDE SENSOR"


        nav_status_col, nav_action_col = st.columns(2)


        with nav_status_col:
            st.markdown(f"### {navigation_status}")


        with nav_action_col:
            st.markdown(f"### ⚙️ {navigation_action}")


    with distance_col:

        st.markdown("### 📡 Sensor Status")

        st.metric(
            "Front",
            sensor_value(front_distance, "cm"),
            "OBSTACLE"
            if front_blocked
            else ("NO INPUT" if front_distance is None else "CLEAR")
        )

        st.metric(
            "Left",
            sensor_value(left_distance, "cm"),
            "BLOCKED"
            if left_blocked
            else ("NO INPUT" if left_distance is None else "CLEAR")
        )

        st.metric(
            "Right",
            sensor_value(right_distance, "cm"),
            "BLOCKED"
            if right_blocked
            else ("NO INPUT" if right_distance is None else "CLEAR")
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

        st.markdown("## 📷 LIVE AI CAMERA FEED")


        if person_model is not None or hazard_model is not None:

            webrtc_streamer(
                key="mineguard-camera",

                video_frame_callback=ai_camera,

                media_stream_constraints={
                    "video": True,
                    "audio": False
                },

                async_processing=True
            )

            st.caption(
                "YOLO11 • PERSON + FIRE + SMOKE DETECTION"
            )

        else:

            st.error(
                "AI models are not available."
            )


# =========================================================
# LIVE AI DETECTION PANEL
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


        # =================================================
        # AUTO REFRESH EVERY 1 SECOND
        # =================================================

        @st.fragment(run_every="1s")
        def live_ai_panel():

            with ai_lock:

                person = ai_state["person"]
                person_count = ai_state["person_count"]
                person_conf = ai_state["person_conf"]

                fire = ai_state["fire"]
                fire_conf = ai_state["fire_conf"]

                smoke = ai_state["smoke"]
                smoke_conf = ai_state["smoke_conf"]


            # =============================================
            # PERSON STATUS
            # =============================================

            if person:

                st.warning(
                    f"👷 PERSON DETECTED — "
                    f"{person_count} PERSON(S)"
                )

            else:

                st.success(
                    "✓ PERSON CLEAR"
                )


            # =============================================
            # FIRE STATUS
            # =============================================

            if fire:

                st.error(
                    f"🔥 FIRE DETECTED — "
                    f"{fire_conf * 100:.1f}%"
                )

            else:

                st.success(
                    "✓ FIRE CLEAR"
                )


            # =============================================
            # SMOKE STATUS
            # =============================================

            if smoke:

                st.warning(
                    f"💨 SMOKE DETECTED — "
                    f"{smoke_conf * 100:.1f}%"
                )

            else:

                st.success(
                    "✓ SMOKE CLEAR"
                )


            # =============================================
            # DETECTION SUMMARY
            # =============================================

            st.markdown("### Detection Summary")


            d1, d2, d3 = st.columns(3)


            # PERSON
            with d1:

                if person:

                    st.metric(
                        "👷 PERSON",
                        str(person_count),
                        f"{person_conf * 100:.1f}%"
                    )

                else:

                    st.metric(
                        "👷 PERSON",
                        "0",
                        "CLEAR"
                    )


            # FIRE
            with d2:

                if fire:

                    st.metric(
                        "🔥 FIRE",
                        "DETECTED",
                        f"{fire_conf * 100:.1f}%"
                    )

                else:

                    st.metric(
                        "🔥 FIRE",
                        "CLEAR"
                    )


            # SMOKE
            with d3:

                if smoke:

                    st.metric(
                        "💨 SMOKE",
                        "DETECTED",
                        f"{smoke_conf * 100:.1f}%"
                    )

                else:

                    st.metric(
                        "💨 SMOKE",
                        "CLEAR"
                    )


        live_ai_panel()


# =========================================================
# ULTRASONIC NAVIGATION
# =========================================================

st.write("")


st.markdown(
    """
    <div class="section-title">
        📡 ULTRASONIC OBSTACLE DETECTION & NAVIGATION
    </div>
    """,
    unsafe_allow_html=True
)


with st.container(border=True):

    nav_col, distance_col = st.columns([3, 2])


    # =====================================================
    # VIRTUAL ULTRASONIC INPUT
    # =====================================================

    with nav_col:

        st.markdown(
            "### 🚙 Rover Navigation"
        )

        u1, u2, u3 = st.columns(3)


        with u1:

            front_distance = st.slider(
                "Front Distance (cm)",
                5,
                200,
                80,
                1,
                key="front_distance"
            )


        with u2:

            left_distance = st.slider(
                "Left Distance (cm)",
                5,
                200,
                100,
                1,
                key="left_distance"
            )


        with u3:

            right_distance = st.slider(
                "Right Distance (cm)",
                5,
                200,
                90,
                1,
                key="right_distance"
            )


    # =====================================================
    # OBSTACLE LOGIC
    # =====================================================

    OBSTACLE_LIMIT = 30

    front_blocked = front_distance < OBSTACLE_LIMIT
    left_blocked = left_distance < OBSTACLE_LIMIT
    right_blocked = right_distance < OBSTACLE_LIMIT


    if not front_blocked:

        navigation_status = "🟢 PATH CLEAR"
        navigation_action = "MOVE FORWARD"

    elif left_blocked and right_blocked:

        navigation_status = "🔴 ALL SIDES BLOCKED"
        navigation_action = "ROTATE 180°"

    elif left_distance > right_distance:

        navigation_status = "🟡 FRONT OBSTACLE"
        navigation_action = "ROTATE LEFT"

    else:

        navigation_status = "🟡 FRONT OBSTACLE"
        navigation_action = "ROTATE RIGHT"


    # =====================================================
    # ULTRASONIC STATUS
    # =====================================================

    with distance_col:

        st.markdown(
            "### 📡 Sensor Status"
        )

        st.metric(
            "Front",
            f"{front_distance} cm",
            "OBSTACLE" if front_blocked else "CLEAR"
        )

        st.metric(
            "Left",
            f"{left_distance} cm",
            "BLOCKED" if left_blocked else "CLEAR"
        )

        st.metric(
            "Right",
            f"{right_distance} cm",
            "BLOCKED" if right_blocked else "CLEAR"
        )


    st.divider()

    nav_status_col, nav_action_col = st.columns(2)


    with nav_status_col:

        st.markdown(
            f"### {navigation_status}"
        )


    with nav_action_col:

        st.markdown(
            f"### ⚙️ {navigation_action}"
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

        st.write(
            "🟢 **Connection:** Connected"
        )

        st.write(
            "⚙️ **Control Mode:** Manual"
        )

        st.write(
            f"🔋 **Battery:** {sensor_value(battery, "%")}"
        )

        st.write(
            "📍 **Mine Zone:** Zone A"
        )

        st.write(
            "📡 **Sensor Link:** Connected"
            if sensors_connected
            else "📡 **Sensor Link:** NO INPUT GIVEN"
        )

        st.write(
            "📡 **Navigation:** Ultrasonic"
        )

        st.write(
            "🤖 **AI:** Person + Fire + Smoke"
        )


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

        @st.fragment(run_every="1s")
        def live_alerts():

            with ai_lock:

                person = ai_state["person"]
                fire = ai_state["fire"]
                smoke = ai_state["smoke"]

                person_conf = ai_state["person_conf"]
                fire_conf = ai_state["fire_conf"]
                smoke_conf = ai_state["smoke_conf"]


            # ---------------------------------------------
            # AI PERSON ALERT
            # ---------------------------------------------

            if person:

                st.warning(
                    f"👷 POSSIBLE HUMAN DETECTED "
                    f"({person_conf * 100:.1f}%)"
                )


            # ---------------------------------------------
            # FIRE ALERT
            # ---------------------------------------------

            if fire:

                st.error(
                    f"🔥 FIRE DETECTED "
                    f"({fire_conf * 100:.1f}%)"
                )


            # ---------------------------------------------
            # SMOKE ALERT
            # ---------------------------------------------

            if smoke:

                st.warning(
                    f"💨 SMOKE DETECTED "
                    f"({smoke_conf * 100:.1f}%)"
                )


            # ---------------------------------------------
            # CLEAR
            # ---------------------------------------------

            if not person and not fire and not smoke:

                st.success(
                    "✓ AI HAZARD STATUS: CLEAR"
                )


            # ---------------------------------------------
            # CH4
            # ---------------------------------------------

            if ch4 is None:

                st.info("⚪ CH₄: NO INPUT GIVEN")

            elif ch4 >= 2:

                st.error(
                    f"🚨 CRITICAL CH₄ LEVEL: {ch4:.2f}%"
                )

            elif ch4 >= 1:

                st.warning(
                    f"⚠️ CH₄ LEVEL WARNING: {ch4:.2f}%"
                )

            else:

                st.success(
                    f"✓ CH₄ LEVEL NORMAL: {ch4:.2f}%"
                )


            # ---------------------------------------------
            # CO
            # ---------------------------------------------

            if co is None:

                st.info("⚪ CO: NO INPUT GIVEN")

            elif co >= 50:

                st.error(
                    f"🚨 CRITICAL CO LEVEL: {co} ppm"
                )

            elif co >= 25:

                st.warning(
                    f"⚠️ CO LEVEL WARNING: {co} ppm"
                )

            else:

                st.success(
                    f"✓ CO LEVEL NORMAL: {co} ppm"
                )


            # ---------------------------------------------
            # TEMPERATURE
            # ---------------------------------------------

            if temperature is None:

                st.info("⚪ TEMPERATURE: NO INPUT GIVEN")

            elif temperature >= 45:

                st.error(
                    f"🔥 CRITICAL TEMPERATURE: "
                    f"{temperature:.1f} °C"
                )

            elif temperature >= 38:

                st.warning(
                    f"⚠️ HIGH TEMPERATURE: "
                    f"{temperature:.1f} °C"
                )

            else:

                st.success(
                    f"✓ TEMPERATURE NORMAL: "
                    f"{temperature:.1f} °C"
                )


            # ---------------------------------------------
            # BATTERY
            # ---------------------------------------------

            if battery is None:

                st.info("⚪ BATTERY: NO INPUT GIVEN")

            elif battery <= 20:

                st.error(
                    f"🔋 CRITICAL BATTERY: {battery}%"
                )

            elif battery <= 40:

                st.warning(
                    f"🔋 LOW BATTERY: {battery}%"
                )

            else:

                st.success(
                    f"✓ BATTERY GOOD: {battery}%"
                )


        live_alerts()


# =========================================================
# PROTOTYPE NOTICE
# =========================================================

st.write("")


st.info(
    "⚠️ PROTOTYPE MODE — Environmental sensor values are "
    "currently simulated. Camera AI uses the laptop webcam. "
    "Real rover sensor data can be connected in the next phase."
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
YOLO11 • PERSON • FIRE • SMOKE • ENVIRONMENT • ULTRASONIC
</div>
""",
unsafe_allow_html=True
)