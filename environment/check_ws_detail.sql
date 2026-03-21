SELECT name, module, public, is_hidden, restrict_to_domain, for_user FROM `tabWorkspace` WHERE name IN ('Asset Management', 'Production Planning', 'Vendor Portal');
SELECT workspace, role FROM `tabWorkspace Role` WHERE workspace IN ('Asset Management', 'Production Planning', 'Vendor Portal');
