---
author: "Ryo Nakagami"
date-modified: "2026-05-30"
project: python-package-guideline
---

# Versioning Policy

- The project version management is based on [Semantic Versioning](https://semver.org/)
- Release numbers are managed in `MAJOR.MINOR.PATCH` format

## MAJOR.MINOR.PATCH

| Release Type | Main Content | Backward Compatibility | Example |
| :-------------- | :---------- | :------------ | :------------ |
| **Major Release** | - Breaking changes (non-backward compatible)<br>- Removal of deprecated features<br>- API updates with specification changes<br>- Changes in Major releases are recorded in **Release Notes**| ❌ None | `v1.0.0 → v2.0.0` |
| **Minor Release** | - Addition of new features<br>- Large-scale bug fixes<br>- Deprecation announcements | ✅ Yes | `v1.1.0 → v1.2.0` |
| **Patch Release** | - Bug fixes<br>- Operational stability and performance improvements (non-breaking)<br>- Ensures existing code continues to work | ✅ Yes | `v1.2.1 → v1.2.2` |

---

### Deprecation Policy

This project follows the following deprecation process:

1. Announce deprecation in a **Minor Release**.
2. Warning messages must explicitly state:
   - The replacement method or attribute
   - The version where removal is planned (e.g., `will be removed in 2.0.0`)
3. After announcement, functionality continues to work within the same major version (`1.x`).
4. Removal occurs in the next **Major Release** (`2.0.0`).

---

### Example: Deprecation Flow

| Version | Status | Details |
| :----------- | :------ | :------ |
| `1.2.0` | 🔔 Announcement | Function `old_method()` is deprecated. `new_method()` recommended as replacement. |
| `1.3.0` | ⚠ Continued Warning | Continues to work with warnings. Migration recommended. |
| `2.0.0` | ⛔ Removal | `old_method()` completely removed. |

---

## References

- [Semantic Versioning](https://semver.org/)
- [Python Package Building Techniques for Regmonkeys > Versioning Policy](https://ryonakagami.github.io/python-statisticalpackage-techniques/posts/python-packaging-guide/versioning.html)
