# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "production_planning_app"
app_title = "Production Planning"
app_publisher = "Your Organization"
app_description = "Advanced production planning and scheduling system"
app_icon = "octicon octicon-gear"
app_color = "orange"
app_email = "info@example.com"
app_license = "MIT"

# Document Events
doc_events = {
	"Sales Order": {
		"on_submit": "production_planning_app.production_planning.utils.sales_order.create_production_plan_from_sales_order"
	},
	"Production Plan": {
		"on_submit": "production_planning_app.production_planning.doctype.production_plan.production_plan.create_work_orders"
	}
}

# Scheduled Tasks
scheduler_events = {
	"all": [],
	"daily": [
		"production_planning_app.tasks.daily.check_material_shortages",
		"production_planning_app.tasks.daily.update_production_status"
	],
	"hourly": [],
	"weekly": [
		"production_planning_app.tasks.weekly.generate_capacity_report"
	],
	"monthly": []
}

# Permissions
permission_query_conditions = {
	"Production Plan": "production_planning_app.production_planning.doctype.production_plan.production_plan.get_permission_query_conditions"
}
