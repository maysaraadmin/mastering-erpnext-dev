# Chapter 16: Performance Tuning for Developers - Optimization Strategies

## 🎯 Learning Objectives

By the end of this chapter, you will master:
- **Identifying and analyzing** database bottlenecks
- **Implementing effective** indexing strategies
- **Using query optimization** techniques with EXPLAIN
- **Leveraging caching** strategies with Redis
- **Optimizing background** jobs and worker scaling
- **Improving frontend** performance and API efficiency
- **Troubleshooting timeout issues** and system freezes
- **Production performance monitoring** and optimization
- **Memory and resource management** for high-load scenarios

## 📚 Chapter Topics

### 16.1 Database Performance Analysis

**Identifying Slow Queries**

```python
# your_app/performance/db_analysis.py - Database performance analysis

import frappe
import time
from collections import defaultdict
from datetime import datetime, timedelta

class DatabaseAnalyzer:
    """Comprehensive database performance analysis tools"""
    
    @staticmethod
    def get_slow_queries(threshold_seconds=1.0, limit=50):
        """Get queries that exceed performance threshold"""
        
        # Enable query logging if not already enabled
        DatabaseAnalyzer.enable_query_logging()
        
        # Get slow queries from Frappe's query log
        slow_queries = frappe.get_all('Query Log',
            filters={
                'duration': ['>', threshold_seconds],
                'timestamp': ['>', datetime.now() - timedelta(hours=24)]
            },
            fields=['query', 'duration', 'timestamp', 'user'],
            order_by='duration desc',
            limit=limit
        )
        
        # Analyze query patterns
        analyzed_queries = []
        
        for query_log in slow_queries:
            analysis = DatabaseAnalyzer.analyze_query(query_log.query)
            analyzed_queries.append({
                'query': query_log.query,
                'duration': query_log.duration,
                'timestamp': query_log.timestamp,
                'user': query_log.user,
                'analysis': analysis
            })
        
        return analyzed_queries
    
    @staticmethod
    def analyze_query(query):
        """Analyze query structure and identify optimization opportunities"""
        
        analysis = {
            'query_type': None,
            'tables_involved': [],
            'has_join': False,
            'has_subquery': False,
            'has_aggregation': False,
            'has_where': False,
            'has_order_by': False,
            'has_limit': False,
            'optimization_suggestions': []
        }
        
        # Basic query type detection
        query_upper = query.upper().strip()
        
        if query_upper.startswith('SELECT'):
            analysis['query_type'] = 'SELECT'
        elif query_upper.startswith('INSERT'):
            analysis['query_type'] = 'INSERT'
        elif query_upper.startswith('UPDATE'):
            analysis['query_type'] = 'UPDATE'
        elif query_upper.startswith('DELETE'):
            analysis['query_type'] = 'DELETE'
        
        # Extract table names (simplified)
        import re
        
        # Find table names after FROM, JOIN, INTO, UPDATE
        table_patterns = [
            r'FROM\s+`?(\w+)`?',
            r'JOIN\s+`?(\w+)`?',
            r'UPDATE\s+`?(\w+)`?',
            r'INTO\s+`?(\w+)`?'
        ]
        
        for pattern in table_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            analysis['tables_involved'].extend(matches)
        
        # Remove duplicates and standard table names
        analysis['tables_involved'] = list(set(analysis['tables_involved']))
        analysis['tables_involved'] = [t.replace('tab', '') for t in analysis['tables_involved']]
        
        # Check for query features
        analysis['has_join'] = 'JOIN' in query_upper
        analysis['has_subquery'] = '(' in query and ')' in query and 'SELECT' in query_upper
        analysis['has_aggregation'] = any(func in query_upper for func in ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN('])
        analysis['has_where'] = 'WHERE' in query_upper
        analysis['has_order_by'] = 'ORDER BY' in query_upper
        analysis['has_limit'] = 'LIMIT' in query_upper
        
        # Generate optimization suggestions
        analysis['optimization_suggestions'] = DatabaseAnalyzer.generate_optimization_suggestions(analysis)
        
        return analysis
    
    @staticmethod
    def generate_optimization_suggestions(analysis):
        """Generate optimization suggestions based on query analysis"""
        
        suggestions = []
        
        # Missing WHERE clause
        if analysis['query_type'] == 'SELECT' and not analysis['has_where']:
            suggestions.append({
                'type': 'warning',
                'message': 'SELECT without WHERE clause may return all rows',
                'recommendation': 'Add WHERE clause to limit results'
            })
        
        # Missing LIMIT clause
        if analysis['query_type'] == 'SELECT' and not analysis['has_limit']:
            suggestions.append({
                'type': 'performance',
                'message': 'SELECT without LIMIT may return excessive data',
                'recommendation': 'Add LIMIT clause to restrict result size'
            })
        
        # Complex joins
        if analysis['has_join'] and len(analysis['tables_involved']) > 3:
            suggestions.append({
                'type': 'performance',
                'message': 'Query joins multiple tables',
                'recommendation': 'Consider breaking into smaller queries or adding indexes'
            })
        
        # Aggregation without proper indexes
        if analysis['has_aggregation'] and analysis['has_where']:
            suggestions.append({
                'type': 'index',
                'message': 'Aggregation with WHERE clause',
                'recommendation': 'Add composite index on WHERE and GROUP BY columns'
            })
        
        # Subquery optimization
        if analysis['has_subquery']:
            suggestions.append({
                'type': 'performance',
                'message': 'Query contains subqueries',
                'recommendation': 'Consider converting subqueries to JOINs'
            })
        
        return suggestions
    
    @staticmethod
    def enable_query_logging():
        """Enable comprehensive query logging"""
        
        # Enable slow query log
        frappe.db.sql("SET GLOBAL slow_query_log = 'ON'")
        frappe.db.sql("SET GLOBAL long_query_time = 1")
        
        # Enable general query log (temporary, for debugging)
        # frappe.db.sql("SET GLOBAL general_log = 'ON'")
        
        # Log to file
        # frappe.db.sql("SET GLOBAL log_output = 'FILE'")
        # frappe.db.sql("SET GLOBAL general_log_file = '/var/log/mysql/general.log'")
    
    @staticmethod
    def get_table_statistics(table_name):
        """Get detailed table statistics"""
        
        # Get table size and row count
        table_info = frappe.db.sql(f"""
            SELECT 
                table_name,
                ROUND(((data_length + index_length) / 1024 / 1024), 2) AS table_size_mb,
                table_rows,
                ROUND((data_length / 1024 / 1024), 2) AS data_size_mb,
                ROUND((index_length / 1024 / 1024), 2) AS index_size_mb
            FROM information_schema.TABLES 
            WHERE table_schema = DATABASE() 
            AND table_name = 'tab{table_name}'
        """, as_dict=True)
        
        if not table_info:
            return None
        
        stats = table_info[0]
        
        # Get index information
        index_info = frappe.db.sql(f"""
            SELECT 
                index_name,
                GROUP_CONCAT(column_name ORDER BY seq_in_index) as columns,
                cardinality,
                non_unique
            FROM information_schema.STATISTICS 
            WHERE table_schema = DATABASE() 
            AND table_name = 'tab{table_name}'
            GROUP BY index_name, non_unique
            ORDER BY index_name, seq_in_index
        """, as_dict=True)
        
        stats['indexes'] = index_info
        
        # Get column statistics
        column_info = frappe.db.sql(f"""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.COLUMNS 
            WHERE table_schema = DATABASE() 
            AND table_name = 'tab{table_name}'
            ORDER BY ordinal_position
        """, as_dict=True)
        
        stats['columns'] = column_info
        
        return stats
    
    @staticmethod
    def analyze_index_usage(table_name):
        """Analyze index usage for a table"""
        
        # Get index usage statistics
        index_usage = frappe.db.sql(f"""
            SELECT 
                object_schema,
                object_name,
                index_name,
                count_read,
                count_fetch,
                sum_timer_fetch / 1000000000 as total_time_seconds,
                sum_timer_fetch / (count_fetch * 1000000000) as avg_time_per_fetch
            FROM performance_schema.table_io_waits_summary_by_index_usage
            WHERE object_schema = DATABASE()
            AND object_name = 'tab{table_name}'
            AND index_name IS NOT NULL
            ORDER BY sum_timer_fetch DESC
        """, as_dict=True)
        
        return index_usage
    
    @staticmethod
    def get_deadlock_analysis():
        """Get recent deadlock information"""
        
        deadlocks = frappe.db.sql("""
            SELECT 
                r.trx_id waiting_trx_id,
                r.trx_mysql_thread_id waiting_thread,
                r.trx_query waiting_query,
                b.trx_id blocking_trx_id,
                b.trx_mysql_thread_id blocking_thread,
                b.trx_query blocking_query
            FROM information_schema.innodb_lock_waits w
            INNER JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id
            INNER JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id
        """, as_dict=True)
        
        return deadlocks

# Usage examples
def analyze_database_performance():
    """Run comprehensive database performance analysis"""
    
    print("=== Database Performance Analysis ===\n")
    
    # 1. Get slow queries
    slow_queries = DatabaseAnalyzer.get_slow_queries(threshold_seconds=0.5, limit=20)
    
    print(f"Found {len(slow_queries)} slow queries:")
    for i, query_info in enumerate(slow_queries[:5], 1):
        print(f"\n{i}. Query: {query_info['query'][:100]}...")
        print(f"   Duration: {query_info['duration']:.3f}s")
        print(f"   Tables: {', '.join(query_info['analysis']['tables_involved'])}")
        
        if query_info['analysis']['optimization_suggestions']:
            print("   Suggestions:")
            for suggestion in query_info['analysis']['optimization_suggestions']:
                print(f"     - {suggestion['message']}")
    
    # 2. Analyze key tables
    key_tables = ['Sales Order', 'Customer', 'Item', 'GL Entry']
    
    print(f"\n=== Table Statistics ===")
    for table in key_tables:
        stats = DatabaseAnalyzer.get_table_statistics(table)
        if stats:
            print(f"\n{table}:")
            print(f"  Size: {stats['table_size_mb']} MB")
            print(f"  Rows: {stats['table_rows']:,}")
            print(f"  Indexes: {len(stats['indexes'])}")
            
            # Check for missing indexes on commonly queried fields
            common_fields = ['name', 'customer', 'date', 'status']
            for field in common_fields:
                has_index = any(field.lower() in idx['columns'].lower() for idx in stats['indexes'])
                if not has_index:
                    print(f"  Missing index on: {field}")
```

**Query Performance Monitoring**

