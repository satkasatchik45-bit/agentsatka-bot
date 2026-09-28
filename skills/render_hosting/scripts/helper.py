import requests

def test_render_connection(api_key):
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    r = requests.get("https://api.render.com/v1/owners", headers=headers)
    return r.status_code == 200
