UPDATE `tabWorkspace` SET
  title = NULL,
  sequence_id = 0,
  parent_page = NULL,
  developer_mode_only = 0,
  restrict_to_domain = NULL
WHERE name IN ('Production Planning', 'Vendor Portal');
