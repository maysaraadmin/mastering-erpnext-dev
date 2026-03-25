# Chapter 34: Advanced UI Patterns and Components

## 🎯 Learning Objectives

By the end of this chapter, you will master:
- **Creating custom buttons** and dialogs for enhanced user interactions
- **Implementing form field wrappers** for advanced field customization
- **Building custom list view** customizations and filters
- **Developing quick entry dialogs** for rapid data entry
- **Creating read-only forms** with conditional editing capabilities
- **Implementing advanced UI patterns** for complex business workflows
- **Building responsive components** that work across devices
- **Optimizing user experience** with modern UI/UX principles

## 📚 Chapter Topics

### 34.1 Custom Buttons and Dialogs

**Understanding frm.custom_make_buttons**

`frm.custom_make_buttons` is a Frappe Framework feature that allows you to customize the "Make" button labels in the form toolbar. When users click the "Make" button to create a new document from the current form, you can control what button text appears for each doctype.

**How It Works**

When `frm.make_new(doctype)` is called:

1. **First Priority**: Checks if `frm.make_methods[doctype]` exists - if so, calls that method
2. **Second Priority**: Checks if `frm.custom_make_buttons[doctype]` exists - if so, triggers the click event on the custom button with that label
3. **Default**: Creates a new document and matches link fields automatically

**Basic Implementation**

```javascript
// your_app/doctype/your_doctype/your_doctype.js
frappe.ui.form.on('Your DocType', {
    refresh: function(frm) {
        // Add custom make buttons
        frm.custom_make_buttons = {
            'Sales Invoice': 'Create Invoice',
            'Payment Entry': 'Record Payment',
            'Journal Entry': 'Create Journal',
            'Delivery Note': 'Ship Items'
        };
        
        // Add custom buttons
        frm.add_custom_button(__('Approve'), function() {
            // Custom approval logic
            frm.set_value('status', 'Approved');
            frm.save();
        }, __('Actions'));
        
        frm.add_custom_button(__('Reject'), function() {
            // Custom rejection logic
            frappe.confirm('Are you sure you want to reject this document?', function() {
                frm.set_value('status', 'Rejected');
                frm.save();
            });
        }, __('Actions'));
        
        // Add primary action button
        frm.add_custom_button(__('Process Payment'), function() {
            // Process payment logic
            process_payment(frm);
        }, __('Payment')).addClass('btn-primary');
    }
});

// Custom make method
frappe.ui.form.on('Your DocType', {
    make_sales_invoice: function(frm) {
        // Custom logic for creating sales invoice
        frappe.model.with_doctype('Sales Invoice', function() {
            let invoice = frappe.model.get_new_doc('Sales Invoice');
            
            // Set customer from current document
            invoice.customer = frm.doc.customer;
            invoice.company = frm.doc.company;
            
            // Add items from current document
            if (frm.doc.items) {
                frm.doc.items.forEach(function(item) {
                    invoice.append('items', {
                        item_code: item.item_code,
                        qty: item.qty,
                        rate: item.rate
                    });
                });
            }
            
            // Open the new invoice
            frappe.set_route('Form', 'Sales Invoice', invoice.name);
        });
    }
});
```

**Advanced Dialog Implementation**

```javascript
// Custom dialog with complex form
frappe.ui.form.on('Your DocType', {
    refresh: function(frm) {
        frm.add_custom_button(__('Advanced Dialog'), function() {
            show_advanced_dialog(frm);
        });
    }
});

function show_advanced_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Advanced Processing Options'),
        fields: [
            {
                fieldname: 'processing_type',
                fieldtype: 'Select',
                label: __('Processing Type'),
                options: 'Standard\nExpress\nBulk',
                reqd: 1
            },
            {
                fieldname: 'priority',
                fieldtype: 'Select',
                label: __('Priority'),
                options: 'Low\nMedium\nHigh\nUrgent'
            },
            {
                fieldname: 'due_date',
                fieldtype: 'Date',
                label: __('Due Date'),
                default: frappe.datetime.add_days(frappe.datetime.now_date(), 7)
            },
            {
                fieldname: 'notes',
                fieldtype: 'Small Text',
                label: __('Processing Notes')
            },
            {
                fieldname: 'attach_documents',
                fieldtype: 'Check',
                label: __('Attach Supporting Documents')
            },
            {
                fieldname: 'documents_section',
                fieldtype: 'Section Break',
                label: __('Documents'),
                depends_on: 'attach_documents'
            },
            {
                fieldname: 'attachment',
                fieldtype: 'Attach',
                label: __('Upload Document'),
                depends_on: 'attach_documents'
            }
        ],
        primary_action: function() {
            let values = dialog.get_values();
            
            // Validate required fields
            if (!values.processing_type) {
                frappe.msgprint(__('Processing Type is required'));
                return;
            }
            
            // Process the request
            frappe.call({
                method: 'your_app.api.process_advanced_request',
                args: {
                    docname: frm.doc.name,
                    processing_data: values
                },
                callback: function(response) {
                    if (response.message && response.message.success) {
                        frappe.show_alert({
                            message: __('Request processed successfully'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    } else {
                        frappe.show_alert({
                            message: __('Processing failed'),
                            indicator: 'red'
                        });
                    }
                }
            });
            
            dialog.hide();
        },
        secondary_action: function() {
            dialog.hide();
        }
    });
    
    // Show dialog
    dialog.show();
}
```

**Multi-Step Dialog Pattern**

