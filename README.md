# MAVLink Viewer

These scripts were writtent to interperet data being sent from an Unmanned Surface Vessel (USV) using a Pixhawk flight controller running ardupilot.  The USV has an RPi Pico sending 'NAMED_VALUE_FLOAT' data through Serial 5 in the MAVlink format.  This data ends up included as data across the telemetry link from the USV to Ground Controll Station (GCS).  We are using QGroundControl as the GCS and it is setup with the default port to share MAVlink data as network traffic.  With those systems in place, the software in this repo can capture MAVLink data from QGroundControl and log the readings with GPS coordinates using ```capture.py```.  You can visualize the data in realtime with ```visualize.py```.  Both scripts should be run at the same time in separate terminals.  The current configuration is setup to send water depth measurements from a sonar distance sensor under the name 'WaterDist'.

## Creativity on the Canal June 13th, 2026 data
Included is a .csv file of the data captured during the creativity on the canal festival in Brockport, NY.

![alt text](images/screencap.png)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pymavlink dash numpy
```

## Capture Data

```bash
python3 capture.py
```

- Connects to QGroundControl on `127.0.0.1:14445` (UDPM mode)
- Writes each WaterDist reading with timestamp and GPS coords to a CSV file
- CSV files are named `waterdist_capture_YYYYMMDD_HHMMSS.csv`
- Press Ctrl+C to stop

## Visualize (Real-time Dashboard)

```bash
python3 visualize.py
```

- Opens a web dashboard at http://127.0.0.1:8050
- Auto-refreshes every 3 seconds as new CSV data arrives
- Shows a scatter plot of WaterDist values by GPS position
- Shows a WaterDist distribution histogram