```python
# your_app/performance/query_monitor.py - Real-time query monitoring

import frappe
import time
import threading
from collections import deque
from datetime import datetime

class QueryMonitor:
    """Real-time query performance monitoring"""
    
    def __init__(self, max_history=1000):
        self.max_history = max_history
        self.query_history = deque(maxlen=max_history)
        self.slow_queries = deque(maxlen=100)
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval=60):
        """Start background monitoring"""
        
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        print(f"Query monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        print("Query monitoring stopped")
    
    def _monitor_loop(self, interval):
        """Background monitoring loop"""
        
        while self.monitoring:
            try:
                # Get recent queries from performance schema
                queries = self._get_recent_queries()
                
                for query in queries:
                    self.query_history.append(query)
                    
                    # Check if it's a slow query
                    if query['duration'] > 1.0:  # 1 second threshold
                        self.slow_queries.append(query)
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error in monitoring loop: {str(e)}")
                time.sleep(interval)
    
    def _get_recent_queries(self):
        """Get recent queries from performance schema"""
        
        queries = frappe.db.sql("""
            SELECT 
                DIGEST_TEXT as query,
                COUNT_STAR as execution_count,
                SUM_TIMER_WAIT / 1000000000 as total_time_seconds,
                AVG_TIMER_WAIT / 1000000000 as avg_time_seconds,
                MAX_TIMER_WAIT / 1000000000 as max_time_seconds,
                SUM_ROWS_EXAMINED as total_rows_examined,
                SUM_ROWS_AFFECTED as total_rows_affected,
                FIRST_SEEN as first_seen,
                LAST_SEEN as last_seen
            FROM performance_schema.events_statements_summary_by_digest
            WHERE LAST_SEEN > DATE_SUB(NOW(), INTERVAL 1 HOUR)
            ORDER BY AVG_TIMER_WAIT DESC
            LIMIT 50
        """, as_dict=True)
        
        return queries
    
    def get_performance_summary(self):
        """Get performance summary statistics"""
        
        if not self.query_history:
            return {"status": "no_data"}
        
        # Calculate statistics
        total_queries = len(self.query_history)
        slow_query_count = len(self.slow_queries)
        avg_duration = sum(q['avg_time_seconds'] for q in self.query_history) / total_queries
        max_duration = max(q['max_time_seconds'] for q in self.query_history)
        
        # Group by query type
        query_types = defaultdict(int)
        for query in self.query_history:
            query_type = self._classify_query(query['query'])
            query_types[query_type] += 1
        
        return {
            "total_queries": total_queries,
            "slow_queries": slow_query_count,
            "slow_query_percentage": (slow_query_count / total_queries) * 100,
            "avg_duration": avg_duration,
            "max_duration": max_duration,
            "query_types": dict(query_types),
            "top_slow_queries": list(self.slow_queries)[:5]
        }
    
    def _classify_query(self, query):
        """Classify query type"""
        
        query_upper = query.upper().strip()
        
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith('ALTER'):
            return 'ALTER'
        else:
            return 'OTHER'
    
    def generate_optimization_report(self):
        """Generate optimization recommendations"""
        
        summary = self.get_performance_summary()
        
        if summary["status"] == "no_data":
            return {"status": "no_data"}
        
        recommendations = []
        
        # High slow query percentage
        if summary["slow_query_percentage"] > 10:
            recommendations.append({
                "priority": "high",
                "issue": f"High slow query percentage: {summary['slow_query_percentage']:.1f}%",
                "recommendation": "Review and optimize slow queries, consider adding indexes"
            })
        
        # High average duration
        if summary["avg_duration"] > 0.5:
            recommendations.append({
                "priority": "medium",
                "issue": f"High average query duration: {summary['avg_duration']:.3f}s",
                "recommendation": "Analyze query patterns and optimize frequently executed queries"
            })
        
        # Very slow queries
        if summary["max_duration"] > 5.0:
            recommendations.append({
                "priority": "high",
                "issue": f"Very slow query detected: {summary['max_duration']:.3f}s",
                "recommendation": "Immediate optimization required for slowest queries"
            })
        
        return {
            "summary": summary,
            "recommendations": recommendations
        }

# Global query monitor instance
query_monitor = QueryMonitor()

# Hook into Frappe's query execution for monitoring
def monitor_query_execution(query, params=None):
    """Monitor individual query execution"""
    
    start_time = time.time()
    
    try:
        # Execute query
        if params:
            result = frappe.db.sql(query, params, as_dict=True)
        else:
            result = frappe.db.sql(query, as_dict=True)
        
        duration = time.time() - start_time
        
        # Log slow queries
        if duration > 1.0:
            frappe.logger().warning(f"Slow query ({duration:.3f}s): {query}")
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        frappe.logger().error(f"Query failed ({duration:.3f}s): {query} - {str(e)}")
        raise
```

### 16.2 Indexing Strategies

**Strategic Index Design**

```python
# your_app/performance/indexing.py - Advanced indexing strategies

import frappe
from frappe.utils import cint

class IndexManager:
    """Advanced index management and optimization"""
    
    @staticmethod
    def analyze_missing_indexes(doctype, sample_queries=None):
        """Analyze and suggest missing indexes for a DocType"""
        
        table_name = f"tab{doctype}"
        
        # Get table statistics
        table_stats = DatabaseAnalyzer.get_table_statistics(doctype)
        if not table_stats:
            return {"error": f"Table {table_name} not found"}
        
        # Get existing indexes
        existing_indexes = {idx['index_name']: idx for idx in table_stats['indexes']}
        
        # Analyze common query patterns
        query_patterns = IndexManager._get_common_query_patterns(doctype, sample_queries)
        
        # Generate index recommendations
        recommendations = []
        
        for pattern in query_patterns:
            suggestion = IndexManager._generate_index_suggestion(
                doctype, pattern, existing_indexes
            )
            if suggestion:
                recommendations.append(suggestion)
        
        return {
            'doctype': doctype,
            'table_size_mb': table_stats['table_size_mb'],
            'row_count': table_stats['table_rows'],
            'existing_indexes': len(existing_indexes),
            'recommendations': recommendations
        }
    
    @staticmethod
    def _get_common_query_patterns(doctype, sample_queries=None):
        """Get common query patterns for a DocType"""
        
        patterns = []
        
        # Standard Frappe patterns
        standard_patterns = [
            {
                'type': 'primary_lookup',
                'description': 'Primary document lookup',
                'columns': ['name'],
                'where_conditions': ['name = %s'],
                'frequency': 'high'
            },
            {
                'type': 'status_filter',
                'description': 'Document status filtering',
                'columns': ['docstatus', 'status'],
                'where_conditions': ['docstatus = %s', 'status = %s'],
                'frequency': 'high'
            },
            {
                'type': 'date_range',
                'description': 'Date-based filtering',
                'columns': ['creation', 'modified', 'transaction_date'],
                'where_conditions': ['creation >= %s', 'creation <= %s'],
                'frequency': 'medium'
            },
            {
                'type': 'user_filter',
                'description': 'User-based filtering',
                'columns': ['owner', 'modified_by'],
                'where_conditions': ['owner = %s', 'modified_by = %s'],
                'frequency': 'medium'
            },
            {
                'type': 'company_filter',
                'description': 'Company-based filtering',
                'columns': ['company'],
                'where_conditions': ['company = %s'],
                'frequency': 'high'
            }
        ]
        
        patterns.extend(standard_patterns)
        
        # Add DocType-specific patterns based on common fields
        meta = frappe.get_meta(doctype)
        
        # Link fields
        link_fields = [f for f in meta.fields if f.fieldtype == 'Link']
        for field in link_fields[:5]:  # Limit to top 5 link fields
            patterns.append({
                'type': 'link_filter',
                'description': f'Link field filter: {field.fieldname}',
                'columns': [field.fieldname],
                'where_conditions': [f'{field.fieldname} = %s'],
                'frequency': 'medium'
            })
        
        # Common combinations
        if any(f.fieldname == 'customer' for f in meta.fields):
            patterns.append({
                'type': 'customer_status',
                'description': 'Customer with status',
                'columns': ['customer', 'docstatus'],
                'where_conditions': ['customer = %s', 'docstatus = %s'],
                'frequency': 'high'
            })
        
        if any(f.fieldname == 'date' for f in meta.fields):
            patterns.append({
                'type': 'date_status',
                'description': 'Date with status',
                'columns': ['date', 'docstatus'],
                'where_conditions': ['date >= %s', 'date <= %s', 'docstatus = %s'],
                'frequency': 'high'
            })
        
        return patterns
    
    @staticmethod
    def _generate_index_suggestion(doctype, pattern, existing_indexes):
        """Generate index suggestion for a query pattern"""
        
        columns = pattern['columns']
        
        # Check if similar index already exists
        for idx_name, idx_info in existing_indexes.items():
            idx_columns = [col.strip() for col in idx_info['columns'].split(',')]
            
            # Check if pattern columns are covered by existing index
            if all(col in idx_columns for col in columns):
                return None  # Index already exists
        
        # Generate index name
        column_suffix = '_'.join(col.replace('_', '') for col in columns[:3])
        index_name = f"idx_{doctype.lower()}_{column_suffix}"
        
        # Estimate index size (rough calculation)
        estimated_size = IndexManager._estimate_index_size(doctype, columns)
        
        # Calculate priority based on frequency and table size
        priority_score = IndexManager._calculate_priority_score(doctype, pattern)
        
        return {
            'index_name': index_name,
            'columns': columns,
            'pattern_type': pattern['type'],
            'description': pattern['description'],
            'frequency': pattern['frequency'],
            'estimated_size_mb': estimated_size,
            'priority_score': priority_score,
            'sql': f"CREATE INDEX `{index_name}` ON `tab{doctype}` ({', '.join(columns)})"
        }
    
    @staticmethod
    def _estimate_index_size(doctype, columns):
        """Estimate index size in MB"""
        
        try:
            # Get table row count
            row_count = frappe.db.count(doctype)
            
            # Get column information
            column_info = frappe.db.sql(f"""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.COLUMNS
                WHERE table_schema = DATABASE()
                AND table_name = 'tab{doctype}'
                AND column_name IN ({', '.join(['%s'] * len(columns))})
            """, columns, as_dict=True)
            
            # Estimate index row size
            index_row_size = 0
            for col in column_info:
                if col['data_type'] in ['varchar', 'char']:
                    index_row_size += min(col['character_maximum_length'] or 50, 50)
                elif col['data_type'] in ['int', 'bigint']:
                    index_row_size += 8
                elif col['data_type'] in ['date', 'datetime']:
                    index_row_size += 8
                else:
                    index_row_size += 20  # Default estimate
            
            # Add overhead for B-tree structure
            index_row_size += 20
            
            # Calculate total size (rough estimate)
            total_size_bytes = row_count * index_row_size
            total_size_mb = total_size_bytes / (1024 * 1024)
            
            return round(total_size_mb, 2)
            
        except Exception:
            return 10.0  # Default estimate
    
    @staticmethod
    def _calculate_priority_score(doctype, pattern):
        """Calculate priority score for index recommendation"""
        
        # Base score based on frequency
        frequency_scores = {'high': 10, 'medium': 6, 'low': 3}
        base_score = frequency_scores.get(pattern['frequency'], 3)
        
        # Adjust based on table size (larger tables benefit more from indexes)
        try:
            row_count = frappe.db.count(doctype)
            if row_count > 100000:
                size_multiplier = 1.5
            elif row_count > 10000:
                size_multiplier = 1.2
            else:
                size_multiplier = 1.0
            
            base_score *= size_multiplier
            
        except Exception:
            pass
        
        # Adjust based on number of columns (fewer columns = more efficient)
        column_count = len(pattern['columns'])
        if column_count == 1:
            column_multiplier = 1.2
        elif column_count == 2:
            column_multiplier = 1.0
        else:
            column_multiplier = 0.8
        
        base_score *= column_multiplier
        
        return round(base_score, 1)
    
    @staticmethod
    def create_recommended_indexes(doctype, max_indexes=5):
        """Create recommended indexes for a DocType"""
        
        analysis = IndexManager.analyze_missing_indexes(doctype)
        
        if 'error' in analysis:
            return analysis
        
        # Sort recommendations by priority score
        recommendations = sorted(
            analysis['recommendations'], 
            key=lambda x: x['priority_score'], 
            reverse=True
        )
        
        created_indexes = []
        
        for i, rec in enumerate(recommendations[:max_indexes]):
            try:
                # Create index
                frappe.db.sql(rec['sql'])
                frappe.db.commit()
                
                created_indexes.append({
                    'index_name': rec['index_name'],
                    'columns': rec['columns'],
                    'priority_score': rec['priority_score'],
                    'status': 'created'
                })
                
                print(f"Created index: {rec['index_name']}")
                
            except Exception as e:
                created_indexes.append({
                    'index_name': rec['index_name'],
                    'columns': rec['columns'],
                    'priority_score': rec['priority_score'],
                    'status': 'failed',
                    'error': str(e)
                })
                
                print(f"Failed to create index {rec['index_name']}: {str(e)}")
        
        return {
            'doctype': doctype,
            'total_recommendations': len(recommendations),
            'created_indexes': created_indexes
        }
    
    @staticmethod
    def analyze_index_usage(doctype, days=7):
        """Analyze index usage statistics"""
        
        # Get index usage from performance schema
        index_usage = frappe.db.sql(f"""
            SELECT 
                object_name,
                index_name,
                count_read,
                count_fetch,
                sum_timer_wait / 1000000000 as total_time_seconds,
                sum_timer_wait / (count_fetch * 1000000000) as avg_time_per_fetch
            FROM performance_schema.table_io_waits_summary_by_index_usage
            WHERE object_schema = DATABASE()
            AND object_name = 'tab{doctype}'
            AND index_name IS NOT NULL
            AND count_fetch > 0
            ORDER BY sum_timer_wait DESC
        """, as_dict=True)
        
        # Get unused indexes
        all_indexes = frappe.db.sql(f"""
            SELECT DISTINCT index_name
            FROM information_schema.STATISTICS
            WHERE table_schema = DATABASE()
            AND table_name = 'tab{doctype}'
            AND index_name != 'PRIMARY'
        """, as_dict=True)
        
        used_index_names = {idx['index_name'] for idx in index_usage}
        unused_indexes = []
        
        for idx in all_indexes:
            if idx['index_name'] not in used_index_names:
                unused_indexes.append(idx['index_name'])
        
        return {
            'doctype': doctype,
            'index_usage': index_usage,
            'unused_indexes': unused_indexes,
            'total_indexes': len(all_indexes),
            'used_indexes': len(index_usage),
            'unused_count': len(unused_indexes)
        }
    
    @staticmethod
    def drop_unused_indexes(doctype, confirm=False):
        """Drop unused indexes (with confirmation)"""
        
        usage_analysis = IndexManager.analyze_index_usage(doctype)
        
        if not usage_analysis['unused_indexes']:
            return {"message": "No unused indexes found"}
        
        if not confirm:
            return {
                "message": "Use confirm=True to drop unused indexes",
                "unused_indexes": usage_analysis['unused_indexes']
            }
        
        dropped_indexes = []
        
        for index_name in usage_analysis['unused_indexes']:
            try:
                # Don't drop primary or unique indexes
                if index_name.upper() in ['PRIMARY', 'UNIQUE']:
                    continue
                
                frappe.db.sql(f"DROP INDEX `{index_name}` ON `tab{doctype}`")
                frappe.db.commit()
                
                dropped_indexes.append(index_name)
                print(f"Dropped unused index: {index_name}")
                
            except Exception as e:
                print(f"Failed to drop index {index_name}: {str(e)}")
        
        return {
            'doctype': doctype,
            'dropped_indexes': dropped_indexes,
            'total_unused': len(usage_analysis['unused_indexes'])
        }

# Index optimization commands
def optimize_doctype_indexes(doctype, dry_run=True):
    """Comprehensive index optimization for a DocType"""
    
    print(f"=== Index Optimization for {doctype} ===\n")
    
    # 1. Analyze missing indexes
    print("1. Analyzing missing indexes...")
    missing_analysis = IndexManager.analyze_missing_indexes(doctype)
    
    if 'error' in missing_analysis:
        print(f"Error: {missing_analysis['error']}")
        return
    
    print(f"Table size: {missing_analysis['table_size_mb']} MB")
    print(f"Row count: {missing_analysis['row_count']:,}")
    print(f"Existing indexes: {missing_analysis['existing_indexes']}")
    print(f"Recommendations: {len(missing_analysis['recommendations'])}")
    
    # Show top recommendations
    print("\nTop recommendations:")
    for i, rec in enumerate(missing_analysis['recommendations'][:5], 1):
        print(f"{i}. {rec['index_name']}")
        print(f"   Columns: {', '.join(rec['columns'])}")
        print(f"   Priority: {rec['priority_score']}")
        print(f"   Description: {rec['description']}")
        print()
    
    # 2. Analyze current index usage
    print("2. Analyzing current index usage...")
    usage_analysis = IndexManager.analyze_index_usage(doctype)
    
    print(f"Used indexes: {usage_analysis['used_indexes']}")
    print(f"Unused indexes: {usage_analysis['unused_count']}")
    
    if usage_analysis['unused_indexes']:
        print("Unused indexes:")
        for idx in usage_analysis['unused_indexes']:
            print(f"  - {idx}")
    
    # 3. Create recommendations (if not dry run)
    if not dry_run and missing_analysis['recommendations']:
        print("\n3. Creating recommended indexes...")
        result = IndexManager.create_recommended_indexes(doctype, max_indexes=3)
        
        print(f"Created {len(result['created_indexes'])} indexes:")
        for idx in result['created_indexes']:
            if idx['status'] == 'created':
                print(f"  ✓ {idx['index_name']}")
            else:
                print(f"  ✗ {idx['index_name']} - {idx.get('error', 'Failed')}")
    
    # 4. Drop unused indexes (if not dry run)
    if not dry_run and usage_analysis['unused_indexes']:
        print("\n4. Dropping unused indexes...")
        result = IndexManager.drop_unused_indexes(doctype, confirm=True)
        
        print(f"Dropped {len(result['dropped_indexes'])} unused indexes:")
        for idx in result['dropped_indexes']:
            print(f"  ✓ {idx}")
    
    print(f"\n=== Optimization Complete ===")
```

