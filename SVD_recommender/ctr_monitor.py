import requests

POSTHOG_API_URL = "https://us.posthog.com/api/projects/159877/query"
POSTHOG_API_KEY = "phx_ohDz76fmSS6TbYHXtfMWMJSWayhhOtl8h2PWWhxMRHb8XYR"

def get_ctr_last_7_days():
    headers = {
        "Authorization": f"Bearer {POSTHOG_API_KEY}",
        "Content-Type": "application/json"
    }

    # Read SQL or HogQL from file
    with open("ctr_query.sql", "r") as file:
        sql_query = file.read()

    # Use "HogQL" if your query uses PostHog's query language; otherwise, use "SQL"
    payload = {
        "query": {
            "kind": "HogQLQuery",
            "query": sql_query
        }
    }


    print("[DEBUG] Sending SQL query to PostHog API...")
    response = requests.post(POSTHOG_API_URL, headers=headers, json=payload)

    print(f"[DEBUG] Status Code: {response.status_code}")
    print(f"[DEBUG] Response Text (first 300 chars):\n{response.text[:300]}")

    if response.status_code == 200:
        try:
            result = response.json()
            rows = result.get("results", [])  # "results" is the correct field
            if rows:
                ctr = rows[-1][2]  # Adjust index based on your actual result
                return float(ctr)
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
    else:
        print("Failed to fetch CTR:", response.status_code, response.text)

    return None
