# Chapter 9: Advanced Reporting and Data Visualization

## 🎯 Learning Objectives

By the end of this chapter, you will master:

- **How** Frappe's reporting engine processes queries and renders reports
- **Why** different report types have specific performance characteristics
- **When** to use custom queries vs standard report builders
- **How** data visualization components work internally
- **Advanced patterns** for building high-performance reports
- **Performance optimization** techniques for complex data aggregations

## 📚 Chapter Topics

### 9.1 Understanding the Reporting Engine Architecture

**The Report Processing Pipeline**

Frappe's reporting engine is a sophisticated system that handles query generation, data processing, caching, and visualization. Understanding its internal architecture is crucial for building high-performance, scalable reports.

#### How Reports Are Processed

```python
# Simplified version of Frappe's report processing engine
class ReportProcessor:
    def __init__(self, report_name):
        self.report_name = report_name
        self.report_config = None
        self.query_builder = QueryBuilder()
        self.data_processor = DataProcessor()
        self.cache_manager = ReportCacheManager()
        self.performance_monitor = ReportPerformanceMonitor()
        self.visualization_engine = VisualizationEngine()
        
        # Load report configuration
        self.load_report_config()
    
    def load_report_config(self):
        """Load report configuration from database"""
        self.report_config = frappe.get_doc('Report', self.report_name)
        
        if not self.report_config:
            raise ReportException(f"Report {self.report_name} not found")
        
        # Parse report configuration
        self.parse_report_config()
    
    def parse_report_config(self):
        """Parse report configuration into internal format"""
        self.config = {
            'doctype': self.report_config.ref_doctype,
            'query': self.report_config.query or self.build_default_query(),
            'filters': self.parse_filters(self.report_config.filters),
            'columns': self.parse_columns(self.report_config.columns),
            'group_by': self.report_config.group_by,
            'order_by': self.report_config.order_by,
            'chart_type': self.report_config.chart_type,
            'chart_options': self.parse_chart_options(self.report_config.chart_options)
        }
    
    def build_default_query(self):
        """Build default query for report"""
        doctype = self.report_config.ref_doctype
        
        # Get standard fields
        standard_fields = ['name', 'creation', 'modified', 'owner', 'modified_by']
        
        # Get custom fields
        custom_fields = frappe.get_meta(doctype).get('fields', [])
        field_names = [f.fieldname for f in custom_fields if f.in_list_view]
        
        # Build SELECT clause
        all_fields = standard_fields + field_names
        select_clause = ', '.join([f"`{field}`" for field in all_fields])
        
        # Build query
        query = f"""
            SELECT {select_clause}
            FROM `tab{doctype}`
            WHERE docstatus != 2
        """
        
        return query
    
    def parse_filters(self, filters_json):
        """Parse filters from JSON"""
        if not filters_json:
            return {}
        
        try:
            return json.loads(filters_json)
        except json.JSONDecodeError:
            return {}
    
    def parse_columns(self, columns_json):
        """Parse columns from JSON"""
        if not columns_json:
            return []
        
        try:
            return json.loads(columns_json)
        except json.JSONDecodeError:
            return []
    
    def parse_chart_options(self, chart_options_json):
        """Parse chart options from JSON"""
        if not chart_options_json:
            return {}
        
        try:
            return json.loads(chart_options_json)
        except json.JSONDecodeError:
            return {}
    
    def execute_report(self, filters=None, as_dict=True):
        """Execute report with performance monitoring"""
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self.generate_cache_key(filters)
            
            # Try to get from cache
            cached_result = self.cache_manager.get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # Build query with filters
            query = self.build_query_with_filters(filters)
            
            # Execute query
            data = self.execute_query(query, as_dict)
            
            # Process data
            processed_data = self.data_processor.process(data, self.config)
            
            # Generate visualizations
            if self.config['chart_type']:
                chart_data = self.visualization_engine.generate_chart(
                    processed_data, 
                    self.config['chart_type'], 
                    self.config['chart_options']
                )
                processed_data['chart'] = chart_data
            
            # Cache result
            self.cache_manager.cache_result(cache_key, processed_data)
            
            # Track performance
            execution_time = time.time() - start_time
            self.performance_monitor.track_report_execution(
                self.report_name, 
                execution_time, 
                len(processed_data.get('data', []))
            )
            
            return processed_data
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.performance_monitor.track_report_error(
                self.report_name, 
                execution_time, 
                str(e)
            )
            raise ReportException(f"Report execution failed: {str(e)}")
    
    def build_query_with_filters(self, filters):
        """Build query with applied filters"""
        query = self.config['query']
        
        if not filters:
            return query
        
        # Parse existing query
        parsed_query = self.query_builder.parse(query)
        
        # Apply filters
        where_conditions = []
        
        for field, value in filters.items():
            if value is not None and value != '':
                if isinstance(value, list):
                    # Handle list values (IN clause)
                    if len(value) > 0:
                        placeholders = ', '.join(['%s'] * len(value))
                        where_conditions.append(f"`{field}` IN ({placeholders})")
                elif isinstance(value, dict):
                    # Handle range filters
                    if value.get('from') and value.get('to'):
                        where_conditions.append(f"`{field}` BETWEEN %s AND %s")
                    elif value.get('from'):
                        where_conditions.append(f"`{field}` >= %s")
                    elif value.get('to'):
                        where_conditions.append(f"`{field}` <= %s")
                else:
                    # Handle simple equality
                    where_conditions.append(f"`{field}` = %s")
        
        # Add WHERE clause if conditions exist
        if where_conditions:
            if 'WHERE' in parsed_query:
                parsed_query['where'].extend(where_conditions)
            else:
                parsed_query['where'] = where_conditions
        
        # Rebuild query
        return self.query_builder.build(parsed_query)
    
    def execute_query(self, query, as_dict=True):
        """Execute database query with error handling"""
        try:
            return frappe.db.sql(query, as_dict=as_dict)
        except Exception as e:
            frappe.log_error(f"Report query failed: {query}\nError: {str(e)}")
            raise ReportException(f"Query execution failed: {str(e)}")
    
    def generate_cache_key(self, filters):
        """Generate cache key for report"""
        cache_components = [
            self.report_name,
            json.dumps(filters or {}, sort_keys=True),
            self.config['query'],
            str(frappe.session.user)
        ]
        
        cache_string = '|'.join(cache_components)
        return f"report:{hashlib.md5(cache_string.encode()).hexdigest()}"
    
    def get_report_columns(self):
        """Get report column definitions"""
        columns = []
        
        # Get columns from query result
        sample_data = self.execute_query("SELECT * FROM (" + self.config['query'] + ") AS subquery LIMIT 1")
        
        if sample_data:
            column_names = sample_data[0].keys() if isinstance(sample_data[0], dict) else sample_data[0]
            
            for col_name in column_names:
                col_def = {
                    'fieldname': col_name,
                    'label': col_name.replace('_', ' ').title(),
                    'fieldtype': 'Data',
                    'width': 120
                }
                
                # Try to determine field type from database
                field_type = self.get_field_type_from_database(col_name)
                if field_type:
                    col_def['fieldtype'] = field_type
                
                columns.append(col_def)
        
        return columns
    
    def get_field_type_from_database(self, field_name):
        """Get field type from database schema"""
        try:
            # Get table name from query
            table_match = re.search(r'FROM `?([^`\s]+)`?', self.config['query'], re.IGNORECASE)
            if not table_match:
                return None
            
            table_name = table_match.group(1)
            
            # Get column information
            column_info = frappe.db.sql(f"""
                SELECT DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = %s AND COLUMN_NAME = %s
            """, (table_name, field_name))
            
            if column_info:
                data_type = column_info[0][0].upper()
                
                # Map SQL types to Frappe field types
                type_mapping = {
                    'VARCHAR': 'Data',
                    'TEXT': 'Text',
                    'LONGTEXT': 'Text Editor',
                    'INT': 'Int',
                    'DECIMAL': 'Currency',
                    'FLOAT': 'Float',
                    'DATE': 'Date',
                    'DATETIME': 'Datetime',
                    'BOOLEAN': 'Check',
                    'JSON': 'JSON'
                }
                
                for sql_type, frappe_type in type_mapping.items():
                    if sql_type in data_type:
                        return frappe_type
            
            return 'Data'
            
        except Exception:
            return 'Data'
    
    def export_report(self, format_type='csv', filters=None):
        """Export report in specified format"""
        # Get report data
        data = self.execute_report(filters)
        
        # Export based on format
        if format_type == 'csv':
            return self.export_to_csv(data)
        elif format_type == 'excel':
            return self.export_to_excel(data)
        elif format_type == 'pdf':
            return self.export_to_pdf(data)
        else:
            raise ReportException(f"Unsupported export format: {format_type}")
    
    def export_to_csv(self, data):
        """Export report data to CSV"""
        import csv
        import io
        
        if not data.get('data'):
            return "No data to export"
        
        output = io.StringIO()
        
        # Get column names
        if data['data']:
            fieldnames = list(data['data'][0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data
            for row in data['data']:
                writer.writerow(row)
        
        return output.getvalue()
    
    def export_to_excel(self, data):
        """Export report data to Excel"""
        try:
            import openpyxl
            from openpyxl.utils import get_column_letter
            
            if not data.get('data'):
                return "No data to export"
            
            # Create workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = self.report_name
            
            # Get column names
            fieldnames = list(data['data'][0].keys())
            
            # Write header
            for col_idx, fieldname in enumerate(fieldnames, 1):
                col_letter = get_column_letter(col_idx)
                ws[f"{col_letter}1"] = fieldname.replace('_', ' ').title()
            
            # Write data
            for row_idx, row in enumerate(data['data'], 2):
                for col_idx, fieldname in enumerate(fieldnames, 1):
                    col_letter = get_column_letter(col_idx)
                    ws[f"{col_letter}{row_idx}"] = row.get(fieldname, '')
            
            # Save to bytes
            from io import BytesIO
            excel_buffer = BytesIO()
            wb.save(excel_buffer)
            excel_buffer.seek(0)
            
            return excel_buffer.getvalue()
            
        except ImportError:
            raise ReportException("openpyxl is required for Excel export")
    
    def export_to_pdf(self, data):
        """Export report data to PDF"""
        # This would require additional PDF generation library
        # For now, return a simple text representation
        if not data.get('data'):
            return "No data to export"
        
        output = []
        output.append(f"Report: {self.report_name}")
        output.append("=" * 50)
        
        # Add header
        if data['data']:
            headers = list(data['data'][0].keys())
            output.append("\t".join(headers))
            output.append("-" * 50)
            
            # Add data
            for row in data['data']:
                values = [str(row.get(header, '')) for header in headers]
                output.append("\t".join(values))
        
        return "\n".join(output)

# Report exception class
class ReportException(Exception):
    pass
```

#### Data Processing Engine

```python
# Advanced data processing for reports
class DataProcessor:
    def __init__(self):
        self.aggregators = {
            'sum': self.aggregate_sum,
            'avg': self.aggregate_avg,
            'count': self.aggregate_count,
            'min': self.aggregate_min,
            'max': self.aggregate_max
        }
    
    def process(self, data, config):
        """Process raw data according to report configuration"""
        processed_data = {
            'data': data,
            'summary': {},
            'columns': config.get('columns', []),
            'filters_applied': config.get('filters', {})
        }
        
        # Apply grouping
        if config.get('group_by'):
            processed_data = self.apply_grouping(processed_data, config['group_by'])
        
        # Apply aggregations
        if config.get('aggregations'):
            processed_data = self.apply_aggregations(processed_data, config['aggregations'])
        
        # Apply calculations
        if config.get('calculations'):
            processed_data = self.apply_calculations(processed_data, config['calculations'])
        
        # Apply formatting
        processed_data = self.apply_formatting(processed_data)
        
        return processed_data
    
    def apply_grouping(self, data_dict, group_by_fields):
        """Apply grouping to data"""
        if not data_dict.get('data'):
            return data_dict
        
        data = data_dict['data']
        grouped_data = {}
        
        for row in data:
            # Create group key
            group_key = tuple(row.get(field, '') for field in group_by_fields)
            
            if group_key not in grouped_data:
                grouped_data[group_key] = []
            
            grouped_data[group_key].append(row)
        
        # Convert to list format
        grouped_list = []
        for group_key, group_rows in grouped_data.items():
            group_dict = dict(zip(group_by_fields, group_key))
            group_dict['group_rows'] = group_rows
            group_dict['group_count'] = len(group_rows)
            grouped_list.append(group_dict)
        
        data_dict['data'] = grouped_list
        data_dict['grouped'] = True
        data_dict['group_by'] = group_by_fields
        
        return data_dict
    
    def apply_aggregations(self, data_dict, aggregations):
        """Apply aggregations to grouped data"""
        if not data_dict.get('grouped'):
            return data_dict
        
        grouped_data = data_dict['data']
        
        for group in grouped_data:
            group_rows = group.get('group_rows', [])
            
            for agg_config in aggregations:
                field = agg_config['field']
                agg_type = agg_config['type']
                alias = agg_config.get('alias', f"{field}_{agg_type}")
                
                if agg_type in self.aggregators:
                    result = self.aggregators[agg_type](group_rows, field)
                    group[alias] = result
        
        data_dict['aggregations'] = aggregations
        return data_dict
    
    def aggregate_sum(self, rows, field):
        """Calculate sum of field"""
        total = 0
        for row in rows:
            value = row.get(field, 0)
            try:
                total += float(value) if value else 0
            except (ValueError, TypeError):
                continue
        return total
    
    def aggregate_avg(self, rows, field):
        """Calculate average of field"""
        total = 0
        count = 0
        
        for row in rows:
            value = row.get(field, 0)
            try:
                total += float(value) if value else 0
                count += 1
            except (ValueError, TypeError):
                continue
        
        return total / count if count > 0 else 0
    
    def aggregate_count(self, rows, field):
        """Count non-null values"""
        count = 0
        for row in rows:
            if row.get(field) is not None and row.get(field) != '':
                count += 1
        return count
    
    def aggregate_min(self, rows, field):
        """Find minimum value"""
        values = []
        for row in rows:
            value = row.get(field)
            try:
                if value is not None and value != '':
                    values.append(float(value))
            except (ValueError, TypeError):
                continue
        
        return min(values) if values else None
    
    def aggregate_max(self, rows, field):
        """Find maximum value"""
        values = []
        for row in rows:
            value = row.get(field)
            try:
                if value is not None and value != '':
                    values.append(float(value))
            except (ValueError, TypeError):
                continue
        
        return max(values) if values else None
    
    def apply_calculations(self, data_dict, calculations):
        """Apply calculated fields"""
        data = data_dict['data']
        
        for calc_config in calculations:
            field_name = calc_config['field']
            expression = calc_config['expression']
            
            for row in data:
                try:
                    # Replace field references with actual values
                    eval_expression = expression
                    for key, value in row.items():
                        if isinstance(value, (int, float)):
                            eval_expression = eval_expression.replace(f'{{{key}}}', str(value))
                    
                    # Evaluate expression
                    result = eval(eval_expression)
                    row[field_name] = result
                    
                except Exception:
                    row[field_name] = None
        
        data_dict['calculations'] = calculations
        return data_dict
    
    def apply_formatting(self, data_dict):
        """Apply formatting to data"""
        data = data_dict['data']
        columns = data_dict.get('columns', [])
        
        # Create column mapping
        column_map = {col['fieldname']: col for col in columns}
        
        for row in data:
            for field_name, value in row.items():
                if field_name in column_map:
                    column_def = column_map[field_name]
                    field_type = column_def.get('fieldtype', 'Data')
                    
                    # Apply formatting based on field type
                    if field_type == 'Currency' and value is not None:
                        try:
                            row[field_name] = float(value)
                        except (ValueError, TypeError):
                            pass
                    elif field_type == 'Date' and value:
                        try:
                            row[field_name] = frappe.utils.format_date(value)
                        except Exception:
                            pass
                    elif field_type == 'Datetime' and value:
                        try:
                            row[field_name] = frappe.utils.format_datetime(value)
                        except Exception:
                            pass
        
        return data_dict
```

#### Visualization Engine

```python
# Data visualization engine
class VisualizationEngine:
    def __init__(self):
        self.chart_generators = {
            'line': self.generate_line_chart,
            'bar': self.generate_bar_chart,
            'pie': self.generate_pie_chart,
            'area': self.generate_area_chart,
            'scatter': self.generate_scatter_chart,
            'table': self.generate_table_chart
        }
    
    def generate_chart(self, data, chart_type, options):
        """Generate chart based on type"""
        generator = self.chart_generators.get(chart_type)
        
        if not generator:
            raise ReportException(f"Unsupported chart type: {chart_type}")
        
        return generator(data, options)
    
    def generate_line_chart(self, data, options):
        """Generate line chart configuration"""
        chart_data = {
            'type': 'line',
            'data': {
                'labels': [],
                'datasets': []
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': options.get('title', 'Line Chart')
                    }
                }
            }
        }
        
        # Extract data points
        labels = []
        datasets = {}
        
        for row in data.get('data', []):
            # Get x-axis label
            x_field = options.get('x_field', 'name')
            label = row.get(x_field, '')
            labels.append(label)
            
            # Get y-axis values
            y_fields = options.get('y_fields', [])
            for y_field in y_fields:
                if y_field not in datasets:
                    datasets[y_field] = {
                        'label': y_field.replace('_', ' ').title(),
                        'data': [],
                        'borderColor': self.get_color_for_field(y_field),
                        'backgroundColor': self.get_color_for_field(y_field, 0.2),
                        'fill': False
                    }
                
                value = row.get(y_field, 0)
                datasets[y_field]['data'].append(value)
        
        # Add datasets to chart
        chart_data['data']['labels'] = labels
        chart_data['data']['datasets'] = list(datasets.values())
        
        return chart_data
    
    def generate_bar_chart(self, data, options):
        """Generate bar chart configuration"""
        chart_data = {
            'type': 'bar',
            'data': {
                'labels': [],
                'datasets': []
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': options.get('title', 'Bar Chart')
                    }
                }
            }
        }
        
        # Extract data points
        labels = []
        datasets = {}
        
        for row in data.get('data', []):
            # Get x-axis label
            x_field = options.get('x_field', 'name')
            label = row.get(x_field, '')
            labels.append(label)
            
            # Get y-axis values
            y_fields = options.get('y_fields', [])
            for y_field in y_fields:
                if y_field not in datasets:
                    datasets[y_field] = {
                        'label': y_field.replace('_', ' ').title(),
                        'data': [],
                        'backgroundColor': self.get_color_for_field(y_field),
                        'borderColor': self.get_color_for_field(y_field, 1.0),
                        'borderWidth': 1
                    }
                
                value = row.get(y_field, 0)
                datasets[y_field]['data'].append(value)
        
        # Add datasets to chart
        chart_data['data']['labels'] = labels
        chart_data['data']['datasets'] = list(datasets.values())
        
        return chart_data
    
    def generate_pie_chart(self, data, options):
        """Generate pie chart configuration"""
        chart_data = {
            'type': 'pie',
            'data': {
                'labels': [],
                'datasets': [{
                    'data': [],
                    'backgroundColor': [],
                    'borderColor': '#fff',
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': options.get('title', 'Pie Chart')
                    }
                }
            }
        }
        
        # Extract data points
        labels = []
        values = []
        colors = []
        
        for row in data.get('data', []):
            # Get label field
            label_field = options.get('label_field', 'name')
            label = row.get(label_field, '')
            labels.append(label)
            
            # Get value field
            value_field = options.get('value_field', 'value')
            value = row.get(value_field, 0)
            values.append(value)
            
            # Get color
            colors.append(self.get_color_for_index(len(labels) - 1))
        
        # Add data to chart
        chart_data['data']['labels'] = labels
        chart_data['data']['datasets'][0]['data'] = values
        chart_data['data']['datasets'][0]['backgroundColor'] = colors
        
        return chart_data
    
    def generate_area_chart(self, data, options):
        """Generate area chart configuration"""
        chart_data = self.generate_line_chart(data, options)
        chart_data['type'] = 'line'
        
        # Set fill to true for area chart
        for dataset in chart_data['data']['datasets']:
            dataset['fill'] = True
            dataset['backgroundColor'] = self.get_color_for_field(
                dataset['label'].lower().replace(' ', '_'), 0.3
            )
        
        return chart_data
    
    def generate_scatter_chart(self, data, options):
        """Generate scatter chart configuration"""
        chart_data = {
            'type': 'scatter',
            'data': {
                'datasets': []
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': options.get('title', 'Scatter Chart')
                    }
                }
            }
        }
        
        # Extract data points
        datasets = {}
        
        for row in data.get('data', []):
            # Get x and y values
            x_field = options.get('x_field', 'x')
            y_field = options.get('y_field', 'y')
            category_field = options.get('category_field', 'category')
            
            x_value = row.get(x_field, 0)
            y_value = row.get(y_field, 0)
            category = row.get(category_field, 'default')
            
            if category not in datasets:
                datasets[category] = {
                    'label': category,
                    'data': [],
                    'backgroundColor': self.get_color_for_index(len(datasets)),
                    'borderColor': self.get_color_for_index(len(datasets), 1.0)
                }
            
            datasets[category]['data'].append({'x': x_value, 'y': y_value})
        
        # Add datasets to chart
        chart_data['data']['datasets'] = list(datasets.values())
        
        return chart_data
    
    def generate_table_chart(self, data, options):
        """Generate table visualization"""
        table_data = {
            'type': 'table',
            'data': {
                'headers': [],
                'rows': []
            },
            'options': {
                'title': options.get('title', 'Table'),
                'sortable': options.get('sortable', True),
                'filterable': options.get('filterable', True)
            }
        }
        
        # Extract headers
        if data.get('data'):
            headers = list(data['data'][0].keys())
            table_data['data']['headers'] = headers
            
            # Extract rows
            for row in data['data']:
                table_row = [row.get(header, '') for header in headers]
                table_data['data']['rows'].append(table_row)
        
        return table_data
    
    def get_color_for_field(self, field_name, alpha=1.0):
        """Get color for field name"""
        colors = [
            'rgba(255, 99, 132, {alpha})',   # Red
            'rgba(54, 162, 235, {alpha})',   # Blue
            'rgba(255, 206, 86, {alpha})',   # Yellow
            'rgba(75, 192, 192, {alpha})',   # Green
            'rgba(153, 102, 255, {alpha})', # Purple
            'rgba(255, 159, 64, {alpha})',  # Orange
            'rgba(199, 199, 199, {alpha})',  # Grey
            'rgba(83, 102, 255, {alpha})',   # Indigo
            'rgba(255, 99, 255, {alpha})',  # Pink
            'rgba(99, 255, 132, {alpha})'    # Teal
        ]
        
        # Use hash of field name to get consistent color
        hash_value = hash(field_name) % len(colors)
        color = colors[hash_value]
        
        return color.format(alpha=alpha)
    
    def get_color_for_index(self, index, alpha=1.0):
        """Get color for index"""
        colors = [
            'rgba(255, 99, 132, {alpha})',   # Red
            'rgba(54, 162, 235, {alpha})',   # Blue
            'rgba(255, 206, 86, {alpha})',   # Yellow
            'rgba(75, 192, 192, {alpha})',   # Green
            'rgba(153, 102, 255, {alpha})', # Purple
            'rgba(255, 159, 64, {alpha})',  # Orange
            'rgba(199, 199, 199, {alpha})',  # Grey
            'rgba(83, 102, 255, {alpha})',   # Indigo
            'rgba(255, 99, 255, {alpha})',  # Pink
            'rgba(99, 255, 132, {alpha})'    # Teal
        ]
        
        color = colors[index % len(colors)]
        return color.format(alpha=alpha)