### 16.3 Query Optimization with EXPLAIN

**Advanced Query Analysis**

```python
# your_app/performance/query_optimizer.py - Query optimization with EXPLAIN

import frappe
import re
from collections import defaultdict

class QueryOptimizer:
    """Advanced query optimization using EXPLAIN"""
    
    @staticmethod
    def explain_query(query, params=None):
        """Get EXPLAIN plan for a query"""
        
        explain_query = f"EXPLAIN FORMAT=JSON {query}"
        
        try:
            if params:
                result = frappe.db.sql(explain_query, params, as_dict=True)
            else:
                result = frappe.db.sql(explain_query, as_dict=True)
            
            if result and result[0].get('EXPLAIN'):
                explain_data = frappe.parse_json(result[0]['EXPLAIN'])
                return QueryOptimizer._analyze_explain_plan(explain_data)
            
        except Exception as e:
            return {"error": f"EXPLAIN failed: {str(e)}"}
        
        return {"error": "No EXPLAIN data available"}
    
    @staticmethod
    def _analyze_explain_plan(explain_data):
        """Analyze EXPLAIN plan and identify optimization opportunities"""
        
        analysis = {
            'query_block': explain_data.get('query_block', {}),
            'table_operations': [],
            'optimization_issues': [],
            'recommendations': [],
            'estimated_cost': 0,
            'estimated_rows': 0
        }
        
        # Extract table operations
        query_block = explain_data.get('query_block', {})
        
        # Find table operations recursively
        def find_table_operations(node, path=""):
            operations = []
            
            if isinstance(node, dict):
                if 'table' in node:
                    operations.append({
                        'table': node['table'],
                        'access_type': node.get('access_type', ''),
                        'possible_keys': node.get('possible_keys', []),
                        'key': node.get('key', ''),
                        'key_length': node.get('key_length', ''),
                        'ref': node.get('ref', ''),
                        'rows_examined_per_scan': node.get('rows_examined_per_scan', 0),
                        'rows_produced_per_join': node.get('rows_produced_per_join', 0),
                        'filtered': node.get('filtered', 0),
                        'using_index': node.get('using_index', False),
                        'using_temporary': node.get('using_temporary', False),
                        'using_where': node.get('using_where', False),
                        'path': path
                    })
                
                # Recursively check nested operations
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        nested_ops = find_table_operations(value, f"{path}.{key}")
                        operations.extend(nested_ops)
            
            elif isinstance(node, list):
                for i, item in enumerate(node):
                    nested_ops = find_table_operations(item, f"{path}[{i}]")
                    operations.extend(nested_ops)
            
            return operations
        
        analysis['table_operations'] = find_table_operations(explain_data)
        
        # Analyze optimization issues
        for op in analysis['table_operations']:
            issues = []
            
            # Full table scan
            if op['access_type'] == 'ALL' and op['rows_examined_per_scan'] > 1000:
                issues.append({
                    'type': 'full_table_scan',
                    'severity': 'high',
                    'message': f"Full table scan on {op['table']} examining {op['rows_examined_per_scan']:,} rows",
                    'recommendation': "Add appropriate index or optimize WHERE clause"
                })
            
            # No index used
            if not op['key'] and op['access_type'] != 'ALL':
                issues.append({
                    'type': 'no_index',
                    'severity': 'medium',
                    'message': f"No index used for {op['table']}",
                    'recommendation': "Consider adding index on filtered columns"
                })
            
            # Using temporary table
            if op['using_temporary']:
                issues.append({
                    'type': 'temporary_table',
                    'severity': 'medium',
                    'message': f"Using temporary table for {op['table']}",
                    'recommendation': "Optimize GROUP BY or ORDER BY, add composite indexes"
                })
            
            # Low selectivity
            if op['filtered'] and op['filtered'] < 10:
                issues.append({
                    'type': 'low_selectivity',
                    'severity': 'low',
                    'message': f"Low selectivity ({op['filtered']}%) on {op['table']}",
                    'recommendation': "Consider different index strategy or query rewrite"
                })
            
            # High row count
            if op['rows_examined_per_scan'] > 100000:
                issues.append({
                    'type': 'high_row_count',
                    'severity': 'medium',
                    'message': f"High row count ({op['rows_examined_per_scan']:,}) on {op['table']}",
                    'recommendation': "Add more selective WHERE conditions or better indexes"
                })
            
            analysis['optimization_issues'].extend(issues)
        
        # Calculate totals
        analysis['estimated_rows'] = sum(op['rows_examined_per_scan'] for op in analysis['table_operations'])
        
        # Generate overall recommendations
        analysis['recommendations'] = QueryOptimizer._generate_query_recommendations(analysis)
        
        return analysis
    
    @staticmethod
    def _generate_query_recommendations(analysis):
        """Generate overall query optimization recommendations"""
        
        recommendations = []
        
        # Check for full table scans
        full_scans = [issue for issue in analysis['optimization_issues'] if issue['type'] == 'full_table_scan']
        if full_scans:
            recommendations.append({
                'priority': 'high',
                'type': 'index_optimization',
                'message': f"Found {len(full_scans)} full table scans",
                'details': [scan['message'] for scan in full_scans]
            })
        
        # Check for temporary tables
        temp_tables = [issue for issue in analysis['optimization_issues'] if issue['type'] == 'temporary_table']
        if temp_tables:
            recommendations.append({
                'priority': 'medium',
                'type': 'query_rewrite',
                'message': f"Using temporary tables in {len(temp_tables)} operations",
                'details': [temp['message'] for temp in temp_tables]
            })
        
        # Check for missing indexes
        missing_indexes = [issue for issue in analysis['optimization_issues'] if issue['type'] == 'no_index']
        if missing_indexes:
            recommendations.append({
                'priority': 'high',
                'type': 'index_creation',
                'message': f"Missing indexes for {len(missing_indexes)} table operations",
                'details': [idx['message'] for idx in missing_indexes]
            })
        
        return recommendations
    
    @staticmethod
    def optimize_query(query, params=None):
        """Suggest query optimizations"""
        
        # Get EXPLAIN analysis
        explain_analysis = QueryOptimizer.explain_query(query, params)
        
        if 'error' in explain_analysis:
            return explain_analysis
        
        # Generate optimization suggestions
        optimizations = []
        
        # Analyze query structure
        query_upper = query.upper()
        
        # 1. Check for SELECT *
        if 'SELECT *' in query_upper:
            optimizations.append({
                'type': 'column_selection',
                'issue': 'Using SELECT *',
                'recommendation': 'Specify only required columns',
                'impact': 'Reduces data transfer and memory usage',
                'example': QueryOptimizer._generate_column_specific_example(query)
            })
        
        # 2. Check for missing WHERE clauses
        if 'WHERE' not in query_upper and 'SELECT' in query_upper:
            optimizations.append({
                'type': 'filtering',
                'issue': 'Missing WHERE clause',
                'recommendation': 'Add WHERE clause to limit results',
                'impact': 'Reduces rows processed',
                'example': None
            })
        
        # 3. Check for LIMIT on large result sets
        if 'SELECT' in query_upper and 'LIMIT' not in query_upper:
            optimizations.append({
                'type': 'result_limiting',
                'issue': 'No LIMIT clause',
                'recommendation': 'Add LIMIT to restrict result size',
                'impact': 'Prevents excessive data retrieval',
                'example': f"{query.rstrip(';')} LIMIT 1000;"
            })
        
        # 4. Check for subqueries that could be JOINs
        subquery_pattern = r'SELECT.*FROM.*WHERE.*IN\s*\(SELECT'
        if re.search(subquery_pattern, query, re.IGNORECASE):
            optimizations.append({
                'type': 'subquery_optimization',
                'issue': 'Subquery in WHERE clause',
                'recommendation': 'Consider converting to JOIN',
                'impact': 'Often better performance',
                'example': None  # Would need query-specific transformation
            })
        
        # 5. Add EXPLAIN-based recommendations
        for rec in explain_analysis['recommendations']:
            optimizations.append({
                'type': rec['type'],
                'issue': rec['message'],
                'recommendation': rec['details'][0] if rec['details'] else 'See EXPLAIN analysis',
                'impact': 'Improved query performance',
                'example': None
            })
        
        return {
            'original_query': query,
            'explain_analysis': explain_analysis,
            'optimizations': optimizations,
            'estimated_improvement': QueryOptimizer._estimate_improvement(explain_analysis, optimizations)
        }
    
    @staticmethod
    def _generate_column_specific_example(query):
        """Generate example with specific columns"""
        
        # Simple transformation - in practice would be more sophisticated
        if 'SELECT *' in query.upper():
            # Replace with common columns (would need table analysis)
            common_columns = 'name, creation, modified, owner'
            example = query.replace('SELECT *', f'SELECT {common_columns}', 1)
            return example
        
        return None
    
    @staticmethod
    def _estimate_improvement(explain_analysis, optimizations):
        """Estimate potential performance improvement"""
        
        improvement_score = 0
        
        # Base score from EXPLAIN issues
        high_priority_issues = len([rec for rec in explain_analysis['recommendations'] if rec['priority'] == 'high'])
        medium_priority_issues = len([rec for rec in explain_analysis['recommendations'] if rec['priority'] == 'medium'])
        
        improvement_score += high_priority_issues * 30
        improvement_score += medium_priority_issues * 15
        
        # Add score from optimizations
        for opt in optimizations:
            if opt['type'] in ['index_optimization', 'index_creation']:
                improvement_score += 25
            elif opt['type'] == 'column_selection':
                improvement_score += 10
            elif opt['type'] == 'filtering':
                improvement_score += 20
            elif opt['type'] == 'result_limiting':
                improvement_score += 15
            else:
                improvement_score += 5
        
        # Cap at 100
        improvement_score = min(improvement_score, 100)
        
        return improvement_score

# Query optimization utilities
def analyze_and_optimize_query(query, params=None):
    """Comprehensive query analysis and optimization"""
    
    print(f"=== Query Analysis ===")
    print(f"Query: {query}")
    print()
    
    # Get EXPLAIN analysis
    print("1. EXPLAIN Analysis:")
    explain_result = QueryOptimizer.explain_query(query, params)
    
    if 'error' in explain_result:
        print(f"Error: {explain_result['error']}")
        return
    
    print(f"Estimated rows examined: {explain_result['estimated_rows']:,}")
    print(f"Table operations: {len(explain_result['table_operations'])}")
    
    # Show table operations
    for i, op in enumerate(explain_result['table_operations'], 1):
        print(f"\n  Operation {i}: {op['table']}")
        print(f"    Access type: {op['access_type']}")
        print(f"    Key used: {op['key'] or 'None'}")
        print(f"    Rows examined: {op['rows_examined_per_scan']:,}")
        print(f"    Using index: {op['using_index']}")
        print(f"    Using temporary: {op['using_temporary']}")
    
    # Show optimization issues
    if explain_result['optimization_issues']:
        print(f"\n2. Optimization Issues:")
        for i, issue in enumerate(explain_result['optimization_issues'], 1):
            print(f"  {i}. {issue['message']} ({issue['severity']})")
    
    # Get optimization suggestions
    print(f"\n3. Optimization Suggestions:")
    optimization_result = QueryOptimizer.optimize_query(query, params)
    
    for i, opt in enumerate(optimization_result['optimizations'], 1):
        print(f"  {i}. {opt['issue']}")
        print(f"     Recommendation: {opt['recommendation']}")
        print(f"     Impact: {opt['impact']}")
        if opt['example']:
            print(f"     Example: {opt['example']}")
        print()
    
    # Show estimated improvement
    improvement = optimization_result['estimated_improvement']
    print(f"Estimated potential improvement: {improvement}%")
    
    return optimization_result
```

