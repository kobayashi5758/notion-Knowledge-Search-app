import streamlit as st
import requests
from groq import Groq

# APIキーの設定
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
PAGE_ID = "36cf18f0e7a480a8a4d6e4c6326b7b52"

groq_client = Groq(api_key=GROQ_API_KEY)

# Notionページからデータ取得
def get_notion_data():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    url = f"https://api.notion.com/v1/blocks/{PAGE_ID}/children"
    response = requests.get(url, headers=headers)
    results = response.json().get("results", [])
    items = []
    for block in results:
        if block["type"] == "synced_block":
            url2 = f"https://api.notion.com/v1/blocks/{block['id']}/children"
            response2 = requests.get(url2, headers=headers)
            children = response2.json().get("results", [])
            for child in children:
                if child["type"] == "bulleted_list_item":
                    rich_text = child["bulleted_list_item"].get("rich_text", [])
                    title = rich_text[0]["plain_text"] if rich_text else ""
                    url3 = f"https://api.notion.com/v1/blocks/{child['id']}/children"
                    response3 = requests.get(url3, headers=headers)
                    grandchildren = response3.json().get("results", [])
                    pdf_url = ""
                    for gc in grandchildren:
                        if gc["type"] == "file":
                            pdf_url = gc["file"]["file"]["url"]
                    if title:
                        # タイトルとURLを別々に保存
                        items.append({"title": title, "url": pdf_url})
    return items

def ask_groq(items, question):
    # Groqには機種名だけ送る
    context = "\n".join([f"・{item['title']}" for item in items])
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"以下の機種一覧をもとに質問に答えてください。該当する機種名のみ答えてください。\n\n{context}"},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

# 画面
st.title("Notion AI検索アプリ")
st.write("Notionのデータをもとに質問に答えます")

question = st.text_input("質問を入力してください")

if st.button("回答を取得"):
    with st.spinner("回答を生成中..."):
        items = get_notion_data()
        answer = ask_groq(items, question)
        st.write("【AIの回答】")
        st.write(answer)
        # 該当機種のURLを表示
        for item in items:
            if item["title"] in answer:
                st.write(f"📄 {item['title']}のPDF")
                st.write(item["url"])