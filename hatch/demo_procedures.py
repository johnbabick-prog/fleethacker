"""Representative maintenance checklists; approved equipment instructions govern execution."""
import hashlib
TASKS={
 'demo-watch-electrical':('Electrical distribution panel voltage checks','Electrical distribution panel',[
  'Identify the specified test points, nominal supply and acceptance limits from the applicable electrical maintenance card.',
  'Confirm the meter, leads, calibration status and protective equipment meet the approved test requirements. Complete required meter verification.',
  'Obtain authorization for the required equipment condition and any energized testing; use the approved test method and access controls.',
  'Measure and record each required voltage, test-point identifier, units and equipment condition using the approved sequence.',
  'Compare readings with the documented limits. Record abnormal readings and stop for the prescribed discrepancy response; do not adjust equipment without authorization.' ]),
 'demo-watch-electrical-2':('Electrical motor terminal inspection','Auxiliary pump motor',[
  'Identify the motor, terminal enclosure and approved electrical isolation boundary; confirm required isolation verification before opening.',
  'Inspect accessible leads, insulation and terminals for discoloration, damage, moisture or corrosion as directed by the maintenance card.',
  'Inspect cable supports, glands and enclosure seals; record defects and photograph affected locations.',
  'Perform only the cleaning or connection checks specified in the approved card. Use the stated materials and torque requirements where applicable.',
  'Restore the enclosure and conduct the authorized post-maintenance checks; record any unresolved defects before requesting return to service.' ]),
 'demo-watch-electrical-3':('Emergency lighting battery condition test','Emergency lighting unit',[
  'Identify the lighting unit, battery type and approved inspection and test criteria.',
  'Inspect the enclosure and battery for damage, leakage or swelling without disturbing unsafe components.',
  'Check the charger indications and record the initial condition against the maintenance card.',
  'Perform the approved functional test for the specified duration and record illumination and battery indications.',
  'Restore normal supply, verify the required charging indications and document any failed test or replacement requirement.' ]),
 'demo-watch-mechanical':('Auxiliary cooling-water valve replacement','Auxiliary cooling-water isolation valve',[
  'Verify the replacement valve specification, flow direction, pressure rating and required seals against the approved parts list.',
  'Establish the approved isolation, drainage and pressure/temperature verification before opening the system.',
  'Remove the valve using the approved support and disassembly method; inspect exposed sealing faces and retain defect evidence.',
  'Install the verified replacement and specified seals using the approved alignment, fastener sequence and torque requirements.',
  'Conduct the authorized refill, venting and leak/function checks. Record results and any restrictions before requesting return to service.' ]),
 'demo-watch-mechanical-2':('Auxiliary steam-generator water chemistry check','Auxiliary steam generator — training installation',[
  'Confirm this task applies to an auxiliary, non-nuclear steam plant. Identify the approved chemistry instruction, sampling point and operating condition.',
  'Verify the required sampling equipment, sample conditioning provisions, PPE and chemical handling instructions.',
  'Collect and identify the sample using the approved sampling and cooling method; record collection time and operating condition.',
  'Run the chemistry tests specified for this plant using verified test equipment and reagents. Record each result with units and test method.',
  'Compare results with the plant-specific control limits and notify the responsible operator of deviations. Chemical dosing requires the approved instruction and authorization.' ]),
 'demo-watch-mechanical-3':('Cooling-water pump strainer inspection and cleaning','Auxiliary cooling-water pump strainer',[
  'Record the strainer identification and available differential-pressure or flow indication before shutdown, if required by the maintenance card.',
  'Complete the approved isolation, drain and zero-pressure verification before opening the strainer.',
  'Remove and inspect the basket and seals using the approved method; record damage and the type of collected debris.',
  'Clean the basket with approved materials and replace only verified defective components; reinstall using the specified sealing and fastening requirements.',
  'Restore the system under the approved sequence, check for leakage and record the required post-maintenance flow or pressure indications.' ]),
 'demo-watch-sonar':('SONAR cabinet cooling-air filter service','SONAR electronics cabinet cooling assembly',[
  'Identify the cabinet and filter specification; confirm the approved shutdown and access conditions.',
  'Inspect the accessible filter, air inlet and cooling path for contamination, obstruction or damage.',
  'Remove and service or replace the filter as specified; avoid disturbing adjacent connectors and electronics.',
  'Reinstall the verified filter in the specified orientation and secure the access covers.',
  'Perform the approved cooling indication and alarm checks; record observations and report unresolved airflow or temperature concerns.' ]),
 'demo-watch-sonar-2':('SONAR cabinet connector and cable inspection','SONAR cabinet cable interfaces',[
  'Identify the interfaces covered by the maintenance card and establish the required equipment shutdown and electrostatic-discharge controls.',
  'Inspect accessible cables, bend support and strain relief for abrasion, damage or loose support.',
  'Inspect the specified connector exteriors and locking features for corrosion, damage or looseness; do not disconnect interfaces unless the instruction requires it.',
  'Carry out only the approved cleaning or corrective actions and record the affected connector identifiers.',
  'Restore covers and perform the prescribed post-maintenance status checks; document remaining interface faults.' ]),
 'demo-watch-sonar-3':('SONAR equipment built-in test','SONAR operator console',[
  'Confirm the approved test procedure, authorized system mode and coordination requirements with the watch team.',
  'Record the initial system status and existing fault indications before starting the test.',
  'Run only the approved built-in test sequence and record the test identifier and completion status.',
  'Capture fault codes and messages exactly as displayed; compare them with the applicable troubleshooting reference.',
  'Restore the authorized operating configuration and report unresolved faults. Further troubleshooting follows the approved fault-isolation procedure.' ])
}
CORRECTIVE_TASKS={
 'demo-corrective-electrical':('Diagnose lighting zone failure','Electrical distribution panel','corrective',[
  'Identify the affected lighting zone, circuit designator and distribution panel from the reported discrepancy.',
  'Interview the reporting sailor: when did it fail, was it intermittent or sudden, were any other systems affected at the same time?',
  'Verify the circuit breaker position and condition. Record tripped, closed or damaged. Check adjacent breakers for related tripping.',
  'Inspect accessible wiring runs, junction boxes and fixture connections in the affected zone for visible damage, discoloration or moisture.',
  'Measure voltage at the panel output and at the first accessible fixture. Record both readings with test-point identifiers.',
  'Compare findings with class troubleshooting history. Record the probable cause, what was verified, and what remains uncertain.',
  'Document the corrective action taken or the recommended follow-up. Attach evidence photographs and update the watch handoff.' ]),
 'demo-corrective-mechanical':('Investigate cooling-water leak','Auxiliary cooling-water isolation valve','corrective',[
  'Identify the reported leak location, affected system and isolation boundaries from the discrepancy report.',
  'Verify system pressure and flow indications. Record gauge readings and note any abnormal trends since the last watch.',
  'Inspect accessible piping, valve bodies, flanges and packing glands in the reported area. Mark and photograph leak sources.',
  'Assess leak severity: seepage, drip or spray. Determine if immediate isolation is required or if monitoring is adequate.',
  'Check maintenance history and class troubleshooting reports for similar leaks on this equipment or piping run.',
  'Record findings, actions taken, and whether the system remains in service with restrictions or requires isolation and follow-up repair.' ]),
 'demo-corrective-sonar':('Troubleshoot SONAR fault indication','SONAR operator console','corrective',[
  'Record the exact fault code, affected channel and operating mode when the fault appeared.',
  'Run the built-in test sequence and compare results with the original fault indication. Record any new or changed codes.',
  'Check cabinet cooling, connector seating and cable condition in the area associated with the fault code.',
  'Review class troubleshooting history for this fault code or related symptoms on sister ships.',
  'If the fault clears after inspection, document what was found and what changed. If it persists, record the isolation boundary for the next level of maintenance.',
  'Update the watch handoff with the fault timeline, what was checked, and what the next watch needs to verify.' ]),
}
TASKS.update({k:(v[0],v[1],v[3]) for k,v in CORRECTIVE_TASKS.items()})
SIMULATOR_STEPS={
 'demo-watch-electrical':[
  'Set selector SIM-ES-101 to TEST. Confirm indicator SIM-L-101 reads TEST ENABLED.',
  'Select meter SIM-VM-101 and test-point pair SIM-TP-01/02. Record the displayed voltage; target: 24.0 V DC, acceptable band: 23.5–24.5 V DC.',
  'Select SIM-TP-03/04 and record the second channel. Target: 12.0 V DC, acceptable band: 11.8–12.2 V DC.',
  'Check alarm SIM-A-101. Record NORMAL or FAULT; flag any reading outside the band and do not mark the check passed.',
  'Return selector SIM-ES-101 to NORMAL and confirm SIM-L-101 reads TEST DISABLED.' ],
 'demo-watch-electrical-2':[
  'Set motor switch SIM-MS-201 to OFF. Confirm RUN lamp SIM-L-201 is OFF and isolation status SIM-ISO-201 is VERIFIED.',
  'Open the terminal-cover view SIM-TB-201. Check terminals T1, T2 and T3 for the indicators: loose connection, discoloration or damaged insulation.',
  'Check cable supports SIM-CS-201 and SIM-CS-202. Record each as SECURE or DEFECT; attach an image of any displayed defect.',
  'Select test SIM-CT-201. Record displayed connection-check results for T1, T2 and T3; pass condition: all three show PASS.',
  'Close the cover and run SIM-BIT-201. Confirm COVER CLOSED and TEST PASS; leave SIM-MS-201 OFF pending supervisor release.' ],
 'demo-watch-electrical-3':[
  'Check charger switch SIM-CH-301 is NORMAL and indicator SIM-L-301 is green. Record battery gauge SIM-BV-301; target: 12.6 V DC.',
  'Inspect battery SIM-BAT-301 and record the displayed condition: NORMAL, SWELLING or LEAKAGE. A defect blocks the test.',
  'Set selector SIM-EL-301 to TEST and start the 30-second timer. Confirm emergency lamp SIM-L-302 is ON.',
  'At 30 seconds, record SIM-BV-301. Pass condition: at least 12.0 V DC and SIM-L-302 remains ON.',
  'Return SIM-EL-301 to NORMAL. Confirm charging indicator SIM-L-301 is green and record the test result.' ],
 'demo-watch-mechanical':[
  'Set pump switch SIM-PS-101 to OFF. Close upstream valve SIM-V-101 and downstream valve SIM-V-102. Confirm all three position indicators match.',
  'Open drain SIM-V-103. Check gauge SIM-PI-101 reads 0 psig and isolation status SIM-ISO-101 reads VERIFIED before unlocking the work view.',
  'Select valve SIM-V-104 for removal. Match replacement part SIM-PN-V104 and seal kit SIM-SK-104; record stock used: one valve and one kit.',
  'Install the replacement in the assembly. Confirm SIM-V-104 shows INSTALLED, direction arrow matches the drawing, and assembly check SIM-AC-104 reports PASS.',
  'Run the RESTORE sequence: SIM-V-103 CLOSED, SIM-V-101 and SIM-V-102 OPEN, SIM-PS-101 RUN. Record SIM-PI-101; target 30 psig, band 28–32 psig. Confirm leak indicator SIM-LK-104 reads NONE.' ],
 'demo-watch-mechanical-2':[
  'Select the auxiliary steam-generator chemistry station SIM-SG-201.',
  'Set sample selector SIM-SS-201 to SAMPLE A and confirm SIM-SAMPLE-READY is green. Read temperature indicator SIM-TI-201; display target: 25 °C.',
  'Create sample SIM-SG201-A and record the timestamp. Select analyzer SIM-AN-201 and confirm its self-check reads PASS.',
  'Record analyzer values: pH 8.5 and conductivity 100 µS/cm. Compare with limits: pH 8.3–8.7 and conductivity 90–110 µS/cm.',
  'Set SIM-SS-201 to CLOSED, save the sample results and flag any deviation. Do not calculate or perform chemical dosing from this checklist.' ],
 'demo-watch-mechanical-3':[
  'Record differential-pressure gauge SIM-DPI-301. The starts at 8 psid, above the service threshold of 5 psid.',
  'Set pump switch SIM-PS-301 to OFF, close valves SIM-V-301 and SIM-V-302, and open drain SIM-V-303. Confirm SIM-PI-301 reads 0 psig and SIM-ISO-301 reads VERIFIED.',
  'Open strainer SIM-ST-301 and inspect basket SIM-BK-301. Record DEBRIS PRESENT, CLEAN or DAMAGED and capture the displayed condition.',
  'Select CLEAN BASKET or REQUEST REPLACEMENT. Reinstall basket SIM-BK-301 and seal SIM-G-301; confirm assembly status CLOSED / PASS.',
  'Run the RESTORE sequence. Confirm SIM-V-303 CLOSED, SIM-V-301 and SIM-V-302 OPEN, and SIM-PS-301 RUN. Record SIM-DPI-301; pass band: 0–2 psid with leak indication NONE.' ],
 'demo-watch-sonar':[
  'Set cabinet switch SIM-CS-401 to MAINTENANCE and confirm SIM-ISO-401 is VERIFIED. Record cooling gauge SIM-DPI-401; initial value: 0.8 in H2O.',
  'Open access panel SIM-AP-401. Inspect filter SIM-F-401 and inlet screen SIM-SC-401; record contamination or damage.',
  'Replace filter SIM-F-401 with part SIM-PN-F401. Confirm the airflow arrow matches the cabinet arrow and record one filter consumed.',
  'Close SIM-AP-401 and set SIM-CS-401 to NORMAL. Confirm fan indicator SIM-FAN-401 is RUNNING.',
  'Record SIM-DPI-401 and temperature indicator SIM-TI-401. Pass limits: differential pressure at most 0.3 in H2O, temperature 20–30 °C, and SIM-A-401 alarm NORMAL.' ],
 'demo-watch-sonar-2':[
  'Set cabinet switch SIM-CS-501 to MAINTENANCE and confirm isolation status SIM-ISO-501 is VERIFIED.',
  'Inspect cables SIM-CBL-501 and SIM-CBL-502. Check supports SIM-CL-501 through SIM-CL-504 and record SECURE or DEFECT for each.',
  'Inspect connector exteriors SIM-J-501, SIM-J-502 and SIM-J-503. Record locking indication LOCKED or UNLOCKED and any visible corrosion or damage.',
  'Run interface check SIM-IT-501. Record channels CH-1, CH-2 and CH-3 individually; pass condition: each shows PASS.',
  'Close the access view, return SIM-CS-501 to NORMAL and confirm status SIM-A-501 reads NO INTERFACE FAULT.' ],
 'demo-watch-sonar-3':[
  'Select console SIM-CON-601 and set mode selector SIM-MS-601 to TRAINING. Confirm SIM-L-601 reads TRAINING ONLY.',
  'Record initial status indicators SIM-PWR-601, SIM-COOL-601 and SIM-LINK-601. Prerequisite: all three display NORMAL.',
  'Select test SIM-BIT-601 and press START. Wait for the 15-second test to finish.',
  'Record test result SIM-R-601 and any displayed code. PASS with code 000 is the successful result; code E101 indicates a interface fault requiring a follow-up record.',
  'Select END TEST, confirm SIM-BIT-601 is IDLE and leave SIM-MS-601 in TRAINING. Save the displayed results and unresolved faults.' ]
}
CORRECTIVE_STEPS={
 'demo-corrective-electrical':[
  'Reported: lighting zone 2 forward went dark at 0215. No other systems affected. Zone was working normally at 0200 rounds. No work in adjacent spaces.',
  'Locate panel SIM-LP-201. Check circuit breaker SIM-CB-LZ2: position reads TRIPPED. Adjacent breakers SIM-CB-LZ1 and SIM-CB-LZ3 are CLOSED/NORMAL.',
  'Reset SIM-CB-LZ2 to CLOSED. Monitor for 60 seconds. Result: breaker holds — no immediate retrip. Zone 2 forward lighting restored.',
  'Measure load current on SIM-CB-LZ2 with clamp meter SIM-CM-201: reads 4.2 A on a 15 A breaker. Within normal range.',
  'Inspect junction box SIM-JB-LZ2-FWD. Fixture connector SIM-FC-207 shows discoloration and signs of arcing on the neutral terminal.',
  'Record: breaker tripped due to suspected arcing at SIM-FC-207. Zone restored after reset. Connector requires replacement at next maintenance period. Monitoring for retrip.',
  'Photograph SIM-FC-207 damage. Update watch handoff: zone 2 forward restored, breaker holding, connector replacement needed, monitor every 30 minutes until next watch.' ],
 'demo-corrective-mechanical':[
  'Reported: drip observed at base of valve SIM-V-104 during 0400 rounds. Approximately one drip every 3 seconds. No associated pressure or flow anomaly reported.',
  'Check gauge SIM-PI-101: reads 30 psig, within normal band (28–32 psig). Flow indicator SIM-FI-101 shows NORMAL. System operating parameters are stable.',
  'Inspect valve body SIM-V-104. Leak source: packing gland SIM-PG-104. Moisture visible around the gland follower. No pipe or flange wetness.',
  'Assess severity: seepage, approximately 15 mL/hr estimated. Containment: drip pan SIM-DP-104 in place, not overflowing. Bilge level monitor SIM-BL-01 reads NORMAL.',
  'Class history shows DDG-65 Benfold recorded similar packing seepage on this valve model — resolved by packing adjustment, not replacement. Verify torque specification.',
  'Tighten packing gland SIM-PG-104 one-quarter turn. Wait 10 minutes. Leak rate reduced to trace weep — within acceptable limits. No isolation required.' ],
 'demo-corrective-sonar':[
  'Reported: fault code E101 (interface fault) appeared on SIM-CON-601 during active tracking. Operator lost CH-2 data. CH-1 and CH-3 remained operational.',
  'Run built-in test SIM-BIT-601. Result: E101 confirmed on CH-2. CH-1 code 000 (PASS). CH-3 code 000 (PASS). Fault is repeatable and isolated to channel 2.',
  'Set SIM-CS-501 to MAINTENANCE. Inspect connector SIM-J-502 (CH-2 interface). Locking ring is LOCKED but corrosion visible on pin face. Adjacent SIM-J-501 and SIM-J-503 are clean.',
  'Clean connector SIM-J-502 with approved contact cleaner. Reseat and verify locking ring torque. Corrosion was light surface oxidation, no pit damage visible.',
  'Return SIM-CS-501 to NORMAL. Rerun SIM-BIT-601. Result: CH-2 now shows code 000 (PASS). All three channels operational. Fault cleared.',
  'Record: E101 caused by corroded CH-2 connector. Cleaned and reseated. Recommend adding SIM-J-502 to accelerated inspection interval for this hull. Monitor for recurrence.' ],
}


