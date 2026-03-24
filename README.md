# Mastering ERPNext Development

![ERPNext](https://img.shields.io/badge/ERPNext-v16-blue)
![Frappe](https://img.shields.io/badge/Frappe-v16-blue)
![Tests](https://img.shields.io/badge/Tests-34%20passing-brightgreen)
![Chapters](https://img.shields.io/badge/Chapters-32-orange)
![License](https://img.shields.io/badge/License-GPL-blue)

A comprehensive technical guide for developers who want to master Frappe Framework and ERPNext development — from environment setup to production deployment.

## What's Inside

- **32 chapters** covering the full ERPNext development lifecycle
- **3 production-ready apps** — Asset Management, Production Planning, Vendor Portal
- **34 passing tests** — unit, integration, E2E, and performance
- **Fully compatible with ERPNext v16 / Frappe v16**
- **frappe_docker** environment for instant local setup

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/maysaraadmin/mastering-erpnext-dev.git
cd mastering-erpnext-dev
```

### 2. Start the environment

Uses [frappe_docker](https://github.com/frappe/frappe_docker) with ERPNext v16.

```bash
cd frappe_docker
docker compose -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  up -d
```

### 3. Install the book apps

```bash
bash environment/install-book-apps.sh
```

This installs all three apps (`asset_management_app`, `production_planning_app`, `vendor_portal_app`) on the `frontend` site.

### 4. Run the tests

```bash
bash environment/run-tests.sh
```

Expected output: **34 tests passing** across all three apps.

---

## Project Structure

```
mastering-erpnext-dev/
├── environment/                    # Setup and utility scripts
│   ├── install-book-apps.sh        # Install all 3 apps
│   ├── run-tests.sh                # Run all tests
│   └── console.sh                  # Open bench console
│
├── chapter-01-frappe-mindset/
├── chapter-02-dev-environment/
├── chapter-03-anatomy-of-app/
├── chapter-04-advanced-doctypes/
├── chapter-05-controller-deep-dive/
├── chapter-06-mastering-orm/
├── chapter-07-client-side-mastery/
├── chapter-08-server-script-hooks/
├── chapter-09-permissions-system/
├── chapter-10-custom-print-formats/
├── chapter-11-ecommerce-platform/
├── chapter-12-crm-system/
├── chapter-13-project-management/
├── chapter-14-debugging/
├── chapter-15-automated-testing/   # 34 test cases
├── chapter-16-performance-tuning/
├── chapter-17-production-pipeline/
├── chapter-18-hooks-deep-dive/
├── chapter-19-workflows/
├── chapter-20-translations-i18n/
├── chapter-21-virtual-doctypes/
├── chapter-22-patches-and-migrations/
├── chapter-23-asset-bundling/
├── chapter-24-monkey-patching/
├── chapter-25-advanced-bench/
├── chapter-26-api-patterns/
├── chapter-27-realtime-and-ui/
├── chapter-28-devops-and-deployment/
├── chapter-29-erpnext-customization/
├── chapter-30-client-scripting-advanced/
├── chapter-31-installation-guide/
├── chapter-32-snippets-and-reference/
│
└── projects/
    ├── asset_management/           # Asset Management app
    ├── production_planning/        # Production Planning app
    └── vendor_portal/              # Vendor Portal app
```

---

## The Three Apps

### Asset Management (`projects/asset_management/`)

Enterprise asset tracking system.

- DocTypes: Asset, Asset Category, Asset Assignment, Asset Maintenance
- Automated depreciation (Straight Line, Double Declining Balance)
- Real-time dashboard with utilization metrics
- Maintenance scheduling with email notifications
- Scheduled tasks (daily, weekly, monthly)
- **31 passing tests**

Access: `http://localhost:8080/app/asset`

### Production Planning (`projects/production_planning/`)

Manufacturing planning and scheduling system.

- Production Plan DocType with child tables
- Sales Order → Production Plan conversion
- Multi-level BOM explosion
- Work order generation and material shortage detection
- Capacity planning
- **3 passing tests**

Access: `http://localhost:8080/app/production-plan`

### Vendor Portal (`projects/vendor_portal/`)

REST API portal for external vendor integration.

- Token-based authentication (24-hour expiry, rate limiting)
- Purchase Order retrieval and acknowledgement
- HMAC-SHA256 signed webhooks
- Vendor-specific data access control
- Vendor doctype with API key/secret management

Access: `http://localhost:8080/app/vendor`

API example:
```bash
curl -X POST http://localhost:8080/api/method/vendor_portal_app.vendor_portal.api.vendor.authenticate \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your_key", "api_secret": "your_secret"}'
```

---

## ERPNext v16 Compatibility

All code has been updated and verified against **ERPNext v16.9.1 / Frappe v16.11.0**:

- `frappe.cache().setex()` — correct v16 param order `(key, ttl, value)`
- `add_months()` — wrapped with `getdate()` where needed
- `psutil` replaced with stdlib `shutil` + `/proc/meminfo`
- Method names renamed to avoid DB column clashes
- All module import paths corrected

---

## Chapter Overview

| # | Chapter | Key Content |
|---|---------|-------------|
| 1 | The Frappe Mindset | Metadata-driven development philosophy |
| 2 | Dev Environment | frappe_docker, bench setup |
| 3 | Anatomy of an App | App structure, hooks, modules |
| 4 | Advanced DocTypes | 7 DocType designs, naming series, property setters |
| 5 | Controller Deep Dive | Document lifecycle, validation patterns |
| 6 | Mastering the ORM | 15+ query examples, bulk operations |
| 7 | Client-Side Mastery | Form events, dynamic UI, API calls, dialogs |
| 8 | Server Scripts & Hooks | Document events, schedulers, background jobs |
| 9 | Permissions System | Role-based and row-level permissions |
| 10 | Custom Print Formats | Jinja templates, CSS, barcode labels |
| 11 | Asset Management | Complete app — 31 tests passing |
| 12 | Production Planning | Complete app — 3 tests passing |
| 13 | Vendor Portal | REST API app — token auth, webhooks |
| 14 | Debugging | Debug utilities, error tracing |
| 15 | Automated Testing | Unit, integration, E2E, performance tests |
| 16 | Performance Tuning | Query optimization, caching, benchmarks |
| 17 | Production Pipeline | GitHub Actions CI/CD, health checks, deployment |
| 18 | Hooks Deep Dive | Hook theory, all hook types, custom hook types |
| 19 | Workflows | States, transitions, docstatus, JS/Python APIs |
| 20 | Translations & i18n | CSV translation files, `_()`, context, language codes |
| 21 | Virtual DocTypes | Virtual DocTypes, Virtual Fields, external backends |
| 22 | Patches & Migrations | patches.txt, pre/post model sync, safe data migration |
| 23 | Asset Bundling | Webpack, JS/CSS bundling, public assets, build pipeline |
| 24 | Monkey Patching | Override classes, methods, whitelisted functions |
| 25 | Advanced Bench | Multi-site, custom commands, bench internals, supervisor |
| 26 | API Patterns | REST design, versioning, authentication, rate limiting |
| 27 | Realtime & UI | Socket.IO, frappe.realtime, custom pages, workspaces |
| 28 | DevOps & Deployment | Docker Compose, nginx, SSL, monitoring, backups |
| 29 | ERPNext Customization | Custom Fields, Property Setters, Fixtures, hooks.py deep dive |
| 30 | Advanced Client Scripting | Child tables, list view, dialogs, overrides, Jinja filters |
| 31 | Installation Guide | Bare-metal, Docker, devcontainers, app boilerplate |
| 32 | Snippets & Reference | Python/JS patterns, API reference, bench commands, shortcuts |

---

## Requirements

- Docker and Docker Compose
- Git
- 4GB RAM minimum (8GB recommended)

No local Python or Node.js installation needed — everything runs inside Docker.

---

## Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[GNU General Public License](LICENSE)

## Resources

- [Frappe Documentation](https://frappeframework.com/docs)
- [ERPNext Documentation](https://erpnext.com/docs)
- [Frappe Community Forum](https://discuss.frappe.io)
- [frappe_docker](https://github.com/frappe/frappe_docker)
