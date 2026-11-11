# Hyperlink Audit

Last full audit: **2026-11-11**

The audit covers:

- Markdown links in the repository;
- relative documentation links;
- Markdown anchors;
- HTML `href` / `src` targets;
- console static assets;
- unique external destinations referenced by docs or runtime source.

## Internal links

All real internal repository links resolve.

The automated regression test is:

~~~bash
python scripts/check_links.py
~~~

It runs in CI through `pytest` and fails when a Markdown/HTML target or anchor no longer exists.

## External destinations verified

The following unique public destinations were checked during the 2026-11-11 audit:

- https://github.com/NVIDIA/garak/issues/2453
- https://github.com/elastic/detection-rules/issues/6722
- https://atlas.mitre.org/
- https://www.nist.gov/itl/applied-cybersecurity/nice/nice-framework-resource-center
- https://multipass.run/
- https://api.openai.com/v1/responses

The OpenAI Responses endpoint is an authenticated API endpoint. An unauthenticated request returning HTTP 401 is expected and confirms the route exists.

`multipass.run` currently redirects to Canonical's Multipass product page; that redirect is valid.

## Live external audit

External availability is intentionally **not** part of normal CI because third-party downtime, bot protection, or authentication could create false failures.

Run an explicit live audit when preparing a release:

~~~bash
python scripts/check_links.py --external
~~~

HTTP 401/403 is treated as reachable for protected endpoints.

## Policy

When adding a documentation or UI hyperlink:

1. prefer an official / authoritative source;
2. use repository-relative links for internal docs;
3. avoid hard-coded local filesystem links;
4. keep external URLs stable and canonical where practical;
5. rerun the explicit external audit before a tagged release.

## Customer-routing policy

Competitor training-platform URLs are intentionally excluded from the learner-facing product and public product-reference documentation. Market benchmarking informs AASL pricing internally without sending learners to competing training services.
