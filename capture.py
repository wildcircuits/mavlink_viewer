#!/usr/bin/env python3
"""Capture MAVLink data from QGroundControl and log GPS + WaterDist.

Usage:
    source .venv/bin/activate && python3 capture.py
"""

import csv
import sys
import time
import socket
from datetime import datetime, timezone
from pymavlink import mavutil


def check_qgc_config():
    """Check if QGroundControl is actively sending on port 14445."""
    print("Diagnostic: checking QGroundControl on localhost:14445 ...")

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('0.0.0.0', 14445))
        print("  Port 14445 is FREE (not bound by QGroundControl)")
        print("  -> QGroundControl is in UDPM mode, sending TO 14445")
        print("  -> Connection: 'udp:127.0.0.1:14445'")
        s.close()
        return "udpm"
    except OSError:
        print("  Port 14445 is OCCUPIED by QGroundControl")
        print("  -> QGroundControl is in UDPR mode, listening ON 14445")
        print("  -> It will NOT relay vehicle data unless configured to do so")
        s.close()
        return "udpr"


def connect_qgc(mode):
    """Connect to QGroundControl based on detected mode."""
    if mode == "udpm":
        addr = "udp:127.0.0.1:14445"
    else:
        addr = "udpin:127.0.0.1:14445"

    print(f"\nConnecting with: {addr}")
    try:
        master = mavutil.mavlink_connection(addr, autoreconnect=True, timeout=10.0)
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("\nINSTRUCTIONS:")
        print("=" * 60)
        print("1. In QGroundControl, go to:")
        print("   Vehicle Setup -> Platform -> MAVLink")
        print("2. Enable 'MAVLink UDP Output' or similar relay setting")
        print("3. Set the output to send to 127.0.0.1:14445")
        print("4. Restart QGroundControl and try again")
        print("=" * 60)
        sys.exit(1)

    return master


def main():
    mode = check_qgc_config()
    master = connect_qgc(mode)
    master.mav._seq = 0

    # Determine output filename
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"waterdist_capture_{now_str}.csv"

    print(f"Capturing WaterDist + GPS data to {csv_file} ...\n")
    print("Waiting for WaterDist values (press Ctrl+C to stop)...\n")

    # Open CSV file
    fieldnames = ["timestamp", "gps_lat", "gps_lon", "WaterDist"]
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        last_gps_lat = None
        last_gps_lon = None

        try:
            while True:
                msg = master.recv_match(type=None, blocking=True, timeout=1)
                if msg is None:
                    continue

                msg_type = msg.get_type()

                # Update latest GPS
                if msg_type == "GPS_RAW_INT":
                    if hasattr(msg, 'lat') and msg.lat != 0:
                        last_gps_lat = msg.lat / 1e7
                    if hasattr(msg, 'lon') and msg.lon != 0:
                        last_gps_lon = msg.lon / 1e7

                # Also try GLOBAL_POSITION_INT as fallback
                if msg_type == "GLOBAL_POSITION_INT":
                    if hasattr(msg, 'lat') and msg.lat != 0:
                        last_gps_lat = msg.lat / 1e7
                    if hasattr(msg, 'lon') and msg.lon != 0:
                        last_gps_lon = msg.lon / 1e7

                # Capture WaterDist
                if msg_type == "NAMED_VALUE_FLOAT" and msg.name == "WaterDist":
                    waterdist = msg.value
                    ts = datetime.now(timezone.utc).strftime(
                        "%Y-%m-%d %H:%M:%S.%f")[:-3] + " UTC"
                    row = {
                        "timestamp": ts,
                        "gps_lat": last_gps_lat,
                        "gps_lon": last_gps_lon,
                        "WaterDist": waterdist,
                    }
                    writer.writerow(row)
                    f.flush()
                    print(f"  [{ts}] lat={last_gps_lat}  lon={last_gps_lon}  "
                          f"WaterDist={waterdist}")

        except KeyboardInterrupt:
            print("\n\nStopped.")
            master.close()


if __name__ == "__main__":
    main()
