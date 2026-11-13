# IEC 62443-3-3 ↔ Wazuh mapping

How the detections and checks in this kit support evidence for selected IEC 62443-3-3 system requirements (SRs).

> This mapping **supports evidence** for these SRs. It does not replace a full IEC 62443 risk assessment or a security-level (SL-T / SL-A) evaluation. Check SR titles against your own copy of the standard.

| SR | Requirement | Wazuh capability | Kit content | Evidence for the auditor |
|---|---|---|---|---|
| SR 1.1 | Human user identification & authentication | Windows/Linux authentication log analysis | Rule 100240, SCA 90002 | Logon success/failure trends per zone; NLA enforced |
| SR 1.13 | Access via untrusted networks | Jump-host log analysis, time-based rules | Rule 100240, SCA 90002 | Off-hours / vendor remote sessions reviewed |
| SR 2.3 | Use control for portable & mobile devices | Registry FIM + SCA | Rule 100230, SCA 90001, 90003 | USB history per HMI; "USB storage disabled" result |
| SR 2.8 | Auditable events | Centralised log collection | All agent configs | Retained, searchable audit trail |
| SR 3.2 | Malicious code protection | Malware detection + AV/EDR log ingestion | SCA 90003 | Detections per host & zone |
| SR 3.4 | Software & information integrity | FIM with whodata | Rule 100235 | Who changed PLC projects/configs, when, with which process |
| SR 6.2 | Continuous monitoring | Rules + NSM integration + dashboards | Rules 100200–100250 | 24/7 alerting, MTTD/MTTR metrics |
| SR 7.6 | Network & security configuration settings | SCA custom policy | `sca/ot_hmi_baseline.yml` | Baseline compliance score per HMI |
| SR 7.8 | Control system component inventory | Syscollector | Built-in | Hardware, software & open ports per asset |

## MITRE ATT&CK for ICS coverage

| Technique | Name | Kit rule |
|---|---|---|
| T0855 | Unauthorized Command Message | 100210 |
| T0836 | Modify Parameter | 100210 |
| T0843 | Program Download | 100235 (EWS side) |
| T0847 | Replication Through Removable Media | 100230 |
| T0886 | Remote Services | 100240 |
| T0859 | Valid Accounts | 100240 |

Verify technique IDs at https://attack.mitre.org/matrices/ics/.