```javascript
// Multi-step wizard dialog
function show_multi_step_dialog(frm) {
    let current_step = 1;
    let total_steps = 3;
    let dialog_data = {};
    
    let dialog = new frappe.ui.Dialog({
        title: __('Multi-Step Processing'),
        fields: get_step_fields(current_step),
        primary_action_label: current_step === total_steps ? __('Complete') : __('Next'),
        primary_action: function() {
            let values = dialog.get_values();
            
            // Validate current step
            if (!validate_step(current_step, values)) {
                return;
            }
            
            // Save step data
            Object.assign(dialog_data, values);
            
            if (current_step < total_steps) {
                // Move to next step
                current_step++;
                dialog.fields_dict = {};
                dialog.fields = get_step_fields(current_step);
                dialog.refresh();
                dialog.set_primary_action_label(current_step === total_steps ? __('Complete') : __('Next'));
            } else {
                // Complete the process
                complete_multi_step_process(frm, dialog_data);
                dialog.hide();
            }
        },
        secondary_action_label: current_step === 1 ? __('Cancel') : __('Previous'),
        secondary_action: function() {
            if (current_step === 1) {
                dialog.hide();
            } else {
                // Move to previous step
                current_step--;
                dialog.fields_dict = {};
                dialog.fields = get_step_fields(current_step);
                dialog.refresh();
                dialog.set_secondary_action_label(current_step === 1 ? __('Cancel') : __('Previous'));
                dialog.set_primary_action_label(current_step === total_steps ? __('Complete') : __('Next'));
            }
        }
    });
    
    dialog.show();
}

function get_step_fields(step) {
    switch(step) {
        case 1:
            return [
                {
                    fieldname: 'customer',
                    fieldtype: 'Link',
                    label: __('Customer'),
                    options: 'Customer',
                    reqd: 1
                },
                {
                    fieldname: 'order_type',
                    fieldtype: 'Select',
                    label: __('Order Type'),
                    options: 'Sales\nPurchase\nTransfer',
                    reqd: 1
                }
            ];
        case 2:
            return [
                {
                    fieldname: 'item_section',
                    fieldtype: 'Section Break',
                    label: __('Items')
                },
                {
                    fieldname: 'items',
                    fieldtype: 'Table',
                    label: __('Items'),
                    reqd: 1,
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
                            fieldname: 'quantity',
                            fieldtype: 'Float',
                            label: __('Quantity'),
                            in_list_view: 1,
                            reqd: 1
                        },
                        {
                            fieldname: 'rate',
                            fieldtype: 'Currency',
                            label: __('Rate'),
                            in_list_view: 1,
                            reqd: 1
                        }
                    ]
                }
            ];
        case 3:
            return [
                {
                    fieldname: 'payment_section',
                    fieldtype: 'Section Break',
                    label: __('Payment Details')
                },
                {
                    fieldname: 'payment_method',
                    fieldtype: 'Select',
                    label: __('Payment Method'),
                    options: 'Cash\nBank Transfer\nCredit Card\nCheck',
                    reqd: 1
                },
                {
                    fieldname: 'payment_terms',
                    fieldtype: 'Link',
                    label: __('Payment Terms'),
                    options: 'Payment Terms'
                }
            ];
    }
}
```

### 34.2 Form Field Wrappers

**Understanding Form Field $Wrapper**

Form field wrappers provide powerful ways to customize individual field appearances and behaviors beyond the standard Frappe field types. They allow you to create completely custom field interfaces while maintaining integration with Frappe's form system.

**Basic Field Wrapper Implementation**

```javascript
// Custom field wrapper for enhanced date picker
frappe.ui.form.on('Your DocType', {
    refresh: function(frm) {
        // Replace standard date field with custom wrapper
        enhance_date_field(frm, 'delivery_date');
    }
});

function enhance_date_field(frm, fieldname) {
    let field = frm.fields_dict[fieldname];
    let $wrapper = field.$wrapper;
    
    // Clear existing content
    $wrapper.empty();
    
    // Create custom date picker
    let $custom_date = $(`
        <div class="custom-date-wrapper">
            <div class="input-group">
                <input type="text" class="form-control" id="${fieldname}_custom" 
                       placeholder="Select Date" readonly>
                <div class="input-group-append">
                    <button class="btn btn-outline-secondary" type="button" id="${fieldname}_picker">
                        <i class="fa fa-calendar"></i>
                    </button>
                </div>
            </div>
            <div class="date-info mt-2">
                <small class="text-muted">
                    <span id="${fieldname}_info"></span>
                </small>
            </div>
        </div>
    `);
    
    $wrapper.append($custom_date);
    
    // Initialize flatpickr
    let datepicker = flatpickr(`#${fieldname}_custom`, {
        dateFormat: 'Y-m-d',
        minDate: 'today',
        onChange: function(selectedDates, dateStr) {
            frm.set_value(fieldname, dateStr);
            update_date_info(frm, fieldname, selectedDates[0]);
        }
    });
    
    // Set current value
    if (frm.doc[fieldname]) {
        $(`#${fieldname}_custom`).val(frm.doc[fieldname]);
        update_date_info(frm, fieldname, new Date(frm.doc[fieldname]));
    }
    
    // Handle field change
    frm.add_fetch(fieldname, 'fieldname', function(value) {
        $(`#${fieldname}_custom`).val(value);
        if (value) {
            update_date_info(frm, fieldname, new Date(value));
        }
    });
}

function update_date_info(frm, fieldname, date) {
    let $info = $(`#${fieldname}_info`);
    
    if (date) {
        let today = new Date();
        let diff_time = date - today;
        let diff_days = Math.ceil(diff_time / (1000 * 60 * 60 * 24));
        
        let info_text = '';
        if (diff_days === 0) {
            info_text = 'Today';
        } else if (diff_days === 1) {
            info_text = 'Tomorrow';
        } else if (diff_days === -1) {
            info_text = 'Yesterday';
        } else if (diff_days > 0) {
            info_text = `${diff_days} days from now`;
        } else {
            info_text = `${Math.abs(diff_days)} days ago`;
        }
        
        // Add day of week
        let day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        info_text += ` (${day_names[date.getDay()]})`;
        
        $info.text(info_text);
    } else {
        $info.text('');
    }
}
```

**Advanced Field Wrapper with Validation**

```javascript
// Custom field wrapper for enhanced currency input
function create_currency_field_wrapper(frm, fieldname) {
    let field = frm.fields_dict[fieldname];
    let $wrapper = field.$wrapper;
    
    // Clear existing content
    $wrapper.empty();
    
    // Create custom currency input
    let $currency_wrapper = $(`
        <div class="custom-currency-wrapper">
            <div class="input-group">
                <div class="input-group-prepend">
                    <span class="input-group-text" id="${fieldname}_currency_symbol">$</span>
                </div>
                <input type="text" class="form-control text-right" 
                       id="${fieldname}_input" placeholder="0.00">
                <div class="input-group-append">
                    <button class="btn btn-outline-secondary" type="button" id="${fieldname}_calc">
                        <i class="fa fa-calculator"></i>
                    </button>
                </div>
            </div>
            <div class="currency-validation mt-1">
                <small class="text-muted" id="${fieldname}_validation"></small>
            </div>
        </div>
    `);
    
    $wrapper.append($currency_wrapper);
    
    let $input = $(`#${fieldname}_input`);
    let $validation = $(`#${fieldname}_validation`);
    
    // Format input as currency
    $input.on('input', function() {
        let value = $(this).val();
        let formatted = format_currency_input(value);
        $(this).val(formatted);
        
        // Validate and update form
        let numeric_value = parse_currency_value(formatted);
        if (numeric_value !== null) {
            frm.set_value(fieldname, numeric_value);
            validate_currency_value(frm, fieldname, numeric_value);
        }
    });
    
    // Calculator button
    $(`#${fieldname}_calc`).on('click', function() {
        show_currency_calculator(frm, fieldname);
    });
    
    // Set initial value
    if (frm.doc[fieldname]) {
        $input.val(format_currency_value(frm.doc[fieldname]));
        validate_currency_value(frm, fieldname, frm.doc[fieldname]);
    }
    
    // Handle field change from form
    frm.add_fetch(fieldname, 'fieldname', function(value) {
        $input.val(format_currency_value(value));
        validate_currency_value(frm, fieldname, value);
    });
}

