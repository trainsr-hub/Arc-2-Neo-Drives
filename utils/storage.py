# utils/storage.py

import pymongo
import streamlit as st

# Kết nối tới MongoDB (Sử dụng Secrets để bảo mật Connection String)
def get_db_collection():
    try:
        # Link connection string sẽ được cấu hình trên Streamlit Cloud Secrets
        client = pymongo.MongoClient(st.secrets["mongo"]["uri"])
        db = client[st.secrets["mongo"]["db_name"]]
        return db["vault_collection"]
    except Exception as e:
        st.error(f"Không thể kết nối tới MongoDB: {e}")
        return None

def load_data():
    """Tải dữ liệu từ MongoDB."""
    collection = get_db_collection()
    if collection is not None:
        # Tìm document của user (giả sử dùng một ID cố định cho cá nhân bạn)
        doc = collection.find_one({"user_id": "main_user"})
        if doc:
            return doc.get("vault", [])
    return []

def save_data(data):
    """Lưu/Ghi đè dữ liệu vào MongoDB."""
    collection = get_db_collection()
    if collection is not None:
        # upsert=True: Nếu chưa có thì tạo mới, có rồi thì ghi đè
        collection.update_one(
            {"user_id": "main_user"},
            {"$set": {"vault": data}},
            upsert=True
        )

def clear_all_data():
    """Xóa trắng dữ liệu của user trong DB."""
    collection = get_db_collection()
    if collection is not None:
        collection.update_one({"user_id": "main_user"}, {"$set": {"vault": []}})