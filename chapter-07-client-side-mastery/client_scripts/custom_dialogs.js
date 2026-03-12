/**
 * Custom Dialog Examples
 * Chapter 7: Client-Side Mastery
 * 
 * Demonstrates creating custom dialogs and prompts
 */

// Example 1: Simple Dialog
function show_simple_dialog() {
	let d = new frappe.ui.Dialog({
		title: __('Enter Details'),
		fields: [
			{
				fieldname: 'customer_name',
				fieldtype: 'Data',
				label: __('Customer Name'),
				reqd: 1
			},
			{
				fieldname: 'email',
				fieldtype: 'Data',
				label: __('Email'),
				options: 'Email'
			}
		],
		primary_action_label: __('Submit'),
		primary_action: function(values) {
			console.log(values);
			d.hide();
		}
	});
	
	d.show();
}

// Example 2: Multi-Step Dialog
function show_wizard_dialog() {
	let step = 1;
	
	let d = new frappe.ui.Dialog({
		title: __('Setup Wizard - Step {0}', [step]),
		fields: get_wizard_fields(step)
	});
	
	d.set_primary_action(__('Next'), function() {
		let values = d.get_values();
		
		if (step < 3) {
			step++;
			d.set_title(__('Setup Wizard - Step {0}', [step]));
			d.fields = get_wizard_fields(step);
			d.refresh();
		} else {
			// Final step
			complete_wizard(values);
			d.hide();
		}
	});
	
	d.show();
}

function get_wizard_fields(step) {
	const field_sets = {
		1: [
			{fieldname: 'company_name', fieldtype: 'Data', label: __('Company Name'), reqd: 1},
			{fieldname: 'country', fieldtype: 'Link', label: __('Country'), options: 'Country', reqd: 1}
		],
		2: [
			{fieldname: 'currency', fieldtype: 'Link', label: __('Currency'), options: 'Currency', reqd: 1},
			{fieldname: 'fiscal_year', fieldtype: 'Data', label: __('Fiscal Year'), reqd: 1}
		],
		3: [
			{fieldname: 'admin_email', fieldtype: 'Data', label: __('Admin Email'), options: 'Email', reqd: 1},
			{fieldname: 'admin_password', fieldtype: 'Password', label: __('Admin Password'), reqd: 1}
		]
	};
	
	return field_sets[step] || [];
}

// Example 3: Confirmation Dialog
function confirm_delete_records(records) {
	frappe.confirm(
		__('Are you sure you want to delete {0} records? This action cannot be undone.', [records.length]),
		function() {
			// User confirmed
			delete_records(records);
		},
		function() {
			// User cancelled
			frappe.show_alert(__('Deletion cancelled'), 3);
		}
	);
}

// Example 4: Prompt Dialog
function prompt_for_reason() {
	frappe.prompt({
		fieldname: 'reason',
		fieldtype: 'Small Text',
		label: __('Reason for Cancellation'),
		reqd: 1
	}, function(values) {
		// Process with reason
		cancel_document_with_reason(values.reason);
	}, __('Cancel Document'));
}

// Example 5: Multi-Field Prompt
function prompt_for_payment_details() {
	frappe.prompt([
		{
			fieldname: 'payment_method',
			fieldtype: 'Select',
			label: __('Payment Method'),
			options: 'Cash\nCredit Card\nBank Transfer',
			reqd: 1
		},
		{
			fieldname: 'amount',
			fieldtype: 'Currency',
			label: __('Amount'),
			reqd: 1
		},
		{
			fieldname: 'reference_no',
			fieldtype: 'Data',
			label: __('Reference Number')
		},
		{
			fieldname: 'remarks',
			fieldtype: 'Small Text',
			label: __('Remarks')
		}
	], function(values) {
		create_payment_entry(values);
	}, __('Payment Details'));
}

// Example 6: Dialog with Dynamic Fields
function show_dynamic_dialog(doctype) {
	frappe.call({
		method: 'frappe.client.get_meta',
		args: {
			doctype: doctype
		},
		callback: function(r) {
			if (r.message) {
				let fields = r.message.fields
					.filter(f => !f.hidden && f.fieldtype !== 'Table')
					.map(f => ({
						fieldname: f.fieldname,
						fieldtype: f.fieldtype,
						label: f.label,
						options: f.options,
						reqd: f.reqd
					}));
				
				let d = new frappe.ui.Dialog({
					title: __('Create {0}', [doctype]),
					fields: fields,
					primary_action_label: __('Create'),
					primary_action: function(values) {
						create_document(doctype, values);
						d.hide();
					}
				});
				
				d.show();
			}
		}
	});
}

// Example 7: Dialog with Table
function show_bulk_update_dialog() {
	let d = new frappe.ui.Dialog({
		title: __('Bulk Update Items'),
		fields: [
			{
				fieldname: 'items',
				fieldtype: 'Table',
				label: __('Items to Update'),
				cannot_add_rows: false,
				cannot_delete_rows: false,
				fields: [
					{
						fieldname: 'item_code',
						fieldtype: 'Link',
						label: __('Item'),
						options: 'Item',
						in_list_view: 1,
						reqd: 1
					},
					{
						fieldname: 'new_rate',
						fieldtype: 'Currency',
						label: __('New Rate'),
						in_list_view: 1,
						reqd: 1
					}
				]
			}
		],
		primary_action_label: __('Update All'),
		primary_action: function(values) {
			bulk_update_items(values.items);
			d.hide();
		}
	});
	
	d.show();
}

// Helper Functions
function delete_records(records) {
	frappe.call({
		method: 'custom_app.api.bulk_delete',
		args: {
			records: records
		},
		callback: function(r) {
			frappe.msgprint(__('Records deleted successfully'));
		}
	});
}

function cancel_document_with_reason(reason) {
	cur_frm.set_value('cancellation_reason', reason);
	cur_frm.save().then(() => {
		cur_frm.amend_doc();
	});
}

function create_payment_entry(values) {
	frappe.call({
		method: 'erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry',
		args: values,
		callback: function(r) {
			if (r.message) {
				frappe.model.sync(r.message);
				frappe.set_route('Form', 'Payment Entry', r.message.name);
			}
		}
	});
}

function create_document(doctype, values) {
	frappe.call({
		method: 'frappe.client.insert',
		args: {
			doc: Object.assign({doctype: doctype}, values)
		},
		callback: function(r) {
			if (r.message) {
				frappe.msgprint(__('Created {0}', [r.message.name]));
				frappe.set_route('Form', doctype, r.message.name);
			}
		}
	});
}

function bulk_update_items(items) {
	frappe.call({
		method: 'custom_app.api.bulk_update_item_rates',
		args: {
			items: items
		},
		callback: function(r) {
			frappe.msgprint(__('Updated {0} items', [items.length]));
		}
	});
}