```

### 9.2 Building Custom Reports

#### Creating Advanced Custom Reports

```python
# Advanced custom report examples
@frappe.whitelist()
def get_sales_performance_report(filters=None):
    """Generate comprehensive sales performance report"""
    # Parse filters
    if not filters:
        filters = {}
    
    # Build base query
    query = """
        SELECT 
            so.name as order_name,
            so.transaction_date,
            so.customer,
            c.customer_name,
            c.territory,
            so.grand_total,
            so.status,
            so.sales_person,
            sp.full_name as sales_person_name,
            COUNT(soi.item_code) as item_count,
            AVG(soi.rate) as avg_item_rate
        FROM `tabSales Order` so
        LEFT JOIN `tabCustomer` c ON so.customer = c.name
        LEFT JOIN `tabSales Person` sp ON so.sales_person = sp.name
        LEFT JOIN `tabSales Order Item` soi ON so.name = soi.parent
        WHERE so.docstatus = 1
    """
    
    # Apply filters
    conditions = []
    params = []
    
    if filters.get('from_date'):
        conditions.append("so.transaction_date >= %s")
        params.append(filters['from_date'])
    
    if filters.get('to_date'):
        conditions.append("so.transaction_date <= %s")
        params.append(filters['to_date'])
    
    if filters.get('customer'):
        conditions.append("so.customer = %s")
        params.append(filters['customer'])
    
    if filters.get('territory'):
        conditions.append("c.territory = %s")
        params.append(filters['territory'])
    
    if filters.get('sales_person'):
        conditions.append("so.sales_person = %s")
        params.append(filters['sales_person'])
    
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    query += """
        GROUP BY so.name
        ORDER BY so.transaction_date DESC
    """
    
    # Execute query
    data = frappe.db.sql(query, params, as_dict=True)
    
    # Calculate additional metrics
    for row in data:
        # Calculate profit margin (simplified)
        row['profit_margin'] = (row['grand_total'] * 0.2)  # Assume 20% profit
        
        # Format date
        row['transaction_date'] = frappe.utils.format_date(row['transaction_date'])
        
        # Format currency
        row['grand_total_formatted'] = frappe.format(row['grand_total'], {'fieldtype': 'Currency'})
    
    # Generate summary statistics
    summary = {
        'total_orders': len(data),
        'total_revenue': sum(row['grand_total'] for row in data),
        'avg_order_value': sum(row['grand_total'] for row in data) / len(data) if data else 0,
        'total_items_sold': sum(row['item_count'] for row in data),
        'top_customer': max(data, key=lambda x: x['grand_total'])['customer_name'] if data else None,
        'top_sales_person': max(data, key=lambda x: x['grand_total'])['sales_person_name'] if data else None
    }
    
    return {
        'data': data,
        'summary': summary,
        'columns': [
            {'fieldname': 'order_name', 'label': 'Order', 'fieldtype': 'Link', 'options': 'Sales Order'},
            {'fieldname': 'transaction_date', 'label': 'Date', 'fieldtype': 'Date'},
            {'fieldname': 'customer_name', 'label': 'Customer', 'fieldtype': 'Data'},
            {'fieldname': 'territory', 'label': 'Territory', 'fieldtype': 'Data'},
            {'fieldname': 'sales_person_name', 'label': 'Sales Person', 'fieldtype': 'Data'},
            {'fieldname': 'grand_total_formatted', 'label': 'Total', 'fieldtype': 'Currency'},
            {'fieldname': 'item_count', 'label': 'Items', 'fieldtype': 'Int'},
            {'fieldname': 'profit_margin', 'label': 'Profit Margin', 'fieldtype': 'Currency'}
        ]
    }

