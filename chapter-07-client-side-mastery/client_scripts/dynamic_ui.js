/**
 * Dynamic UI Examples
 * Chapter 7: Client-Side Mastery
 * 
 * Demonstrates dynamic form manipulation
 */

// Example 1: Conditional Field Display
frappe.ui.form.on('Customer', {
	refresh: function(frm) {
		// Show/hide fields based on customer type
		toggle_fields_by_customer_type(frm);
	},
	
	customer_type: function(frm) {
		toggle_fields_by_customer_type(frm);
	}
});

function toggle_fields_by_customer_type(frm) {
	if (frm.doc.customer_type === 'Company') {
		frm.set_df_property('tax_id', 'reqd', 1);
		frm.set_df_property('tax_id', 'hidden', 0);
		frm.set_df_property('company_name', 'reqd', 1);
		frm.set_df_property('company_name', 'hidden', 0);
	} else {
		frm.set_df_property('tax_id', 'reqd', 0);
		frm.set_df_property('tax_id', 'hidden', 1);
		frm.set_df_property('company_name', 'reqd', 0);
		frm.set_df_property('company_name', 'hidden', 1);
	}
}

// Example 2: Dynamic Filters
frappe.ui.form.on('Purchase Order', {
	onload: function(frm) {
		// Set dynamic query for supplier
		frm.set_query('supplier', function() {
			return {
				filters: {
					'supplier_group': frm.doc.supplier_group || '',
					'disabled': 0
				}
			};
		});
		
		// Set dynamic query for items
		frm.set_query('item_code', 'items', function() {
			return {
				filters: {
					'is_purchase_item': 1,
					'disabled': 0
				}
			};
		});
	},
	
	supplier_group: function(frm) {
		// Refresh supplier field when group changes
		frm.set_value('supplier', '');
	}
});

// Example 3: Custom Buttons and Actions
frappe.ui.form.on('Asset', {
	refresh: function(frm) {
		// Add custom buttons based on status
		if (frm.doc.status === 'Available') {
			frm.add_custom_button(__('Assign Asset'), function() {
				show_assignment_dialog(frm);
			}, __('Actions'));
			
			frm.add_custom_button(__('Mark Under Maintenance'), function() {
				mark_under_maintenance(frm);
			}, __('Actions'));
		}
		
		if (frm.doc.status === 'In Use') {
			frm.add_custom_button(__('Release Asset'), function() {
				release_asset(frm);
			}, __('Actions'));
		}
		
		// Add report button
		frm.add_custom_button(__('Asset History'), function() {
			frappe.set_route('query-report', 'Asset History', {
				asset: frm.doc.name
			});
		});
	}
});

function show_assignment_dialog(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Assign Asset'),
		fields: [
			{
				fieldname: 'employee',
				fieldtype: 'Link',
				label: __('Employee'),
				options: 'Employee',
				reqd: 1
			},
			{
				fieldname: 'from_date',
				fieldtype: 'Date',
				label: __('From Date'),
				default: frappe.datetime.get_today(),
				reqd: 1
			},
			{
				fieldname: 'to_date',
				fieldtype: 'Date',
				label: __('To Date')
			},
			{
				fieldname: 'notes',
				fieldtype: 'Small Text',
				label: __('Notes')
			}
		],
		primary_action_label: __('Assign'),
		primary_action: function(values) {
			frappe.call({
				method: 'asset_management_app.api.assign_asset',
				args: {
					asset: frm.doc.name,
					employee: values.employee,
					from_date: values.from_date,
					to_date: values.to_date,
					notes: values.notes
				},
				callback: function(r) {
					if (r.message) {
						frappe.msgprint(__('Asset assigned successfully'));
						frm.reload_doc();
						d.hide();
					}
				}
			});
		}
	});
	
	d.show();
}

function mark_under_maintenance(frm) {
	frappe.confirm(
		__('Are you sure you want to mark this asset as under maintenance?'),
		function() {
			frm.set_value('status', 'Under Maintenance');
			frm.save();
		}
	);
}

function release_asset(frm) {
	frappe.call({
		method: 'asset_management_app.api.release_asset',
		args: {
			asset: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				frappe.msgprint(__('Asset released successfully'));
				frm.reload_doc();
			}
		}
	});
}

// Example 4: Real-time Field Updates
frappe.ui.form.on('Quotation', {
	refresh: function(frm) {
		// Setup real-time updates
		setup_realtime_updates(frm);
	}
});

function setup_realtime_updates(frm) {
	// Listen for real-time events
	frappe.realtime.on('quotation_updated', function(data) {
		if (data.quotation === frm.doc.name) {
			frappe.show_alert({
				message: __('Quotation was updated by {0}', [data.user]),
				indicator: 'blue'
			});
			
			// Optionally reload
			frm.reload_doc();
		}
	});
}

// Example 5: Field Formatting
frappe.ui.form.on('Item', {
	item_code: function(frm) {
		// Auto-format item code to uppercase
		if (frm.doc.item_code) {
			frm.set_value('item_code', frm.doc.item_code.toUpperCase());
		}
	},
	
	standard_rate: function(frm) {
		// Format currency display
		if (frm.doc.standard_rate) {
			frm.set_df_property('standard_rate', 'description', 
				__('Formatted: {0}', [format_currency(frm.doc.standard_rate)]));
		}
	}
});
