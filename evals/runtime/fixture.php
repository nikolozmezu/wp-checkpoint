<?php
/**
 * Plugin Name: WP Checkpoint Runtime Fixture
 * Version: 1.0.0
 * Description: Disposable regression fixture only. Never install on a client site.
 */
if (!defined('WP_CHECKPOINT_FIXTURE') || WP_CHECKPOINT_FIXTURE !== true) {
    return;
}
add_filter('pre_wp_mail', '__return_false');
add_filter('pre_http_request', function () {
    return new WP_Error('fixture_offline', 'External services disabled in this fixture.');
}, 10, 3);
function checkpoint_fixture_broken() {
    return get_option('checkpoint_fixture_variant', 'healthy') === 'broken';
}
add_action('rest_api_init', function () {
    register_rest_route('checkpoint-fixture/v1', '/contact', [
        'methods' => 'POST', 'permission_callback' => '__return_true',
        'callback' => function ($request) {
            if (!is_email($request->get_param('email'))) {
                return new WP_Error('invalid_email', 'Enter a valid email.', ['status' => 400]);
            }
            if (checkpoint_fixture_broken()) {
                return new WP_Error('fixture_submit', 'Submission failed.', ['status' => 400]);
            }
            update_option('checkpoint_fixture_message', 'Synthetic local message');
            return ['message' => 'Message saved.'];
        },
    ]);
    register_rest_route('checkpoint-fixture/v1', '/cart', [
        'methods' => 'POST', 'permission_callback' => '__return_true',
        'callback' => function ($request) {
            if ($request->get_param('product_id') !== 'oak') {
                return new WP_Error('unknown_product', 'Unknown product.', ['status' => 400]);
            }
            return ['quantity' => checkpoint_fixture_broken() ? 2 : 1];
        },
    ]);
    register_rest_route('checkpoint-fixture/v1', '/search', [
        'methods' => 'GET', 'permission_callback' => '__return_true',
        'callback' => function ($request) {
            $query = trim((string) $request->get_param('q'));
            if (strlen($query) < 2) {
                return new WP_Error('query_short', 'Enter at least two characters.', ['status' => 400]);
            }
            return ['titles' => stripos('Oak field notes', $query) !== false ? ['Oak field notes'] : []];
        },
    ]);
});
add_action('template_redirect', function () {
    $route = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
    if (!in_array($route, ['/checkpoint-fixture/', '/checkpoint-fixture/catalogue/', '/checkpoint-fixture/fatal/'], true)) return;
    status_header(200);
    if ($route === '/checkpoint-fixture/fatal/') {
        if (checkpoint_fixture_broken()) {
            checkpoint_fixture_missing_function();
        }
        header('Content-Type: text/html; charset=utf-8');
        echo '<!doctype html><html><body><h1>PHP route ready</h1></body></html>';
        exit;
    }
    $catalogue = $route === '/checkpoint-fixture/catalogue/';
    $broken = checkpoint_fixture_broken();
    $api = rest_url('checkpoint-fixture/v1/');
    header('Content-Type: text/html; charset=utf-8');
    ?>
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Checkpoint fixture</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f0e8;color:#1d302b;font:17px/1.5 Arial,sans-serif}
main{max-width:900px;margin:0 auto;padding:40px 24px}nav{display:flex;gap:24px;border-bottom:1px solid #bbc5bf;padding-bottom:20px}
a{color:#285e4b}h1{font-size:42px;line-height:1.15}h2{font-size:24px}section{background:white;border-radius:12px;padding:24px;margin:24px 0}
label{display:block;margin-bottom:6px}input{display:block;padding:12px;width:100%;max-width:450px;border:1px solid #94a89c;border-radius:5px;margin-bottom:16px}
button{background:#285e4b;color:white;border:0;border-radius:5px;padding:12px 20px;font-size:16px;cursor:pointer}
output{display:block;min-height:32px;margin-top:16px}.card{border:1px solid #b7c6be}.eyebrow{letter-spacing:2px;font-size:12px;text-transform:uppercase}
@media(max-width:600px){main{padding:24px 16px}h1{font-size:32px}}
<?php if ($broken) echo '@media(max-width:600px){#buy-button{display:none}}'; ?>
</style></head><body><main>
<nav><a href="/checkpoint-fixture/">Field notes</a><a href="/checkpoint-fixture/catalogue/">Catalogue</a></nav>
<p class="eyebrow">Isolated WordPress evaluation</p>
<?php if ($catalogue): ?>
<h1>Field notes catalogue</h1><section class="card"><h2>Oak notebook</h2><p>A small catalogue fixture, powered by a custom WordPress plugin.</p><button id="buy-button" type="button">Add to cart</button><output id="cart" aria-live="polite">Cart: 0</output></section>
<?php else: ?>
<h1>Field notes</h1>
<section><h2>Article search</h2><form id="search-form"><label for="query">Search articles</label><input id="query" name="q"><button>Search</button></form><output id="results" aria-live="polite"></output></section>
<section><h2>Contact the editor</h2><form id="contact-form" novalidate><label for="email">Email</label><input id="email" name="email"><button>Send message</button></form><output id="message" aria-live="polite"></output></section>
<?php endif; ?>
</main><script>
const api = <?php echo wp_json_encode($api); ?>;
async function send(path, data) {
  const response = await fetch(api + path, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  return {response, body:await response.json()};
}
document.querySelector('#contact-form')?.addEventListener('submit', async event => {
  event.preventDefault();
  const {body} = await send('contact', {email:document.querySelector('#email').value});
  document.querySelector('#message').textContent = body.message;
});
document.querySelector('#buy-button')?.addEventListener('click', async () => {
  const {body} = await send('cart', {product_id:'oak'});
  document.querySelector('#cart').textContent = 'Cart: ' + body.quantity;
});
document.querySelector('#search-form')?.addEventListener('submit', async event => {
  event.preventDefault();
  const response = await fetch(api + 'search?q=' + encodeURIComponent(document.querySelector('#query').value));
  const body = await response.json();
  document.querySelector('#results').textContent = body.titles ? (body.titles.join(', ') || 'No matching articles.') : body.message;
});
</script></body></html>
<?php
    exit;
});
