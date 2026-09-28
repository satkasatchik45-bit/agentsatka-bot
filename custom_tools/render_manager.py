import requests
import json

RENDER_API_KEY = "rnd_ZozposSR5tia9ixipdEY0UcjKy1b"

def render_manager(action: str, **kwargs):
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {RENDER_API_KEY}"
    }
    base_url = "https://api.render.com/v1"
    
    if action == "get_owner":
        res = requests.get(f"{base_url}/owners", headers=headers)
        return res.json()
    elif action == "list_services":
        res = requests.get(f"{base_url}/services", headers=headers)
        return res.json()
    elif action == "get_service":
        service_id = kwargs.get("service_id")
        res = requests.get(f"{base_url}/services/{service_id}", headers=headers)
        return res.json()
    elif action == "trigger_deploy":
        service_id = kwargs.get("service_id")
        res = requests.post(f"{base_url}/services/{service_id}/deploys", headers=headers)
        return res.json()
    elif action == "create_service":
        # expects payload in kwargs
        payload = kwargs.get("payload")
        res = requests.post(f"{base_url}/services", headers=headers, json=payload)
        return res.json()
    else:
        return {"error": f"Noma'lum amal: {action}"}
