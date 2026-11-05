# Fleet Tech deployment candidate

For the repeatable build → CVE scans → live HTTP probes → report demonstration, see [Security demo](../docs/SECURITY_DEMO.md). Run `python3 scripts/security_demo.py` and open `security/evidence/readiness.html`.

This is a local demonstration with generated evidence, not Iron Bank acceptance, UDS certification, an ATO, or approval to operate on fleet networks.

## Evidence and claim boundaries

- The container build uses a digest-pinned public Python base and hash-locked Python dependencies. It does NOT yet use an Iron Bank base. Its dependency acquisition requires Internet access.
- The Docker build context is allowlisted: application code, static UI, synthetic/public config and the dependency lock. No local database, uploaded manuals, device key, model weights or host credentials are included.
- The offline smoke test uses `--network none`, a non-root UID, read-only root filesystem, dropped capabilities and a temporary data volume. It tests startup, work-order completion and encrypted record persistence. It does NOT test local model inference, fleet delivery, or an air-gapped build.
- Helm lint/render verifies template structure only. The chart has one replica (SQLite), PVC storage and default-deny networking. UDS mode generates a Package CR with no public exposure. UDS admission, Istio, storage, SSO, policy and disconnected deployment have NOT been tested.
- Bandit findings are reported without suppression. URL-opening findings require verification of loopback enforcement and redirects. SQL construction findings require review of fixed/allowlisted table and column names. Scan success is not absence of security defects.
- Dependency vulnerability results are point-in-time database checks. A scan error or missing scanner is NOT a passing result.

## Gates before fleet integration

1. Implement identity, authentication, authorization, session handling and audit records; the current app has no user authentication. Do not expose this prototype to an operational network.
2. Replace the locally stored encryption key with an approved key-management design; complete whole-database and backup protection. FIPS validation is not claimed.
3. Add bounded PDF parsing and resource-isolated ingestion; scan uploaded content and validate reference provenance. Cryptographic integrity and model prompt boundaries need adversarial tests.
4. Package and scan the local inference server and licensed model weights, define resource needs, and test a same-pod loopback inference sidecar. The app currently permits only loopback model endpoints.
5. Implement and validate the actual onboard/shore sync transports, conflict handling and ERP interfaces. Current receipts are simulated in one SQLite instance.
6. Pin/sign the released application image and package; add trusted build provenance, signature verification and release/rollback checks. A local image ID or SHA-256 inventory is not a trusted signature.
7. Rebase on an authorized Iron Bank image, pre-stage every build dependency, complete a valid hardening manifest and maintenance ownership, submit through Repo1, and disposition pipeline findings.
8. Build a Zarf package and deploy to the target UDS Core version. Validate Package CR admission, mesh behavior, SSO/RBAC, least-privilege network rules, storage/backup, air-gap installation and uninstall/rollback.
9. Review dependencies and redistribution terms, including PyMuPDF/MuPDF licensing, before delivery. No blanket licensing approval is claimed.

## Demonstration sequence (60–90 seconds)

1. Open `/security/readiness`. Show the timestamp, source fingerprint, tested image ID, scan findings and untested gates.
2. Show the container SBOM and raw reports under `security/evidence`. Distinguish application dependency results from the complete OS image scan.
3. Run `python3 scripts/container_smoke.py fleet-tech:demo`. Show measured startup time and `network_mode: none`. This is a repeatable workstation measurement, not a fleet deployment SLA.
4. Show `deploy/zarf.yaml`, the Helm chart and the unsubmitted Iron Bank manifest example. Explain what remains to be validated.

Suggested narration:

“We are shortening the delivery path by shipping the application with its dependency inventory, scan evidence and deployment configuration. This build starts without network access and captures a maintenance completion locally. We can show the exact image and what we tested. Our next integration gates are identity, the local model package, actual fleet sync, Iron Bank's pipeline and validation on the target UDS platform. We are demonstrating a repeatable deployment candidate, not claiming an operational authorization.”

## Sources checked for this implementation

- Iron Bank overview: https://docs-ironbank.dso.mil/overview/
- Iron Bank manifest: https://docs-ironbank.dso.mil/hardening/manifest/
- Iron Bank pipeline: https://docs-ironbank.dso.mil/quickstart/pipeline/
- UDS package requirements: https://docs.defenseunicorns.com/core/v1-16/concepts/configuration--packaging/package-requirements/
- UDS Package CR reference: https://docs.defenseunicorns.com/core/v1-15/reference/operator--crds/packages-v1alpha1-cr/
- Zarf create: https://docs.zarf.dev/commands/zarf_package_create/

The documents are versioned; pin the target platform versions before testing.

## Reproduce the evidence locally

Prerequisites: Docker, Python 3, npm, Helm and Syft. The first build and scans need Internet access to acquire dependencies and vulnerability databases. Application runtime smoke testing then disables networking. The scan runs against local code and container contents; pip-audit and npm audit query dependency advisory services.

```sh
python3 -m venv .security-venv
.security-venv/bin/python -m pip install -r security/requirements-tools.txt
docker build -t fleet-tech:demo .
python3 scripts/container_smoke.py fleet-tech:demo
python3 scripts/security_scan.py --image fleet-tech:demo
python3 scripts/readiness_report.py
```

The scan command returns 2 for tooling or test errors. Findings remain in the reports even when a scanner itself completes successfully. Review the generated page and raw reports before making any passing claim. The `image.tar` file is a local scanner input and excluded from version control.

In the running app, choose **06 Deckplate impact → View security scans & deployment evidence**. Restart the app after installing this route. To serve the evidence from a container, mount the generated directory read-only and set `HATCH_SECURITY_EVIDENCE` to its mount path. Evidence is intentionally separate from the application image to avoid embedding a stale self-referential image digest.
