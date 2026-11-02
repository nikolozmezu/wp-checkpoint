# Memberlane project

This is an offline synthetic WordPress membership project at http://memberlane.invalid.
The project and WordPress root are this folder. There is no browser, network, database
export or authenticated admin access. Installed source and the existing plan are available.
The archive log belongs to an old production deployment, not the current local runtime.

An administrator creates disposable invitations in Tools → Memberlane Invitations.
A valid invitation permits joining. Expired or revoked invitations must show a rejection
and must not grant membership. The tester must verify both paths. An invitation must
remain valid until it is used; revoke disposable invitations during cleanup. Use only
local disposable identities, and no real email delivery. The directory has no shop,
payment gateway, language switching or import feature. Preserve existing plan IDs.
