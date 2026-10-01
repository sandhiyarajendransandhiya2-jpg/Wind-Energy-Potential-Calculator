import io
import math
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# WIND ENERGY POTENTIAL CALCULATOR
# NASA POWER DATA - KANYAKUMARI, TAMIL NADU
# ============================================================

st.set_page_config(
    page_title="Wind Energy Potential Calculator",
    page_icon="🌬️",
    layout="wide"
)

NASA_FILE = "wind_data_real.csv"

LOCATION = "Kanyakumari, Tamil Nadu"
LATITUDE = 8.0883
LONGITUDE = 77.5385
DATA_YEAR = 2025
WIND_PARAMETER = "WS50M"


# ============================================================
# LOAD NASA DATA
# ============================================================

@st.cache_data
def load_nasa_data():

    if not os.path.exists(NASA_FILE):
        return None

    df = pd.read_csv(NASA_FILE)

    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    numeric_columns = [
        "Wind_Speed_m_s",
        "Wind_Direction_deg",
        "Temperature",
        "Pressure",
        "Humidity_pct",
        "Air_Density"
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Timestamp", "Wind_Speed_m_s"])

    return df


data = load_nasa_data()


# ============================================================
# TURBINE POWER CALCULATION
# ============================================================

def turbine_power_kw(
    wind_speed,
    air_density,
    area,
    cp,
    efficiency,
    cut_in,
    cut_out,
    rated_power
):

    wind_speed = np.asarray(wind_speed, dtype=float)
    air_density = np.asarray(air_density, dtype=float)

    raw_power = (
        0.5
        * air_density
        * area
        * wind_speed ** 3
        * cp
        * efficiency
        / 1000
    )

    power = np.minimum(raw_power, rated_power)

    power = np.where(
        (wind_speed < cut_in) | (wind_speed > cut_out),
        0,
        power
    )

    return power


# ============================================================
# HEADER
# ============================================================

st.title("🌬️ Wind Energy Potential Calculator")

st.caption(
    "Team 8 · NASA POWER hourly wind data · "
    "Kanyakumari, Tamil Nadu · 2025"
)


# ============================================================
# CHECK NASA FILE
# ============================================================

if data is None:

    st.error("NASA data file was not found.")

    st.info(
        "Make sure wind_data_real.csv is inside the same folder as app.py."
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ Turbine Configuration")

radius = st.sidebar.number_input(
    "Rotor radius (m)",
    min_value=1.0,
    max_value=100.0,
    value=35.0,
    step=1.0
)

cp = st.sidebar.slider(
    "Power coefficient Cp",
    min_value=0.10,
    max_value=0.59,
    value=0.40,
    step=0.01
)

efficiency = st.sidebar.slider(
    "System efficiency (%)",
    min_value=50,
    max_value=100,
    value=85
) / 100

rated_power = st.sidebar.number_input(
    "Rated power (kW)",
    min_value=100.0,
    max_value=15000.0,
    value=2000.0,
    step=100.0
)

cut_in = st.sidebar.number_input(
    "Cut-in speed (m/s)",
    min_value=0.0,
    max_value=10.0,
    value=3.0,
    step=0.5
)

cut_out = st.sidebar.number_input(
    "Cut-out speed (m/s)",
    min_value=10.0,
    max_value=40.0,
    value=25.0,
    step=1.0
)


# ============================================================
# CALCULATIONS
# ============================================================

area = math.pi * radius ** 2

average_wind = data["Wind_Speed_m_s"].mean()
maximum_wind = data["Wind_Speed_m_s"].max()
minimum_wind = data["Wind_Speed_m_s"].min()

if "Air_Density" in data.columns:
    average_density = data["Air_Density"].mean()
else:
    average_density = 1.225

data["Power_kW"] = turbine_power_kw(
    data["Wind_Speed_m_s"],
    data["Air_Density"] if "Air_Density" in data.columns else average_density,
    area,
    cp,
    efficiency,
    cut_in,
    cut_out,
    rated_power
)

data["Energy_kWh"] = data["Power_kW"]

annual_energy_kwh = data["Energy_kWh"].sum()

annual_energy_mwh = annual_energy_kwh / 1000

capacity_factor = (
    annual_energy_kwh
    / (rated_power * len(data))
    * 100
)


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "① NASA Data",
        "② Energy Analysis",
        "③ Turbine Analysis",
        "④ Report"
    ]
)