# Synthetic workflow checklists for the original demo work orders.
TASKS.update({
 'demo-equipment-condition': ('Equipment condition inspection', 'Selected demo equipment', []),
 'demo-consumables-check': ('Maintenance consumables readiness check', 'Selected demo equipment', []),
})
SIMULATOR_STEPS.update({
 'demo-equipment-condition': [
  'Demo exercise: identify the selected equipment and record its displayed asset tag and compartment. These steps are synthetic, not an approved maintenance card.',
  'Inspect the simulated enclosure, access covers and labels. Record each condition as INTACT or DEFECT; attach an example photograph for a defect.',
  'Read the simulated power, cooling and fault status indicators. Record their displayed states without changing the equipment configuration.',
  'Inspect the simulated external cable supports and cooling inlets. Record visible obstruction, loose support or damage against its location.',
  'Compare the observations with the demo baseline: enclosure INTACT, indicators NORMAL, cooling inlet CLEAR. Record deviations as follow-up work rather than marking them passed.',
 ],
 'demo-consumables-check': [
  'Demo exercise: open the selected equipment inventory snapshot and record its timestamp. These steps are synthetic, not an approved maintenance card.',
  'Match each planned consumable to its equipment model, part identifier and unit of issue in the demo parts list.',
  'Record required, on-hand and reserved quantities separately. Calculate available stock as on-hand minus reserved.',
  'Compare available quantities with the planned requirement. Mark each item AVAILABLE, SHORT or UNKNOWN; record the shortage quantity where known.',
  'Record the demo storage location and any replenishment request. Keep the job blocked when required stock is short or unverified.',
 ],
})

