# wazuh-ot-lab

**Open-source OT/ICS security monitoring with Wazuh: rules, configs and a laptop lab you can build in a weekend.**

Companion kit to the Wazuh Ambassadors webinar *"Seeing the invisible: OT/ICS Security Monitoring with Wazuh"* by [Muhammad Imtiaz](https://muhammadimtiaz.com/ot-wazuh/) (GICSP · CISM · ISO 27001 LA · ISA/IEC 62443).

> **Lab use first.** Everything here was designed for an isolated lab. Before you put any of it near a production plant, review it with operations and the OEM, and follow your site's management-of-change process.

---

## What's inside

| Path | What it does |
|---|---|
| `rules/ot_rules.xml` | Detection rules (IDs 100200–100299) for the six OT use cases below |
| `lists/ot-eng` | CDB allowlist of approved engineering workstations (sample) |
| `manager-config/ossec_ruleset.xml` | Registers the CDB list on the manager |
| `agent-config/nsm_sensor_ossec.xml` | Ships Zeek `modbus.log` (and Suricata EVE) to Wazuh |
| `agent-config/ews_hmi_agent.conf` | Group config for HMIs/EWS: throttling, FIM whodata, USB registry FIM, SCA |
| `sca/ot_hmi_baseline.yml` | Hardening checks tagged with IEC 62443-3-3 SRs |
| `samples/` | Test events for `wazuh-logtest` |
| `tools/modbus_write_sim.py` | Lab-only Modbus write simulator for the demo |
| `docs/LAB-GUIDE.md` | Step-by-step lab build |
| `docs/IEC62443-MAPPING.md` | Detections ↔ IEC 62443-3-3 system requirements |

## The six use cases

| # | Use case | Wazuh feature | Rule | Maps to |
|---|---|---|---|---|
| UC1 | Modbus write from an unapproved host | Zeek JSON + CDB allowlist | 100210 (L12) | ATT&CK ICS T0855 / T0836 |
| UC2 | PLC project file changed | FIM with whodata | 100235 (L10) | ATT&CK ICS T0843 |
| UC3 | USB storage on HMI/EWS | Registry FIM | 100230 (L10) | ATT&CK ICS T0847 |
| UC4 | Off-hours RDP to jump host | Windows logon + `<time>` | 100240 (L8) | ATT&CK ICS T0886 / T0859 |
| UC5 | Hardening drift on HMIs | SCA custom policy | SCA 90001–90004 | IEC 62443-3-3 SR 7.6 |
| UC6 | Vulnerable OT software | Syscollector + vulnerability detection | built-in | IEC 62443-3-3 SR 7.8 |
| ✱ | 3+ OT alerts in 30 min | Correlation (`frequency`/`timeframe`) | 100250 (L15) | Incident trigger |

## Reference architecture (Purdue model)

```
L4-5  Enterprise SOC / SIEM            <- alerts only, northbound via DMZ (one-way where possible)
L3.5  OT DMZ: jump host [agent], OT firewalls [syslog]
L3    Wazuh server (manager, indexer, dashboard), historian [agent]
L2    HMI [agent], EWS [agent], Zeek/Suricata sensor [agent] <- SPAN/TAP (read-only)
L1    PLC / RTU / SIS: NO agents, monitored passively
L0    Sensors, actuators, drives
```

Agents connect **outbound** to the manager on **1514/TCP** (enrollment 1515/TCP), which keeps zone conduits simple to document.

## Quick start (manager)

```bash
# 1. Rules and allowlist
sudo cp rules/ot_rules.xml /var/ossec/etc/rules/
sudo cp lists/ot-eng /var/ossec/etc/lists/
sudo chown wazuh:wazuh /var/ossec/etc/rules/ot_rules.xml /var/ossec/etc/lists/ot-eng

# 2. Register the list: add <list>etc/lists/ot-eng</list> inside <ruleset> in /var/ossec/etc/ossec.conf

# 3. HMI/EWS agent group
sudo /var/ossec/bin/agent_groups -a -g ot-hmi-ews -q
sudo cp agent-config/ews_hmi_agent.conf /var/ossec/etc/shared/ot-hmi-ews/agent.conf
sudo cp sca/ot_hmi_baseline.yml /var/ossec/etc/shared/ot-hmi-ews/

# 4. Restart and test
sudo systemctl restart wazuh-manager
sudo /var/ossec/bin/wazuh-logtest     # paste a line from samples/
```

Full walkthrough: **[docs/LAB-GUIDE.md](docs/LAB-GUIDE.md)**

## Field rules that matter more than any config

- **Start passive.** NSM and firewall syslog before any agent.
- **Never enable active response on Level 1–2 assets.**
- **Never scan PLCs.** Observe them via SPAN/TAP.
- **Throttle agents** on old HMIs (`client_buffer`) and keep FIM scopes tight.
- **Observe for 2–4 weeks** before alerts page your 24/7 SOC.

## Tested with

Written for **Wazuh 4.14.x** and **Zeek 6/7** JSON logs. Field names can differ between Zeek versions, so always confirm with `wazuh-logtest` before relying on a rule.

## Learn more

- Free lab guide & updates: **https://muhammadimtiaz.com/ot-wazuh/**
- Wazuh documentation: https://documentation.wazuh.com
- MITRE ATT&CK for ICS: https://attack.mitre.org/matrices/ics/

## License

MIT. See [LICENSE](LICENSE). Not affiliated with or endorsed by Wazuh Inc. or MITRE.