function format_currency_input(value) {
    // Remove all non-numeric characters except decimal point
    let cleaned = value.replace(/[^0-9.]/g, '');
    
    // Split into integer and decimal parts
    let parts = cleaned.split('.');
    let integer_part = parts[0] || '0';
    let decimal_part = parts[1] ? parts[2].substring(0, 2) : '';
    
    // Add thousand separators
    integer_part = integer_part.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    
    // Combine parts
    if (decimal_part) {
        return integer_part + '.' + decimal_part;
    } else {
        return integer_part;
    }
}

function parse_currency_value(formatted) {
    let cleaned = formatted.replace(/[^0-9.]/g, '');
    let parsed = parseFloat(cleaned);
    return isNaN(parsed) ? null : parsed;
}

function validate_currency_value(frm, fieldname, value) {
    let $validation = $(`#${fieldname}_validation`);
    let validation_message = '';
    let validation_class = 'text-muted';
    
    // Check for negative values
    if (value < 0) {
        validation_message = '⚠️ Negative value';
        validation_class = 'text-warning';
    }
    
    // Check for large amounts
    if (value > 1000000) {
        validation_message = '💰 Large amount: ' + format_currency(value);
        validation_class = 'text-info';
    }
    
    // Check for zero
    if (value === 0) {
        validation_message = 'Zero amount';
        validation_class = 'text-muted';
    }
    
    // Update validation display
    $validation.removeClass('text-muted text-warning text-info text-danger')
               .addClass(validation_class)
               .text(validation_message);
}

function show_currency_calculator(frm, fieldname) {
    let dialog = new frappe.ui.Dialog({
        title: __('Currency Calculator'),
        fields: [
            {
                fieldname: 'amount1',
                fieldtype: 'Currency',
                label: __('Amount 1'),
                default: 0
            },
            {
                fieldname: 'operation',
                fieldtype: 'Select',
                label: __('Operation'),
                options: 'Add\nSubtract\nMultiply\nDivide',
                default: 'Add'
            },
            {
                fieldname: 'amount2',
                fieldtype: 'Currency',
                label: __('Amount 2'),
                default: 0
            },
            {
                fieldname: 'result',
                fieldtype: 'Currency',
                label: __('Result'),
                default: 0,
                read_only: 1
            }
        ],
        primary_action: function() {
            let values = dialog.get_values();
            let result = 0;
            
            switch(values.operation) {
                case 'Add':
                    result = values.amount1 + values.amount2;
                    break;
                case 'Subtract':
                    result = values.amount1 - values.amount2;
                    break;
                case 'Multiply':
                    result = values.amount1 * values.amount2;
                    break;
                case 'Divide':
                    result = values.amount2 !== 0 ? values.amount1 / values.amount2 : 0;
                    break;
            }
            
            dialog.set_value('result', result);
        },
        secondary_action: function() {
            let result = dialog.get_value('result');
            frm.set_value(fieldname, result);
            dialog.hide();
        }
    });
    
    dialog.show();
}
```

### 34.3 List View Customization

**Enhanced List View Filters**

```javascript
// Custom list view filters and actions
frappe.listview_settings['Your DocType'] = {
    add_fields: ["customer", "status", "grand_total", "creation"],
    get_indicator: function(doc) {
        if (doc.status === "Open") {
            return [__("Open"), "orange", "status,=,Open"];
        } else if (doc.status === "Closed") {
            return [__("Closed"), "green", "status,=,Closed"];
        } else if (doc.status === "Cancelled") {
            return [__("Cancelled"], "red", "status,=,Cancelled"];
        }
    },
    onload: function(listview) {
        // Add custom filters
        add_custom_filters(listview);
        
        // Add bulk actions
        add_bulk_actions(listview);
        
        // Add custom toolbar buttons
        add_toolbar_buttons(listview);
        
        // Enhance row rendering
        enhance_row_rendering(listview);
    }
};

function add_custom_filters(listview) {
    // Add date range filter
    let date_filter = frappe.ui.form.make_control({
        parent: listview.page.page_actions.find('.custom-filters'),
        df: {
            fieldname: 'date_range',
            fieldtype: 'DateRange',
            label: __('Date Range'),
            change: function() {
                let date_range = this.get_value();
                if (date_range && date_range.length === 2) {
                    listview.filter_area.add_filter('Your DocType', 'creation', '>=', date_range[0]);
                    listview.filter_area.add_filter('Your DocType', 'creation', '<=', date_range[1]);
                    listview.refresh();
                }
            }
        },
        render_input: true,
        only_input: true
    });
    
    // Add amount range filter
    let amount_filter = frappe.ui.form.make_control({
        parent: listview.page.page_actions.find('.custom-filters'),
        df: {
            fieldname: 'amount_range',
            fieldtype: 'Float',
            label: __('Min Amount'),
            change: function() {
                let min_amount = this.get_value();
                if (min_amount) {
                    listview.filter_area.add_filter('Your DocType', 'grand_total', '>=', min_amount);
                    listview.refresh();
                }
            }
        },
        render_input: true,
        only_input: true
    });
    
    // Add status quick filters
    let status_filters = ['Open', 'Closed', 'Cancelled'];
    status_filters.forEach(function(status) {
        listview.page.add_button(status, function() {
            listview.filter_area.add_filter('Your DocType', 'status', '=', status);
            listview.refresh();
        });
    });
}

function add_bulk_actions(listview) {
    // Add bulk status update
    listview.page.add_menu_item(__('Bulk Update Status'), function() {
        let selected_docs = listview.get_checked_items();
        
        if (selected_docs.length === 0) {
            frappe.msgprint(__('Please select documents to update'));
            return;
        }
        
        let dialog = new frappe.ui.Dialog({
            title: __('Bulk Update Status'),
            fields: [
                {
                    fieldname: 'new_status',
                    fieldtype: 'Select',
                    label: __('New Status'),
                    options: 'Open\nClosed\nCancelled',
                    reqd: 1
                },
                {
                    fieldname: 'reason',
                    fieldtype: 'Text',
                    label: __('Reason for Change')
                }
            ],
            primary_action: function() {
                let values = dialog.get_values();
                let docnames = selected_docs.map(doc => doc.name);
                
                frappe.call({
                    method: 'your_app.api.bulk_update_status',
                    args: {
                        docnames: docnames,
                        new_status: values.new_status,
                        reason: values.reason
                    },
                    callback: function(response) {
                        if (response.message && response.message.success) {
                            frappe.show_alert({
                                message: __('Status updated for {0} documents', [selected_docs.length]),
                                indicator: 'green'
                            });
                            listview.refresh();
                        }
                    }
                });
                
                dialog.hide();
            }
        });
        
        dialog.show();
    });
    
    // Add bulk export
    listview.page.add_menu_item(__('Export Selected'), function() {
        let selected_docs = listview.get_checked_items();
        
        if (selected_docs.length === 0) {
            frappe.msgprint(__('Please select documents to export'));
            return;
        }
        
        let docnames = selected_docs.map(doc => doc.name);
        export_selected_documents(docnames);
    });
}

