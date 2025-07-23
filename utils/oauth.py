import requests

def get_access_token(client_id, client_secret, code, redirect_uri="https://web-scheduler.streamlit.app"):
    url = "https://public-api.wordpress.com/oauth2/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code": code
    }

    response = requests.post(url, data=data)

    if response.status_code == 200:
        return {
            "success": True,
            "access_token": response.json().get("access_token")
        }
    else:
        return {
            "success": False,
            "error": response.text
        }