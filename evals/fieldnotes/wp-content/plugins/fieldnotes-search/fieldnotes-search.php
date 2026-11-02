<?php
/* Plugin Name: Fieldnotes Search
Version: 2.4
*/
add_action('rest_api_init', function () {
    register_rest_route('fieldnotes/v2', '/lookup', [
        'methods' => 'GET',
        'permission_callback' => '__return_true',
        'callback' => function ($request) {
            $query = trim((string) $request->get_param('q'));
            if (strlen($query) < 2) {
                return new WP_Error('query_short', 'Enter at least two characters.', ['status' => 400]);
            }
            return get_posts(['s' => $query, 'post_status' => 'publish']);
        },
    ]);
});
