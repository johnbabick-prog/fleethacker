# Show the security workflow

Run a fresh build, CVE scans, static analysis, and bounded live HTTP security probes:

```sh
python3 scripts/security_demo.py
open security/evidence/readiness.html
```

The app also serves the generated page at `/security/readiness`. The run takes longer on a cold workstation because it downloads scanner images and advisory databases. Dependencies and advisory queries need Internet access; runtime smoke tests and HTTP probes use containers with `--network none`.

The page presents an assurance dashboard with validation coverage, an Iron Bank preparation matrix, searchable findings, HTTP probe outcomes, and an evidence library. **Export evidence index** downloads sanitized summaries and artifact hashes; **Print report** prints the current view. Artifact dialogs show the original file's fingerprint and let you download its summary. Raw artifacts stay in `security/evidence`. The dashboard does not claim Iron Bank acceptance or comprehensive penetration-testing coverage.

Page layout and interactions live in `security/templates/assurance.html`; `scripts/readiness_report.py` fills it from recorded reports. Run `python3 scripts/readiness_report.py` to update the HTML after a presentation change without repeating scans. Its source fingerprint continues to identify the original scan snapshot.

Prerequisites: Docker running, npm, Helm, Syft, and the project Python dependencies installed in the Python used to run the command. Install the pinned Python scanners once:

```sh
python3 -m venv .security-venv
.security-venv/bin/python -m pip install -r security/requirements-tools.txt
npm ci
```

The container build installs the hash-locked application dependencies. The host regression test step also needs application dependencies installed (`python3 -m pip install --require-hashes -r requirements.lock` in your application virtual environment).

## A three-minute walkthrough

1. **Identify what was tested.** Open the report and show the generation time, image ID, source fingerprint, and source/image match. `scan-run.json` records scanner versions and the Trivy database timestamp. These scans apply to that snapshot.
2. **Separate dependency checks from the whole image.** Show `pip-audit.json` and `npm-audit.json`, then `trivy-image.json`. The image contains OS packages and Python packaging tools beyond the application's dependency lock. Show the inventory in `sbom.cdx.json`.
3. **Demonstrate a real access-control failure.** Open `http-probes.json`. The disposable instance returns HTTP 200 to an unauthenticated work-order read and completion request. The completion creates an event. That is evidence of a missing control, even when application dependency audits are clear.
4. **Show defenses and weaknesses together.** Replay, oversized fields, invalid chat roles, non-loopback model configuration, upload size/type checks, filename traversal, static traversal and download headers are exercised. An invalid PNG with a valid magic header is accepted: file prefixes alone do not validate an image. Browser defense headers are also checked.
5. **Show the gate.** The command exits 1 when findings require review and 2 for execution errors. Rebuild and rerun after remediation. A clean scan would cover only the tested controls.

Suggested narration:

> “We build an identifiable artifact, inventory its components, check known advisories, review risky code patterns, and exercise the running API. Here, clean application dependency audits coexist with image CVEs and a confirmed missing access control. We retain the requests' outcomes, fix the controls, rebuild, and run the same checks again. The evidence shows both what worked and what still blocks release.”

## Initial observed results — November 5, 2026

The saved evidence is authoritative; later runs replace these files and may change the results.

| Layer | Observed result |
| --- | --- |
| Python lock and npm dependency advisories | Zero reported advisories in each audit |
| Full image | 52 HIGH, 74 MEDIUM, 63 LOW, 6 UNKNOWN package/advisory findings; zero CRITICAL |
| Bandit | 7 MEDIUM, 1 LOW; review required |
| Source configuration and secrets | Zero reported matches within the configured scope |
| Live HTTP probes | 21 checks: 17 passed, 4 findings |
| Runtime hardening | Non-root, read-only root, network disabled, encrypted completion payload and key mode 0600 passed |

The four HTTP findings are unauthenticated reads (HIGH), unauthenticated work-order completion (HIGH), acceptance of invalid PNG content (MEDIUM), and missing browser defense headers (LOW). These are local triage severities, not CVSS scores. Image counts represent package/advisory pairs, not unique CVEs. Acceptance of malformed content demonstrates insufficient validation; it does not establish code execution.

## Repeat individual stages

```sh
docker build -t fleet-tech:security-demo .
python3 scripts/container_smoke.py fleet-tech:security-demo
python3 scripts/security_scan.py --image fleet-tech:security-demo
python3 scripts/security_probe.py --image fleet-tech:security-demo
python3 scripts/readiness_report.py
```

The probe command intentionally returns 1 when findings exist; it is not a broken execution. Its JSON distinguishes `passed`, `findings`, and `error`. The aggregate runner continues to generate the report after findings. A failed build stops the runner so it cannot silently scan a previous image under the same tag. Logs and `security-demo.json` are retained in `security/evidence`.

## Scope and next work

The probe runner accepts an image name, not a target URL. It creates a uniquely named, resource-limited container with a disposable tmpfs database, exposes no host ports, issues requests only to that container's loopback interface, and removes the container afterward. It does not mount your working data or contact a model server. It generates one synthetic completion and one malformed attachment inside that disposable container.

This is a bounded automated security demonstration, not a comprehensive penetration test. No browser XSS execution, authenticated roles, TLS termination, model prompt injection, model endpoint redirects, denial-of-service campaign, or deployed cluster perimeter was tested. SQL-like input receiving HTTP 200 only confirms request handling; it does not prove SQL-injection resistance. The network-disabled environment also cannot validate actual external egress behavior.

Next: implement identity and per-work-order permissions; validate uploads in isolated bounded parsers; configure and browser-test security headers; disposition Bandit items; rebuild on a patched base and remove/update unnecessary runtime packages. Then repeat the same probes and scan the final image. A deployment assessment should add authenticated browser/API coverage and an agreed OWASP WSTG test plan.

OWASP ZAP is a useful next layer: its [baseline scan](https://www.zaproxy.org/docs/docker/baseline-scan/) spiders a target and performs passive scanning. Its [active scanner](https://www.zaproxy.org/docs/desktop/start/features/ascan/) sends attack requests. Neither was executed in this run; the recorded dynamic results come from `security_probe.py`. Use the [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) to plan broader coverage.
