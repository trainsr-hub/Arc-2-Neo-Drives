# app.py
import streamlit as st
import drive_module.drive_ops as drive_ops  
import utils.storage as storage  # Import module lưu trữ gốc của bạn

# --- CẤU HÌNH TRANG STREAMLIT ---
st.set_page_config(page_title="GDrive Folder Cloner & Description Manager", layout="wide")
st.title("📂 Google Drive Tool - Clone & Description Manager")

# --- HÀM ĐỆ QUY SAO CHÉP CẤU TRÚC (TAB 1) ---
def clone_folder_structure_templated(source_id, target_parent_id, log_area, collected_metadata, is_root=False):
    """
    Hàm đệ quy quét cấu trúc cây thư mục gốc và tạo bản sao trống tương ứng.
    Sử dụng trực tiếp đối tượng drive_service và hàm từ drive_module.drive_ops.
    """
    try:
        # 1. Lấy thông tin chi tiết (bao gồm cả Description) của folder hiện tại
        folder_meta = drive_ops.get_file_metadata(source_id)
        folder_name = folder_meta.get('name', 'Thư mục không tên')
        folder_desc = folder_meta.get('description', '') or ''

        # Chỉ đổi tên duy nhất Subfolder được chọn ban đầu (Root của bản copy)
        if is_root:
            folder_name = f"Z ~ {folder_name}"

        # Trích xuất cặp dữ liệu Key: Value từ Description và tích lũy vào bộ nhớ tạm RAM
        if folder_desc:
            for line in folder_desc.splitlines():
                if ":" in line:
                    key_part, val_part = line.split(":", 1)
                    key_clean = key_part.strip()
                    values = [v.strip() for v in val_part.split(",") if v.strip()]
                    
                    if key_clean:
                        if key_clean not in collected_metadata:
                            collected_metadata[key_clean] = []
                        # Gom góp các value độc bản vào dict tạm
                        for val in values:
                            if val not in collected_metadata[key_clean]:
                                collected_metadata[key_clean].append(val)

        # 2. Tạo một folder trống mới tại thư mục đích sử dụng Drive Service instance từ module
        new_folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [target_parent_id],
            'description': folder_desc
        }
        cloned_folder = drive_ops.drive_service.files().create(
            body=new_folder_metadata, 
            fields='id'
        ).execute()
        cloned_id = cloned_folder.get('id')
        
        # In hành động trực tiếp ra ngoài giao diện
        log_area.code(f"[ Đã sao chép ] Thư mục: {folder_name} | Mô tả: '{folder_desc}'")

        # 3. Tìm các thư mục con trực tiếp bằng hàm có sẵn của bạn
        sub_items = drive_ops.list_folder_contents(source_id)

        # Duyệt qua các item, nếu là folder thì đệ quy sâu xuống tiếp
        for item in sub_items:
            if item.get("mimeType") == "application/vnd.google-apps.folder":
                # Các thư mục con cấp dưới truyền vào is_root=False
                clone_folder_structure_templated(item['id'], cloned_id, log_area, collected_metadata, is_root=False)
            
    except Exception as e:
        log_area.error(f"❌ Lỗi trong quá trình clone Folder ID {source_id}: {e}")

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
tab1, tab2 = st.tabs(["📂 Tab 1 - Folder Template", "📝 Tab 2 - Folder Description"])

# =========================================================================
# XỬ LÝ CHI TIẾT TAB 1
# =========================================================================
with tab1:
    st.subheader("⚠️ Sao chép cấu trúc hình cây (Chỉ sao chép thư mục trống)")
    
    if not selected_subfolder_id:
        st.info("💡 Hãy nhập link thư mục cha ở thanh Sidebar và chọn một Subfolder để bắt đầu.")
    else:
        st.markdown(f"""
        * **Thư mục chọn nhân bản:** `{selected_subfolder_name}`
        * **ID Thư mục:** `{selected_subfolder_id}`
        * **Vị trí lưu bản sao:** Sẽ được tạo mới ngay bên trong thư mục gốc (cùng cấp với thư mục `{selected_subfolder_name}` hiện tại).
        """)
        
        # Nút bấm kích hoạt tiến trình nhân bản cấu trúc
        if st.button("🚀 Bắt đầu nhân bản cấu trúc (Clone Tree)", type="primary"):
            st.info("🔄 Đang thiết lập kết nối và tiến hành quét đệ quy...")
            
            # Khởi tạo vùng hiển thị tiến độ thời gian thực
            log_monitor = st.empty()
            
            # Thư mục đích chính là thư mục gốc của link nhập vào để đảm bảo "lưu cùng path với bản chính"
            destination_parent_id = st.session_state.selected_root_id
            
            # Khởi tạo dict trống để tích lũy dữ liệu thu thập được từ tất cả các folder con trong RAM
            collected_metadata = {}
            
            with st.spinner("Đang clone cấu trúc cây thư mục..."):
                clone_folder_structure_templated(
                    source_id=selected_subfolder_id, 
                    target_parent_id=destination_parent_id, 
                    log_area=log_monitor,
                    collected_metadata=collected_metadata,
                    is_root=True
                )
            
            # Gộp dữ liệu thu thập được và đẩy lên MongoDB thông qua module gốc storage.py (1 LẦN DUY NHẤT)
            if collected_metadata:
                with st.spinner("Đang đồng bộ và mở rộng bể dữ liệu gợi ý lên MongoDB..."):
                    try:
                        # Gọi hàm load_data() gốc của bạn (trả về list từ trường vault)
                        vault_data = storage.load_data()
                        
                        # Lấy dict pool từ phần tử đầu tiên nếu có, nếu không thì khởi tạo dict trống
                        current_pool = vault_data[0] if (vault_data and isinstance(vault_data[0], dict)) else {}
                        
                        is_updated = False
                        for k, v_list in collected_metadata.items():
                            if k not in current_pool or not isinstance(current_pool[k], list):
                                current_pool[k] = []
                                is_updated = True
                            for v in v_list:
                                if v not in current_pool[k]:
                                    current_pool[k].append(v)
                                    is_updated = True
                                    
                        if is_updated:
                            # Bọc dict thành một list phần tử duy nhất để truyền đúng cấu trúc vào hàm save_data(data) gốc của bạn
                            storage.save_data([current_pool])
                            st.toast("✨ Đã đồng bộ thành công dữ liệu metadata mới lên MongoDB!", icon="💾")
                    except Exception as db_err:
                        st.error(f"❌ Không thể đồng bộ dữ liệu lên MongoDB: {db_err}")
                
            st.success(f"🎉 Đã hoàn thành sao chép hoàn toàn cấu trúc trống của thư mục 'Z ~ {selected_subfolder_name}'!")