### 16.4 Caching Strategies with Redis

**Advanced Caching Implementation**

```python
# your_app/performance/caching.py - Advanced caching strategies

import frappe
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from frappe.utils import now_datetime, add_to_date

class CacheManager:
    """Advanced caching manager with multiple strategies"""
    
    def __init__(self, prefix="app_cache"):
        self.prefix = prefix
        self.redis_client = frappe.cache()
        self.default_ttl = 3600  # 1 hour
    
    def get(self, key, default=None):
        """Get cached value with automatic deserialization"""
        
        cache_key = f"{self.prefix}:{key}"
        
        try:
            value = self.redis_client.get_value(cache_key)
            
            if value is None:
                return default
            
            # Try to deserialize as JSON first
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Try pickle
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError):
                    # Return as string
                    return value.decode('utf-8') if isinstance(value, bytes) else value
        
        except Exception as e:
            frappe.logger().error(f"Cache get error for key {key}: {str(e)}")
            return default
    
    def set(self, key, value, ttl=None):
        """Set cached value with automatic serialization"""
        
        cache_key = f"{self.prefix}:{key}"
        ttl = ttl or self.default_ttl
        
        try:
            # Serialize based on value type
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, default=str)
            elif hasattr(value, '__dict__'):
                # For objects, use pickle
                serialized_value = pickle.dumps(value)
            else:
                # For simple types, convert to string
                serialized_value = str(value)
            
            self.redis_client.set_value(cache_key, serialized_value, expires_in_sec=ttl)
            return True
        
        except Exception as e:
            frappe.logger().error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def delete(self, key):
        """Delete cached value"""
        
        cache_key = f"{self.prefix}:{key}"
        
        try:
            self.redis_client.delete_value(cache_key)
            return True
        except Exception as e:
            frappe.logger().error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern):
        """Clear cache keys matching pattern"""
        
        try:
            full_pattern = f"{self.prefix}:{pattern}"
            keys = self.redis_client.get_keys(full_pattern)
            
            for key in keys:
                self.redis_client.delete_value(key)
            
            return len(keys)
        
        except Exception as e:
            frappe.logger().error(f"Cache clear pattern error: {str(e)}")
            return 0
    
    def get_or_set(self, key, callback, ttl=None):
        """Get value from cache or set using callback"""
        
        value = self.get(key)
        
        if value is None:
            # Cache miss - call callback
            value = callback()
            self.set(key, value, ttl)
        
        return value
    
    def cache_function(self, ttl=None, key_prefix=None):
        """Decorator for caching function results"""
        
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                key_parts = [func.__name__]
                
                if key_prefix:
                    key_parts.insert(0, key_prefix)
                
                # Add args and kwargs to key
                if args:
                    key_parts.extend(str(arg) for arg in args)
                
                if kwargs:
                    sorted_kwargs = sorted(kwargs.items())
                    key_parts.extend(f"{k}:{v}" for k, v in sorted_kwargs)
                
                cache_key = ":".join(key_parts)
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator

class QueryCache:
    """Specialized cache for database queries"""
    
    def __init__(self):
        self.cache = CacheManager("query_cache")
    
    def get_query_result(self, query, params=None, ttl=300):
        """Get cached query result"""
        
        # Generate cache key from query and params
        query_hash = self._generate_query_hash(query, params)
        cache_key = f"query:{query_hash}"
        
        return self.cache.get(cache_key)
    
    def set_query_result(self, query, params, result, ttl=300):
        """Cache query result"""
        
        query_hash = self._generate_query_hash(query, params)
        cache_key = f"query:{query_hash}"
        
        return self.cache.set(cache_key, result, ttl)
    
    def _generate_query_hash(self, query, params=None):
        """Generate hash for query and parameters"""
        
        query_str = query.strip()
        
        if params:
            if isinstance(params, (list, tuple)):
                param_str = str(params)
            elif isinstance(params, dict):
                param_str = json.dumps(params, sort_keys=True)
            else:
                param_str = str(params)
            
            query_str += f"|{param_str}"
        
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def invalidate_table_cache(self, table_name):
        """Invalidate cache for specific table"""
        
        pattern = f"*{table_name}*"
        return self.cache.clear_pattern(pattern)

class DocumentCache:
    """Specialized cache for Frappe documents"""
    
    def __init__(self):
        self.cache = CacheManager("doc_cache")
    
    def get_document(self, doctype, name):
        """Get cached document"""
        
        cache_key = f"{doctype}:{name}"
        return self.cache.get(cache_key)
    
    def set_document(self, doc, ttl=1800):
        """Cache document"""
        
        cache_key = f"{doc.doctype}:{doc.name}"
        
        # Cache document data (not the full document object)
        doc_data = {
            'name': doc.name,
            'doctype': doc.doctype,
            'docstatus': doc.docstatus,
            'owner': doc.owner,
            'creation': doc.creation,
            'modified': doc.modified,
            'modified_by': doc.modified_by
        }
        
        # Add all field values
        for field in doc.meta.fields:
            fieldname = field.get('fieldname')
            if fieldname and hasattr(doc, fieldname):
                doc_data[fieldname] = doc.get(fieldname)
        
        return self.cache.set(cache_key, doc_data, ttl)
    
    def invalidate_document(self, doctype, name):
        """Invalidate specific document cache"""
        
        cache_key = f"{doctype}:{name}"
        return self.cache.delete(cache_key)
    
    def invalidate_doctype(self, doctype):
        """Invalidate all documents of a doctype"""
        
        pattern = f"{doctype}:*"
        return self.cache.clear_pattern(pattern)

class ReportCache:
    """Specialized cache for reports and analytics"""
    
    def __init__(self):
        self.cache = CacheManager("report_cache")
    
    def get_report_data(self, report_name, filters=None, ttl=600):
        """Get cached report data"""
        
        cache_key = self._generate_report_key(report_name, filters)
        return self.cache.get(cache_key)
    
    def set_report_data(self, report_name, filters, data, ttl=600):
        """Cache report data"""
        
        cache_key = self._generate_report_key(report_name, filters)
        return self.cache.set(cache_key, data, ttl)
    
    def _generate_report_key(self, report_name, filters):
        """Generate cache key for report"""
        
        key_parts = [report_name]
        
        if filters:
            # Sort filters for consistent key
            sorted_filters = sorted(filters.items()) if isinstance(filters, dict) else filters
            key_parts.extend(f"{k}:{v}" for k, v in sorted_filters)
        
        # Add date component for time-based invalidation
        date_part = now_datetime().strftime('%Y-%m-%d-%H')  # Hourly granularity
        key_parts.append(date_part)
        
        return ":".join(key_parts)

# Global cache instances
query_cache = QueryCache()
document_cache = DocumentCache()
report_cache = ReportCache()

# Cache decorators and utilities
def cached_query(ttl=300, cache_table=None):
    """Decorator for caching database queries"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get from cache first
            if len(args) > 0:
                query = args[0]
                params = args[1] if len(args) > 1 else None
            else:
                query = kwargs.get('query')
                params = kwargs.get('params')
            
            cached_result = query_cache.get_query_result(query, params, ttl)
            
            if cached_result is not None:
                return cached_result
            
            # Execute query and cache result
            result = func(*args, **kwargs)
            query_cache.set_query_result(query, params, result, ttl)
            
            return result
        
        return wrapper
    return decorator

def cached_document(ttl=1800):
    """Decorator for caching document operations"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract doctype and name from arguments
            doctype = kwargs.get('doctype') or args[0] if args else None
            name = kwargs.get('name') or args[1] if len(args) > 1 else None
            
            if not doctype or not name:
                return func(*args, **kwargs)
            
            # Try cache first
            cached_doc = document_cache.get_document(doctype, name)
            
            if cached_doc is not None:
                return cached_doc
            
            # Get document and cache it
            doc = func(*args, **kwargs)
            
            if doc:
                document_cache.set_document(doc, ttl)
            
            return doc
        
        return wrapper
    return decorator

# Cache invalidation hooks
def invalidate_cache_on_document_change(doc, method):
    """Invalidate relevant caches when document changes"""
    
    doctype = doc.doctype
    name = doc.name
    
    # Invalidate document cache
    document_cache.invalidate_document(doctype, name)
    
    # Invalidate query cache for related tables
    table_name = f"tab{doctype}"
    query_cache.invalidate_table_cache(table_name)
    
    # Invalidate report cache (reports might use this data)
    report_cache.cache.clear_pattern("*")

# Register cache invalidation in hooks.py
# doc_events = {
#     "*": {
#         "on_update": "your_app.performance.caching.invalidate_cache_on_document_change",
#         "on_trash": "your_app.performance.caching.invalidate_cache_on_document_change"
#     }
# }
```

