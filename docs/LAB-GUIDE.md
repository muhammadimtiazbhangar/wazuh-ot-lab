# OT/ICS Monitoring with Wazuh: Lab Build Guide

*Version 1.0 · Muhammad Imtiaz · muhammadimtiaz.com/ot-wazuh*

This guide builds a small but realistic OT monitoring lab on one laptop: a soft PLC, an HMI/engineering workstation, a passive network sensor, an attacker box, and a Wazuh all-in-one server. By the end, you will be able to reproduce the five-step intrusion shown in the webinar and see every step in Wazuh.

> **Safety first.** Build this on an isolated, host-only network. Never point the simulator or any scanner at a real plant, and never connect lab VMs to a production OT network.

---

## 1. What you need

| Item | Recommendation |
|---|---|
| Host | 32 GB RAM recommended (16 GB works with smaller VMs), 8 cores, ~250 GB SSD |
| Hypervisor | VirtualBox, VMware Workstation/Fusion, UTM, or Proxmox |
| Network | One host-only / internal network, e.g. `10.10.0.0/16`, no gateway to the internet once built |

### Lab addressing (used throughout this guide)

| VM | Role | IP |
|---|---|---|
| `wazuh` | Wazuh server (manager, indexer, dashboard) | 10.10.10.10 |
| `ews-01` | Windows HMI / engineering workstation | 10.10.20.15 |
| `attacker` | Linux "unapproved" host | 10.10.20.99 |
| `plc-01` | OpenPLC Runtime (Modbus TCP server) | 10.10.30.10 |
| `nsm-01` | Zeek / Suricata sensor (+ Wazuh agent) | 10.10.40.10 (sniffing on mirrored traffic) |

A flat `/16` keeps the lab simple. If you want to practise zones and conduits, split it into VLANs or subnets behind a pfSense/OPNsense VM later.

---

## 2. Wazuh server (all-in-one)

1. Create an Ubuntu 24.04 VM: 4 vCPU, 8 GB RAM, 50 GB disk (the Wazuh quickstart sizing for up to ~25 agents).
2. Run the official installation assistant (check the version in the URL against the current docs):

   ```bash
   curl -sO https://packages.wazuh.com/4.14/wazuh-install.sh && sudo bash ./wazuh-install.sh -a
   ```

3. Note the admin password from the summary, then open `https://10.10.10.10` in a browser.
4. Optional but recommended: disable the Wazuh package repository afterwards so the lab doesn't upgrade by accident (see the Wazuh quickstart).

---

## 3. Soft PLC: OpenPLC Runtime

