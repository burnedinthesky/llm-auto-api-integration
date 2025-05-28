import os
import http.client
import json


def notion_create_page_in_database_API_runner(
    token: str,
    database_id: str,
    page_title: str
) -> dict:
    """
    在指定的 Notion Database 底下創建一個新頁面。

    參數:
        token (str):       Notion Integration 的 Bearer Token，通常以 "secret_" 開頭。
        database_id (str): 目標 Database 的 UUID（帶 '-' 的格式）。
        page_title (str):  新頁面的標題文字。

    回傳值:
        dict:  Notion API 回傳的 JSON 解析結果，包含新頁面的詳細資料。
    """
    host = "api.notion.com"
    path = "/v1/pages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # payload 指定 parent 為 database，並設定 title
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            # 假設你的 Database schema 第一欄是「Title」
            "Title": {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": page_title}
                    }
                ]
            }
        }
    }

    conn = http.client.HTTPSConnection(host)
    conn.request("POST", path, body=json.dumps(payload), headers=headers)
    response = conn.getresponse()
    resp_data = response.read().decode("utf-8")
    conn.close()

    return json.loads(resp_data)


if __name__ == "__main__":
    # 從環境變數讀取
    NOTION_TOKEN = "secret_123"
    NOTION_DATABASE_ID = "1fff918a-e5ea-8062-a5a0-e2378e610e24"

    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        raise RuntimeError(
            "請先設定環境變數 NOTION_TOKEN 與 NOTION_DATABASE_ID"
        )

    # 範例：在你的 Database 底下創建一個新頁面
    result = notion_create_page_in_database_API_runner(
        token=NOTION_TOKEN,
        database_id=NOTION_DATABASE_ID,
        page_title="我的 API 新頁面"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
