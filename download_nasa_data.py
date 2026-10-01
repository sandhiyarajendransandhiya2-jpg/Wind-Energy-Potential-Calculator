"""Download real hourly NASA POWER data and save it in the format app.py expects.
Run:  python download_nasa_data.py      (needs internet, no extra installs beyond pandas)"""
import io
import urllib.request

import pandas as pd

# ---- change these if needed
LAT, LON = 8.0883, 77.5385        # Kanyakumari, Tamil Nadu
START, END = "20250101", "20251231"
OUT = "wind_data_real.csv"

URL = (
    "https://power.larc.nasa.gov/api/temporal/hourly/point"
    f"?parameters=WS50M,WD50M,T2M,PS,RH2M&community=RE&longitude={LON}&latitude={LAT}"
    f"&start={START}&end={END}&format=CSV&time-standard=UTC"
)

def parse_nasa_csv(text: str) -> pd.DataFrame:
    body = text.split("-END HEADER-")[-1].strip()
    raw = pd.read_csv(io.StringIO(body))
    raw = raw.replace(-999, pd.NA).dropna()
    ts = pd.to_datetime(dict(year=raw.YEAR, month=raw.MO, day=raw.DY, hour=raw.HR))
    pressure_hpa = raw.PS.astype(float) * 10                         # kPa -> hPa
    temp = raw.T2M.astype(float)
    rho = pressure_hpa * 100 / (287.058 * (temp + 273.15))          # kg/m3
    return pd.DataFrame({
        "Timestamp": ts, "Wind_Speed_m_s": raw.WS50M.astype(float).round(2),
        "Wind_Direction_deg": raw.WD50M.astype(float).round(0),
        "Temperature": temp.round(1), "Pressure": pressure_hpa.round(1),
        "Humidity_pct": raw.RH2M.astype(float).round(0), "Air_Density": rho.round(3),
    })

if __name__ == "__main__":
    print("Downloading from NASA POWER ... (can take up to a minute)")
    with urllib.request.urlopen(URL, timeout=120) as r:
        text = r.read().decode("utf-8")
    df = parse_nasa_csv(text)
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df)} rows to {OUT}")
    print(f"Mean wind speed: {df.Wind_Speed_m_s.mean():.2f} m/s | max: {df.Wind_Speed_m_s.max():.2f} m/s")
    print(f"Mean air density: {df.Air_Density.mean():.3f} kg/m3")