1. Create a small Ubuntu/Debian VM (`plc-01`, 1 vCPU, 1–2 GB RAM).
2. Install OpenPLC Runtime following the project's instructions (autonomylogic.com / GitHub `thiagoralves/OpenPLC_v3`).
3. In the OpenPLC web UI, upload a simple program (e.g. a tank-level or compressor-pressure example) and **start the PLC**. Modbus TCP listens on port **502**.
4. Note one holding register you can safely write in the lab (e.g. `%QW100` → holding register 100 in OpenPLC's mapping).

---

## 4. HMI / engineering workstation (Windows)

1. Create a Windows 10/11 VM (`ews-01`, 2 vCPU, 4 GB RAM).
2. Create the folder `D:\PLC_Projects` (or change the path in `agent-config/ews_hmi_agent.conf`) and drop a few dummy project files in it, e.g. `Compressor_Skid.ap18`, `Tank_Farm.ACD`.
3. Install the Wazuh agent from the dashboard (*Agents → Deploy new agent*), pointing it at `10.10.10.10`.
4. Optional: install Sysmon with a well-known config (e.g. SwiftOnSecurity or Olaf Hartong's sysmon-modular).
5. Enable whodata prerequisites: Wazuh uses Windows auditing for whodata. The agent configures the SACLs on monitored folders; make sure the *Audit File System* subcategory isn't blocked by a local or domain GPO.

---

## 5. Network sensor: Zeek (+ Suricata)

1. Create an Ubuntu VM (`nsm-01`, 2 vCPU, 4 GB RAM) with **two NICs**: one for management (`10.10.40.10`) and one in **promiscuous mode** on the lab network for sniffing.
   - VirtualBox: *Network → Adapter 2 → Promiscuous Mode: Allow All*.
   - Proxmox/VMware: use a port-mirror / promiscuous port group.
2. Install Zeek from the official packages (zeek.org) and set the sniffing interface in `node.cfg`.
3. Enable JSON logs. Add to `local.zeek`:

   ```zeek
   @load policy/tuning/json-logs.zeek
   ```

4. Deploy Zeek (`zeekctl deploy`) and confirm `/opt/zeek/logs/current/modbus.log` appears once Modbus traffic flows.
5. Optional: install Suricata and enable EVE JSON output for signature-based alerts.
6. Install the Wazuh agent on `nsm-01` and add the `<localfile>` blocks from `agent-config/nsm_sensor_ossec.xml`.

---

## 6. Load the OT detection pack on the manager

```bash
git clone https://github.com/muhammadimtiazbhangar/wazuh-ot-lab.git
cd wazuh-ot-lab

sudo cp rules/ot_rules.xml /var/ossec/etc/rules/
sudo cp lists/ot-eng /var/ossec/etc/lists/
sudo chown wazuh:wazuh /var/ossec/etc/rules/ot_rules.xml /var/ossec/etc/lists/ot-eng
```

Edit `/var/ossec/etc/ossec.conf` and add the list inside the existing `<ruleset>` block:

```xml
<list>etc/lists/ot-eng</list>
```

Create the HMI/EWS group and push its configuration and SCA policy:

```bash
sudo /var/ossec/bin/agent_groups -a -g ot-hmi-ews -q
sudo cp agent-config/ews_hmi_agent.conf /var/ossec/etc/shared/ot-hmi-ews/agent.conf
sudo cp sca/ot_hmi_baseline.yml /var/ossec/etc/shared/ot-hmi-ews/
sudo chown -R wazuh:wazuh /var/ossec/etc/shared/ot-hmi-ews
sudo /var/ossec/bin/agent_groups -a -i <EWS_AGENT_ID> -g ot-hmi-ews -q
sudo systemctl restart wazuh-manager
```

### Test before you trust

```bash
sudo /var/ossec/bin/wazuh-logtest
```

Paste the line from `samples/zeek_modbus_write_unapproved.json`. Phase 3 should show **rule 100210, level 12**. The approved sample should only reach **100200, level 3**. If a rule doesn't fire, compare the decoded field names with your Zeek version's output.

---

## 7. Run the attack story (the webinar demo)

| Step | Do this (lab only) | Expect in Wazuh |
|---|---|---|
| 1 | Attach a USB stick (or virtual USB disk) to `ews-01` | Rule 100230 after the next registry scan (frequency set to 1 h in the group config; run a manual scan from the dashboard to speed it up) |
| 2 | RDP into `ews-01` between 19:00 and 06:00 with a "vendor" account | Rule 100240 (requires logon type 10) |
| 3 | Edit `D:\PLC_Projects\Compressor_Skid.ap18` with Notepad or PowerShell | Rule 100235 with user and process (whodata) |
| 4 | From `attacker`: `python3 tools/modbus_write_sim.py --plc 10.10.30.10 --register 100 --value 9999` | Rule 100210, level 12 |
| 5 | Steps 1–4 within 30 minutes | Rule 100250, level 15 correlation |

In the dashboard, open **Threat Hunting** and filter on `rule.groups: ot` to see the full story in one view.

---

## 8. Hardening drift (SCA)

On `ews-01`, open the agent's **Configuration Assessment** tab and find the policy **"OT HMI/EWS baseline (IEC 62443-3-3 aligned)"**. Each failed check shows its IEC 62443 SR tag. Fix one setting (e.g. disable AutoRun), wait for the next SCA scan, and watch the score change.

---

## 9. Taking it towards production

- **Get OEM approval** before installing any agent on a vendor-supported HMI or EWS.
- **Throttle** agents (`client_buffer`) and keep FIM scopes tight on old hardware.
- Run in **observe mode for 2–4 weeks**: rules on, notifications off, then tune.
- **Never enable active response on Level 1–2 assets.** Detection only.
- Keep the Wazuh server **inside the OT zone** and send only alerts northbound, one-way where possible.
- Replace the global correlation in rule 100250 with per-zone correlation (`<same_field>` on a zone or site field you add via labels).
- Document every Wazuh connection as an IEC 62443 conduit.

---

## 10. Troubleshooting

| Symptom | Check |
|---|---|
| No `modbus.log` | Zeek not seeing traffic: promiscuous mode, correct interface in `node.cfg`, Modbus actually flowing |
| Rule 100200 never fires | `wazuh-logtest` with a real line; JSON must be single-line; Zeek JSON logging enabled |
| 100210 fires for the EWS | IP in `lists/ot-eng` must match exactly; restart the manager after editing lists |
| No whodata user/process | Audit policy blocked by GPO; check `ossec.log` on the agent for whodata errors |
| USB alert slow | Registry FIM is scheduled. Lower `<frequency>` or trigger a scan |

---

*Free to use and share under the MIT license. Not affiliated with or endorsed by Wazuh Inc. Questions or improvements: open an issue on GitHub or email security@muhammadimtiaz.com.*