def structured(source):
    if source not in TASKS:return None
    title,asset,work=TASKS[source]
    corrective=source in CORRECTIVE_TASKS
    if corrective:
        steps=[
          f'Confirm the reported discrepancy, affected equipment ({asset.lower()}) and work-order assignment.',
        ]+list(CORRECTIVE_STEPS[source])+[
          'Record all findings, measurements, photographs and remaining uncertainty. Attach the evidence to the work order.',
          'Update the watch handoff with what was found, what was done, and what the next watch needs to monitor or verify.'
        ]
        return {'source':source,'title':title,'revision_hash':hashlib.sha256(('CORRECTIVE v2\n'+title+'\n'+'\n'.join(steps)).encode()).hexdigest(),'sections':steps,'structured_steps':True,'corrective':True,'scope':'Corrective maintenance fault-isolation procedure.'}
    work=list(SIMULATOR_STEPS[source])
    steps=[
      f'Confirm the work-order identifier, assigned technician, ship and equipment identity for {asset.lower()}.',
      'Review hazards, prerequisites, required qualifications, permits and tag-out/isolation requirements with the responsible supervisor.',
      'Verify required tools, calibrated instruments, consumables and replacement parts against the task requirements and current stock.'
    ]+work+[
      'Record measured values, units, observations and discrepancies. Attach photographs and the completed handwritten log where required.',
      'Complete the required independent verification and supervisor/watch coordination. Record equipment status and outstanding restrictions.',
      'Save the maintenance results, parts used and follow-up work. Submit completion for the required review.'
    ]
    return {'source':source,'title':title,'revision_hash':hashlib.sha256(('MAINTENANCE v5\n'+title+'\n'+'\n'.join(steps)).encode()).hexdigest(),'sections':steps,'structured_steps':True,'scope':'Preventive maintenance procedure.'}