@frappe.whitelist()
def get_inventory_analysis_report(filters=None):
    """Generate comprehensive inventory analysis report"""
    # Parse filters
    if not filters:
        filters = {}
    
    # Build query for inventory data
    query = """
        SELECT 
            i.item_code,
            i.item_name,
            i.item_group,
            i.stock_uom,
            COALESCE(SUM(b.actual_qty), 0) as total_stock,
            COALESCE(SUM(b.reserved_qty), 0) as reserved_stock,
            COALESCE(SUM(b.ordered_qty), 0) as ordered_stock,
            COALESCE(SUM(b.indented_qty), 0) as indented_stock,
            i.standard_rate,
            COALESCE(AVG(sle.actual_qty), 0) as avg_daily_movement,
            COUNT(DISTINCT b.warehouse) as warehouse_count
        FROM `tabItem` i
        LEFT JOIN `tabBin` b ON i.name = b.item_code
        LEFT JOIN `tabStock Ledger Entry` sle ON i.name = sle.item_code 
            AND sle.posting_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        WHERE i.disabled = 0
    """
    
    # Apply filters
    conditions = []
    params = []
    
    if filters.get('item_group'):
        conditions.append("i.item_group = %s")
        params.append(filters['item_group'])
    
    if filters.get('warehouse'):
        conditions.append("b.warehouse = %s")
        params.append(filters['warehouse'])
    
    if filters.get('stock_status'):
        if filters['stock_status'] == 'out_of_stock':
            conditions.append("COALESCE(SUM(b.actual_qty), 0) = 0")
        elif filters['stock_status'] == 'low_stock':
            conditions.append("COALESCE(SUM(b.actual_qty), 0) > 0 AND COALESCE(SUM(b.actual_qty), 0) < i.min_order_qty")
        elif filters['stock_status'] == 'in_stock':
            conditions.append("COALESCE(SUM(b.actual_qty), 0) >= i.min_order_qty")
    
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    query += """
        GROUP BY i.name
        HAVING COALESCE(SUM(b.actual_qty), 0) > 0
        ORDER BY total_stock DESC
    """
    
    # Execute query
    data = frappe.db.sql(query, params, as_dict=True)
    
    # Calculate additional metrics
    for row in data:
        # Calculate available stock
        row['available_stock'] = row['total_stock'] - row['reserved_stock']
        
        # Calculate stock value
        row['stock_value'] = row['total_stock'] * row['standard_rate']
        
        # Calculate days of supply (simplified)
        if row['avg_daily_movement'] and row['avg_daily_movement'] > 0:
            row['days_of_supply'] = row['available_stock'] / abs(row['avg_daily_movement'])
        else:
            row['days_of_supply'] = 999  # Infinite supply
        
        # Determine stock status
        if row['available_stock'] <= 0:
            row['stock_status'] = 'Out of Stock'
        elif row['days_of_supply'] < 7:
            row['stock_status'] = 'Low Stock'
        elif row['days_of_supply'] > 90:
            row['stock_status'] = 'Overstock'
        else:
            row['stock_status'] = 'Normal'
        
        # Format currency
        row['stock_value_formatted'] = frappe.format(row['stock_value'], {'fieldtype': 'Currency'})
    
    # Generate summary statistics
    summary = {
        'total_items': len(data),
        'total_stock_value': sum(row['stock_value'] for row in data),
        'out_of_stock_items': len([r for r in data if r['stock_status'] == 'Out of Stock']),
        'low_stock_items': len([r for r in data if r['stock_status'] == 'Low Stock']),
        'overstock_items': len([r for r in data if r['stock_status'] == 'Overstock']),
        'total_warehouses': len(set(r['warehouse_count'] for r in data))
    }
    
    return {
        'data': data,
        'summary': summary,
        'columns': [
            {'fieldname': 'item_code', 'label': 'Item Code', 'fieldtype': 'Link', 'options': 'Item'},
            {'fieldname': 'item_name', 'label': 'Item Name', 'fieldtype': 'Data'},
            {'fieldname': 'item_group', 'label': 'Item Group', 'fieldtype': 'Data'},
            {'fieldname': 'total_stock', 'label': 'Total Stock', 'fieldtype': 'Float'},
            {'fieldname': 'available_stock', 'label': 'Available Stock', 'fieldtype': 'Float'},
            {'fieldname': 'stock_value_formatted', 'label': 'Stock Value', 'fieldtype': 'Currency'},
            {'fieldname': 'days_of_supply', 'label': 'Days of Supply', 'fieldtype': 'Int'},
            {'fieldname': 'stock_status', 'label': 'Stock Status', 'fieldtype': 'Data'}
        ]
    }

