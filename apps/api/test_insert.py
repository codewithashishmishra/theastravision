import clickhouse_connect, uuid, json, datetime
client = clickhouse_connect.get_client(host='localhost', port=8123)
data = [[uuid.uuid4(), 'login', None, None, None, None, 'auth', 'auth.session.password', 'INFO', 'auth', 'Login via password', None, json.dumps({}), datetime.datetime.now()]]
COLUMNS = ['id', 'log_type', 'tenant_id', 'tenant_name', 'user_id', 'user_email', 'module', 'action', 'level', 'service', 'message', 'ip_address', 'metadata', 'created_at']
try:
    client.insert('platform_logs', data, column_names=COLUMNS)
except Exception as e:
    print("CLICKHOUSE ERROR:", e)
    print("ERR DICT:", getattr(e, '__dict__', {}))