function add_toolbar_buttons(listview) {
    // Add custom report button
    listview.page.add_button(__('Custom Report'), function() {
        show_custom_report(listview);
    });
    
    // Add import button
    listview.page.add_button(__('Import Data'), function() {
        show_import_dialog(listview);
    });
    
    // Add refresh button with animation
    listview.page.add_button(__('Refresh'), function() {
        let $button = listview.page.toolbar.find('.btn-refresh');
        $button.find('i').addClass('fa-spin');
        
        listview.refresh().then(function() {
            setTimeout(function() {
                $button.find('i').removeClass('fa-spin');
            }, 1000);
        });
    });
}

function enhance_row_rendering(listview) {
    // Custom row rendering
    listview.render_row = function(row, data) {
        // Call original render
        frappe.ui.ListView.prototype.render_row.call(this, row, data);
        
        // Add custom styling based on data
        if (data.grand_total > 10000) {
            row.find('.level-left').addClass('text-bold');
        }
        
        // Add custom indicators
        if (data.overdue) {
            row.find('.level-left').append(`
                <span class="indicator-pill red">
                    <i class="fa fa-exclamation-triangle"></i> Overdue
                </span>
            `);
        }
        
        // Add quick actions
        row.find('.level-right').append(`
            <div class="quick-actions">
                <button class="btn btn-xs btn-default" onclick="quick_edit('${data.name}')">
                    <i class="fa fa-edit"></i>
                </button>
                <button class="btn btn-xs btn-default" onclick="quick_view('${data.name}')">
                    <i class="fa fa-eye"></i>
                </button>
            </div>
        `);
    };
}

function quick_edit(docname) {
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Your DocType',
            name: docname
        },
        callback: function(response) {
            let doc = response.message;
            
            let dialog = new frappe.ui.Dialog({
                title: __('Quick Edit: {0}', [docname]),
                fields: [
                    {
                        fieldname: 'status',
                        fieldtype: 'Select',
                        label: __('Status'),
                        options: 'Open\nClosed\nCancelled',
                        default: doc.status
                    },
                    {
                        fieldname: 'remarks',
                        fieldtype: 'Small Text',
                        label: __('Remarks')
                    }
                ],
                primary_action: function() {
                    let values = dialog.get_values();
                    
                    frappe.call({
                        method: 'frappe.client.set_value',
                        args: {
                            doctype: 'Your DocType',
                            name: docname,
                            fieldname: values
                        },
                        callback: function(response) {
                            frappe.show_alert({
                                message: __('Document updated successfully'),
                                indicator: 'green'
                            });
                            listview.refresh();
                        }
                    });
                    
                    dialog.hide();
                }
            });
            
            dialog.show();
        }
    });
}

function quick_view(docname) {
    frappe.set_route('Form', 'Your DocType', docname);
}
```

### 34.4 Quick Entry Dialogs

**Enhanced Quick Entry Patterns**

```javascript
// Custom quick entry dialog for rapid data entry
frappe.ui.form.on('Your DocType', {
    refresh: function(frm) {
        // Add quick entry button
        frm.add_custom_button(__('Quick Entry'), function() {
            show_quick_entry_dialog(frm);
        });
    }
});

function show_quick_entry_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Quick Entry - Your DocType'),
        fields: [
            {
                fieldname: 'customer_section',
                fieldtype: 'Section Break',
                label: __('Customer Information')
            },
            {
                fieldname: 'customer',
                fieldtype: 'Link',
                label: __('Customer'),
                options: 'Customer',
                reqd: 1,
                change: function() {
                    // Auto-fill customer details
                    if (this.value) {
                        frappe.call({
                            method: 'frappe.client.get',
                            args: {
                                doctype: 'Customer',
                                name: this.value
                            },
                            callback: function(response) {
                                let customer = response.message;
                                dialog.set_value('customer_name', customer.customer_name);
                                dialog.set_value('email', customer.email_id);
                                dialog.set_value('phone', customer.phone_no);
                            }
                        });
                    }
                }
            },
            {
                fieldname: 'customer_name',
                fieldtype: 'Read Only',
                label: __('Customer Name')
            },
            {
                fieldname: 'email',
                fieldtype: 'Data',
                label: __('Email')
            },
            {
                fieldname: 'phone',
                fieldtype: 'Data',
                label: __('Phone')
            },
            {
                fieldname: 'items_section',
                fieldtype: 'Section Break',
                label: __('Items')
            },
            {
                fieldname: 'items',
                fieldtype: 'Table',
                label: __('Items'),
                reqd: 1,
                fields: [
                    {
                        fieldname: 'item_code',
                        fieldtype: 'Link',
                        label: __('Item'),
                        options: 'Item',
                        in_list_view: 1,
                        reqd: 1,
                        change: function() {
                            // Auto-fill item details
                            if (this.value) {
                                frappe.call({
                                    method: 'frappe.client.get',
                                    args: {
                                        doctype: 'Item',
                                        name: this.value
                                    },
                                    callback: function(response) {
                                        let item = response.message;
                                        this.parent.set_value('item_name', item.item_name);
                                        this.parent.set_value('rate', item.formatted_rate || 0);
                                        this.parent.set_value('uom', item.stock_uom);
                                    }
                                });
                            }
                        }
                    },
                    {
                        fieldname: 'item_name',
                        fieldtype: 'Read Only',
                        label: __('Item Name'),
                        in_list_view: 1
                    },
                    {
                        fieldname: 'quantity',
                        fieldtype: 'Float',
                        label: __('Quantity'),
                        in_list_view: 1,
                        reqd: 1,
                        default: 1,
                        change: function() {
                            // Calculate amount
                            let rate = this.parent.get_value('rate') || 0;
                            let qty = this.value || 0;
                            this.parent.set_value('amount', rate * qty);
                        }
                    },
                    {
                        fieldname: 'uom',
                        fieldtype: 'Link',
                        label: __('UOM'),
                        options: 'UOM',
                        in_list_view: 1
                    },
                    {
                        fieldname: 'rate',
                        fieldtype: 'Currency',
                        label: __('Rate'),
                        in_list_view: 1,
                        change: function() {
                            // Calculate amount
                            let qty = this.parent.get_value('quantity') || 0;
                            let rate = this.value || 0;
                            this.parent.set_value('amount', qty * rate);
                        }
                    },
                    {
                        fieldname: 'amount',
                        fieldtype: 'Currency',
                        label: __('Amount'),
                        in_list_view: 1,
                        read_only: 1
                    }
                ]
            },
            {
                fieldname: 'total_section',
                fieldtype: 'Section Break',
                label: __('Totals')
            },
            {
                fieldname: 'total_amount',
                fieldtype: 'Currency',
                label: __('Total Amount'),
                read_only: 1
            },
            {
                fieldname: 'tax_amount',
                fieldtype: 'Currency',
                label: __('Tax Amount'),
                read_only: 1
            },
            {
                fieldname: 'grand_total',
                fieldtype: 'Currency',
                label: __('Grand Total'),
                read_only: 1
            }
        ],
        primary_action_label: __('Create Document'),
        primary_action: function() {
            let values = dialog.get_values();
            
            // Validate required fields
            if (!values.customer) {
                frappe.msgprint(__('Customer is required'));
                return;
            }
            
            if (!values.items || values.items.length === 0) {
                frappe.msgprint(__('At least one item is required'));
                return;
            }
            
            // Create document
            create_document_from_quick_entry(values, dialog);
        },
        secondary_action_label: __('Save as Draft'),
        secondary_action: function() {
            let values = dialog.get_values();
            
            // Save as draft
            create_document_from_quick_entry(values, dialog, true);
        }
    });
    
    // Calculate totals when items change
    dialog.fields_dict.items.df.onchange = function() {
        calculate_totals(dialog);
    };
    
    dialog.show();
}

