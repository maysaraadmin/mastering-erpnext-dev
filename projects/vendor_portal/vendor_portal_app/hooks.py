# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "vendor_portal_app"
app_title = "Vendor Portal"
app_publisher = "Your Organization"
app_description = "REST API-based vendor portal for external integration"
app_icon = "octicon octicon-link"
app_color = "green"
app_email = "info@example.com"
app_license = "MIT"

# REST API Configuration
# All API endpoints are in vendor_portal/api/

# Document Events
doc_events = {
	"Purchase Order": {
		"on_submit": "vendor_portal_app.vendor_portal.webhooks.purchase_order.notify_vendor"
	}
}

# Scheduled Tasks
scheduler_events = {
	"all": [],
	"daily": [
		"vendor_portal_app.tasks.daily.sync_vendor_data"
	],
	"hourly": [],
	"weekly": [],
	"monthly": []
}

# Override whitelisted methods for custom authentication
override_whitelisted_methods = {
	"frappe.auth.get_logged_user": "vendor_portal_app.vendor_portal.auth.get_logged_user"
}
