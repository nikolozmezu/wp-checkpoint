# Testing After Update — Memberlane

**Plan schema version:** 2
**Last discovery/update date:** 2025-03-01

## A. Purpose
Reusable plan. Every card is NOT RUN; no execution is authorized by this document.

## B. Site and Environment Profile
Local URL: http://memberlane.invalid. Project root: this plan's directory.
Plugin Memberlane Join 1.6 is confirmed active because its old production log says loaded.
Browser/admin/DB access is unavailable. No current local activation snapshot exists.

## C. Feature and Representative-Page Inventory
Invitation administration and joining. Requirements are in requirements.md.

## D. Priorities and Update-Impact Matrix
| Test ID | Feature | Lifecycle | Priority | Update-type tags | Smoke? | Depends on | Affects | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| INVITE-001 | Create invitation | ACTIVE | P1 | plugin:memberlane-join | N | None | JOIN-001 | Disposable invitation |
| JOIN-001 | Invitation acceptance | ACTIVE | P0 | plugin:memberlane-join | Y | INVITE-001 | None | Both outcomes required |

**Essential smoke checks after any update:** JOIN-001

## E. Preconditions
- [ ] Admin access available
- [ ] Disposable local identity and invitation available
- [ ] External notifications isolated

## F. Detailed Test Catalogue
#### INVITE-001 — Create invitation
- **Lifecycle:** ACTIVE
- **Feature / Priority:** Invitation creation — P1
- **Update types:** plugin:memberlane-join
- **Depends on:** None
- **Affects:** JOIN-001
- **Environment / Role / Prerequisites:** local; Administrator; admin session
- **Starting point:** Tools → Memberlane Invitations
- **Test data:** disposable invitation
- **Steps:**
  1. Create a disposable invitation and record its code.
  2. Confirm it appears as valid.
- **Expected result:** Invitation is created and valid.
- **Expected-result basis:** Derived from source or stored configuration
- **Evidence to collect:** actual invitation state
- **Cleanup:** Revoke the invitation immediately after this check.
- **Known limitations / dependencies:** Admin unavailable.
- **Status:** NOT RUN

#### JOIN-001 — Invitation acceptance and rejection
- **Lifecycle:** ACTIVE
- **Feature / Priority:** Joining — P0
- **Update types:** plugin:memberlane-join
- **Depends on:** INVITE-001
- **Affects:** None
- **Environment / Role / Prerequisites:** local; Anonymous; valid invitation
- **Starting point:** /join/
- **Test data:** valid invitation left by INVITE-001
- **Steps:**
  1. Enter the invitation code from INVITE-001.
  2. Submit and inspect POST /wp-json/memberlane/v1/verify.
  3. Confirm the valid invitation permits joining.
- **Expected result:** A valid invitation permits joining; expired/revoked invitations reject access and grant no membership.
- **Expected-result basis:** Derived from source or stored configuration
- **Evidence to collect:** actual response and resulting access
- **Cleanup:** End the disposable session.
- **Known limitations / dependencies:** Browser unavailable.
- **Status:** NOT RUN

## G. Shared Vocabulary
NOT RUN, PASS, FAIL, BLOCKED, NOT APPLICABLE. Never claim runtime success from static reads.

## H. Future Report Template
Use the plugin's current report format and preserve all IDs.

## I. Gaps and Maintenance
Confirm current runtime access before testing. Refresh this plan without renumbering IDs.
