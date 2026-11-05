"""Seed troubleshooting reports so the class-history search has content during the demo."""
import json, sys, uuid
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hatch import store
store.init()

REPORTS = [
    {
        'ship_name': 'USS Benfold', 'hull_number': 'DDG-65', 'ship_class': 'Arleigh Burke',
        'equipment': 'Electrical distribution panel',
        'symptom': 'Intermittent voltage drop on 24V bus during high-load transitions. SIM-TP-01 reading fluctuated between 22.8V and 24.1V over a 30-second observation window.',
        'actions_taken': 'Inspected terminal connections on SIM-ES-101; found slight discoloration on bus-bar contact B2. Cleaned contact surface and retorqued to specification. Monitored voltage across three load transitions.',
        'outcome': 'Voltage stabilized at 24.0V after contact cleaning. Recommend follow-up inspection at next scheduled maintenance to confirm long-term stability. Noted that adjacent panel SIM-ES-102 shows no similar behavior.',
        'technician': 'FC1 Ochoa', 'location': 'DEMO compartment 01',
    },
    {
        'ship_name': 'USS Halsey', 'hull_number': 'DDG-97', 'ship_class': 'Arleigh Burke',
        'equipment': 'Emergency lighting unit',
        'symptom': 'Emergency lighting battery failed 30-second discharge test. Post-test voltage read 11.4V on SIM-BV-301, below the 12.0V minimum. Charger indicator SIM-CH-301 showed normal charge cycle.',
        'actions_taken': 'Replaced battery assembly per SIM-BAT-301 procedure. Verified charger output voltage within limits. Ran full discharge test on replacement battery — post-test reading 12.3V.',
        'outcome': 'Battery replaced and tested satisfactorily. Original battery was 14 months into a 12-month replacement cycle. Recommend flagging overdue battery replacements in the watch schedule.',
        'technician': 'FC2 Donohue', 'location': 'DEMO compartment 03',
    },
    {
        'ship_name': 'USS John Paul Jones', 'hull_number': 'DDG-53', 'ship_class': 'Arleigh Burke',
        'equipment': 'SONAR electronics cabinet cooling assembly',
        'symptom': 'Cabinet temperature alarm SIM-A-401 triggered during sustained operations. Differential pressure gauge SIM-DPI-401 read 1.2 in H2O, well above the 0.3 in H2O maximum.',
        'actions_taken': 'Removed filter SIM-F-401 and found heavy debris accumulation including fibrous material consistent with lagging insulation from adjacent compartment work. Cleaned inlet screen SIM-SC-401. Installed replacement filter SIM-PN-F401.',
        'outcome': 'Post-service differential pressure dropped to 0.15 in H2O. Cabinet temperature returned to 24°C within normal range. Alarm cleared. Recommend coordinating filter service schedule with compartment maintenance activities that generate airborne debris.',
        'technician': 'FC1 Ochoa', 'location': 'DEMO compartment 05',
    },
    {
        'ship_name': 'USS Benfold', 'hull_number': 'DDG-65', 'ship_class': 'Arleigh Burke',
        'equipment': 'Auxiliary cooling-water pump strainer',
        'symptom': 'Differential pressure rising faster than expected between scheduled cleanings. SIM-DPI-301 reached 6 psid in two weeks instead of the usual four-week interval.',
        'actions_taken': 'Opened strainer SIM-ST-301. Basket SIM-BK-301 contained fine sediment and biological growth not typical of normal seawater filtration. Cleaned basket and inspected seal SIM-G-301 — seal intact. Took water sample upstream of strainer for comparison.',
        'outcome': 'Post-cleaning differential pressure returned to 0.8 psid. Accelerated fouling may indicate a change in water intake conditions. Recommend shortening inspection interval to weekly until trend normalizes. Upstream sample retained for shore-side analysis.',
        'technician': 'FC3 Kluzak', 'location': 'DEMO compartment 01',
    },
]

now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
with store.connect() as c:
    c.execute('CREATE TABLE IF NOT EXISTS troubleshooting(id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
    existing = c.execute('SELECT COUNT(*) FROM troubleshooting').fetchone()[0]
    if existing:
        print(f'Troubleshooting table already has {existing} records. Skipping seed.')
        sys.exit(0)
    for r in REPORTS:
        record = {
            **r,
            'id': str(uuid.uuid4()),
            'job_id': 'DEMO-SEED',
            'ship_id': '',
            'equipment_id': '',
            'notes': '',
            'recorded': now,
            'draft_version': 0,
            'procedure': None,
            'evidence': [],
            'job_status': 'Completed locally',
            'status': 'Technician report — unverified',
            'scope': 'Class match only; verify hull, equipment configuration and procedure applicability.',
        }
        c.execute('INSERT INTO troubleshooting VALUES (?,?)', (record['id'], store.seal(record)))
    print(f'Seeded {len(REPORTS)} troubleshooting reports for Arleigh Burke class.')
