UPDATE `tabWorkspace` SET
  title = NULL,
  sequence_id = 0,
  parent_page = NULL,
  restrict_to_domain = NULL
WHERE name IN ('Production Planning', 'Vendor Portal');