# =========================================================================
# XỬ LÝ CHI TIẾT TAB 2 - MỚI: BÓC TÁCH & CẬP NHẬT DESCRIPTION KHÔNG GÂY ĐÈ NỘI DUNG RÁC
# =========================================================================
with tab2:
    st.subheader("📝 Quản lý Key-Value từ Description của Thư mục")
    
    if not selected_subfolder_id:
        st.info("💡 Hãy điền link folder ở sidebar và chọn một Subfolder để cấu hình Tab 2.")
    else:
        st.markdown(f"### Đang xử lý Description cho: `{selected_subfolder_name}`")
        
        # Gọi hàm load_data() gốc của bạn và chuyển đổi cấu trúc list -> dict để hiển thị options gợi ý
        suggest_dict = {}
        with st.spinner("Đang kết nối tải dữ liệu gợi ý từ MongoDB..."):
            try:
                vault_data = storage.load_data()
                suggest_dict = vault_data[0] if (vault_data and isinstance(vault_data[0], dict)) else {}
                
                if suggest_dict:
                    st.success("✅ Đã tải dữ liệu danh sách Options gợi ý từ MongoDB thành công!")
                else:
                    st.info("ℹ️ Bể dữ liệu trên MongoDB trống hoặc chưa có dữ liệu thuộc tính dạng Key:Value.")
            except Exception as e:
                st.error(f"❌ Thất bại khi lấy dữ liệu gợi ý từ MongoDB: {e}")
        
        # 2. Lấy thông tin Description hiện tại của Subfolder được chọn
        try:
            folder_meta = drive_ops.get_file_metadata(selected_subfolder_id)
            current_desc = folder_meta.get("description", "") or ""
        except Exception as e:
            st.error(f"❌ Không thể lấy metadata của folder hiện tại: {e}")
            current_desc = ""
        
        # Hiển thị text gốc để kiểm tra
        with st.expander("🔍 Xem chuỗi Description gốc hiện tại trên Google Drive"):
            st.text(current_desc if current_desc else "[Trống]")
            
        # 3. Phân tích chuỗi Description thành cấu trúc dòng
        lines = current_desc.splitlines()
        updated_values = {}
        
        # --- CHÚ THÍCH CẬP NHẬT: THÀNH PHẦN GIAO DIỆN MỚI - THÊM THUỘC TÍNH (KEY) MỚI VÀO CUỐI DESCRIPTION ---
        st.markdown("---")
        st.markdown("#### ➕ Thêm thuộc tính mới vào Description của thư mục")
        
        # Trích xuất danh sách các Key hiện đang có sẵn trong Description hiện tại
        existing_keysInDesc = [line.split(":", 1)[0].strip() for line in lines if ":" in line]
        # Lọc ra danh sách các Key có trên hệ thống MongoDB nhưng chưa được gán cho thư mục này
        available_db_keys = [k for k in suggest_dict.keys() if k not in existing_keysInDesc]
        
        col1, col2 = st.columns([2, 1])
        with col1:
            add_key_option = st.selectbox(
                "💡 Chọn thuộc tính từ hệ thống hoặc nhập mới:",
                options=["-- Chọn thuộc tính đã có --"] + available_db_keys + ["✍️ Tự nhập thuộc tính mới hoàn toàn..."],
                key=f"add_key_select_{selected_subfolder_id}"
            )
            
            custom_new_key = ""
            if add_key_option == "✍️ Tự nhập thuộc tính mới hoàn toàn...":
                custom_new_key = st.text_input(
                    "✏️ Nhập tên thuộc tính tùy chỉnh mới của bạn:", 
                    key=f"custom_key_input_{selected_subfolder_id}"
                ).strip()
                
        with col2:
            # Tạo khoảng trống bằng CSS để nút bấm thẳng hàng với ô input bên cạnh
            st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 Xác nhận thêm thuộc tính", key=f"btn_add_key_{selected_subfolder_id}", type="secondary", use_container_width=True):
                # Quyết định lấy Key từ selectbox hay từ text_input tự gõ
                target_new_key = custom_new_key if add_key_option == "✍️ Tự nhập thuộc tính mới hoàn toàn..." else add_key_option
                
                if target_new_key and target_new_key != "-- Chọn thuộc tính đã có --":
                    # Xử lý nối chuỗi rỗng: Nếu description đang có chữ thì xuống dòng, nếu trống thì ghi thẳng
                    if current_desc.strip():
                        appended_desc = f"{current_desc.strip()}\n{target_new_key}: "
                    else:
                        appended_desc = f"{target_new_key}: "
                        
                    with st.spinner("Đang tạo dòng thuộc tính trống lên Google Drive..."):
                        try:
                            drive_ops.drive_service.files().update(
                                fileId=selected_subfolder_id,
                                body={"description": appended_desc}
                            ).execute()
                            st.toast(f"🎉 Đã thêm thuộc tính '{target_new_key}' thành công!", icon="✅")
                            st.rerun() # Re-render lại để hệ thống splitlines bắt được dòng mới này
                        except Exception as err:
                            st.error(f"❌ Không thể thêm thuộc tính mới lên Drive: {err}")
                else:
                    st.warning("⚠️ Vui lòng điền thông tin hoặc lựa chọn thuộc tính hợp lệ trước khi nhấn!")
        # --- KẾT THÚC ĐOẠN PHẦN THÊM THUỘC TÍNH MỚI ---

        st.markdown("---")
        st.markdown("#### 🛠️ Các thuộc tính Key-Value phát hiện được:")
        
        has_kv = False
        # Duyệt qua từng dòng để dựng giao diện Multi-select tương ứng
        for index, line in enumerate(lines):
            if ":" in line:
                has_kv = True
                key_part, val_part = line.split(":", 1)
                key_clean = key_part.strip()
                
                # Cắt nhỏ các value hiện tại bằng dấu "," làm default value
                default_values = [v.strip() for v in val_part.split(",") if v.strip()]
                
                # Kiểm tra tính hợp lệ của dữ liệu gợi ý từ JSON DB để tránh lỗi giao diện
                suggested_options = suggest_dict.get(key_clean, [])
                if not isinstance(suggested_options, list):
                    suggested_options = [str(suggested_options)]
                
                # Gộp default_values vào suggested_options và xóa trùng để tránh lỗi giao diện Streamlit khi option không chứa default
                final_options = list(default_values)
                for opt in suggested_options:
                    if opt not in final_options:
                        final_options.append(opt)
                        
                # Hiển thị Multi-select cho dòng key hiện tại
                selected_opts = st.multiselect(
                    label=f"🔑 Thuộc tính: **{key_clean}** (Dòng {index + 1})",
                    options=final_options,
                    default=default_values,
                    key=f"kv_{selected_subfolder_id}_{index}_{key_clean}"
                )
                # Lưu kết quả thay đổi của dòng này vào dict tạm thời kèm theo index dòng để ráp lại chính xác
                updated_values[index] = {"key": key_clean, "values": selected_opts}
                
        if not has_kv:
            st.info("ℹ️ Không tìm thấy cặp dữ liệu dạng `Key: Value` nào trong Description của thư mục này.")
            
        # 4. Nút cập nhật và đẩy ngược Description mới lên Google Drive
        if has_kv:
            st.markdown("---")
            if st.button("💾 Cập nhật thay đổi Description lên Google Drive", type="primary"):
                new_lines = []
                # Tái cấu trúc chuỗi chính xác theo index dòng cũ. 
                # Việc này đảm bảo giữ nguyên các dòng văn bản tự do không chứa dấu ":" thay vì xóa hoặc ghi đè rác.
                for index, line in enumerate(lines):
                    if index in updated_values:
                        k = updated_values[index]["key"]
                        v_list = updated_values[index]["values"]
                        val_str = ", ".join(v_list)
                        new_lines.append(f"{k}: {val_str}")
                    else:
                        new_lines.append(line)
                        
                final_new_desc = "\n".join(new_lines)
                
                # Tiến hành update metadata lên Drive thông qua đối tượng service của bạn
                with st.spinner("Đang đồng bộ dữ liệu mới lên Google Drive..."):
                    try:
                        drive_ops.drive_service.files().update(
                            fileId=selected_subfolder_id,
                            body={"description": final_new_desc}
                        ).execute()
                        st.success("🎉 Đã cập nhật thành công Description mới lên Google Drive!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Thất bại khi lưu Description: {e}")