@frappe.whitelist()
def get_customer_analysis_report(filters=None):
    """Generate comprehensive customer analysis report"""
    # Parse filters
    if not filters:
        filters = {}
    
    # Build query for customer data
    query = """
        SELECT 
            c.name as customer,
            c.customer_name,
            c.customer_group,
            c.territory,
            c.outstanding_balance,
            c.credit_limit,
            c.total_billing,
            c.total_unpaid,
            COUNT(DISTINCT so.name) as total_orders,
            COALESCE(SUM(so.grand_total), 0) as total_revenue,
            COALESCE(AVG(so.grand_total), 0) as avg_order_value,
            MAX(so.transaction_date) as last_order_date,
            DATEDIFF(CURDATE(), MAX(so.transaction_date)) as days_since_last_order,
            COUNT(DISTINCT CASE WHEN so.docstatus = 1 THEN so.name END) as submitted_orders,
            COUNT(DISTINCT CASE WHEN so.docstatus = 0 THEN so.name END) as draft_orders
        FROM `tabCustomer` c
        LEFT JOIN `tabSales Order` so ON c.name = so.customer
        WHERE c.disabled = 0
    """
    
    # Apply filters
    conditions = []
    params = []
    
    if filters.get('customer_group'):
        conditions.append("c.customer_group = %s")
        params.append(filters['customer_group'])
    
    if filters.get('territory'):
        conditions.append("c.territory = %s")
        params.append(filters['territory'])
    
    if filters.get('has_outstanding'):
        conditions.append("c.outstanding_balance > 0")
    
    if filters.get('activity_period'):
        if filters['activity_period'] == 'active':
            conditions.append("MAX(so.transaction_date) >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)")
        elif filters['activity_period'] == 'inactive':
            conditions.append("MAX(so.transaction_date) < DATE_SUB(CURDATE(), INTERVAL 90 DAY)")
    
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    query += """
        GROUP BY c.name
        ORDER BY total_revenue DESC
    """
    
    # Execute query
    data = frappe.db.sql(query, params, as_dict=True)
    
    # Calculate additional metrics
    for row in data:
        # Calculate credit utilization
        if row['credit_limit'] and row['credit_limit'] > 0:
            row['credit_utilization'] = (row['outstanding_balance'] / row['credit_limit']) * 100
        else:
            row['credit_utilization'] = 0
        
        # Calculate customer lifetime value
        row['lifetime_value'] = row['total_billing']
        
        # Determine customer tier
        if row['total_revenue'] >= 100000:
            row['customer_tier'] = 'Platinum'
        elif row['total_revenue'] >= 50000:
            row['customer_tier'] = 'Gold'
        elif row['total_revenue'] >= 10000:
            row['customer_tier'] = 'Silver'
        else:
            row['customer_tier'] = 'Bronze'
        
        # Determine activity status
        if row['days_since_last_order'] <= 30:
            row['activity_status'] = 'Active'
        elif row['days_since_last_order'] <= 90:
            row['activity_status'] = 'Recent'
        else:
            row['activity_status'] = 'Inactive'
        
        # Format currency
        row['total_revenue_formatted'] = frappe.format(row['total_revenue'], {'fieldtype': 'Currency'})
        row['outstanding_balance_formatted'] = frappe.format(row['outstanding_balance'], {'fieldtype': 'Currency'})
    
    # Generate summary statistics
    summary = {
        'total_customers': len(data),
        'total_revenue': sum(row['total_revenue'] for row in data),
        'total_outstanding': sum(row['outstanding_balance'] for row in data),
        'avg_customer_value': sum(row['total_revenue'] for row in data) / len(data) if data else 0,
        'active_customers': len([r for r in data if r['activity_status'] == 'Active']),
        'high_value_customers': len([r for r in data if r['customer_tier'] in ['Platinum', 'Gold']]),
        'customers_with_outstanding': len([r for r in data if r['outstanding_balance'] > 0])
    }
    
    return {
        'data': data,
        'summary': summary,
        'columns': [
            {'fieldname': 'customer', 'label': 'Customer', 'fieldtype': 'Link', 'options': 'Customer'},
            {'fieldname': 'customer_name', 'label': 'Customer Name', 'fieldtype': 'Data'},
            {'fieldname': 'customer_group', 'label': 'Customer Group', 'fieldtype': 'Data'},
            {'fieldname': 'territory', 'label': 'Territory', 'fieldtype': 'Data'},
            {'fieldname': 'total_orders', 'label': 'Total Orders', 'fieldtype': 'Int'},
            {'fieldname': 'total_revenue_formatted', 'label': 'Total Revenue', 'fieldtype': 'Currency'},
            {'fieldname': 'avg_order_value', 'label': 'Avg Order Value', 'fieldtype': 'Currency'},
            {'fieldname': 'outstanding_balance_formatted', 'label': 'Outstanding', 'fieldtype': 'Currency'},
            {'fieldname': 'customer_tier', 'label': 'Customer Tier', 'fieldtype': 'Data'},
            {'fieldname': 'activity_status', 'label': 'Activity Status', 'fieldtype': 'Data'}
        ]
    }
