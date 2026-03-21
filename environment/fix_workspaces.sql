-- Make sure workspaces are public and not user-restricted
UPDATE `tabWorkspace` SET public=1, is_hidden=0, for_user=NULL WHERE name IN ('Production Planning', 'Vendor Portal', 'Asset Management');
