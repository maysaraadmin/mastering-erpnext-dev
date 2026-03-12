/**
 * API Call Examples
 * Chapter 7: Client-Side Mastery
 * 
 * Demonstrates frappe.call() patterns
 */

// Example 1: Basic API Call
function get_customer_balance(customer) {
	frappe.call({
		method: 'erpnext.accounts.utils.get_balance_on',
		args: {
			party_type: 'Customer',
			party: customer,
			date: frappe.datetime.get_today()
		},
		callback: function(r) {
			if (r.message) {
				frappe.msgprint(__('Customer Balance: {0}', [format_currency(r.message)]));
			}
		}
	});
}

// Example 2: API Call with Error Handling
function create_sales_invoice_from_order(sales_order) {
	frappe.call({
		method: 'erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice',
		args: {
			source_name: sales_order
		},
		freeze: true,
		freeze_message: __('Creating Sales Invoice...'),
		callback: function(r) {
			if (r.message) {
				frappe.model.sync(r.message);
				frappe.set_route('Form', r.message.doctype, r.message.name);
			}
		},
		error: function(r) {
			frappe.msgprint({
				title: __('Error'),
				message: __('Failed to create Sales Invoice'),
				indicator: 'red'
			});
		}
	});
}

// Example 3: Async/Await Pattern
async function get_item_stock(item_code, warehouse) {
	try {
		const response = await frappe.call({
			method: 'erpnext.stock.utils.get_stock_balance',
			args: {
				item_code: item_code,
				warehouse: warehouse
			}
		});
		
		return response.message || 0;
	} catch (error) {
		console.error('Failed to get stock:', error);
		return 0;
	}
}

// Example 4: Multiple API Calls in Sequence
async function process_bulk_orders(orders) {
	let results = [];
	
	for (let order of orders) {
		try {
			const result = await frappe.call({
				method: 'custom_app.api.process_order',
				args: {
					order_id: order
				}
			});
			
			results.push({
				order: order,
				status: 'success',
				data: result.message
			});
		} catch (error) {
			results.push({
				order: order,
				status: 'failed',
				error: error.message
			});
		}
	}
	
	return results;
}

// Example 5: API Call with Progress Indicator
function import_bulk_data(file_url) {
	let progress_dialog = new frappe.ui.Dialog({
		title: __('Importing Data'),
		fields: [
			{
				fieldname: 'progress_html',
				fieldtype: 'HTML',
				options: '<div class="progress"><div class="progress-bar" style="width: 0%">0%</div></div>'
			}
		]
	});
	
	progress_dialog.show();
	
	frappe.call({
		method: 'custom_app.api.import_data',
		args: {
			file_url: file_url
		},
		callback: function(r) {
			if (r.message) {
				progress_dialog.hide();
				frappe.msgprint(__('Import completed: {0} records', [r.message.count]));
			}
		},
		// Update progress
		progress: function(progress) {
			let percent = Math.round(progress * 100);
			progress_dialog.fields_dict.progress_html.$wrapper.find('.progress-bar')
				.css('width', percent + '%')
				.text(percent + '%');
		}
	});
}

// Example 6: Batch API Calls
async function update_multiple_records(records) {
	const batch_size = 10;
	let batches = [];
	
	// Split into batches
	for (let i = 0; i < records.length; i += batch_size) {
		batches.push(records.slice(i, i + batch_size));
	}
	
	// Process batches
	for (let batch of batches) {
		await Promise.all(batch.map(record => 
			frappe.call({
				method: 'frappe.client.set_value',
				args: {
					doctype: record.doctype,
					name: record.name,
					fieldname: record.fieldname,
					value: record.value
				}
			})
		));
	}
	
	frappe.show_alert(__('All records updated'), 5);
}
