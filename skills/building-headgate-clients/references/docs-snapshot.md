# Snapshot the API's docs

Before writing any client code, save the API's documented surface beside the client as `docs_paths.json`. The
method-name test (`check_names`) compares the client with it: a documented read with no method, a method whose path
the docs do not list, and a misnamed read all fail the test. The snapshot is what makes "one method per documented
endpoint, named after its path" checkable.

Both worked examples carry one: [lda](../../../examples/msgspec/lda/docs_paths.json) (one OpenAPI document) and
[Open-Meteo](../../../examples/pydantic/open_meteo/docs_paths.json) (two documents, two hosts).

## The file

```json
{
  "source": "https://lda.gov/api/openapi/v1/",
  "retrieved": "2026-10-27",
  "reason": null,
  "endpoints": [
    {"verb": "GET", "path": "/api/v1/clients/"},
    {"verb": "GET", "path": "/api/v1/clients/{id}/"}
  ]
}
```

- `source`: one URL, the one the endpoints were read from, or `null` when the API publishes nothing
  machine-readable. When the reads come from several documents, it is the one URL that holds them all (a pinned
  directory, a docs index).
- `retrieved`: the date you read it, `YYYY-MM-DD`. Use the date the server's `Date` header gives (UTC), so it matches
  the dates the client's docstring records.
- `reason`: one sentence, or `null`. Required when `source` is `null`: why nothing could be saved. Beside a non-null
  `source` it is allowed when the reads come from several documents: it names each one and what it documents.
  Otherwise it is `null`.
- `endpoints`: every documented verb and path, sorted by `(path, verb)`, no repeats. Keep the paths as the docs write
  them: with any prefix the API serves them under (`/api/v1/`), holes named as the docs name them (`{id}`). The
  name check strips holes and matches the client's paths by suffix, so neither the hole names nor the prefix need to
  agree with the client's.

No other key is allowed. `headgate_verify.naming.load_snapshot` validates the file, and `headgate-verify` reports a
snapshot that breaks the schema.

## Where to find the surface, in order

Try each source in turn and stop at the first that lists the endpoints.

1. **`llms.txt`** at the docs root (and the pages it links). Some providers publish their reference there as Markdown.
2. **An official OpenAPI or Swagger document.** Look for a "Download" button on the docs page, links named
   `openapi.json`, `openapi.yaml`, `swagger.json`, or the URL a docs renderer loads (below).
3. **A spec embedded in the docs site's JavaScript.** A Redoc or Swagger UI page loads its spec from a URL in its
   init call (`Redoc.init('/api/openapi/v1/', …)`, `SwaggerUIBundle({url: …})`), or carries it inline as a
   `JSON.parse('…')` string in a bundle. Read the page's HTML for the init call before downloading bundles.
4. **The docs pages themselves.** When there is no spec, scrape the verb and path from each endpoint's HTML page.

When the API publishes nothing (no spec, no reference pages), write `"source": null` with a `reason`; the name check
then applies its naming rule without a docs comparison.

## Reading the spec

- Take the endpoints from the spec's `paths` (OpenAPI) only. Prose in the description may mention more URLs (a root
  index, account or login endpoints); those are not the API's documented resources unless `paths` lists them.
- Take every HTTP verb under each path (`get`, `post`, `put`, `patch`, `delete`, `head`); skip `parameters`,
  `summary` and other keys that sit beside them.
- If the spec has a `servers` URL with a path, the snapshot paths are still the `paths` keys as written: the client's
  base URL carries no path, so a prefix belongs in each method's path, and the name check strips the version segment.
- Generate the file with a few lines of code over the parsed spec, not by hand, so the sort order and the set are
  exact. Keep the spec you downloaded out of the repo; the snapshot is the record.

## Fetching politely

The fetch counts against the API's rate limit like any other request. Send a `User-Agent` that names your project, pace
requests as the API's terms ask, and read the terms before the first request.

A docs server may answer the spec URL only for the right `Accept`. lda.gov's spec URL answers
`406 {"detail":"Could not satisfy the request Accept header."}` to `Accept: application/json` (measured 2026-10-27)
and `200` with `Content-Type: application/vnd.oai.openapi` (YAML) to
`Accept: application/vnd.oai.openapi+json, application/vnd.oai.openapi;q=0.9, */*;q=0.1`. Record such a quirk in the
client's module docstring.

## Worked example: lda.gov

1. The docs page `https://lda.gov/api/redoc/v1/` is Redoc. Its HTML calls `Redoc.init('/api/openapi/v1/', …)`.
2. `GET https://lda.gov/api/openapi/v1/` with the OpenAPI `Accept` above returned the spec: OpenAPI 3.0.2,
   `servers: [{url: https://lda.gov}]`, 18 paths, each with one `get`.
3. The snapshot is those 18 `GET`s, sorted, with `source` the spec URL and `retrieved` the `Date` header's day.

Three requests in all (the docs page, a `406`, the spec), paced 10 seconds apart.

## Worked example: Open-Meteo, two hosts and two specs

Open-Meteo documents each API in its own OpenAPI file in its GitHub repository (`openapi/forecast.yml`,
`openapi/historical-weather.yml`), one path each, served from different hosts (`api.open-meteo.com`,
`archive-api.open-meteo.com`). One package holds both clients, so one `docs_paths.json` holds both paths. `source` is
the one URL that holds both files, the `openapi/` directory pinned to the commit read
(`https://github.com/open-meteo/open-meteo/tree/<commit>/openapi`), and `reason` names the two files and the host
each documents. The snapshot has no host field: which class serves which path is the client module's business.

## Then

Cover every documented read: one method per `GET` in the snapshot, named as the name check derives it
([naming.md](naming.md)). The snapshot is
a record of the docs, never trimmed to what the client happens to cover, so `test_method_names.py` passes only when
every documented read has its method.
