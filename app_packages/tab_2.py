# app_packages/tab_2.py
import streamlit as st
import drive_module.drive_ops as drive_ops
import utils.storage as storage

def render_tab2(selected_subfolder_id, selected_subfolder_name):
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
        
        # --- THÀNH PHẦN GIAO DIỆN - THÊM THUỘC TÍNH (KEY) MỚI VÀO CUỐI DESCRIPTION ---
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
            st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 Xác nhận thêm thuộc tính", key=f"btn_add_key_{selected_subfolder_id}", type="secondary", use_container_width=True):
                target_new_key = custom_new_key if add_key_option == "✍️ Tự nhập thuộc tính mới hoàn toàn..." else add_key_option
                
                if target_new_key and target_new_key != "-- Chọn thuộc tính đã có --":
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
                            st.rerun()
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