import requests, uuid, datetime, json
url = "http://localhost:8123/"
query = "INSERT INTO platform_logs FORMAT JSONEachRow"
row = {
    "id": str(uuid.uuid4()),
    "log_type": "login",
    "tenant_id": str(uuid.UUID(int=0)),
    "tenant_name": None,
    "user_id": None,
    "user_email": None,
    "module": "auth",
    "action": "auth.session",
    "level": "INFO",
    "service": "auth",
    "message": "test",
    "ip_address": None,
    "metadata": "{}",
    "created_at": datetime.datetime.now().isoformat()
}
resp = requests.post(url, params={"query": query}, data=json.dumps(row))
print("STATUS:", resp.status_code)
print("BODY:", resp.text)