### 16.5 Background Job Optimization

**Worker Process Management**

```python
# your_app/performance/background_jobs.py - Background job optimization

import frappe
import time
import threading
from frappe.utils.background_jobs import enqueue, get_jobs
from collections import defaultdict, deque

class BackgroundJobOptimizer:
    """Optimize background job performance and monitoring"""
    
    def __init__(self):
        self.job_metrics = defaultdict(list)
        self.queue_stats = defaultdict(dict)
        self.monitoring = False
    
    def start_monitoring(self):
        """Start background job monitoring"""
        
        if self.monitoring:
            return
        
        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        
        frappe.logger().info("Background job monitoring started")
    
    def stop_monitoring(self):
        """Stop background job monitoring"""
        
        self.monitoring = False
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        
        while self.monitoring:
            try:
                # Get current job statistics
                jobs = get_jobs()
                
                for queue_name, queue_jobs in jobs.items():
                    # Update queue statistics
                    self.queue_stats[queue_name] = {
                        'job_count': len(queue_jobs),
                        'timestamp': time.time()
                    }
                
                # Sleep for monitoring interval
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                frappe.logger().error(f"Background job monitoring error: {str(e)}")
                time.sleep(30)
    
    def get_queue_statistics(self):
        """Get current queue statistics"""
        
        stats = {}
        
        for queue_name, queue_info in self.queue_stats.items():
            stats[queue_name] = {
                'current_jobs': queue_info['job_count'],
                'last_updated': queue_info['timestamp']
            }
        
        return stats
    
    def optimize_job_submission(self, method, *args, **kwargs):
        """Optimize job submission with intelligent queue selection"""
        
        # Determine optimal queue based on job characteristics
        queue = self._select_optimal_queue(method, args, kwargs)
        
        # Set appropriate timeout based on job type
        timeout = self._determine_timeout(method, args)
        
        # Set priority if supported
        priority = kwargs.pop('priority', 'normal')
        
        # Submit job with optimizations
        enqueue(
            method,
            *args,
            queue=queue,
            timeout=timeout,
            **kwargs
        )
        
        return {
            'queue': queue,
            'timeout': timeout,
            'priority': priority
        }
    
    def _select_optimal_queue(self, method, args, kwargs):
        """Select optimal queue based on job characteristics"""
        
        # Analyze job characteristics
        job_type = self._classify_job(method, args, kwargs)
        
        # Queue selection rules
        if job_type['is_heavy']:
            return 'long'
        elif job_type['is_frequent']:
            return 'short'
        elif job_type['is_priority']:
            return 'default'
        else:
            return 'default'
    
    def _classify_job(self, method, args, kwargs):
        """Classify job based on characteristics"""
        
        classification = {
            'is_heavy': False,
            'is_frequent': False,
            'is_priority': False
        }
        
        # Check method name for hints
        method_str = method if isinstance(method, str) else str(method)
        method_lower = method_str.lower()
        
        # Heavy operations
        heavy_keywords = ['generate', 'process', 'import', 'export', 'bulk', 'report']
        if any(keyword in method_lower for keyword in heavy_keywords):
            classification['is_heavy'] = True
        
        # Frequent operations
        frequent_keywords = ['sync', 'update', 'refresh', 'cleanup']
        if any(keyword in method_lower for keyword in frequent_keywords):
            classification['is_frequent'] = True
        
        # Priority operations
        priority_keywords = ['urgent', 'critical', 'immediate']
        if any(keyword in method_lower for keyword in priority_keywords):
            classification['is_priority'] = True
        
        # Check arguments for size hints
        if args and len(str(args)) > 1000:
            classification['is_heavy'] = True
        
        return classification
    
    def _determine_timeout(self, method, args):
        """Determine appropriate timeout for job"""
        
        job_type = self._classify_job(method, args, {})
        
        if job_type['is_heavy']:
            return 3600  # 1 hour
        elif job_type['is_frequent']:
            return 300   # 5 minutes
        else:
            return 1800  # 30 minutes
    
    def get_job_performance_metrics(self, hours=24):
        """Get job performance metrics"""
        
        metrics = {
            'total_jobs': 0,
            'failed_jobs': 0,
            'average_duration': 0,
            'queue_performance': {}
        }
        
        # Get job history from Frappe
        job_history = frappe.get_all('Background Job History',
            filters={
                'creation': ['>', frappe.utils.add_to_date(frappe.utils.now(), hours=-24, as_datetime=True)]
            },
            fields=['method', 'status', 'duration', 'queue', 'creation']
        )
        
        metrics['total_jobs'] = len(job_history)
        
        # Calculate metrics
        durations = []
        queue_stats = defaultdict(lambda: {'total': 0, 'failed': 0, 'durations': []})
        
        for job in job_history:
            if job.status == 'Failed':
                metrics['failed_jobs'] += 1
                queue_stats[job.queue]['failed'] += 1
            
            if job.duration:
                durations.append(job.duration)
                queue_stats[job.queue]['durations'].append(job.duration)
            
            queue_stats[job.queue]['total'] += 1
        
        # Calculate average duration
        if durations:
            metrics['average_duration'] = sum(durations) / len(durations)
        
        # Calculate queue performance
        for queue, stats in queue_stats.items():
            avg_duration = sum(stats['durations']) / len(stats['durations']) if stats['durations'] else 0
            failure_rate = (stats['failed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            
            metrics['queue_performance'][queue] = {
                'total_jobs': stats['total'],
                'failed_jobs': stats['failed'],
                'failure_rate': failure_rate,
                'average_duration': avg_duration
            }
        
        return metrics

class JobBatchProcessor:
    """Process multiple jobs efficiently in batches"""
    
    def __init__(self, batch_size=50, max_concurrent=5):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.active_batches = 0
        self.batch_semaphore = threading.Semaphore(max_concurrent)
    
    def submit_batch_jobs(self, method, job_list, **kwargs):
        """Submit multiple jobs as batches"""
        
        results = []
        
        # Split jobs into batches
        batches = [job_list[i:i + self.batch_size] for i in range(0, len(job_list), self.batch_size)]
        
        for batch in batches:
            batch_result = self._submit_batch(method, batch, **kwargs)
            results.append(batch_result)
        
        return results
    
    def _submit_batch(self, method, batch, **kwargs):
        """Submit a single batch of jobs"""
        
        with self.batch_semaphore:
            self.active_batches += 1
            
            try:
                # Modify method to handle batch
                batch_method = self._create_batch_method(method, batch)
                
                # Submit batch job
                enqueue(
                    batch_method,
                    queue='short',
                    timeout=300,
                    **kwargs
                )
                
                return {
                    'status': 'submitted',
                    'batch_size': len(batch),
                    'batch_id': frappe.generate_hash(length=10)
                }
            
            finally:
                self.active_batches -= 1
    
    def _create_batch_method(self, original_method, batch):
        """Create a method that processes a batch"""
        
        def batch_processor():
            results = []
            
            for job_args in batch:
                try:
                    if isinstance(job_args, dict):
                        result = original_method(**job_args)
                    elif isinstance(job_args, (list, tuple)):
                        result = original_method(*job_args)
                    else:
                        result = original_method(job_args)
                    
                    results.append({'status': 'success', 'result': result})
                
                except Exception as e:
                    results.append({'status': 'error', 'error': str(e)})
            
            return results
        
        return batch_processor

# Global optimizer instance
job_optimizer = BackgroundJobOptimizer()

# Optimized job submission functions
def optimized_enqueue(method, *args, **kwargs):
    """Submit job with automatic optimization"""
    
    return job_optimizer.optimize_job_submission(method, *args, **kwargs)

def enqueue_batch(method, job_list, **kwargs):
    """Submit multiple jobs as optimized batches"""
    
    processor = JobBatchProcessor()
    return processor.submit_batch_jobs(method, job_list, **kwargs)

# Performance monitoring hooks
def monitor_job_performance():
    """Monitor and log job performance"""
    
    metrics = job_optimizer.get_job_performance_metrics()
    
    # Log performance metrics
    frappe.logger().info(f"Job Performance Metrics (24h):")
    frappe.logger().info(f"  Total Jobs: {metrics['total_jobs']}")
    frappe.logger().info(f"  Failed Jobs: {metrics['failed_jobs']}")
    frappe.logger().info(f"  Average Duration: {metrics['average_duration']:.2f}s")
    
    for queue, stats in metrics['queue_performance'].items():
        frappe.logger().info(f"  Queue {queue}: {stats['total_jobs']} jobs, "
                           f"{stats['failure_rate']:.1f}% failure rate")

# Start monitoring on app load
def start_job_monitoring():
    """Start background job monitoring"""
    job_optimizer.start_monitoring()
    
    # Schedule periodic performance monitoring
    enqueue(
        'your_app.performance.background_jobs.monitor_job_performance',
        queue='short',
        repeat_every=3600  # Every hour
    )
```

### 16.6 Frontend Performance Optimization

**Client-Side Performance Strategies**

