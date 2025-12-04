import requests

def post_to_wordpress(title, content, tags, publish_date, access_token, site_url):
    endpoint = f"https://public-api.wordpress.com/rest/v1.1/sites/{site_url}/posts/new"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "title": title,
        "content": content,
        "tags": tags,
        "date": publish_date,
        "status": "future"
    }

    try:
        if not access_token:
            return {
                "success": False,
                "error": "Access token tidak diberikan.",
                "status_code": None,
            }
        response = requests.post(endpoint, headers=headers, data=data)
        status_code = response.status_code
        try:
            resp_json = response.json()
        except Exception:
            resp_json = None

        # Treat 200 and 201 as success responses (some WP endpoints return 200)
        if status_code in (200, 201):
            return {
                "success": True,
                "status": "terjadwal",
                "url": resp_json.get("URL", "") if isinstance(resp_json, dict) else "",
                "status_code": status_code,
                "detail": resp_json,
            }

        # Authentication errors
        if status_code in (401, 403):
            err_msg = f"Autentikasi gagal (HTTP {status_code}). Periksa Access Token atau Client credentials."
            # try to append any message from the response
            if isinstance(resp_json, dict) and resp_json.get("message"):
                err_msg += f" Detail: {resp_json.get('message')}"
            return {
                "success": False,
                "error": err_msg,
                "status_code": status_code,
                "detail": resp_json or response.text,
            }

        # Other errors: include as much detail as possible
        # Build a concise error message and keep full detail in `detail`.
        if isinstance(resp_json, dict):
            err_detail_msg = resp_json.get("message") or resp_json.get("error") or resp_json.get("code")
            if not err_detail_msg:
                err_detail_msg = str(resp_json)
        else:
            err_detail_msg = response.text

        # Truncate long messages to keep UI readable
        err_summary = str(err_detail_msg)
        if len(err_summary) > 400:
            err_summary = err_summary[:400] + "... (truncated)"

        return {
            "success": False,
            "error": f"HTTP {status_code}: {err_summary}",
            "status_code": status_code,
            "detail": resp_json or response.text,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": None,
            "detail": None,
        }