function calculate_totals(dialog) {
    let items = dialog.get_value('items') || [];
    let total_amount = 0;
    
    items.forEach(function(item) {
        total_amount += item.amount || 0;
    });
    
    let tax_amount = total_amount * 0.1; // 10% tax
    let grand_total = total_amount + tax_amount;
    
    dialog.set_value('total_amount', total_amount);
    dialog.set_value('tax_amount', tax_amount);
    dialog.set_value('grand_total', grand_total);
}

function create_document_from_quick_entry(values, dialog, as_draft = false) {
    frappe.call({
        method: 'your_app.api.create_from_quick_entry',
        args: {
            doc_data: values,
            as_draft: as_draft
        },
        callback: function(response) {
            if (response.message && response.message.success) {
                frappe.show_alert({
                    message: __('Document created successfully'),
                    indicator: 'green'
                });
                
                // Open the created document
                frappe.set_route('Form', 'Your DocType', response.message.docname);
                
                dialog.hide();
            } else {
                frappe.show_alert({
                    message: __('Failed to create document'),
                    indicator: 'red'
                });
            }
        }
    });
}
```

### 34.5 Read-Only Forms with Conditional Editing

**Advanced Read-Only Patterns**

```javascript
// Conditional read-only form implementation
frappe.ui.form.on('Your DocType', {
    refresh: function(frm) {
        setup_conditional_readonly(frm);
        add_edit_controls(frm);
        setup_field_permissions(frm);
    },
    onload: function(frm) {
        // Check document status and apply readonly
        apply_readonly_based_on_status(frm);
    }
});

function setup_conditional_readonly(frm) {
    // Make form read-only based on conditions
    let is_readonly = should_be_readonly(frm);
    
    if (is_readonly) {
        make_form_readonly(frm);
    } else {
        enable_form_editing(frm);
    }
}

function should_be_readonly(frm) {
    // Define conditions for read-only
    let conditions = [
        frm.doc.docstatus === 1,  // Submitted document
        frm.doc.status === 'Closed',
        frm.doc.status === 'Cancelled',
        !frappe.user.has_role('System Manager') && frm.doc.owner !== frappe.session.user,
        new Date(frm.doc.creation) < new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) // Older than 30 days
    ];
    
    return conditions.some(condition => condition);
}

function make_form_readonly(frm) {
    // Disable all fields
    frm.fields.forEach(function(field) {
        if (field.df.fieldtype !== 'Button' && field.df.fieldtype !== 'Section Break') {
            field.df.read_only = 1;
            field.refresh();
        }
    });
    
    // Hide save buttons
    frm.disable_save();
    frm.disable_form();
    
    // Add visual indicator
    frm.dashboard.add_comment(__('This document is read-only'), 'blue');
    
    // Show edit controls
    show_edit_controls(frm);
}

function enable_form_editing(frm) {
    // Enable all fields
    frm.fields.forEach(function(field) {
        if (field.df.fieldtype !== 'Button' && field.df.fieldtype !== 'Section Break') {
            field.df.read_only = 0;
            field.refresh();
        }
    });
    
    // Enable save buttons
    frm.enable_save();
    frm.enable_form();
    
    // Hide edit controls
    hide_edit_controls(frm);
}

function show_edit_controls(frm) {
    // Add edit button
    frm.add_custom_button(__('Edit Document'), function() {
        request_edit_permission(frm);
    }, __('Actions')).addClass('btn-primary');
    
    // Add view changes button
    frm.add_custom_button(__('View Changes'), function() {
        show_document_history(frm);
    }, __('Actions'));
    
    // Add print button
    frm.add_custom_button(__('Print'), function() {
        frappe.ui.print_preview('Your DocType', frm.docname);
    }, __('Actions'));
}

function hide_edit_controls(frm) {
    // Remove edit-related buttons
    frm.remove_custom_button('Edit Document', 'Actions');
    frm.remove_custom_button('View Changes', 'Actions');
}