```javascript
// public/js/performance_optimizer.js - Frontend performance optimization

window.PerformanceOptimizer = {
    // Cache for frequently used data
    cache: new Map(),
    
    // Performance metrics
    metrics: {
        apiCalls: 0,
        totalResponseTime: 0,
        slowQueries: [],
        cacheHits: 0,
        cacheMisses: 0
    },
    
    // Initialize performance optimization
    init: function() {
        this.setupAPIMonitoring();
        this.setupCaching();
        this.setupLazyLoading();
        this.setupDebouncing();
        this.setupResourceOptimization();
        
        console.log('Performance Optimizer initialized');
    },
    
    // API call monitoring and optimization
    setupAPIMonitoring: function() {
        // Override frappe.call for monitoring
        const originalCall = frappe.call;
        const self = this;
        
        frappe.call = function(options) {
            const startTime = performance.now();
            
            // Add performance tracking
            self.metrics.apiCalls++;
            
            return originalCall.call(this, options)
                .then(function(response) {
                    const endTime = performance.now();
                    const duration = endTime - startTime;
                    
                    self.metrics.totalResponseTime += duration;
                    
                    // Log slow queries
                    if (duration > 1000) {
                        self.metrics.slowQueries.push({
                            method: options.method,
                            duration: duration,
                            timestamp: new Date()
                        });
                        
                        console.warn(`Slow API call: ${options.method} took ${duration.toFixed(2)}ms`);
                    }
                    
                    return response;
                })
                .catch(function(error) {
                    const endTime = performance.now();
                    const duration = endTime - startTime;
                    
                    console.error(`API call failed: ${options.method} after ${duration.toFixed(2)}ms`, error);
                    
                    throw error;
                });
        };
    },
    
    // Intelligent caching system
    setupCaching: function() {
        const self = this;
        
        // Cache wrapper for frappe.call
        window.cachedCall = function(options, cacheTTL = 300000) { // 5 minutes default TTL
            const cacheKey = self.generateCacheKey(options);
            const cached = self.cache.get(cacheKey);
            
            if (cached && (Date.now() - cached.timestamp) < cacheTTL) {
                self.metrics.cacheHits++;
                return Promise.resolve(cached.data);
            }
            
            self.metrics.cacheMisses++;
            
            return frappe.call(options).then(function(response) {
                self.cache.set(cacheKey, {
                    data: response,
                    timestamp: Date.now()
                });
                
                return response;
            });
        };
        
        // Cache cleanup
        setInterval(function() {
            self.cleanupCache();
        }, 60000); // Clean every minute
    },
    
    generateCacheKey: function(options) {
        const key = `${options.method}:${JSON.stringify(options.args || {})}`;
        return btoa(key).replace(/[^a-zA-Z0-9]/g, '');
    },
    
    cleanupCache: function() {
        const now = Date.now();
        const maxAge = 600000; // 10 minutes
        
        for (const [key, value] of this.cache.entries()) {
            if (now - value.timestamp > maxAge) {
                this.cache.delete(key);
            }
        }
    },
    
    // Lazy loading for images and components
    setupLazyLoading: function() {
        // Image lazy loading
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            document.querySelectorAll('img[data-src]').forEach(function(img) {
                imageObserver.observe(img);
            });
        }
        
        // Component lazy loading
        this.lazyComponents = new Map();
    },
    
    // Debouncing for frequent operations
    setupDebouncing: function() {
        window.debounce = function(func, wait, immediate) {
            let timeout;
            return function executedFunction() {
                const context = this;
                const args = arguments;
                const later = function() {
                    timeout = null;
                    if (!immediate) func.apply(context, args);
                };
                const callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func.apply(context, args);
            };
        };
        
        // Throttling for scroll events
        window.throttle = function(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        };
    },
    
    // Resource optimization
    setupResourceOptimization: function() {
        // Optimize form rendering
        this.optimizeFormRendering();
        
        // Optimize list view
        this.optimizeListView();
        
        // Preload critical resources
        this.preloadCriticalResources();
    },
    
    optimizeFormRendering: function() {
        // Override form refresh for optimization
        const originalRefresh = frappe.ui.form.Form.prototype.refresh;
        
        frappe.ui.form.Form.prototype.refresh = function() {
            // Debounce rapid refreshes
            if (this._refreshTimeout) {
                clearTimeout(this._refreshTimeout);
            }
            
            this._refreshTimeout = setTimeout(() => {
                originalRefresh.call(this);
                this._refreshTimeout = null;
            }, 100);
        };
    },
    
    optimizeListView: function() {
        // Virtual scrolling for large lists
        if (frappe.ui.ListView) {
            const original_render = frappe.ui.ListView.prototype.render;
            
            frappe.ui.ListView.prototype.render = function() {
                const startRender = performance.now();
                
                originalRender.call(this);
                
                const endRender = performance.now();
                console.log(`List view rendered in ${(endRender - startRender).toFixed(2)}ms`);
            };
        }
    },
    
    preloadCriticalResources: function() {
        // Preload commonly used doctypes
        const criticalDoctypes = ['User', 'Role', 'Company', 'Customer'];
        
        criticalDoctypes.forEach(function(doctype) {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = `/assets/frappe/css/doctype.css?doctype=${doctype}`;
            link.as = 'style';
            document.head.appendChild(link);
        });
    },
    
    // Performance monitoring and reporting
    getPerformanceReport: function() {
        const avgResponseTime = this.metrics.apiCalls > 0 ? 
            this.metrics.totalResponseTime / this.metrics.apiCalls : 0;
        
        const cacheHitRate = (this.metrics.cacheHits + this.metrics.cacheMisses) > 0 ?
            (this.metrics.cacheHits / (this.metrics.cacheHits + this.metrics.cacheMisses)) * 100 : 0;
        
        return {
            apiCalls: this.metrics.apiCalls,
            averageResponseTime: avgResponseTime.toFixed(2),
            slowQueries: this.metrics.slowQueries.length,
            cacheHitRate: cacheHitRate.toFixed(2),
            cacheSize: this.cache.size,
            recommendations: this.generateRecommendations(avgResponseTime, cacheHitRate)
        };
    },
    
    generateRecommendations: function(avgResponseTime, cacheHitRate) {
        const recommendations = [];
        
        if (avgResponseTime > 500) {
            recommendations.push({
                type: 'performance',
                message: 'Average API response time is high',
                suggestion: 'Consider implementing server-side caching or query optimization'
            });
        }
        
        if (cacheHitRate < 50) {
            recommendations.push({
                type: 'caching',
                message: 'Low cache hit rate',
                suggestion: 'Increase cache TTL or cache more frequently accessed data'
            });
        }
        
        if (this.metrics.slowQueries.length > 5) {
            recommendations.push({
                type: 'queries',
                message: 'Multiple slow queries detected',
                suggestion: 'Review and optimize slow API calls'
            });
        }
        
        return recommendations;
    },
    
    // Memory management
    checkMemoryUsage: function() {
        if (performance.memory) {
            const memory = performance.memory;
            const used = memory.usedJSHeapSize / 1048576; // MB
            const total = memory.totalJSHeapSize / 1048576; // MB
            
            if (used > 100) { // 100MB threshold
                console.warn(`High memory usage: ${used.toFixed(2)}MB`);
                this.cleanupCache();
            }
        }
    }
};

// Form-specific optimizations
window.FormOptimizer = {
    optimizeFormEvents: function(frm) {
        // Debounce field changes
        const originalTrigger = frm.trigger;
        
        frm.trigger = function(event, fieldname) {
            debounce(function() {
                originalTrigger.call(frm, event, fieldname);
            }, 300)();
        };
        
        // Optimize query fields
        frm.fields_dict.forEach(function(field) {
            if (field.df.fieldtype === 'Link') {
                field.get_query = debounce(field.get_query, 500);
            }
        });
    },
    
    optimizeDataLoading: function(frm) {
        // Load only necessary data
        if (frm.doc.__islocal) {
            // New document - minimal loading
            return;
        }
        
        // Check if document data is cached
        const cacheKey = `doc:${frm.doctype}:${frm.docname}`;
        const cached = PerformanceOptimizer.cache.get(cacheKey);
        
        if (cached) {
            // Use cached data
            Object.assign(frm.doc, cached.data);
            frm.refresh_fields();
            return;
        }
        
        // Cache loaded data
        PerformanceOptimizer.cache.set(cacheKey, {
            data: frm.doc,
            timestamp: Date.now()
        });
    }
};

// Initialize performance optimizer
$(document).ready(function() {
    PerformanceOptimizer.init();
    
    // Monitor memory usage periodically
    setInterval(function() {
        PerformanceOptimizer.checkMemoryUsage();
    }, 30000);
    
    // Add performance report shortcut
    window.getPerformanceReport = function() {
        console.table(PerformanceOptimizer.getPerformanceReport());
    };
});
```

## 🛠️ Practical Exercises

### Exercise 16.1: Database Performance Analysis

1. Set up query monitoring for your application
2. Identify top 10 slow queries
3. Analyze and optimize query patterns
4. Implement appropriate indexes

### Exercise 16.2: Caching Strategy Implementation

1. Implement multi-level caching for your app
2. Add intelligent cache invalidation
3. Monitor cache hit rates and performance
4. Optimize cache TTL and strategies

### Exercise 16.3: Background Job Optimization

1. Analyze current background job performance
2. Implement batch processing for bulk operations
3. Set up job monitoring and alerting
4. Optimize worker configuration

## 🤔 Thought Questions

1. How do you balance performance optimization with code complexity?
2. What are the trade-offs between different caching strategies?
3. How do you determine the right level of indexing?
4. What performance metrics are most important for your application?

## 📖 Further Reading

