# app.py
import streamlit as st
import drive_module.drive_ops as drive_ops  

# CHÚ THÍCH CẬP NHẬT: Thực hiện import phân rã các file tab độc lập từ package app_packages
import app_packages.tab_1 as tab_1
import app_packages.tab_2 as tab_2
import app_packages.tab_3 as tab_3

# --- CẤU HÌNH TRANG STREAMLIT ---
st.set_page_config(page_title="GDrive Folder Cloner & Description Manager", layout="wide")
st.title("📂 Google Drive Tool - Clone & Description Manager")

# --- KHỞI TẠO CÁC BIẾN TRONG STREAMLIT SESSION STATE ---
if "subfolders_list" not in st.session_state:
    st.session_state.subfolders_list = []
if "selected_root_id" not in st.session_state:
    st.session_state.selected_root_id = None
if "parent_link_cached" not in st.session_state:
    st.session_state.parent_link_cached = ""

# --- PHẦN GIAO DIỆN CHUNG TRÊN SIDEBAR ---
st.sidebar.header("⚙️ Cấu hình kết nối GDrive")
folder_link_input = st.sidebar.text_input("🔗 Nhập link thư mục Google Drive (Working Folder):")

# Xử lý tự động khi người dùng nhập link mới hoặc thay đổi link
if folder_link_input and folder_link_input != st.session_state.parent_link_cached:
    root_id = drive_ops.extract_folder_id_from_url(folder_link_input)
    
    if root_id:
        with st.sidebar:
            with st.spinner("Đang quét danh sách subfolders cấp 1..."):
                all_contents = drive_ops.list_folder_contents(root_id)
                # Lọc ra chỉ lấy các subfolder cấp 1
                subs = [item for item in all_contents if item.get("mimeType") == "application/vnd.google-apps.folder"]
                
                # Lưu thông tin vào session state để dùng chung giữa các tab
                st.session_state.subfolders_list = subs
                st.session_state.selected_root_id = root_id
                st.session_state.parent_link_cached = folder_link_input
    else:
        st.sidebar.warning("❌ Link không hợp lệ. Link phải có dạng chứa /folders/<ID>")

# Hiển thị Selector dùng chung nếu tìm thấy dữ liệu subfolder
selected_subfolder_id = None
selected_subfolder_name = ""

if st.session_state.subfolders_list:
    options = {f["name"]: f["id"] for f in st.session_state.subfolders_list}
    choice = st.sidebar.selectbox("📂 Chọn 1 Subfolder để xử lý:", list(options.keys()))
    selected_subfolder_id = options[choice]
    selected_subfolder_name = choice
else:
    st.sidebar.info("Vui lòng nhập link folder cha hợp lệ để hiển thị danh sách subfolder.")

# --- CHIA TABS GIAO DIỆN ---
tab1, tab2, tab3 = st.tabs(["📂 Tab 1 - Folder Template", "📝 Tab 2 - Folder Description", "📊 Tab 3 - Export JSON Tree"])

# CHÚ THÍCH CẬP NHẬT: Gọi trực tiếp các hàm giao diện từ file module tab riêng lẻ
with tab1:
    tab_1.render_tab1(
        selected_subfolder_id=selected_subfolder_id, 
        selected_subfolder_name=selected_subfolder_name, 
        selected_root_id=st.session_state.selected_root_id
    )

with tab2:
    tab_2.render_tab2(
        selected_subfolder_id=selected_subfolder_id, 
        selected_subfolder_name=selected_subfolder_name
    )

with tab3:
    tab_3.render_tab3(
        selected_subfolder_id=selected_subfolder_id, 
        selected_subfolder_name=selected_subfolder_name
    )