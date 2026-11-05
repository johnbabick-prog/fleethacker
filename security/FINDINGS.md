# Initial finding disposition

The raw JSON in `security/evidence` is authoritative for the associated scan run. Findings below are not risk acceptances or suppressions.

## Live HTTP probes — November 5, 2026

`scripts/security_probe.py` exercised 21 checks against a disposable, network-disabled container. Seventeen checks passed. Four findings remain: unauthenticated work-order reads (HIGH), unauthenticated completion with a created event (HIGH), acceptance of malformed PNG content based on its magic header (MEDIUM), and absent browser defense headers (LOW). These are local triage severities. The malformed upload demonstrates insufficient validation, not code execution. See `http-probes.json` for request outcomes and scope limitations, and [the walkthrough](../docs/SECURITY_DEMO.md) to reproduce the demonstration.

## High-priority remediation before operational deployment

- Full image scan reported 52 HIGH findings on the initial candidate: 47 in Debian packages and five in Python components present in the image. Counts are package/advisory findings, not unique CVE counts. There were no CRITICAL findings in that run.
- Python image-component findings include msgpack, setuptools and urllib3. They are outside the 19 locked application dependencies reported clean by pip-audit. Review SBOM package locations, remove unneeded build/package-management components from runtime, or update affected components; then rebuild and rescan.
- OS findings include both available fixes and findings with no reported fix. Rebase onto an appropriate supported/hardened image, apply available vendor fixes, and document applicability/mitigation with the receiving security team. Do not relabel unpatched findings as passed.
- Bandit findings remain review items: urllib request handling, dynamic SQL built with controlled identifiers, and process launch. Validate all request paths, schemes, redirects and fixed/allowlisted SQL values; document individual dispositions with evidence.
- Application authentication, roles, protected key storage and actual sync transport remain design/implementation gaps. Scanners do not establish these controls.

## Changes already made for the candidate

- Added a digest-pinned base and exact, hash-checked application dependencies.
- Excluded host databases, upload contents, local keys and model files from the image build context.
- Added non-root execution, a read-only root filesystem in deployment/test, capability dropping, health checks and default-deny network declarations.
- Fixed the namespace declaration flagged by the initial configuration scan; the subsequent configuration/secrets scan reported no findings in its defined source/config scope.

## Retest gates

Do not release until high findings have a receiving-authority-approved disposition and the missing controls are implemented. Run the same scanners against the final immutable image, record database/tool versions, generate an SBOM, bind evidence to the image digest, and verify the signed artifact through the actual Iron Bank/UDS delivery process. User data and local models need separate handling and scans.