# ============================================================
# TAB 1 - NASA DATA
# ============================================================

with tab1:

    st.subheader("🛰️ NASA POWER Wind Data")

    st.write(
        "This dashboard uses the downloaded NASA POWER hourly dataset. "
        "No synthetic or randomly generated weather data is used."
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Location",
        LOCATION
    )

    c2.metric(
        "Year",
        DATA_YEAR
    )

    c3.metric(
        "Records",
        f"{len(data):,}"
    )

    c4.metric(
        "Frequency",
        "Hourly"
    )

    st.divider()

    st.subheader("🌬️ Wind Statistics")

    s1, s2, s3, s4 = st.columns(4)

    s1.metric(
        "Average Wind Speed",
        f"{average_wind:.2f} m/s"
    )

    s2.metric(
        "Maximum Wind Speed",
        f"{maximum_wind:.2f} m/s"
    )

    s3.metric(
        "Minimum Wind Speed",
        f"{minimum_wind:.2f} m/s"
    )

    s4.metric(
        "Average Air Density",
        f"{average_density:.3f} kg/m³"
    )

    st.divider()

    st.subheader("📈 Hourly Wind Speed")

    chart_data = data.set_index("Timestamp")[
        ["Wind_Speed_m_s"]
    ]

    st.line_chart(chart_data)

    st.subheader("📊 Wind Speed Distribution")

    fig, ax = plt.subplots(figsize=(9, 4))

    ax.hist(
        data["Wind_Speed_m_s"],
        bins=40,
        edgecolor="black"
    )

    ax.set_xlabel("Wind Speed (m/s)")
    ax.set_ylabel("Number of Hours")
    ax.set_title("NASA POWER Wind Speed Distribution")

    st.pyplot(fig)

    plt.close(fig)

    st.subheader("📋 NASA Dataset Preview")

    st.dataframe(
        data.head(50),
        use_container_width=True
    )

    csv_data = data.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download NASA Data CSV",
        csv_data,
        "wind_data_real.csv",
        "text/csv"
    )


# ============================================================
# TAB 2 - ENERGY ANALYSIS
# ============================================================

with tab2:

    st.subheader("⚡ Wind Energy Analysis")

    e1, e2, e3, e4 = st.columns(4)

    e1.metric(
        "Rotor Swept Area",
        f"{area:,.0f} m²"
    )

    e2.metric(
        "Annual Energy",
        f"{annual_energy_mwh:,.1f} MWh"
    )

    e3.metric(
        "Rated Power",
        f"{rated_power:,.0f} kW"
    )

    e4.metric(
        "Capacity Factor",
        f"{capacity_factor:.1f}%"
    )

    st.divider()

    st.subheader("📅 Monthly Energy Production")

    monthly_energy = (
        data.set_index("Timestamp")["Energy_kWh"]
        .resample("MS")
        .sum()
        .to_frame()
    )

    monthly_energy["Energy_MWh"] = (
        monthly_energy["Energy_kWh"] / 1000
    )

    st.bar_chart(
        monthly_energy["Energy_MWh"]
    )

    st.dataframe(
        monthly_energy[["Energy_MWh"]].round(2),
        use_container_width=True
    )

    st.divider()

    st.subheader("📊 Power Output Statistics")

    p1, p2, p3 = st.columns(3)

    p1.metric(
        "Average Power",
        f"{data['Power_kW'].mean():,.2f} kW"
    )

    p2.metric(
        "Maximum Power",
        f"{data['Power_kW'].max():,.2f} kW"
    )

    p3.metric(
        "Total Energy",
        f"{annual_energy_mwh:,.2f} MWh"
    )

    st.subheader("⚡ Hourly Turbine Power")

    st.line_chart(
        data.set_index("Timestamp")[
            ["Power_kW"]
        ]
    )