```

#### Performance-Optimized Report Patterns

```python
# Performance optimization for reports
class OptimizedReportBuilder:
    def __init__(self):
        self.cache_manager = ReportCacheManager()
        self.query_optimizer = QueryOptimizer()
        self.batch_processor = BatchProcessor()
    
    def build_optimized_report(self, report_config):
        """Build report with performance optimizations"""
        # Generate cache key
        cache_key = self.generate_cache_key(report_config)
        
        # Try to get from cache
        cached_result = self.cache_manager.get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        # Optimize query
        optimized_query = self.query_optimizer.optimize(report_config['query'])
        
        # Process in batches if large dataset
        if self.is_large_dataset(report_config):
            result = self.batch_processor.process_in_batches(optimized_query, report_config)
        else:
            result = self.execute_optimized_query(optimized_query, report_config)
        
        # Cache result
        self.cache_manager.cache_result(cache_key, result)
        
        return result
    
    def generate_cache_key(self, report_config):
        """Generate cache key for report"""
        key_components = [
            report_config.get('name', ''),
            json.dumps(report_config.get('filters', {}), sort_keys=True),
            report_config.get('query', ''),
            str(frappe.session.user)
        ]
        
        cache_string = '|'.join(key_components)
        return f"optimized_report:{hashlib.md5(cache_string.encode()).hexdigest()}"
    
    def is_large_dataset(self, report_config):
        """Check if report will return large dataset"""
        # Estimate row count
        estimated_count = self.query_optimizer.estimate_row_count(report_config['query'])
        return estimated_count > 10000
    
    def execute_optimized_query(self, query, config):
        """Execute optimized query"""
        start_time = time.time()
        
        try:
            # Execute query
            data = frappe.db.sql(query, as_dict=True)
            
            # Apply post-processing
            processed_data = self.apply_post_processing(data, config)
            
            # Track performance
            execution_time = time.time() - start_time
            self.track_performance(config['name'], execution_time, len(data))
            
            return processed_data
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.track_error(config['name'], execution_time, str(e))
            raise ReportException(f"Query execution failed: {str(e)}")
    
    def apply_post_processing(self, data, config):
        """Apply post-processing optimizations"""
        # Apply calculations
        if config.get('calculations'):
            data = self.apply_calculations(data, config['calculations'])
        
        # Apply formatting
        if config.get('formatting'):
            data = self.apply_formatting(data, config['formatting'])
        
        # Apply sorting
        if config.get('sort_by'):
            data = self.apply_sorting(data, config['sort_by'])
        
        return data

# Query optimizer
class QueryOptimizer:
    def __init__(self):
        self.index_hints = {}
        self.query_cache = {}
    
    def optimize(self, query):
        """Optimize SQL query"""
        # Check cache
        if query in self.query_cache:
            return self.query_cache[query]
        
        optimized_query = query
        
        # Add index hints
        optimized_query = self.add_index_hints(optimized_query)
        
        # Optimize JOIN order
        optimized_query = self.optimize_joins(optimized_query)
        
        # Add LIMIT if missing
        optimized_query = self.add_limit_if_needed(optimized_query)
        
        # Cache optimized query
        self.query_cache[query] = optimized_query
        
        return optimized_query
    
    def add_index_hints(self, query):
        """Add index hints to query"""
        # This is a simplified example
        # In practice, you would analyze the query and add appropriate hints
        
        # Common patterns for Frappe tables
        if 'tabSales Order' in query and 'WHERE' in query:
            if 'customer' in query:
                query = query.replace('FROM `tabSales Order`', 
                                   'FROM `tabSales Order` USE INDEX (idx_customer)')
        
        return query
    
    def optimize_joins(self, query):
        """Optimize JOIN order"""
        # Simplified join optimization
        # In practice, you would analyze table sizes and join conditions
        
        return query
    
    def add_limit_if_needed(self, query):
        """Add LIMIT clause if not present"""
        if 'LIMIT' not in query.upper():
            query += ' LIMIT 10000'  # Prevent runaway queries
        
        return query
    
    def estimate_row_count(self, query):
        """Estimate number of rows query will return"""
        try:
            # Create count query
            count_query = f"SELECT COUNT(*) as count FROM ({query}) as subquery"
            result = frappe.db.sql(count_query)
            return result[0][0] if result else 0
        except Exception:
            return 1000  # Default estimate

# Batch processor
class BatchProcessor:
    def __init__(self):
        self.batch_size = 1000
    
    def process_in_batches(self, query, config):
        """Process query in batches"""
        all_data = []
        offset = 0
        
        while True:
            # Add LIMIT and OFFSET
            batch_query = f"{query} LIMIT {self.batch_size} OFFSET {offset}"
            
            # Execute batch
            batch_data = frappe.db.sql(batch_query, as_dict=True)
            
            if not batch_data:
                break
            
            all_data.extend(batch_data)
            offset += self.batch_size
            
            # Prevent infinite loops
            if len(batch_data) < self.batch_size:
                break
        
        # Apply post-processing
        processed_data = self.apply_post_processing(all_data, config)
        
        return processed_data
    
    def apply_post_processing(self, data, config):
        """Apply post-processing to batched data"""
        # Apply aggregations if needed
        if config.get('group_by'):
            data = self.apply_grouping(data, config['group_by'])
        
        return data
    
    def apply_grouping(self, data, group_by_fields):
        """Apply grouping to data"""
        grouped_data = {}
        
        for row in data:
            group_key = tuple(row.get(field, '') for field in group_by_fields)
            
            if group_key not in grouped_data:
                grouped_data[group_key] = []
            
            grouped_data[group_key].append(row)
        
        # Convert grouped data back to list
        result = []
        for group_key, group_rows in grouped_data.items():
            group_dict = dict(zip(group_by_fields, group_key))
            group_dict['group_rows'] = group_rows
            result.append(group_dict)
        
        return result
```

### 9.3 Report Performance Optimization

#### Caching and Optimization Strategies

```python
# Advanced caching and optimization
class ReportCacheManager:
    def __init__(self):
        self.cache = frappe.cache()
        self.cache_ttl = {
            'daily_reports': 86400,    # 24 hours
            'weekly_reports': 604800,   # 7 days
            'monthly_reports': 2592000, # 30 days
            'real_time_reports': 300    # 5 minutes
        }
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def get_cached_result(self, cache_key):
        """Get cached report result"""
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            self.cache_stats['hits'] += 1
            return json.loads(cached_data)
        
        self.cache_stats['misses'] += 1
        return None
    
    def cache_result(self, cache_key, data, ttl=None):
        """Cache report result"""
        if ttl is None:
            ttl = self.cache_ttl.get('real_time_reports', 300)
        
        # Convert data to JSON
        json_data = json.dumps(data, default=str)
        
        # Cache with TTL
        self.cache.set(cache_key, json_data, expires_in_sec=ttl)
    
    def invalidate_cache_pattern(self, pattern):
        """Invalidate cache by pattern"""
        # This would require Redis pattern matching
        # For simplicity, we'll clear all cache
        self.cache.clear()
        self.cache_stats['evictions'] += 1
    
    def get_cache_stats(self):
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hit_rate': hit_rate,
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions']
        }

