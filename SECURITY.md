# Security policy

Report vulnerabilities privately through [GitHub private vulnerability reporting](https://github.com/ricardoleal20/ReleaseWeave/security/advisories/new).

Please include the affected commit/version, operating system, reproduction steps, expected impact and any mitigation. Do not post credentials, tokens or private repository contents in public issues.

## Supported code

Security fixes target the current main branch and the latest ReleaseWeave release, starting with v0.2.0. Historical ChangeForge packages remain distinct. Native release files are covered by SHA256SUMS; both installers verify their archive and executable version.

Relevant reports include path traversal, unexpected file deletion or corruption, command injection, unsafe changeset handling, and vulnerabilities in the GitHub automation. Describe a practical reproduction where possible. Reports are triaged by the maintainer without a guaranteed response deadline.

We will reproduce the issue, coordinate a fix and disclosure with the reporter, and credit the reporter when requested. Keep vulnerability details private until a fix or coordinated disclosure is ready.
