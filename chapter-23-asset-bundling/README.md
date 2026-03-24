# Chapter 23: JavaScript Asset Bundling

## What is Bundling?

Bundling takes multiple JavaScript files and combines them into a single file that the browser loads. Instead of 20 separate HTTP requests, you make one.

**The old way (problematic):**
```html
<script src="jquery.js"></script>
<script src="bootstrap.js"></script>
<script src="my-app.js"></script>
<script src="utils.js"></script>
```

Problems: multiple HTTP requests, manual load ordering, hard dependency management.

**The bundled way:**
```html
<script src="app.bundle.js"></script>
```

---

## Why Frappe Uses esbuild

Frappe uses **esbuild** — a JavaScript bundler written in Go. It's 10-100x faster than Webpack.

Frappe also uses its own PostCSS plugin (`@frappe/esbuild-plugin-postcss2`) for CSS processing. PostCSS automatically adds browser prefixes, minifies CSS, and handles modern CSS features.

---

## How Frappe's Bundle System Works

### The `.bundle.js` file is NOT a bundle — it's an entry point

A `.bundle.js` file is:
- An **entry point** (a "shopping list" of imports)
- A **build instruction** for esbuild
- A **source file** that gets processed

It is NOT the final output.

### Build pipeline

```
Source .bundle.js files
        ↓
   esbuild reads file
        ↓
  Follows all imports
        ↓
  Combines all files
        ↓
Creates app.bundle.ABC123.js (with hash)
        ↓
  Updates assets.json
```

### The `assets.json` manifest

`assets.json` is a **manifest file** — a map that tells the system where to find the right assets. It maps logical names to hashed filenames:

```json
{
  "erpnext.bundle.js": "/assets/erpnext/dist/js/erpnext.bundle.ABC123.js"
}
```

At runtime, Frappe looks up `assets.json` to resolve the actual file path.

---

## Step-by-Step: Creating a Bundle

### 1. Create the bundle entry point

```javascript
// your_app/public/js/your_app.bundle.js
// This is a "shopping list" — not actual code

import "./form_guard";
import "./utils/helpers";
import "./utils/validation";
import "./controllers/user_controller";
```

### 2. Create your source files

```javascript
// your_app/public/js/form_guard.js
(function() {
    function attachUnloadGuard(frm) {
        window.onbeforeunload = function(e) {
            if (frm && frm.is_dirty && frm.is_dirty()) {
                e.preventDefault();
                e.returnValue = "";
                return "";
            }
        };
    }

    function clearUnloadGuard() {
        window.onbeforeunload = null;
    }

    frappe.ui.form.on('*', {
        onload(frm) { clearUnloadGuard(); },
        refresh(frm) { attachUnloadGuard(frm); },
        after_save(frm) { clearUnloadGuard(); }
    });
})();
```

```javascript
// your_app/public/js/utils/helpers.js
export function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
```

### 3. Register in hooks.py

```python
# your_app/hooks.py
app_include_js = [
    "your_app.bundle.js"
]
```

### 4. Build assets

```bash
bench build --app your_app
bench clear-cache
```

---

## Development vs Production Mode

### Development mode
- HTML shows bundle path: `<script src="/assets/your_app/js/your_app.bundle.ABC123.js">`
- But Frappe **serves source files directly** — no rebuild needed
- Edit a `.js` file → save → refresh browser → changes appear instantly

### Production mode
- Frappe serves the **actual bundled, minified file**
- Edit a `.js` file → must run `bench build` to update the bundle
- Changes won't appear until rebuild

> **Key insight**: Edit your actual code in `.js` files — changes appear immediately in dev mode. Only edit `.bundle.js` files when adding/removing imports, which requires `bench build`.

---

## Advanced Patterns

### Multiple bundles for different features

```python
# hooks.py
app_include_js = [
    "core.bundle.js",      # Core functionality — changes rarely
    "ui.bundle.js",        # UI components
    "reports.bundle.js",   # Reporting features
]
```

Benefits: better caching (core bundle rarely changes), parallel loading.

### CSS bundling

```scss
/* your_app/public/css/your_app.bundle.scss */
@import "./variables";
@import "./components/forms";
@import "./components/tables";
```

```python
# hooks.py
app_include_css = [
    "your_app.bundle.css"
]
```

### HTML template import

```javascript
// In your bundle.js
import "./templates/notification.html";

// esbuild converts this to:
// frappe.templates["notification"] = '<div class="notification">...</div>';
```

```javascript
// Usage in JavaScript
const html = frappe.templates["notification"].replace('{message}', 'Hello World');
```

### Cross-app dependencies

```javascript
// Import from another app
import "frappe/public/js/frappe/form/controls/autocomplete.js";
import "erpnext/public/js/controllers/stock_controller.js";
```

---

## ERPNext Bundle Example

```javascript
// apps/erpnext/erpnext/public/js/erpnext.bundle.js
import "./conf";
import "./utils";
import "./queries";
import "./sms_manager";
import "./utils/party";
import "./controllers/stock_controller";
// ... more imports
```

```python
# apps/erpnext/erpnext/hooks.py
app_include_js = "erpnext.bundle.js"
```

What happens during build:
1. esbuild reads `erpnext.bundle.js`
2. Follows all `import` statements
3. Combines all imported files
4. Creates `erpnext.bundle.ABC123.js`
5. Updates `assets.json`

---

## Common Q&A

**Q: Do I need to understand esbuild?**
No. Frappe handles all esbuild configuration. You just create `.bundle.js` files.

**Q: Can I use npm packages?**
Yes. Install with `yarn add package-name` in your app directory, then import in your bundle.

**Q: What's a manifest file?**
A configuration file that lists references to other files. `assets.json` is Frappe's manifest — it maps bundle names to actual compiled file paths with version hashes.

**Q: Is a manifest the same as a bundle?**
No. Manifest = index pointing to files (`assets.json`). Bundle = the actual compiled code.

**Q: How do I debug bundled code?**
Frappe generates source maps automatically. Open browser dev tools and you'll see your original source files, not the bundled version.
