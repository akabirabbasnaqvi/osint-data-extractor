# Security policy

## Supported versions

Only the latest version on the `main` branch receives security fixes.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability or exposed secret. Use GitHub’s private vulnerability-reporting feature when it is enabled, or contact the repository owner privately with a reproduction, impact, and affected version.

Do not include real personal data, credentials, or access tokens in a report.

## Deployment requirements

Before public deployment, enable authentication, HTTPS, backups, monitoring, a documented retention/deletion policy, restricted network access, and unique secrets. Keep PostgreSQL, Redis, SearxNG, and the API off the public internet unless each is explicitly protected and required.
