# Sample events

Paste a line into `/var/ossec/bin/wazuh-logtest` on the manager.

| File | Expected result |
|---|---|
| `zeek_modbus_write_unapproved.json` | Rule **100210**, level 12 (source 10.10.20.99 is not in `lists/ot-eng`) |
| `zeek_modbus_write_approved.json` | Rule **100200**, level 3 only (10.10.20.15 is an approved EWS) |

If Phase 1 shows no `json` decoding, check that the line is valid single-line JSON.