# ============================================================
# TAB 3 - TURBINE ANALYSIS
# ============================================================

with tab3:

    st.subheader("⚙️ Turbine Power Curve")

    curve_speed = np.linspace(
        0,
        max(cut_out + 2, 30),
        300
    )

    curve_density = average_density

    curve_power = turbine_power_kw(
        curve_speed,
        curve_density,
        area,
        cp,
        efficiency,
        cut_in,
        cut_out,
        rated_power
    )

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        curve_speed,
        curve_power,
        linewidth=2
    )

    ax.axvline(
        cut_in,
        linestyle="--",
        label="Cut-in"
    )

    ax.axvline(
        cut_out,
        linestyle="--",
        label="Cut-out"
    )

    ax.set_xlabel("Wind Speed (m/s)")
    ax.set_ylabel("Power (kW)")
    ax.set_title("Turbine Power Curve")

    ax.legend()

    ax.grid(True, alpha=0.3)

    st.pyplot(fig)

    plt.close(fig)

    st.divider()

    st.subheader("🔧 Current Turbine Settings")

    settings = pd.DataFrame(
        {
            "Parameter": [
                "Rotor radius",
                "Swept area",
                "Power coefficient Cp",
                "System efficiency",
                "Rated power",
                "Cut-in speed",
                "Cut-out speed",
                "Average air density"
            ],
            "Value": [
                f"{radius:.2f} m",
                f"{area:.2f} m²",
                f"{cp:.2f}",
                f"{efficiency * 100:.0f}%",
                f"{rated_power:.0f} kW",
                f"{cut_in:.1f} m/s",
                f"{cut_out:.1f} m/s",
                f"{average_density:.3f} kg/m³"
            ]
        }
    )

    st.dataframe(
        settings,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TAB 4 - REPORT
# ============================================================

with tab4:

    st.subheader("📄 Wind Energy Assessment Report")

    report = f"""
WIND ENERGY POTENTIAL ASSESSMENT
================================

Location:
{LOCATION}

Coordinates:
Latitude  : {LATITUDE}
Longitude : {LONGITUDE}

Data Source:
NASA POWER

Wind Parameter:
{WIND_PARAMETER}

Year:
{DATA_YEAR}

Frequency:
Hourly

Number of Records:
{len(data):,}

WIND RESOURCE
=============

Average Wind Speed:
{average_wind:.2f} m/s

Maximum Wind Speed:
{maximum_wind:.2f} m/s

Minimum Wind Speed:
{minimum_wind:.2f} m/s

Average Air Density:
{average_density:.3f} kg/m³


TURBINE CONFIGURATION
=====================

Rotor Radius:
{radius:.2f} m

Rotor Swept Area:
{area:.2f} m²

Power Coefficient:
{cp:.2f}

System Efficiency:
{efficiency * 100:.0f}%

Rated Power:
{rated_power:.0f} kW

Cut-in Speed:
{cut_in:.1f} m/s

Cut-out Speed:
{cut_out:.1f} m/s


ENERGY RESULTS
==============

Annual Energy:
{annual_energy_mwh:,.2f} MWh

Average Power:
{data["Power_kW"].mean():,.2f} kW

Maximum Power:
{data["Power_kW"].max():,.2f} kW

Capacity Factor:
{capacity_factor:.2f}%


DATA NOTE
=========

The wind resource data used in this application
comes from the NASA POWER dataset.

No synthetic/random weather data is generated
by this application.
"""

    st.text_area(
        "Report",
        report,
        height=550
    )

    st.download_button(
        "⬇️ Download Report",
        report,
        "Wind_Energy_Assessment_Report.txt",
        "text/plain"
    )