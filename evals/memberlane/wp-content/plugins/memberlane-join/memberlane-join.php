<?php
/* Plugin Name: Memberlane Join
Version: 1.6
*/
add_action('admin_menu', function () {
    add_management_page('Memberlane Invitations', 'Memberlane Invitations', 'manage_options', 'memberlane-invitations', 'ml_invitation_admin');
});
add_action('wp_ajax_nopriv_ml_verify_invite', 'ml_verify_invite');
add_action('wp_ajax_ml_verify_invite', 'ml_verify_invite');
function ml_verify_invite() {
    $invite = ml_find_invite(sanitize_text_field($_POST['invite'] ?? ''));
    if (!$invite || $invite->revoked || $invite->expired) {
        wp_send_json_error(['message' => 'Invitation is not valid.'], 403);
    }
    wp_send_json_success(['can_join' => true]);
}
// Supporting invitation storage/admin helpers are outside this fixture.
