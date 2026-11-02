export async function verifyInvitation(invite) {
  const response = await fetch('/wp-admin/admin-ajax.php', {
    method: 'POST',
    body: new URLSearchParams({ action: 'ml_verify_invite', invite })
  });
  return { status: response.status, body: await response.json() };
}
