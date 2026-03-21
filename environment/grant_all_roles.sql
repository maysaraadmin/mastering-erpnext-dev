-- Grant roles needed to see Production Planning and Vendor Portal workspaces
INSERT IGNORE INTO `tabHas Role` (name, parent, parenttype, parentfield, role, creation, modified, modified_by, owner, docstatus, idx)
SELECT UUID(), 'maysara.mubarak.mohamed@gmail.com', 'User', 'roles', r.role, NOW(), NOW(), 'Administrator', 'Administrator', 0, 1
FROM (
  SELECT 'Manufacturing Manager' AS role UNION ALL
  SELECT 'Manufacturing User' UNION ALL
  SELECT 'Purchase Manager' UNION ALL
  SELECT 'Purchase User' UNION ALL
  SELECT 'Stock Manager' UNION ALL
  SELECT 'Stock User' UNION ALL
  SELECT 'Accounts Manager' UNION ALL
  SELECT 'Accounts User'
) r
WHERE NOT EXISTS (
  SELECT 1 FROM `tabHas Role`
  WHERE parent='maysara.mubarak.mohamed@gmail.com' AND role=r.role
);
