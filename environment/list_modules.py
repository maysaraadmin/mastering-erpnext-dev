import frappe
mods = frappe.db.sql("SELECT name, app_name FROM `tabModule Def` ORDER BY app_name", as_dict=True)
for m in mods:
    print(m.name, "->", m.app_name)