# Performance monitoring
class ReportPerformanceMonitor:
    def __init__(self):
        self.performance_data = {}
        self.slow_queries = []
        self.error_log = []
    
    def track_report_execution(self, report_name, execution_time, row_count):
        """Track report execution performance"""
        if report_name not in self.performance_data:
            self.performance_data[report_name] = {
                'executions': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'avg_time': 0,
                'total_rows': 0
            }
        
        stats = self.performance_data[report_name]
        stats['executions'] += 1
        stats['total_time'] += execution_time
        stats['min_time'] = min(stats['min_time'], execution_time)
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['avg_time'] = stats['total_time'] / stats['executions']
        stats['total_rows'] += row_count
        
        # Track slow queries
        if execution_time > 5.0:  # 5 seconds threshold
            self.slow_queries.append({
                'report': report_name,
                'execution_time': execution_time,
                'row_count': row_count,
                'timestamp': frappe.utils.now()
            })
    
    def track_error(self, report_name, execution_time, error_message):
        """Track report execution errors"""
        self.error_log.append({
            'report': report_name,
            'execution_time': execution_time,
            'error': error_message,
            'timestamp': frappe.utils.now()
        })
    
    def get_performance_report(self):
        """Get comprehensive performance report"""
        return {
            'reports': self.performance_data,
            'slow_queries': self.slow_queries,
            'errors': self.error_log,
            'summary': self.generate_summary()
        }
    
    def generate_summary(self):
        """Generate performance summary"""
        if not self.performance_data:
            return {}
        
        total_executions = sum(stats['executions'] for stats in self.performance_data.values())
        total_time = sum(stats['total_time'] for stats in self.performance_data.values())
        avg_time = total_time / total_executions if total_executions > 0 else 0
        
        slowest_report = max(
            self.performance_data.items(), 
            key=lambda x: x[1]['avg_time']
        ) if self.performance_data else None
        
        return {
            'total_executions': total_executions,
            'total_time': total_time,
            'avg_time': avg_time,
            'slowest_report': slowest_report[0] if slowest_report else None,
            'slowest_time': slowest_report[1]['avg_time'] if slowest_report else 0,
            'error_count': len(self.error_log),
            'slow_query_count': len(self.slow_queries)
        }
```

## 🛠️ Practical Exercises

### Exercise 9.1: Build a Complex Custom Report

Create a comprehensive report with:
- Multiple data sources
- Complex aggregations
- Custom calculations
- Interactive visualizations

### Exercise 9.2: Optimize Report Performance

Implement performance optimizations:
- Query optimization
- Caching strategies
- Batch processing
- Performance monitoring

### Exercise 9.3: Create Interactive Dashboards

Build interactive dashboards with:
- Multiple chart types
- Real-time data updates
- User interactions
- Export capabilities

## 🚀 Best Practices

### Report Design

- **Use appropriate chart types** for different data patterns
- **Implement proper filtering** for user flexibility
- **Provide clear labels** and descriptions
- **Use consistent formatting** across reports
- **Include summary statistics** for quick insights

### Performance Optimization

- **Optimize database queries** with proper indexing
- **Use caching** for frequently accessed reports
- **Implement pagination** for large datasets
- **Monitor performance** regularly
- **Use batch processing** for complex calculations

### Data Visualization

- **Choose the right visualization** for your data
- **Keep charts simple** and easy to understand
- **Use consistent color schemes**
- **Provide interactive features** when appropriate
- **Ensure accessibility** for all users

## 📖 Further Reading

- [Frappe Report Builder Documentation](https://frappeframework.com/docs/user/en/report-builder)
- [Data Visualization Best Practices](https://www.data-to-viz.com/)
- [SQL Performance Optimization](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)
- [Chart.js Documentation](https://www.chartjs.org/docs/latest/)

## 🎯 Chapter Summary

Mastering advanced reporting is essential for data-driven decisions:

- **Report Architecture** provides the foundation for scalable reporting
- **Custom Reports** enable tailored business insights
- **Performance Optimization** ensures responsive report interactions
- **Data Visualization** makes complex data understandable
- **Caching Strategies** improve report performance and user experience

---

**Next Chapter**: Custom print formats and template design.


---

## 📌 Addendum: How to Create Custom Reports in Frappe

### Report Types Overview

| Type | Language | Flexibility | Use Case |
|------|----------|-------------|---------|
| **Script Report** | Python | High | Complex logic, dynamic columns, aggregations |
| **Query Report** | SQL | Moderate | Simple data extraction |
| **Report Builder** | Visual/GUI | Low | No-code, user-friendly |

### File Structure

```
apps/your_app/your_app/your_module/report/your_report_name/
├── __init__.py
├── your_report_name.json    # Report configuration
├── your_report_name.py      # Python logic (Script Reports only)
└── your_report_name.js      # Frontend filters (optional)
```

### Script Report: Step-by-Step

**Step 1: Create via UI**
1. Enable Developer Mode
2. Go to Report List → New Report
3. Set Report Type = "Script Report", Is Standard = Yes
4. Save — Frappe creates the folder with boilerplate files

**Step 2: Python Logic (`report_name.py`)**

```python
import frappe
from frappe import _

def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {
            "label": _("ID"),
            "fieldtype": "Link",
            "fieldname": "name",
            "options": "Your DocType",
            "width": 120,
        },
        {
            "label": _("Status"),
            "fieldtype": "Data",
            "fieldname": "status",
            "width": 100,
        },
        {
            "label": _("Amount"),
            "fieldtype": "Currency",
            "fieldname": "amount",
            "width": 120,
        }
    ]

def get_data(filters):
    conditions = []
    values = {}

    if filters.get("organization"):
        conditions.append("organization = %(organization)s")
        values["organization"] = filters.organization

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    return frappe.db.sql(f"""
        SELECT name, status, amount
        FROM `tabYour DocType`
        {where_clause}
        ORDER BY creation DESC
    """, values=values, as_dict=True)
```

**Step 3: JavaScript Filters (`report_name.js`)**

```javascript
frappe.query_reports["My Custom Report"] = {
    "filters": [
        {
            fieldname: "organization",
            label: __("Organization"),
            fieldtype: "Link",
            options: "Organization",
            reqd: 1,
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.year_start(),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.year_end(),
            reqd: 1,
        }
    ]
};
```

### Query Report: Step-by-Step

Select "Query Report" as Report Type, then enter SQL in the "Query" field:

```sql
SELECT
  name AS "Name:Link/Item:200",
  stock_uom AS "UOM:Data:100",
  ifnull(sum(bin.actual_qty), 0) AS "Stock:Float:100"
FROM `tabItem`
LEFT JOIN `tabBin` bin ON bin.item_code = `tabItem`.name
GROUP BY `tabItem`.name, `tabItem`.stock_uom;
```

Use `%(filter_name)s` syntax to inject filter values in SQL.

### Advanced Features

**Dynamic Columns:**

```python
def get_columns(filters, project_types):
    columns = [{"label": _("Product"), "fieldtype": "Data", "fieldname": "product"}]
    for project_type in project_types:
        columns.append({
            "label": _(project_type["title"]),
            "fieldtype": "Int",
            "fieldname": project_type["id"],
        })
    return columns
```

**Conditional Filter Logic:**

```javascript
{
    fieldname: "time_window",
    label: __("Time Window"),
    fieldtype: "Select",
    options: ['Annual', 'Quarterly', 'Monthly'],
    on_change: function(report) {
        const value = this.get_value();
        if (value == "Annual") {
            report.set_filter_value('from_date', frappe.datetime.year_start());
            report.set_filter_value('to_date', frappe.datetime.year_end());
        }
        report.refresh();
    }
}
```

### Custom Print Format for Script Report

Create `your_report_name.html` in the same directory:

```html
<h2>{{ report.report_name }}</h2>
<table class="table table-bordered">
  <thead>
    <tr>
      {% for col in columns %}
        <th>{{ col.label }}</th>
      {% endfor %}
    </tr>
  </thead>
  <tbody>
    {% for row in data %}
      <tr>
        {% for col in columns %}
          <td>{{ row[col.fieldname] }}</td>
        {% endfor %}
      </tr>
    {% endfor %}
  </tbody>
</table>
```

> Note: Frappe uses John Resig's MicroTemplate engine (not Jinja2) for Script Report HTML files. Use Jinja only for server-side contexts like Print Formats, Email Templates, and Web Pages.

### Column Format Specifications

```python
# Dictionary format (recommended)
{"label": _("Amount"), "fieldtype": "Currency", "fieldname": "amount", "width": 120}

# String shorthand format
"Amount:Currency:120"
"ID:Link/DocType:90"
```

### Best Practices

- Use parameterized queries to prevent SQL injection
- Add WHERE clauses to limit data
- Use indexes on filtered columns
- Set appropriate role permissions in the JSON config
- Provide sensible default filter values


---

## Addendum: Practical Reporting Patterns from the Field

### Report Types at a Glance

| Type | Language | Use Case | Files |
|------|----------|----------|-------|
| Script Report | Python | Complex logic, calculations, dynamic columns | `.py`, `.js`, `.json` |
| Query Report | SQL | Straightforward data extraction | `.json`, `.js` |
| Report Builder | GUI | Simple reports, no code | `.json` |

### File Structure

Every report lives in a predictable location:
```
apps/your_app/your_app/your_module/report/your_report_name/
├── __init__.py
├── your_report_name.json    # metadata (auto-generated)
├── your_report_name.py      # Python logic (Script Reports)
├── your_report_name.js      # filters (optional)
└── your_report_name.html    # custom print format (optional)
```

### Script Report — Minimal Working Example

```python
# your_report.py
import frappe
from frappe import _

