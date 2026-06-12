# app_packages/tab_3.py
import streamlit as st
import utils.logic as logic  # Import logic từ package utils mới cấu trúc lại
import json

def render_tab3(selected_subfolder_id, selected_subfolder_name):
    st.subheader("📊 Xuất cấu trúc cây thư mục JSON kèm liên kết ảnh")
    
    if not selected_subfolder_id:
        st.info("💡 Hãy nhập link thư mục cha ở thanh Sidebar và chọn một Subfolder để bắt đầu xuất JSON.")
    else:
        # CHÚ THÍCH CẬP NHẬT: Chỉnh sửa lại text hiển thị phần Quy trình trong markdown để mô tả đúng cấu trúc Key-Value mới
        st.markdown(f"""
        * **Thư mục quét dữ liệu:** `{selected_subfolder_name}`
        * **ID Thư mục:** `{selected_subfolder_id}`
        * **Quy trình:** Hệ thống sẽ quét đệ quy toàn bộ thư mục con, bóc tách mô tả (Description) thành các cặp `Key: [Values]` bên trong đối tượng `metatag` và định dạng toàn bộ liên kết hình ảnh theo mã ID tương ứng.
        """)
        
        # Thiết lập nút kích hoạt tiến trình build JSON Tree
        if st.button("🔍 Bắt đầu quét & Tạo cấu trúc JSON", key=f"btn_build_json_{selected_subfolder_id}", type="primary"):
            st.info("🔄 Đang bắt đầu quét đệ quy cấu trúc thư mục và tệp ảnh...")
            
            log_monitor_t3 = st.empty()
            
            with st.spinner("Hệ thống đang bóc tách cây thư mục thời gian thực..."):
                # Gọi hàm đệ quy bóc tách dữ liệu từ module utils.logic
                raw_tree_result = logic.build_json_tree_with_images(
                    folder_id=selected_subfolder_id, 
                    log_area=log_monitor_t3
                )
                
                # Bọc kết quả vào dict có key chính là ID của thư mục gốc theo yêu cầu
                final_json_tree = {selected_subfolder_id: raw_tree_result}
                
            st.success("🎉 Đã thiết lập và khởi tạo cấu trúc cây dữ liệu JSON thành công!")
            
            # Chuẩn bị dữ liệu chuỗi JSON thụt lề 4 khoảng trắng trực quan phục vụ download
            json_string = json.dumps(final_json_tree, ensure_ascii=False, indent=4)
            
            # Hiển thị khu vực xem trước kết quả
            with st.expander("🔍 Xem trước nội dung tệp JSON vừa khởi tạo"):
                st.json(final_json_tree)
            
            st.markdown("---")
            # Nút bấm tải tệp JSON về máy cục bộ của người dùng
            st.download_button(
                label="📥 Tải file JSON về máy",
                data=json_string,
                file_name=f"tree_{selected_subfolder_id}.json",
                mime="application/json",
                use_container_width=True
            )