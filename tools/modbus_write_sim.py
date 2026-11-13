#!/usr/bin/env python3
"""
Lab-only Modbus write simulator for the wazuh-ot-lab demo.

Sends a single holding-register write to a soft PLC (e.g. OpenPLC) so that
Zeek logs it and Wazuh rule 100200/100210 fires.

NEVER run this against a production or safety system.

Usage:
    pip install pymodbus
    python3 modbus_write_sim.py --plc 10.10.30.10 --register 1 --value 1234
"""
import argparse
import sys

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    sys.exit("pymodbus is required:  pip install pymodbus")


def write_register(client, register, value, unit):
    # pymodbus renamed the unit-id keyword over time (unit -> slave -> device_id)
    for kw in ("device_id", "slave", "unit"):
        try:
            return client.write_register(register, value, **{kw: unit})
        except TypeError:
            continue
    return client.write_register(register, value)


def main():
    ap = argparse.ArgumentParser(description="Lab-only Modbus write simulator")
    ap.add_argument("--plc", required=True, help="Soft-PLC IP address (lab only)")
    ap.add_argument("--port", type=int, default=502)
    ap.add_argument("--register", type=int, default=1, help="Holding register address")
    ap.add_argument("--value", type=int, default=1234)
    ap.add_argument("--unit", type=int, default=1, help="Modbus unit / slave id")
    a = ap.parse_args()

    client = ModbusTcpClient(a.plc, port=a.port)
    if not client.connect():
        sys.exit(f"Cannot connect to {a.plc}:{a.port}")
    try:
        rr = write_register(client, a.register, a.value, a.unit)
        print(f"Wrote {a.value} to HR{a.register} on {a.plc}: {rr}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
