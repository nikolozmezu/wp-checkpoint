export async function searchArticles(query) {
  const endpoint = new URL('/wp-json/fieldnotes/v2/lookup', window.location.origin);
  endpoint.searchParams.set('q', query);
  const response = await fetch(endpoint);
  return { status: response.status, body: await response.json() };
}