def execute(filters=None):
    filters = frappe._dict(filters or {})
    return get_columns(), get_data(filters)

def get_columns():
    return [
        {"label": _("Order"), "fieldtype": "Link", "fieldname": "name",
         "options": "Sales Order", "width": 150},
        {"label": _("Customer"), "fieldtype": "Link", "fieldname": "customer",
         "options": "Customer", "width": 200},
        {"label": _("Date"), "fieldtype": "Date", "fieldname": "posting_date", "width": 100},
        {"label": _("Total"), "fieldtype": "Currency", "fieldname": "grand_total", "width": 120},
    ]

def get_data(filters):
    conditions = build_conditions(filters)
    return frappe.db.sql(f"""
        SELECT name, customer, posting_date, grand_total
        FROM `tabSales Order`
        WHERE docstatus = 1 {conditions}
        ORDER BY posting_date DESC
        LIMIT 10000
    """, filters, as_dict=True)

def build_conditions(filters):
    conditions = []
    if filters.get("from_date"):
        conditions.append("AND posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("AND posting_date <= %(to_date)s")
    if filters.get("customer"):
        conditions.append("AND customer = %(customer)s")
    return " ".join(conditions)
```

```javascript
// your_report.js
frappe.query_reports["Your Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_end(),
            reqd: 1
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer"
        }
    ]
};
```

### Query Report — SQL-Based

```javascript
// report.json — set report_type to "Query Report" and add the query field
// report.js — same filter syntax as Script Reports
frappe.query_reports["Stock Summary"] = {
    filters: [
        { fieldname: "item_code", label: __("Item"), fieldtype: "Link", options: "Item" }
    ]
};
```

```sql
-- The query goes in the "query" field of the JSON config
SELECT
    i.name AS "Item:Link/Item:200",
    i.stock_uom AS "UOM:Data:80",
    IFNULL(SUM(b.actual_qty), 0) AS "Stock:Float:100"
FROM `tabItem` i
LEFT JOIN `tabBin` b ON b.item_code = i.name
WHERE i.disabled = 0
    {% if filters.item_code %}
    AND i.name = %(item_code)s
    {% endif %}
GROUP BY i.name, i.stock_uom
ORDER BY i.name
```

### Dynamic Columns

```python
def execute(filters=None):
    filters = frappe._dict(filters or {})

    # Fetch the dynamic dimension (e.g., project types)
    project_types = frappe.get_all("Project Type", fields=["name as id", "title"])

    columns = get_columns(project_types)
    data = get_data(filters, project_types)
    return columns, data

def get_columns(project_types):
    cols = [
        {"label": _("Product"), "fieldtype": "Data", "fieldname": "product", "width": 200}
    ]
    for pt in project_types:
        cols.append({
            "label": _(pt.title),
            "fieldtype": "Int",
            "fieldname": pt.id,
            "width": 100
        })
    cols.append({"label": _("Total"), "fieldtype": "Int", "fieldname": "total", "width": 100})
    return cols

def get_data(filters, project_types):
    # Build a CASE-based pivot query
    case_clauses = "\n".join([
        f"SUM(CASE WHEN project_type = %(val_{i})s THEN amount ELSE 0 END) AS `{pt.id}`"
        for i, pt in enumerate(project_types)
    ])

    for i, pt in enumerate(project_types):
        filters[f"val_{i}"] = pt.id

    return frappe.db.sql(f"""
        SELECT
            product_name AS product,
            {case_clauses},
            SUM(amount) AS total
        FROM `tabProject Revenue`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY product_name
        ORDER BY total DESC
    """, filters, as_dict=True)
```

### Advanced Filter Patterns

```javascript
// Filter with dependency
{
    fieldname: "warehouse",
    label: __("Warehouse"),
    fieldtype: "Link",
    options: "Warehouse",
    get_query() {
        return {
            filters: { company: frappe.query_report.get_filter_value("company") }
        };
    }
},

// Auto-update date range on select
{
    fieldname: "period",
    label: __("Period"),
    fieldtype: "Select",
    options: ["Monthly", "Quarterly", "Annual"],
    on_change(report) {
        const v = this.get_value();
        if (v === "Annual") {
            report.set_filter_value("from_date", frappe.datetime.year_start());
            report.set_filter_value("to_date", frappe.datetime.year_end());
        } else if (v === "Monthly") {
            report.set_filter_value("from_date", frappe.datetime.month_start());
            report.set_filter_value("to_date", frappe.datetime.month_end());
        }
        report.refresh();
    }
},

// Multi-select
{
    fieldname: "item_codes",
    label: __("Items"),
    fieldtype: "MultiSelectList",
    options: "Item",
    get_data(txt) {
        return frappe.db.get_link_options("Item", txt);
    }
}
```

### Performance Optimization

The single biggest cause of slow or crashing reports is loading too much data into Python memory. Fix it at the query level.

**The N+1 problem — and how to fix it:**

```python
# BAD: 10,000 orders = 10,001 queries
for order in orders:
    customer_name = frappe.db.get_value("Customer", order.customer, "customer_name")

# GOOD: single JOIN query
data = frappe.db.sql("""
    SELECT
        so.name,
        c.customer_name,
        so.grand_total
    FROM `tabSales Order` so
    INNER JOIN `tabCustomer` c ON so.customer = c.name
    WHERE so.posting_date BETWEEN %(from_date)s AND %(to_date)s
    LIMIT 10000
""", filters, as_dict=True)
```

**Push aggregation to the database:**

```python
# BAD: load all rows, aggregate in Python
items = frappe.db.sql("SELECT * FROM `tabSales Order Item`", as_dict=True)
totals = {}
for item in items:
    totals[item.item_code] = totals.get(item.item_code, 0) + item.amount

# GOOD: let the database aggregate
data = frappe.db.sql("""
    SELECT
        soi.item_code,
        i.item_name,
        SUM(soi.qty) AS total_qty,
        SUM(soi.amount) AS total_amount
    FROM `tabSales Order Item` soi
    INNER JOIN `tabItem` i ON soi.item_code = i.name
    INNER JOIN `tabSales Order` so ON soi.parent = so.name
    WHERE so.posting_date BETWEEN %(from_date)s AND %(to_date)s
        AND so.docstatus = 1
    GROUP BY soi.item_code
    ORDER BY total_amount DESC
    LIMIT 1000
""", filters, as_dict=True)
```

**Use generators for very large datasets:**

```python
def get_data(filters):
    data = []
    with frappe.db.unbuffered_cursor():
        rows = frappe.db.sql("""
            SELECT name, customer, grand_total
            FROM `tabSales Order`
            WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
        """, filters, as_iterator=True)

        for (name, customer, total) in rows:
            data.append({"name": name, "customer": customer, "grand_total": total})
            if len(data) >= 10000:
                break
    return data
```

**Cache expensive calculations:**

```python
def get_data(filters):
    orders = frappe.get_all("Sales Order",
        filters={"posting_date": ["between", [filters.from_date, filters.to_date]]},
        fields=["name", "customer"])

    # Pre-fetch all customer LTVs in one query
    ltv_map = {
        row.customer: row.ltv
        for row in frappe.db.sql("""
            SELECT customer, SUM(grand_total) AS ltv
            FROM `tabSales Order`
            WHERE docstatus = 1
            GROUP BY customer
        """, as_dict=True)
    }

    return [
        {"name": o.name, "customer": o.customer, "ltv": ltv_map.get(o.customer, 0)}
        for o in orders
    ]
```

### Prepared Reports — For Heavy Operations

If a report takes more than 15 seconds, Frappe automatically suggests enabling Prepared Reports. They run in the background queue and store compressed results.

**How it works:**
```
User clicks "Generate" → Background job created → Report runs (up to 25 min)
→ Results compressed (gzip) → Saved as attachment → User notified via realtime
```

**Enable it:**
1. Open the Report DocType record
2. Check "Enable Prepared Report"
3. Set Timeout (default: 25 minutes)
4. No code changes needed — same `execute()` function runs in background

**Frappe's automatic trigger (from source):**
```python
# If report takes > 15 seconds, Frappe auto-enables prepared report mode
threshold = 15  # seconds
prepared_report_watcher = threading.Timer(
    interval=threshold,
    function=enable_prepared_report,
    kwargs={"report": self.name, "site": frappe.local.site}
)
```

**Frontend limit:** The browser refuses to render more than 100,000 rows (configurable via `sysdefaults.max_report_rows`). For larger datasets, use Prepared Reports and export.

### Adding Indexes for Report Performance

```python
# In a patch or migration
def execute():
    # Add composite index for common report filter pattern
    if not frappe.db.has_index("Sales Order", "idx_so_date_status"):
        frappe.db.sql("""
            ALTER TABLE `tabSales Order`
            ADD INDEX idx_so_date_status (posting_date, docstatus, company)
        """)
