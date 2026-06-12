# app_packages/tab_1.py
import streamlit as st
import utils.storage as storage
import utils.logic as logic  # CHÚ THÍCH CẬP NHẬT: Import logic từ package utils mới cấu trúc lại

def render_tab1(selected_subfolder_id, selected_subfolder_name, selected_root_id):
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
            destination_parent_id = selected_root_id
            
            # Khởi tạo dict trống để tích lũy dữ liệu thu thập được từ tất cả các folder con trong RAM
            collected_metadata = {}
            
            with st.spinner("Đang clone cấu trúc cây thư mục..."):
                # Gọi hàm lõi từ module utils.logic
                logic.clone_folder_structure_templated(
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
                        vault_data = storage.load_data()
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
                            storage.save_data([current_pool])
                            st.toast("✨ Đã đồng bộ thành công dữ liệu metadata mới lên MongoDB!", icon="💾")
                    except Exception as db_err:
                        st.error(f"❌ Không thể đồng bộ dữ liệu lên MongoDB: {db_err}")
                
            st.success(f"🎉 Đã hoàn thành sao chép hoàn toàn cấu trúc trống của thư mục 'Z ~ {selected_subfolder_name}'!")