/**
 * Field Validation Examples
 * Chapter 7: Client-Side Mastery
 * 
 * Demonstrates client-side validation patterns
 */

// Example 1: Email Validation
frappe.ui.form.on('Customer', {
	email_id: function(frm) {
		if (frm.doc.email_id) {
			if (!validate_email(frm.doc.email_id)) {
				frappe.msgprint(__('Please enter a valid email address'));
				frm.set_value('email_id', '');
			}
		}
	}
});

function validate_email(email) {
	const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	return re.test(email);
}

// Example 2: Phone Number Validation
frappe.ui.form.on('Customer', {
	phone: function(frm) {
		if (frm.doc.phone) {
			let cleaned = clean_phone_number(frm.doc.phone);
			if (cleaned) {
				frm.set_value('phone', cleaned);
			}
		}
	}
});

function clean_phone_number(phone) {
	// Remove non-numeric characters
	let cleaned = phone.replace(/\D/g, '');
	
	// Format based on length
	if (cleaned.length === 10) {
		return cleaned.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
	}
	
	return phone;
}

// Example 3: Date Range Validation
frappe.ui.form.on('Project', {
	expected_start_date: function(frm) {
		validate_date_range(frm);
	},
	
	expected_end_date: function(frm) {
		validate_date_range(frm);
	}
});

function validate_date_range(frm) {
	if (frm.doc.expected_start_date && frm.doc.expected_end_date) {
		if (frappe.datetime.get_diff(frm.doc.expected_end_date, frm.doc.expected_start_date) < 0) {
			frappe.msgprint(__('End date cannot be before start date'));
			frm.set_value('expected_end_date', '');
		}
	}
}

// Example 4: Numeric Range Validation
frappe.ui.form.on('Item', {
	minimum_order_qty: function(frm) {
		validate_numeric_range(frm, 'minimum_order_qty', 1, 10000);
	},
	
	maximum_order_qty: function(frm) {
		validate_numeric_range(frm, 'maximum_order_qty', 1, 10000);
		
		// Ensure max > min
		if (frm.doc.maximum_order_qty && frm.doc.minimum_order_qty) {
			if (frm.doc.maximum_order_qty < frm.doc.minimum_order_qty) {
				frappe.msgprint(__('Maximum order quantity must be greater than minimum'));
				frm.set_value('maximum_order_qty', '');
			}
		}
	}
});

function validate_numeric_range(frm, fieldname, min, max) {
	let value = frm.doc[fieldname];
	
	if (value !== null && value !== undefined) {
		if (value < min || value > max) {
			frappe.msgprint(__('Value must be between {0} and {1}', [min, max]));
			frm.set_value(fieldname, '');
		}
	}
}

// Example 5: Custom Field Validation
frappe.ui.form.on('Sales Order', {
	validate: function(frm) {
		// Validate total items
		if (!frm.doc.items || frm.doc.items.length === 0) {
			frappe.msgprint(__('Please add at least one item'));
			frappe.validated = false;
			return;
		}
		
		// Validate item quantities
		let has_invalid_qty = false;
		frm.doc.items.forEach(function(item) {
			if (!item.qty || item.qty <= 0) {
				frappe.msgprint(__('Row {0}: Quantity must be greater than zero', [item.idx]));
				has_invalid_qty = true;
			}
		});
		
		if (has_invalid_qty) {
			frappe.validated = false;
			return;
		}
		
		// Validate credit limit
		if (frm.doc.customer && frm.doc.grand_total) {
			check_credit_limit(frm);
		}
	}
});

function check_credit_limit(frm) {
	frappe.call({
		method: 'erpnext.selling.doctype.customer.customer.get_credit_limit',
		args: {
			customer: frm.doc.customer,
			company: frm.doc.company
		},
		callback: function(r) {
			if (r.message) {
				let credit_limit = r.message.credit_limit;
				let outstanding = r.message.outstanding_amount;
				let available_credit = credit_limit - outstanding;
				
				if (frm.doc.grand_total > available_credit) {
					frappe.msgprint({
						title: __('Credit Limit Exceeded'),
						message: __('Available credit: {0}', [format_currency(available_credit)]),
						indicator: 'orange'
					});
				}
			}
		}
	});
}

// Example 6: Duplicate Check
frappe.ui.form.on('Customer', {
	email_id: function(frm) {
		if (frm.doc.email_id && frm.is_new()) {
			check_duplicate_email(frm);
		}
	}
});

function check_duplicate_email(frm) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Customer',
			filters: {
				email_id: frm.doc.email_id
			},
			fields: ['name']
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				frappe.msgprint({
					title: __('Duplicate Email'),
					message: __('A customer with this email already exists: {0}', [r.message[0].name]),
					indicator: 'orange'
				});
			}
		}
	});
}
