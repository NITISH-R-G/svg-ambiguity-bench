# Security

This is a research artifact: a benchmark corpus, an offline scorer, and a client that
talks to a locally-running model. It handles no credentials, processes no user data, and
exposes no network service.

## Scope

If you find something genuinely security-relevant, please open an issue. Realistically
the surface is small:

- `svgbench run` makes HTTP requests to a **local** model endpoint (default
  `http://localhost:11434`), configurable in `configs/base.yaml`.
- The SVG parsing path uses Python's `xml.etree.ElementTree`, which does not resolve
  external entities by default. The corpus is generated locally and never fetched.
- Model responses are stored verbatim and parsed as XML. They are never rendered,
  executed, or served.

## Not security issues

- Reproducibility failures, scoring disagreements, or statistical objections. Those are
  research issues and belong in the issue tracker or in
  [`VALIDITY.md`](VALIDITY.md).