- [MySQL Performance Schema](https://dev.mysql.com/doc/refman/8.0/en/performance-schema.html)
- [Redis Caching Best Practices](https://redis.io/docs/manual/patterns/)
- [JavaScript Performance Optimization](https://developers.google.com/web/fundamentals/performance/)

## 🎯 Chapter Summary

Performance optimization requires systematic approach:

- **Database Analysis** identifies bottlenecks and optimization opportunities
- **Strategic Indexing** dramatically improves query performance
- **Query Optimization** with EXPLAIN reveals execution plan issues
- **Advanced Caching** reduces database load and improves response times
- **Background Job Optimization** ensures efficient task processing
- **Frontend Optimization** enhances user experience and reduces latency

---

**Next Chapter**: Building production deployment pipelines.


---

## 📌 Addendum: Production Request Timeout & Performance Tuning

### 1. Check Background Workers and Scheduler

```bash
bench doctor
```

If workers or the scheduler are down, timeout issues and stuck jobs may occur.

### 2. Increase HTTP Timeout

```bash
bench config http_timeout 600   # Timeout in seconds
```

### 3. Apply Config Changes

```bash
bench setup supervisor
bench setup nginx
sudo supervisorctl reload
sudo service nginx reload
```

### 4. Increase Gunicorn Workers

Edit `common_site_config.json`:

```json
{
  "gunicorn_workers": 5
}
```

Recommended formula: `workers = 2 * CPU cores + 1`

```bash
bench setup supervisor
sudo supervisorctl reread
sudo supervisorctl update
bench restart
```

### 5. Tune MariaDB

```bash
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
```

Under `[mysqld]`, add:

```ini
innodb_buffer_pool_size = 8G
```

RAM guidelines:
- 2 GB RAM → 512M–1G
- 4 GB RAM → 1G–2G
- 8 GB RAM → 4G–6G

```bash
sudo systemctl restart mariadb
mysql -u root -p -e "SHOW VARIABLES LIKE 'innodb_buffer_pool_size';"
```

### 6. Tune Redis

```bash
sudo nano /etc/redis/redis.conf
```

Add:

```ini
maxmemory 1gb
maxmemory-policy allkeys-lru
```

```bash
sudo systemctl restart redis
redis-cli info memory
```

### 7. Enable Slow Query Log (MariaDB)

```ini
# In /etc/mysql/mariadb.conf.d/50-server.cnf
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
```

### Performance Summary

| Component | Action |
|-----------|--------|
| Frappe | Set HTTP timeout with `bench config` |
| Supervisor/Nginx | Reload configs after changes |
| Gunicorn | Increase workers in `common_site_config.json` |
| MariaDB | Tune `innodb_buffer_pool_size` |
| Redis | Set `maxmemory` and eviction policy |

### Why Frappe Systems Freeze

Common causes of system freezes:
1. **Too many concurrent requests** — increase Gunicorn workers
2. **Slow database queries** — add indexes, tune `innodb_buffer_pool_size`
3. **Redis memory exhaustion** — set `maxmemory` with LRU eviction
4. **Background job queue overflow** — check `bench doctor`, restart workers
5. **Large file uploads** — increase Nginx `client_max_body_size`
6. **Missing indexes** — use `frappe.db.add_index()` on frequently filtered columns
7. **N+1 query problem** — use `frappe.get_all()` with explicit fields instead of looping `frappe.get_doc()`

### Frappe Report Optimization

```python
# Bad: N+1 queries
for order in frappe.get_all("Sales Order", fields=["name"]):
    doc = frappe.get_doc("Sales Order", order.name)  # N queries!
    process(doc)

# Good: Single query with all needed fields
orders = frappe.get_all(
    "Sales Order",
    fields=["name", "customer", "grand_total", "status"],
    filters={"docstatus": 1}
)
for order in orders:
    process(order)

# Good: Use Query Builder for complex aggregations
from frappe.query_builder.functions import Sum, Count
SalesOrder = frappe.qb.DocType("Sales Order")
result = (
    frappe.qb.from_(SalesOrder)
    .select(SalesOrder.customer, Sum(SalesOrder.grand_total).as_("total"))
    .where(SalesOrder.docstatus == 1)
    .groupby(SalesOrder.customer)
).run(as_dict=True)
```


---

## Addendum: Production Performance Tuning from the Field

### Quick Diagnosis Checklist

Before tuning anything, run `bench doctor` to check the health of workers and the scheduler:

```bash
bench doctor
```

Then check system resources:
```bash
htop                    # CPU and memory usage
free -m                 # RAM and swap
iostat -x 1 5           # Disk I/O
redis-cli info memory   # Redis memory
```

### Fixing Request Timeouts

```bash
# Increase HTTP timeout for long-running requests
bench config http_timeout 600

# Regenerate supervisor and nginx configs
bench setup supervisor
bench setup nginx

# Reload services (as root)
sudo supervisorctl reload
sudo service nginx reload
```

### Gunicorn Worker Tuning

The recommended formula: `workers = 2 × CPU_cores + 1`

```json
// common_site_config.json
{
    "gunicorn_workers": 5
}
```

```bash
bench setup supervisor
sudo supervisorctl reread
sudo supervisorctl update
bench restart
```

Too few workers = requests queue up and timeout. Too many = RAM exhaustion. Start with the formula and adjust based on observed memory usage.

### MariaDB Tuning

The most impactful single setting is `innodb_buffer_pool_size`. Set it to 70–80% of available RAM.

```bash
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
```

```ini
[mysqld]
# Adjust based on your RAM:
# 2 GB RAM  → 512M–1G
# 4 GB RAM  → 1G–2G
# 8 GB RAM  → 4G–6G
# 16 GB RAM → 10G–12G
innodb_buffer_pool_size = 4G

# Enable slow query log to find bottlenecks
slow_query_log = 1
long_query_time = 1
slow_query_log_file = /var/log/mysql/slow.log
```

```bash
sudo systemctl restart mariadb

# Verify
mysql -u root -p -e "SHOW VARIABLES LIKE 'innodb_buffer_pool_size';"
# Value shown in bytes: 4294967296 = 4G
```

**Find and kill stuck queries:**
```sql
SHOW FULL PROCESSLIST;
-- Look for queries in "Sending data" or "Locked" state
KILL <thread_id>;
```

**Analyze slow queries:**
```sql
-- Enable from bench console
SET GLOBAL slow_query_log = 1;
SET GLOBAL long_query_time = 1;
```

Then use `EXPLAIN` on slow queries:
```python
result = frappe.db.sql("""
    EXPLAIN SELECT name, customer FROM `tabSales Order`
    WHERE posting_date BETWEEN '2024-01-01' AND '2024-12-31'
""", as_dict=True)

for row in result:
    print(f"Type: {row.type}, Rows: {row.rows}, Extra: {row.Extra}")
# type=ALL means full table scan — add an index
# type=range or ref means index is being used — good
```

### Redis Tuning

```bash
sudo nano /etc/redis/redis.conf
```

```ini
# Set a memory cap — without this, Redis grows unbounded
maxmemory 1gb
maxmemory-policy allkeys-lru
```

```bash
sudo systemctl restart redis

# Verify
redis-cli info memory
# Look for: maxmemory, used_memory, maxmemory_policy
```

**Enable Redis caching in Frappe:**
```json
// common_site_config.json
{
    "cache": {
        "enabled": 1,
        "redis_server": "redis://localhost:6379"
    }
}
```

### Swap — The Silent Killer

A server with no swap will freeze when RAM is exhausted. Always have swap enabled.

```bash
free -m  # Check if swap is 0

# Add 2GB swap if missing
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Reduce swap aggressiveness (use RAM first)
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Why the System Freezes — Root Causes

**CPU overload:**
- Too many Gunicorn workers for available cores
- Heavy background jobs (bulk imports, large reports)
- Custom scripts with inefficient loops

Fix: Check `htop`, reduce workers, optimize custom code, use `frappe.enqueue` for heavy tasks.

**Memory exhaustion:**
- No swap configured
- Redis growing without `maxmemory` limit
- Reports loading millions of rows into Python

Fix: Add swap, set Redis `maxmemory`, add LIMIT clauses to reports.

**MariaDB locks:**
- Long-running queries locking tables
- Missing indexes causing full table scans
- Deadlocks from concurrent writes

Fix: Enable slow query log, add indexes, use `SHOW FULL PROCESSLIST` to find locks.

**Redis issues:**
- Redis down → Frappe cache misses → DB overload
- Redis memory full → eviction of important keys

Fix: Monitor with `redis-cli info`, set `maxmemory`, restart if unresponsive.

**Scheduler/worker backlog:**
- Workers crashed or not running
- Custom scheduled tasks hanging

Fix: `bench doctor`, check `logs/worker.error.log`, disable problematic scheduled tasks.

**Browser-side freezes:**
- Reports returning 100,000+ rows
- Large child tables in forms
- Stale JavaScript cache after upgrades

Fix: Add LIMIT to reports, clear browser cache, run `bench build` after upgrades.

### Slow Data Migration — The Fixture Trap

If `bench migrate` takes an unusually long time, the most common cause (90% of cases) is a fixture with a huge number of records being re-inserted on every migration.

**Diagnosis:**
```bash
# Check which doctype has excessive records
bench --site your-site console
```
```python
In [1]: frappe.db.count("Has Role")
# If this returns 250,000+ you've found the problem
```

**Quick fix:**
```python
In [1]: frappe.db.truncate("Has Role")
In [2]: frappe.db.commit()
In [3]: exit
```

```bash
bench --site your-site migrate
```

**Permanent fix — use `before_migrate` hook:**

```python
# hooks.py
before_migrate = "your_app.utils.install.before_migrate"
```

```python
# your_app/utils/install.py
def before_migrate():
    """Clean up duplicate fixture data before each migration"""
    remove_duplicate_roles()

def remove_duplicate_roles():
    """
    Frappe doesn't enforce unique constraints on user-role combinations by default.
    Fixtures re-add roles on every migration without checking for duplicates,
    causing the Has Role table to grow to hundreds of thousands of records.
    """
    frappe.db.truncate("Has Role")
    frappe.db.commit()
```

This runs automatically before every `bench migrate`, keeping the table clean.

**Why duplicates accumulate:** Fixtures assign roles to users on each migration without checking if the role is already assigned. Since there's no unique constraint on user-role combinations by default, records pile up silently over time.

### 16.7 Production Performance Troubleshooting

## Fixing Production Request Timeout & Performance Issues

This section covers common solutions for fixing **Production Request Timeout** in Frappe and improving system performance by tuning key services such as **Gunicorn**, **MariaDB**, and **Redis**.

### Check Background Workers and Scheduler

Use `bench doctor` to verify that workers and scheduler are running properly:

```bash
bench doctor
```

**Expected Output:**
```
Checking system health...
✓ Workers are running
✓ Scheduler is running
✓ Redis is running
✓ Database is running
```

If workers or the scheduler are down, timeout issues and stuck jobs may occur.

**Common Issues:**
- Workers not running: `bench start` or restart services
- Scheduler not running: Check cron jobs and scheduler logs
- Redis connection issues: Check Redis server status

### Increase HTTP Timeout

Increase the HTTP timeout for long-running requests:

```bash
bench config http_timeout 600   # Timeout in seconds
```

**When to increase timeout:**
- Large data imports/exports
- Complex report generation
- Bulk operations
- Slow external API calls

### Apply Config Changes to Supervisor and Nginx

After updating the timeout, regenerate supervisor and nginx configs:

```bash
bench setup supervisor
bench setup nginx
bench restart
```

### Optimize Gunicorn Workers

For high-traffic sites, optimize Gunicorn worker configuration:

```bash
# Edit supervisor config
sudo nano /etc/supervisor/conf.d/frappe.conf
```

**Gunicorn Configuration:**
```ini
[program:frappe-frappe]
command=/home/frappe/frappe-bench/env/bin/gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout=600 --max-requests=1000 --max-requests-jitter=100 frappe.app:application
```

**Worker Count Formula:**
```python
# Recommended workers = (2 * CPU cores) + 1
import multiprocessing
workers = (2 * multiprocessing.cpu_count()) + 1
print(f"Recommended workers: {workers}")
```

### Database Performance Tuning

**MariaDB Configuration Optimization:**

```sql
-- Edit /etc/mysql/my.cnf or MariaDB config file
[mysqld]
# Memory settings
innodb_buffer_pool_size = 2G          # 70-80% of available RAM
innodb_log_file_size = 256M           # Larger for high write workloads
innodb_log_buffer_size = 16M
innodb_flush_log_at_trx_commit = 2    # Better performance, less durability

# Connection settings
max_connections = 200                  # Increase for high concurrency
max_connect_errors = 1000
connect_timeout = 10
wait_timeout = 600
interactive_timeout = 600

# Query cache
query_cache_type = 1
query_cache_size = 256M
query_cache_limit = 2M

# Slow query logging
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# InnoDB settings
innodb_file_per_table = 1
innodb_flush_method = O_DIRECT
innodb_io_capacity = 2000
innodb_read_io_threads = 8
innodb_write_io_threads = 8
```

**Apply Changes:**
```bash
sudo systemctl restart mysql
```

### Redis Optimization

**Redis Configuration:**

```conf
# Edit /etc/redis/redis.conf
# Memory settings
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence settings
save 900 1
save 300 10
save 60 10000

# Network settings
tcp-keepalive 60
timeout 300

# Performance settings
tcp-backlog 511
databases 16

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

**Redis Monitoring:**
```bash
# Monitor Redis performance
redis-cli info memory
redis-cli info stats
redis-cli info server
```

### System Resource Monitoring

**Memory Usage Analysis:**
```bash
# Check memory usage
free -h
top

# Check Frappe process memory
ps aux | grep frappe
ps aux | grep gunicorn
ps aux | grep redis
ps aux | grep mysql
```

**CPU Usage Analysis:**
```bash
# Check CPU usage
top -p $(pgrep -d',' frappe)
htop

# Check process count
ps -ef | grep frappe | wc -l
```

**Disk I/O Analysis:**
```bash
# Check disk I/O
iostat -x 1
iotop

# Check disk space
df -h
du -sh /home/frappe/frappe-bench
```

### Common Performance Issues and Solutions

#### Issue 1: System Freezes Under Load

**Symptoms:**
- No response to HTTP requests
- High CPU usage
- Database connections timing out

**Solutions:**
```bash
# 1. Check for stuck processes
ps aux | grep frappe | grep -v grep
kill -9 <stuck-process-pid>

# 2. Restart services
bench restart

# 3. Check system resources
free -h
df -h

# 4. Increase worker timeout
bench config http_timeout 1200
bench setup supervisor
bench restart
```

#### Issue 2: Database Connection Exhaustion

**Symptoms:**
- "Too many connections" errors
- Slow query responses
- Failed background jobs

**Solutions:**
```sql
-- Increase max connections
SET GLOBAL max_connections = 500;

-- Check current connections
SHOW STATUS LIKE 'Threads_connected';
SHOW PROCESSLIST;

-- Kill long-running queries
KILL <process-id>;
```

```bash
# Restart database to clear connections
sudo systemctl restart mysql

# Optimize connection pooling in Frappe
bench config max_connections_per_user 50
```

#### Issue 3: Redis Memory Exhaustion

**Symptoms:**
- Redis out of memory errors
- Cache misses
- Slow API responses

**Solutions:**
```bash
# Check Redis memory usage
redis-cli info memory

# Clear Redis cache
redis-cli flushall

# Increase Redis memory limit
sudo nano /etc/redis/redis.conf
# Set maxmemory 1gb

# Restart Redis
sudo systemctl restart redis
```

#### Issue 4: Slow Report Generation

**Symptoms:**
- Reports taking minutes to load
- Database timeouts during report generation
- High memory usage during reports

**Solutions:**
```python
# Optimize report queries
def get_report_data(filters):
    # Use specific fields instead of *
    fields = ["name", "date", "amount", "status"]
    
    # Add appropriate indexes
    # Use EXPLAIN to analyze queries
    frappe.db.sql("EXPLAIN SELECT ...")
    
    # Implement pagination
    limit = 100
    offset = (page - 1) * limit
    
    # Use caching for expensive reports
    cache_key = f"report_data:{hash(str(filters))}"
    cached_data = frappe.cache().get(cache_key)
    
    if cached_data:
        return cached_data
    
    data = frappe.db.sql(query, as_dict=True)
    frappe.cache().set(cache_key, data, expires_in_sec=3600)
    
    return data
```

### Performance Monitoring Scripts

**Automated Health Check Script:**
```python
# health_check.py
import frappe
import time
import psutil
from datetime import datetime

def system_health_check():
    """Comprehensive system health monitoring"""
    
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Check database
    try:
        start_time = time.time()
        frappe.db.sql("SELECT 1")
        db_time = time.time() - start_time
        health_status["checks"]["database"] = {
            "status": "healthy" if db_time < 1.0 else "slow",
            "response_time": db_time
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check Redis
    try:
        start_time = time.time()
        frappe.cache().set("health_check", "test", expires_in_sec=60)
        redis_time = time.time() - start_time
        health_status["checks"]["redis"] = {
            "status": "healthy" if redis_time < 0.1 else "slow",
            "response_time": redis_time
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check system resources
    health_status["checks"]["system"] = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    # Check Frappe processes
    try:
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'frappe'], 
                              capture_output=True, text=True)
        frappe_processes = len(result.stdout.splitlines())
        health_status["checks"]["frappe_processes"] = frappe_processes
    except:
        health_status["checks"]["frappe_processes"] = "unknown"
    
    return health_status

def performance_alerts(health_status):
    """Generate performance alerts"""
    alerts = []
    
    # Database alerts
    db_status = health_status["checks"].get("database", {})
    if db_status.get("status") == "error":
        alerts.append("CRITICAL: Database connection failed")
    elif db_status.get("response_time", 0) > 2.0:
        alerts.append("WARNING: Database response time slow")
    
    # Redis alerts
    redis_status = health_status["checks"].get("redis", {})
    if redis_status.get("status") == "error":
        alerts.append("CRITICAL: Redis connection failed")
    elif redis_status.get("response_time", 0) > 0.5:
        alerts.append("WARNING: Redis response time slow")
    
    # System resource alerts
    system = health_status["checks"].get("system", {})
    if system.get("cpu_percent", 0) > 80:
        alerts.append("WARNING: High CPU usage")
    if system.get("memory_percent", 0) > 85:
        alerts.append("CRITICAL: High memory usage")
    if system.get("disk_percent", 0) > 90:
        alerts.append("CRITICAL: Low disk space")
    
    return alerts

# Schedule health check (add to crontab)
# */5 * * * * /usr/bin/python3 /path/to/health_check.py >> /var/log/frappe_health.log
```

### Performance Optimization Checklist

**Daily Monitoring:**
- [ ] Check system resource usage
- [ ] Monitor database query performance
- [ ] Review error logs
- [ ] Check background job queue
- [ ] Verify cache hit rates

**Weekly Optimization:**
- [ ] Analyze slow query logs
- [ ] Review and optimize indexes
- [ ] Check database fragmentation
- [ ] Monitor backup performance
- [ ] Review user activity patterns

**Monthly Maintenance:**
- [ ] Database maintenance (optimize, analyze)
- [ ] Review and update configuration
- [ ] Clean up old logs and temporary files
- [ ] Performance baseline updates
- [ ] Security updates and patches

---

## 🎯 **Performance Best Practices Summary**

### **Database Optimization**
- Use appropriate indexes for query patterns
- Monitor and optimize slow queries
- Configure proper connection pooling
- Regular database maintenance

### **Caching Strategy**
- Implement multi-level caching
- Use Redis for session and application cache
- Cache expensive computations
- Monitor cache hit rates

### **System Resources**
- Monitor CPU, memory, and disk usage
- Scale resources based on demand
- Implement proper resource limits
- Use load balancing for high availability

### **Application Optimization**
- Optimize Frappe queries and ORM usage
- Implement background job processing
- Use bulk operations for large datasets
- Monitor and optimize API response times

---

**💡 Pro Tip**: Performance optimization is an ongoing process. Establish baselines, monitor continuously, and optimize iteratively. Use the health check script to detect issues before they impact users.

### Adding Indexes for Common Query Patterns

```python
# In a patch file: your_app/patches/add_performance_indexes.py
import frappe

def execute():
    indexes = [
        # Sales Order — common report filters
        ("Sales Order", "idx_so_date_status", ["posting_date", "docstatus", "company"]),
        # GL Entry — accounting reports
        ("GL Entry", "idx_gle_date_account", ["posting_date", "account", "company"]),
        # Stock Ledger Entry — inventory reports
        ("Stock Ledger Entry", "idx_sle_date_item", ["posting_date", "item_code", "warehouse"]),
    ]

    for doctype, index_name, columns in indexes:
        table = f"tab{doctype}"
        col_list = ", ".join(f"`{c}`" for c in columns)

        # Check if index already exists
        existing = frappe.db.sql(f"""
            SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = '{table}'
            AND INDEX_NAME = '{index_name}'
        """)

        if not existing:
            frappe.db.sql(f"ALTER TABLE `{table}` ADD INDEX `{index_name}` ({col_list})")
            print(f"Created index {index_name} on {table}")
```

### Performance Monitoring Summary

| Component | Check Command | Key Setting |
|-----------|--------------|-------------|
| Workers/Scheduler | `bench doctor` | — |
| HTTP timeout | `bench config http_timeout 600` | 600s |
| Gunicorn workers | `common_site_config.json` | `2 × cores + 1` |
| MariaDB buffer | `SHOW VARIABLES LIKE 'innodb_buffer_pool_size'` | 70–80% RAM |
| Slow queries | `/var/log/mysql/slow.log` | `long_query_time = 1` |
| Redis memory | `redis-cli info memory` | Set `maxmemory` |
| Swap | `free -m` | Never 0 |

### After Any Configuration Change

```bash
bench setup supervisor
bench setup nginx
sudo supervisorctl reload
sudo service nginx reload
bench restart
```


---

## 📌 Addendum: Database Table Trimming and Row Size Management

### The 65KB Row Size Limit

MySQL/MariaDB has a hard limit of 65,535 bytes per row (excluding BLOBs and TEXT). This limit applies to the **maximum possible size** of a row, not actual data.

**What counts toward the limit:**
- `VARCHAR` columns (Data, Link, Select fields) — 140-142 bytes each
- `INT`, `DECIMAL`, `DATE`, `DATETIME` columns

**What does NOT count:**
- `TEXT` columns (Small Text, Text, Long Text) — only 10 bytes in-row (pointer)
- `LONGTEXT` columns — 12 bytes in-row

**Field type impact:**

| Frappe Field | MySQL Type | In-Row Bytes |
|---|---|---|
| Data, Link, Select | VARCHAR(140) | 140-142 |
| Text, Small Text | TEXT | 10 |
| Long Text | LONGTEXT | 12 |
| Int | INT | 4 |
| Currency, Float | DECIMAL | ~8 |

**The paradox:** Text fields "take more disk space" but save row size. Use `Data` for short indexed fields; use `Text` for descriptions and notes.

### What Are Orphan Columns?

When you delete a Custom Field in Frappe:
- ✅ The Custom Field record is deleted
- ✅ The field disappears from the form
- ❌ The database column is **NOT dropped** (safety measure)

These leftover columns are "orphan fields." They waste row size and can eventually cause the "Row size too large" error.

### `bench trim-tables`

```bash
# Preview what will be removed (dry run — always do this first)
bench --site mysite trim-tables --dry-run

# Execute trimming (creates backup automatically)
bench --site mysite trim-tables

# Skip backup (not recommended)
bench --site mysite trim-tables --no-backup

# JSON output
bench --site mysite trim-tables --dry-run --format json
```

### Python API

```python
from frappe.model.meta import trim_table, trim_tables

# Check orphans for one DocType
orphans = trim_table("Customer", dry_run=True)
print(f"Orphan columns: {orphans}")

# Remove orphans
trim_table("Customer", dry_run=False)

# Trim all tables
result = trim_tables(dry_run=False)

# Check row size
row_size = frappe.db.get_row_size("Customer")
print(f"Row size: {row_size} / 65535 bytes")

# Check utilization %
from frappe.core.doctype.doctype.doctype import get_row_size_utilization
pct = get_row_size_utilization("Customer")
print(f"Row size utilization: {pct}%")
```

### Via Customize Form

Go to **Customize Form** → select DocType → **Actions** → **Trim Table**. Shows a warning with the list of columns to be dropped, then executes on confirmation.

### Solutions When Row Size Is Too Large

**Option 1: Change Data fields to Text (saves 130+ bytes per field)**

```python
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

make_property_setter("Customer", "description", "fieldtype", "Text", "Data")
frappe.db.sql("ALTER TABLE `tabCustomer` MODIFY `description` TEXT")
```

**Option 2: Remove unused custom fields**

```python
# Find custom fields with no data
for cf in frappe.get_all("Custom Field", filters={"dt": "Customer"}, fields=["fieldname", "label"]):
    count = frappe.db.count("Customer", {cf.fieldname: ["is", "set"]})
    if count == 0:
        print(f"Unused: {cf.fieldname} ({cf.label})")
```

**Option 3: Trim orphan columns** (see above)

**Option 4: Split the DocType** — move groups of fields to a linked child DocType or separate DocType.

### Safe Trimming Workflow

```python
# 1. Check what will be removed
orphans = trim_table("Customer", dry_run=True)

# 2. Check if orphans have data
for field in orphans:
    count = frappe.db.count("Customer", {field: ["is", "set"]})
    print(f"{field}: {count} records with data")

# 3. Back up data if needed
# 4. Trim
trim_table("Customer", dry_run=False)

# 5. Verify
new_size = frappe.db.get_row_size("Customer")
print(f"New row size: {new_size} bytes")
```

### Monthly Maintenance Script

```bash
#!/bin/bash
SITE="mysite.local"

# Backup first
bench --site $SITE backup --with-files

# Preview
bench --site $SITE trim-tables --dry-run

# Execute
bench --site $SITE trim-tables
```
