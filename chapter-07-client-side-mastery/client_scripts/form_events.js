/**
 * Form Events Examples
 * Chapter 7: Client-Side Mastery
 * 
 * Demonstrates common form events and their usage
 */

// Example 1: Basic Form Events
frappe.ui.form.on('Sales Order', {
	// Triggered when form is loaded/refreshed
	refresh: function(frm) {
		// Add custom button
		if (frm.doc.docstatus === 1 && frm.doc.status !== 'Closed') {
			frm.add_custom_button(__('Create Delivery Note'), function() {
				create_delivery_note(frm);
			});
		}
		
		// Set field properties
		if (frm.doc.customer_type === 'Individual') {
			frm.set_df_property('tax_id', 'hidden', 1);
		}
	},
	
	// Triggered when form is loaded for the first time
	onload: function(frm) {
		// Set default filters for link fields
		frm.set_query('customer', function() {
			return {
				filters: {
					'disabled': 0
				}
			};
		});
	},
	
	// Triggered before form is saved
	validate: function(frm) {
		// Client-side validation
		if (frm.doc.delivery_date && frm.doc.transaction_date) {
			if (frappe.datetime.get_diff(frm.doc.delivery_date, frm.doc.transaction_date) < 0) {
				frappe.msgprint(__('Delivery date cannot be before transaction date'));
				frappe.validated = false;
			}
		}
	},
	
	// Triggered before form is submitted
	// NOTE: before_submit is synchronous in Frappe — setting frappe.validated = false
	// inside an async frappe.confirm() callback does NOT reliably block submission.
	// Use a server-side on_submit validation or a custom button instead for async checks.
	before_submit: function(frm) {
		// For high-value orders, use a custom "Submit" button that shows a confirm
		// dialog and then calls frm.savesubmit() only on confirmation.
		// The pattern below is intentionally kept simple and synchronous.
		if (frm.doc.grand_total > 100000) {
			// Warn the user via a non-blocking alert; actual guard is server-side.
			frappe.show_alert({
				message: __('High-value order — ensure approvals are in place before submitting.'),
				indicator: 'orange'
			}, 8);
		}
	},
	
	// Triggered after form is saved
	after_save: function(frm) {
		frappe.show_alert({
			message: __('Sales Order saved successfully'),
			indicator: 'green'
		}, 5);
	}
});

// Example 2: Field-Level Events
frappe.ui.form.on('Sales Order', {
	// Customer field change
	customer: function(frm) {
		if (frm.doc.customer) {
			// Fetch customer details
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Customer',
					name: frm.doc.customer
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value('customer_name', r.message.customer_name);
						frm.set_value('territory', r.message.territory);
						frm.set_value('customer_group', r.message.customer_group);
					}
				}
			});
		}
	},
	
	// Transaction date change
	transaction_date: function(frm) {
		if (frm.doc.transaction_date) {
			// Auto-set delivery date (7 days from transaction)
			let delivery_date = frappe.datetime.add_days(frm.doc.transaction_date, 7);
			frm.set_value('delivery_date', delivery_date);
		}
	},
	
	// Discount percentage change
	discount_percentage: function(frm) {
		calculate_totals(frm);
	}
});

// Example 3: Child Table Events
frappe.ui.form.on('Sales Order Item', {
	// When item is added to child table
	items_add: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		row.qty = 1;
		frm.refresh_field('items');
	},
	
	// When item code is selected
	item_code: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		
		if (row.item_code) {
			// Fetch item details
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Item',
					name: row.item_code
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'item_name', r.message.item_name);
						frappe.model.set_value(cdt, cdn, 'description', r.message.description);
						frappe.model.set_value(cdt, cdn, 'rate', r.message.standard_rate);
						frappe.model.set_value(cdt, cdn, 'uom', r.message.stock_uom);
					}
				}
			});
		}
	},
	
	// When quantity changes
	qty: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	},
	
	// When rate changes
	rate: function(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	},
	
	// When item is removed
	items_remove: function(frm, cdt, cdn) {
		calculate_totals(frm);
	}
});

// Helper Functions
function calculate_item_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	
	if (row.qty && row.rate) {
		let amount = row.qty * row.rate;
		frappe.model.set_value(cdt, cdn, 'amount', amount);
		calculate_totals(frm);
	}
}

function calculate_totals(frm) {
	let total = 0;
	
	// Sum all item amounts
	frm.doc.items.forEach(function(item) {
		total += item.amount || 0;
	});
	
	frm.set_value('total', total);
	
	// Apply discount
	let discount_amount = 0;
	if (frm.doc.discount_percentage) {
		discount_amount = total * frm.doc.discount_percentage / 100;
	}
	
	frm.set_value('discount_amount', discount_amount);
	frm.set_value('grand_total', total - discount_amount);
}

function create_delivery_note(frm) {
	frappe.model.open_mapped_doc({
		method: 'erpnext.selling.doctype.sales_order.sales_order.make_delivery_note',
		frm: frm
	});
}