```

**Use EXPLAIN to verify:**
```python
result = frappe.db.sql("""
    EXPLAIN SELECT name, customer, grand_total
    FROM `tabSales Order`
    WHERE posting_date BETWEEN '2024-01-01' AND '2024-12-31'
    AND docstatus = 1
""", as_dict=True)

# Look for: type = "range" or "ref" (good), not "ALL" (bad)
for row in result:
    print(f"Table: {row.table}, Type: {row.type}, Rows scanned: {row.rows}")
```

### Custom Print Format for Script Reports

Create a `.html` file matching the report name in the same directory:

```html
<!-- your_report.html — uses John Resig's MicroTemplate, NOT Jinja2 -->
<h2>{{ report.report_name }}</h2>
<p>Generated: {{ frappe.datetime.now_datetime() }}</p>

<table class="table table-bordered table-condensed">
    <thead>
        <tr>
            {% for col in columns %}
            <th>{{ col.label }}</th>
            {% endfor %}
        </tr>
    </thead>
    <tbody>
        {% for row in data %}
        <tr>
            {% for col in columns %}
            <td>{{ row[col.fieldname] || "" }}</td>
            {% endfor %}
        </tr>
        {% endfor %}
    </tbody>
</table>
```

> Note: Frappe uses MicroTemplate (`{% %}`) for client-side report HTML, not Jinja2. Jinja2 is only for server-side templates (Print Formats, Email Templates, Web Pages).

Access via: Report → top-right menu (⋮) → Print.

### Column Format Reference

```python
# Dictionary format (recommended)
{"label": _("Amount"), "fieldtype": "Currency", "fieldname": "amount", "width": 120}
{"label": _("Item"), "fieldtype": "Link", "fieldname": "item_code", "options": "Item", "width": 150}
{"label": _("Date"), "fieldtype": "Date", "fieldname": "posting_date", "width": 100}
{"label": _("Status"), "fieldtype": "Data", "fieldname": "status", "width": 80}

# Shorthand string format
"Amount:Currency:120"
"Item:Link/Item:150"
"Date:Date:100"
```

### Pagination for Large Reports

```python
def execute(filters=None):
    filters = frappe._dict(filters or {})
    page = int(filters.get("page", 1))
    page_size = int(filters.get("page_size", 500))
    offset = (page - 1) * page_size

    total = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabSales Order`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, filters)[0][0]

    data = frappe.db.sql("""
        SELECT name, customer, posting_date, grand_total
        FROM `tabSales Order`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY posting_date DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**filters, "page_size": page_size, "offset": offset}, as_dict=True)

    message = f"Showing {offset + 1}–{offset + len(data)} of {total} records"
    return get_columns(), data, message
```


---

## 📌 Addendum: Script Report Performance Optimization

### Why Reports Crash or Consume 100% RAM

The most common causes:

1. **No filters/limits** — `SELECT * FROM tabGL Entry` with no WHERE clause loads millions of rows
2. **N+1 queries** — fetching related data inside a loop (1 query + N queries)
3. **`SELECT *`** — loading 50+ columns when you need 5
4. **Python aggregation** — doing `SUM`/`GROUP BY` in Python instead of SQL
5. **`frappe.get_doc()` in a loop** — loads full document + all child tables for every row

### The Automatic 15-Second Threshold

Frappe starts a background timer when a report runs. If execution exceeds 15 seconds, Frappe automatically enables "Prepared Report" mode for that report. The execution time is cached in Redis for monitoring.

The frontend also refuses to render more than 100,000 rows (configurable via `sysdefaults.max_report_rows`) — it shows a warning and suggests exporting instead.

### Fix 1: Mandatory Filters + LIMIT

```python
def execute(filters=None):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw("From Date and To Date are required")

    conditions = "posting_date BETWEEN %(from_date)s AND %(to_date)s"
    if filters.get("customer"):
        conditions += " AND customer = %(customer)s"

    data = frappe.db.sql(f"""
        SELECT name, customer, posting_date, grand_total, status
        FROM `tabSales Order`
        WHERE {conditions}
        ORDER BY posting_date DESC
        LIMIT 10000
    """, filters, as_dict=True)

    return get_columns(), data
```

### Fix 2: Eliminate N+1 with a JOIN

```python
# BAD — 10,001 queries for 10,000 orders
for order in orders:
    customer_name = frappe.db.get_value("Customer", order.customer, "customer_name")

# GOOD — 1 query
data = frappe.db.sql("""
    SELECT so.name, c.customer_name, so.grand_total
    FROM `tabSales Order` so
    INNER JOIN `tabCustomer` c ON so.customer = c.name
    WHERE so.posting_date BETWEEN %(from_date)s AND %(to_date)s
    LIMIT 10000
""", filters, as_dict=True)
```

### Fix 3: Aggregate in SQL, Not Python

```python
# BAD — loads millions of rows into Python, then aggregates
items = frappe.db.sql("SELECT * FROM `tabSales Order Item`", as_dict=True)
totals = {}
for item in items:
    totals[item.parent] = totals.get(item.parent, 0) + item.amount

# GOOD — database does the aggregation
data = frappe.db.sql("""
    SELECT so.customer, SUM(soi.amount) as total_amount, COUNT(DISTINCT so.name) as orders
    FROM `tabSales Order` so
    INNER JOIN `tabSales Order Item` soi ON soi.parent = so.name
    WHERE so.posting_date BETWEEN %(from_date)s AND %(to_date)s
    GROUP BY so.customer
    ORDER BY total_amount DESC
    LIMIT 1000
""", filters, as_dict=True)
```

### Fix 4: Generators for Very Large Datasets

When you must process large datasets row-by-row, use an unbuffered cursor with `as_iterator=True` for O(1) memory:

```python
def execute(filters=None):
    data = []
    with frappe.db.unbuffered_cursor():
        rows = frappe.db.sql("""
            SELECT name FROM `tabSales Order`
            WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
        """, filters, as_iterator=True)

        for (order_name,) in rows:
            data.append(process_order(order_name))
            if len(data) >= 10000:
                break

    return get_columns(), data
```

### Fix 5: Cache Repeated Lookups

```python
# BAD — same customer queried multiple times
for order in orders:
    ltv = frappe.db.sql("SELECT SUM(grand_total) FROM `tabSales Order` WHERE customer=%s", order.customer)[0][0]

# GOOD — cache per customer
ltv_cache = {}
for order in orders:
    if order.customer not in ltv_cache:
        ltv_cache[order.customer] = frappe.db.sql(
            "SELECT SUM(grand_total) FROM `tabSales Order` WHERE customer=%s AND docstatus=1",
            order.customer
        )[0][0] or 0
```

### Fix 6: Pagination

```python
def execute(filters=None):
    page = int(filters.get("page", 1))
    page_size = int(filters.get("page_size", 500))
    offset = (page - 1) * page_size

    total = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabSales Order`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, filters)[0][0]

    data = frappe.db.sql("""
        SELECT name, customer, posting_date, grand_total
        FROM `tabSales Order`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY posting_date DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, {**filters, "page_size": page_size, "offset": offset}, as_dict=True)

    message = f"Showing {offset + 1}–{offset + len(data)} of {total} records"
    return get_columns(), data, message
```

### Prepared Reports — For Heavy Operations

Enable via Report DocType → check "Enable Prepared Report". The same `execute()` function runs in the background queue (up to 25 minutes). Results are compressed (gzip) and stored as an attachment. Users get a real-time notification when done.

**When to use:** report takes > 15 seconds, processes 100k+ rows, or is run frequently with the same filters.

### Using EXPLAIN to Diagnose Slow Queries

```python
explain = frappe.db.sql("EXPLAIN SELECT name FROM `tabSales Order` WHERE posting_date > '2024-01-01'", as_dict=True)
for row in explain:
    print(row.type, row.rows, row.Extra)
    # type=ALL means full table scan (bad)
    # type=ref means index lookup (good)
```

Add an index to fix a full table scan:

```sql
ALTER TABLE `tabSales Order` ADD INDEX idx_posting_date (posting_date);
```

Or in Frappe DocType definition, set `search_index: 1` on the field.

### Quick Reference

| Problem | Fix |
|---|---|
| No filters | Add mandatory date range + LIMIT |
| N+1 queries | Use JOIN in single query |
| `SELECT *` | Select only needed columns |
| Python aggregation | Use SQL `GROUP BY` / `SUM` |
| Large dataset in memory | Use `as_iterator=True` + unbuffered cursor |
| Repeated lookups | Cache in dict before loop |
| Report > 15 seconds | Enable Prepared Report |
| > 100k rows | Use Prepared Report + export |