function request_edit_permission(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Request Edit Permission'),
        fields: [
            {
                fieldname: 'reason',
                fieldtype: 'Text',
                label: __('Reason for Edit'),
                reqd: 1
            },
            {
                fieldname: 'duration',
                fieldtype: 'Select',
                label: __('Edit Duration'),
                options: '15 minutes\n1 hour\n1 day\nPermanent',
                default: '1 hour'
            }
        ],
        primary_action: function() {
            let values = dialog.get_values();
            
            frappe.call({
                method: 'your_app.api.request_edit_permission',
                args: {
                    doctype: frm.doctype,
                    docname: frm.docname,
                    reason: values.reason,
                    duration: values.duration
                },
                callback: function(response) {
                    if (response.message && response.message.success) {
                        frappe.show_alert({
                            message: __('Edit permission granted'),
                            indicator: 'green'
                        });
                        
                        // Enable editing
                        enable_form_editing(frm);
                        
                        // Set timeout for temporary permissions
                        if (values.duration !== 'Permanent') {
                            set_edit_timeout(frm, values.duration);
                        }
                        
                        dialog.hide();
                    } else {
                        frappe.show_alert({
                            message: __('Edit permission denied'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    });
    
    dialog.show();
}

function set_edit_timeout(frm, duration) {
    let timeout_minutes = {
        '15 minutes': 15,
        '1 hour': 60,
        '1 day': 1440
    };
    
    let minutes = timeout_minutes[duration] || 60;
    
    setTimeout(function() {
        frappe.show_alert({
            message: __('Edit permission expired'),
            indicator: 'orange'
        });
        make_form_readonly(frm);
    }, minutes * 60 * 1000);
}

function show_document_history(frm) {
    frappe.call({
        method: 'frappe.desk.form.load.get_versions',
        args: {
            doctype: frm.doctype,
            name: frm.docname
        },
        callback: function(response) {
            let versions = response.message || [];
            
            if (versions.length === 0) {
                frappe.msgprint(__('No history available'));
                return;
            }
            
            show_version_dialog(frm, versions);
        }
    });
}

function show_version_dialog(frm, versions) {
    let dialog = new frappe.ui.Dialog({
        title: __('Document History'),
        size: 'large',
        fields: [
            {
                fieldname: 'versions',
                fieldtype: 'HTML',
                options: get_version_html(versions)
            }
        ]
    });
    
    dialog.show();
}

function get_version_html(versions) {
    let html = '<div class="table-responsive"><table class="table table-striped">';
    html += '<thead><tr><th>Date</th><th>User</th><th>Changes</th><th>Action</th></tr></thead>';
    html += '<tbody>';
    
    versions.forEach(function(version) {
        html += '<tr>';
        html += '<td>' + frappe.datetime.str_to_user(version.creation) + '</td>';
        html += '<td>' + version.owner + '</td>';
        html += '<td>' + (version.data || 'No changes recorded') + '</td>';
        html += '<td><button class="btn btn-xs btn-default" onclick="restore_version(\'' + version.name + '\')">Restore</button></td>';
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    return html;
}

function setup_field_permissions(frm) {
    // Set field-level permissions based on user role
    let user_roles = frappe.user_roles;
    
    // Only System Manager can edit certain fields
    if (!user_roles.includes('System Manager')) {
        let restricted_fields = ['total_amount', 'tax_amount', 'grand_total'];
        restricted_fields.forEach(function(fieldname) {
            let field = frm.fields_dict[fieldname];
            if (field) {
                field.df.read_only = 1;
                field.refresh();
            }
        });
    }
    
    // Only Sales Manager can approve documents
    if (!user_roles.includes('Sales Manager')) {
        let field = frm.fields_dict['status'];
        if (field) {
            field.df.options = 'Open\nPending'; // Remove 'Approved' option
            field.refresh();
        }
    }
}

function apply_readonly_based_on_status(frm) {
    // Apply read-only based on document status
    let readonly_statuses = ['Closed', 'Cancelled', 'Approved'];
    
    if (readonly_statuses.includes(frm.doc.status)) {
        make_form_readonly(frm);
    }
}
```

### 34.6 Responsive UI Components

**Mobile-First Design Patterns**

```javascript
// Responsive form layouts
frappe.ui.form.on('Your DocType', {
    refresh: function(frm) {
        setup_responsive_layout(frm);
        add_mobile_optimizations(frm);
    }
});

function setup_responsive_layout(frm) {
    // Check screen size and adjust layout
    if (window.innerWidth < 768) {
        // Mobile layout
        apply_mobile_layout(frm);
    } else {
        // Desktop layout
        apply_desktop_layout(frm);
    }
    
    // Listen for resize events
    window.addEventListener('resize', function() {
        setup_responsive_layout(frm);
    });
}

function apply_mobile_layout(frm) {
    // Compress form sections
    frm.fields_dict.forEach(function(field) {
        if (field.df.fieldtype === 'Section Break') {
            field.df.collapsible = 1;
            field.df.collapsible_depends_on = null;
            field.refresh();
        }
    });
    
    // Hide secondary actions
    frm.page.secondary_button_group.hide();
    
    // Add mobile-specific toolbar
    add_mobile_toolbar(frm);
    
    // Optimize table fields for mobile
    optimize_mobile_tables(frm);
}

function apply_desktop_layout(frm) {
    // Expand form sections
    frm.fields_dict.forEach(function(field) {
        if (field.df.fieldtype === 'Section Break') {
            field.df.collapsible = 0;
            field.refresh();
        }
    });
    
    // Show secondary actions
    frm.page.secondary_button_group.show();
    
    // Remove mobile toolbar
    remove_mobile_toolbar(frm);
}

function add_mobile_toolbar(frm) {
    // Create mobile-friendly toolbar
    let mobile_toolbar = $(`
        <div class="mobile-toolbar">
            <div class="mobile-actions">
                <button class="btn btn-primary mobile-save">Save</button>
                <button class="btn btn-default mobile-cancel">Cancel</button>
            </div>
        </div>
    `);
    
    frm.wrapper.append(mobile_toolbar);
    
    // Bind actions
    mobile_toolbar.find('.mobile-save').on('click', function() {
        frm.save();
    });
    
    mobile_toolbar.find('.mobile-cancel').on('click', function() {
        frappe.set_route();
    });
}

function remove_mobile_toolbar(frm) {
    frm.wrapper.find('.mobile-toolbar').remove();
}

function optimize_mobile_tables(frm) {
    // Optimize table fields for mobile viewing
    frm.fields_dict.forEach(function(field) {
        if (field.df.fieldtype === 'Table') {
            // Hide non-essential columns
            let grid = field.grid;
            if (grid) {
                grid.docfields.forEach(function(df) {
                    if (!df.reqd && df.in_list_view !== 1) {
                        df.hidden = 1;
                    }
                });
                grid.refresh();
            }
        }
    });
}

function add_mobile_optimizations(frm) {
    // Add swipe gestures for mobile
    if ('ontouchstart' in window) {
        add_swipe_gestures(frm);
    }
    
    // Add touch-friendly controls
    add_touch_controls(frm);
}

function add_swipe_gestures(frm) {
    let startX = 0;
    let startY = 0;
    let endX = 0;
    let endY = 0;
    
    frm.wrapper.on('touchstart', function(e) {
        startX = e.originalEvent.touches[0].clientX;
        startY = e.originalEvent.touches[0].clientY;
    });
    
    frm.wrapper.on('touchend', function(e) {
        endX = e.originalEvent.changedTouches[0].clientX;
        endY = e.originalEvent.changedTouches[0].clientY;
        
        let deltaX = endX - startX;
        let deltaY = endY - startY;
        
        // Check for horizontal swipe
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
            if (deltaX > 0) {
                // Swipe right - previous document
                navigate_to_previous(frm);
            } else {
                // Swipe left - next document
                navigate_to_next(frm);
            }
        }
    });
}

function add_touch_controls(frm) {
    // Increase touch target size for mobile
    if (window.innerWidth < 768) {
        frm.wrapper.find('.btn, .control-input').css({
            'min-height': '44px',
            'min-width': '44px'
        });
    }
}

function navigate_to_previous(frm) {
    // Navigate to previous document in list
    frappe.call({
        method: 'your_app.api.get_previous_document',
        args: {
            doctype: frm.doctype,
            current_doc: frm.docname
        },
        callback: function(response) {
            if (response.message) {
                frappe.set_route('Form', frm.doctype, response.message);
            } else {
                frappe.show_alert({
                    message: __('No previous document'),
                    indicator: 'orange'
                });
            }
        }
    });
}

function navigate_to_next(frm) {
    // Navigate to next document in list
    frappe.call({
        method: 'your_app.api.get_next_document',
        args: {
            doctype: frm.doctype,
            current_doc: frm.docname
        },
        callback: function(response) {
            if (response.message) {
                frappe.set_route('Form', frm.doctype, response.message);
            } else {
                frappe.show_alert({
                    message: __('No next document'),
                    indicator: 'orange'
                });
            }
        }
    });
}
```

---

## 🎯 **Advanced UI Best Practices Summary**

### **User Experience Principles**
- **Consistency**: Maintain consistent patterns across all forms
- **Progressive Disclosure**: Show complexity only when needed
- **Mobile-First**: Design for mobile devices first
- **Accessibility**: Ensure keyboard navigation and screen reader support

### **Performance Optimization**
- **Lazy Loading**: Load complex components only when needed
- **Event Delegation**: Use efficient event handling patterns
- **Debouncing**: Prevent excessive API calls
- **Memory Management**: Clean up event listeners and timers

### **Code Organization**
- **Modular Functions**: Create reusable UI components
- **Configuration Driven**: Use configuration objects for flexibility
- **Error Handling**: Provide clear error messages and recovery options
- **Testing**: Test UI components across different devices and browsers

### **Security Considerations**
- **Input Validation**: Validate all user inputs
- **Permission Checks**: Verify user permissions before actions
- **Data Sanitization**: Prevent XSS attacks
- **Rate Limiting**: Prevent abuse of UI features

---

**💡 Pro Tip**: Advanced UI patterns significantly improve user experience but should be used judiciously. Always test with real users and ensure accessibility standards are met. The best UI is often the simplest one that effectively solves the user's problem.


---

## 📌 Addendum: Awesomplete, Keyboard Shortcuts, and Refresh Operations

### Awesomplete in Frappe

Frappe uses [Awesomplete](https://leaverou.github.io/awesomplete/) — a lightweight (~2KB) vanilla JS autocomplete library — for Link fields, Autocomplete fields, Multi-Select fields, and the global search bar.

**Why Awesomplete?** Lightweight, no jQuery dependency, accessible (ARIA), keyboard-navigable.

**How Frappe configures it:**

```javascript
// Link field (frappe/public/js/frappe/form/controls/link.js)
this.awesomplete = new Awesomplete(me.input, {
    tabSelect: true,
    minChars: 0,
    maxItems: 99,
    autoFirst: true,
    list: [],
    filter: function() { return true; },  // Server-side filtering
    data: function(item) {
        return { label: me.get_translated(item.label || item.value), value: item.value };
    },
    replace: function(item) {
        this.input.value = me.get_translated(item.label || item.value);
    }
});
```

**Key events:**

```javascript
$input.on("awesomplete-open", function() { /* suggestions shown */ });
$input.on("awesomplete-close", function() { /* suggestions hidden */ });
$input.on("awesomplete-selectcomplete", function(e) {
    // e.text.value = selected value
    this.parse_validate_and_set_in_model(this.get_input_value());
});
```

**Custom field with Awesomplete:**

```javascript
frappe.ui.form.ControlCustomField = class extends frappe.ui.form.ControlData {
    make_input() {
        super.make_input();
        this.awesomplete = new Awesomplete(this.input, {
            minChars: 2,
            maxItems: 10,
            autoFirst: true,
            list: this.get_suggestions(),
            filter: (text, input) => Awesomplete.FILTER_CONTAINS(text, input)
        });
        this.$input.on("awesomplete-selectcomplete", (e) => {
            this.set_value(e.text.value);
        });
    }
    get_suggestions() {
        return [{ label: "Option 1", value: "opt1" }];
    }
};
```

**Performance:** Frappe caches search results to avoid repeated server calls:

```javascript
this.$input.cache = {};
if (this.$input.cache[doctype]?.[term]) {
    me.awesomplete.list = this.$input.cache[doctype][term];
    return;
}
```

---

### Keyboard Shortcuts Reference

Frappe registers shortcuts via `frappe.ui.keys.add_shortcut()`. Press `Shift+/` to see all shortcuts in the current context.

**Global shortcuts:**

| Shortcut | Action |
|---|---|
| `Ctrl+S` | Save / trigger primary action |
| `Ctrl+G` | Open Awesomebar (search) |
| `Ctrl+H` | Navigate home |
| `Alt+S` | Open settings dropdown |
| `Alt+H` | Open help dropdown |
| `Shift+/` | Show all keyboard shortcuts |
| `Shift+Ctrl+R` | Clear cache and reload |
| `Shift+Ctrl+G` | Switch theme |
| `Escape` | Close dialogs |

**Form shortcuts:**

| Shortcut | Action |
|---|---|
| `Shift+Ctrl+>` | Next record |
| `Shift+Ctrl+<` | Previous record |
| `Ctrl+P` | Print document |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+E` | Email document |
| `Ctrl+J` | Jump to field |
| `Shift+D` | Duplicate document |
| `Shift+Ctrl+D` | Delete document |
| `Ctrl+B` | New document (same DocType) |
| `Alt+Hover` | Show fieldname (click to copy) |

**Child table shortcuts:**

| Shortcut | Action |
|---|---|
| `Up/Down Arrow` | Navigate rows |
| `Tab / Shift+Tab` | Next/previous column |
| `Ctrl+Down` | Add row below |
| `Ctrl+Up` | Add row above |
| `Shift+Alt+Down` | Duplicate current row |

**List view shortcuts:**

| Shortcut | Action |
|---|---|
| `Up/Down Arrow` | Navigate list |
| `Shift+Up/Down` | Select multiple |
| `Enter` | Open focused item |
| `Space` | Toggle checkbox |

**Register custom shortcuts:**

```javascript
frappe.ui.keys.add_shortcut({
    shortcut: "ctrl+shift+a",
    action: function() {
        frappe.msgprint(__("Custom shortcut triggered"));
    },
    description: __("My Custom Action"),
    page: "Form",
    ignore_inputs: false,
    condition: function() { return !!cur_frm; }
});
```

---

### Refresh Operations — Complete Story

Understanding which refresh method to use prevents unnecessary server calls and UI glitches.

**Quick comparison:**

| Method | Server Call | Scope | Use When |
|---|---|---|---|
| `frm.refresh()` | No | Entire form | Switch documents, permission changes |
| `frm.reload_doc()` | **Yes** | Entire form | Need fresh data from server |
| `frm.refresh_field(name)` | No | Single field | After changing one field |
| `frm.refresh_fields()` | No | All fields | After bulk changes |

**`frm.refresh()`** — reads from `locals` (client-side cache), re-renders the form, triggers the `refresh` event. No server call.

**`frm.reload_doc()`** — removes the document from `locals`, fetches fresh data from server via `frappe.model.with_doc()`, then calls `frm.refresh()`. Only works for saved documents.

**`frm.refresh_field(fieldname)`** — calls `field.refresh()` which recalculates field status (Read/Write/None), shows/hides the field, and refreshes dependencies.

**`frm.refresh_fields()`** — calls `layout.refresh(doc)` which loops through all fields, refreshes dependencies (`depends_on` logic), and manages section visibility.

**Common patterns:**

```javascript
// After set_value (usually auto-refreshes, but explicit is safe)
frm.set_value("territory", "Default");
frm.refresh_field("territory");

// After bulk changes
frm.doc.field1 = value1;
frm.doc.field2 = value2;
frm.refresh_fields();

// After server-side changes
frappe.call({
    method: "myapp.api.process",
    args: { name: frm.doc.name },
    callback: (r) => { if (!r.exc) frm.reload_doc(); }
});

// After adding child rows
let row = frm.add_child("items");
row.item_code = "ITEM-001";
frm.refresh_field("items");
```

**Avoiding infinite loops:**

```javascript
// BAD — circular dependency
frappe.ui.form.on("Sales Order", {
    customer: (frm) => frm.set_value("territory", "Default"),
    territory: (frm) => frm.set_value("customer", "Default")  // Loop!
});

// GOOD — use a flag
frappe.ui.form.on("Sales Order", {
    customer: (frm) => {
        if (!frm._updating) {
            frm._updating = true;
            frm.set_value("territory", "Default");
            frm._updating = false;
        }
    }
});
```

**Serial execution in `render_form()`:**

When a form renders, Frappe executes these steps serially:
1. `refresh_header()` — toolbar, buttons, title
2. `$(document).trigger("form-refresh")` — global event
3. `refresh_fields()` — all fields
4. `script_manager.trigger("refresh")` — your custom `refresh` handler
5. `onload_post_render()` — first load only
6. `focus_on_first_input()` — new documents
7. `dashboard.after_refresh()`

This is why custom buttons added in `refresh` are recreated on every refresh — that's intentional.


---

## 📌 Addendum: Custom Workspace Icons and Disabling Console Logs

### Adding Custom Icons to Workspace

Frappe uses an SVG sprite system for icons. You can add your own icons and use them in Workspace shortcuts, DocType icons, and anywhere Frappe renders icons.

**Step 1: Create the SVG sprite file**

```
apps/your_app/your_app/public/icons/my_icons.svg
```

```xml
<?xml version="1.0" encoding="utf-8"?>
<svg id="frappe-symbols" aria-hidden="true"
     style="position: absolute; width: 0; height: 0; overflow: hidden;"
     class="d-block" xmlns="http://www.w3.org/2000/svg">

    <symbol id="icon-invoice" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <!-- Paste SVG path content here (no outer <svg> tag) -->
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
    </symbol>

    <symbol id="icon-delivery" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <rect x="1" y="3" width="15" height="13"/>
        <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
        <circle cx="5.5" cy="18.5" r="2.5"/>
        <circle cx="18.5" cy="18.5" r="2.5"/>
    </symbol>

</svg>
```

The `id` attribute (e.g., `icon-invoice`) is what you'll use when selecting the icon in Frappe's icon picker. The name after `icon-` is the icon name.

**Step 2: Register in `hooks.py`**

```python
app_include_icons = [
    "your_app/icons/my_icons.svg"
]
```

**Step 3: Build and clear cache**

```bash
bench build --app your_app
bench --site mysite clear-cache
```

After this, your custom icons appear in the Workspace icon picker and anywhere Frappe renders icons.

**Where to find free SVG icons:**
- https://tabler.io/icons
- https://feathericons.com/
- https://heroicons.com/

**What is an SVG sprite?** A single SVG file containing multiple icons as `<symbol>` elements. Frappe injects this file into the page DOM, then references individual icons with `<use href="#icon-name">`. This is more performant than loading separate icon files.

---

### Disabling JS Console Logs in Production

In production, console logs can leak sensitive information and add overhead. The fix: override all console methods to no-ops when not in developer mode.

**Step 1: Create `apps/your_app/your_app/public/js/disable_console.js`**

```javascript
(function() {
    function isFrappeContext() {
        return typeof frappe !== "undefined" && frappe.boot && frappe.boot.developer_mode !== undefined;
    }

    function isDeveloperMode() {
        // Use Frappe's developer_mode flag if available
        if (isFrappeContext()) {
            return frappe.boot.developer_mode;
        }
        // Fallback: check hostname for local/dev environments
        const host = window.location.hostname;
        return (
            host === "localhost" ||
            host === "127.0.0.1" ||
            host.includes(".local") ||
            host.includes("dev") ||
            host.includes("staging") ||
            window.location.search.includes("debug=true")
        );
    }

    if (!isDeveloperMode()) {
        const methods = [
            "log", "info", "warn", "error", "debug", "trace",
            "dir", "dirxml", "group", "groupEnd", "time", "timeEnd",
            "count", "assert", "clear", "profile", "profileEnd",
            "timeStamp", "groupCollapsed"
        ];
        methods.forEach((method) => {
            if (console[method]) {
                console[method] = function() {};
            }
        });
    }
})();
```

**Step 2: Register in `hooks.py`**

```python
# Desk pages (admin interface)
app_include_js = ["/assets/your_app/js/disable_console.js"]

# Public web pages (web forms, website)
web_include_js = ["/assets/your_app/js/disable_console.js"]
```

**Step 3: For plain HTML pages in `www/`**

`app_include_js` and `web_include_js` don't apply to static HTML files. Include the script manually:

```html
<head>
    <script src="/assets/your_app/js/disable_console.js"></script>
</head>
```

**No `bench build` needed** — just restart bench after updating `hooks.py`. Frappe loads `app_include_js` files directly without bundling.

**Key notes:**
- `frappe.boot` is only available on Desk and Web Form pages, not plain HTML pages
- In developer mode (`frappe.boot.developer_mode = 1`), logs remain enabled
- The hostname fallback handles cases where `frappe.boot` isn't loaded yet
- This is UI-only — server-side logs are unaffected
