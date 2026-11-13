# WarClaw hosted workspace

Run `hatch.warclaw:app` behind a same-origin `/fleethacker/` reverse proxy.
This deployment starts with synthetic demo data only. Do not copy a workstation's
`data/`, `.env`, encryption key, uploads, or restricted reference corpus.

1. Install the hash-pinned runtime dependencies from `requirements.lock` in an
   isolated virtual environment. Keep deployment tooling up to date separately.
2. Create a private WarClaw Web app owned by the deployment owner, with variable
   `__hosted_app` set to `fleethacker`. Install the WarClaw allowlisted hosted-app
   launcher. Set `HATCH_WARCLAW_APP_ID` to this app's ID.
3. Create a private state directory and a mode-0600 environment file from the
   example. Set `HATCH_DATA` there. Run `scripts/seed_shared_demo.py` with that
   environment **once on an empty directory**; the script replaces the corpus.
   Keep the generated encryption key with the encrypted state for backups.
   Then run `scripts/seed_warclaw_demo.py` in that same synthetic environment to
   associate untouched demo work orders with a sample ship. This second script
   skips records that have already been edited and is safe to repeat.
4. Run the service bound to a private interface reachable only by the ingress.
   Substitute absolute install/state paths and the private bind address in the
   service template. Enable the service for restart after login/boot as appropriate.
5. Add the Caddy route example to the existing WarClaw site, retaining the
   existing default upstream in its own `handle` block. Validate before reload.

The wrapper delegates the browser's `er_session` cookie to WarClaw's app lookup
on **every request**. A missing session is denied; a revoked app share takes effect
on the next request. Shared view users can read; mutations require edit access
and the configured same-origin Origin header. Authentication outages fail closed.
The only unauthenticated endpoint is `/_warclaw_health`, which exposes no records.

The data is one shared workspace, not a separate database per WarClaw user.
Only share this app with users who may read the whole workspace. Use normal
WarClaw Web app sharing to grant view or edit access. Uploading new material
changes the synthetic-only scope and requires a separate data handling review.
The model credential belongs in the private server environment, never in the
Web app variables or frontend. Hosted model requests disable upstream global
retrieval/tools; they use the workspace's own supplied context.

Verification: Python unittest discovery, `npm run test:ui`, pip-audit of the
installed environment, unauthenticated denial, real WarClaw view/edit/revocation
checks, and browser launch/assets/downloads under the URL prefix. This is not a
security accreditation or approval to process restricted maintenance documents.

Rollback: restore the previous Caddy site and launcher asset, validate/reload,
then stop the FleetHacker service. Preserve encrypted state and its key. Removing
or unsharing the native Web app also revokes access immediately.
