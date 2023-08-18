import os
import requests
from datetime import datetime
import pytz


NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('DATABASE_ID')
TIMEZONE = pytz.timezone('Europe/Paris')  # TOOD: remove hardcoded timezone

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def create_row(name, amount_detected):
    create_url = "https://api.notion.com/v1/pages"
    time_now = datetime.now(TIMEZONE).isoformat()
    data = {
        "Name": {"title": [{"text": {"content": name}}]},
        "Last updated": {"date": {"start": time_now, "end": None}},
        "Got it": {"checkbox": True if amount_detected > 0 else False},
        'Amount': {'number': amount_detected},
    }
    payload = {"parent": {"database_id": DATABASE_ID}, "properties": data}
    res = requests.post(create_url, headers=headers, json=payload)
    return res


def update_row(row_id: str, amount_detected: int):
    url = f"https://api.notion.com/v1/pages/{row_id}"
    time_now = datetime.now(TIMEZONE).isoformat()
    payload = {"properties": {
        "Last updated": {"date": {"start": time_now, "end": None}},
        "Got it": {"checkbox": True if amount_detected > 0 else False},
        'Amount': {'number': amount_detected},
    }}

    res = requests.patch(url, json=payload, headers=headers)
    return res


def get_rows(num_rows=None):
    """
    If num_rows is None, get all pages, otherwise just the defined number.
    """
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    get_all = num_rows is None
    page_size = 100 if get_all else num_rows

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()

    results = data["results"]
    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])

    return results


def smart_update_notion(detected_labels_counter, undetected_labels):
    rows = get_rows()
    name_to_row_id = {
        page["properties"]["Name"]["title"][0]["text"]["content"]: page["id"] for page in rows}
    updated_names = []
    for name, count in detected_labels_counter.items():
        if name in name_to_row_id:
            update_row(name_to_row_id[name], count)
        else:
            create_row(name, count)
        updated_names.append(name)
    for name in undetected_labels:
        if name in name_to_row_id:
            update_row(name_to_row_id[name], 0)
        else:
            create_row(name, 0)
        updated_names.append(name)
    for name, row_id in name_to_row_id.items():
        if name not in updated_names and name not in detected_labels_counter:
            update_row(row_id, 0)
