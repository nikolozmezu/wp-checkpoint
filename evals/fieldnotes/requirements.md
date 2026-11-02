# Fieldnotes project

This is an offline synthetic editorial WordPress project. No PHP or JS should be run.
The site URL is http://fieldnotes.invalid. The project and WordPress root are this folder.
There is no live reference or browser/admin session. The supplied options export is a
current read-only local snapshot; the archive directory contains older production data.

The site publishes articles. Readers search by a query of at least two characters;
short queries show a validation message, valid queries show matching titles or an empty
state. Editors need the ordinary draft, preview, publish and scheduled-publishing flow.
Email delivery, payments, membership and imports are not used by this project.
Tests must create disposable editorial data and clean it up without modifying existing
articles. The intended language is English. Current runtime success is not known.
