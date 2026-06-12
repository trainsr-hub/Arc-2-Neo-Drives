# utils/logic.py
import drive_module.drive_ops as drive_ops
import json

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


def build_json_tree_with_images(folder_id, log_area):
    """
    Hàm đệ quy quét cấu trúc thư mục, gom toàn bộ value từ Description vào metatag list,
    đồng thời định dạng link thumbnail cho toàn bộ file ảnh bên trong.
    """
    try:
        # 1. Lấy metadata và description của folder hiện tại
        folder_meta = drive_ops.get_file_metadata(folder_id)
        folder_name = folder_meta.get('name', 'Thư mục không tên')
        folder_desc = folder_meta.get('description', '') or ''
        
        log_area.code(f"[ Đang quét cây ] Thư mục: {folder_name}")
        
        # --- CHÚ THÍCH CẬP NHẬT: Thay đổi metatags từ list [] thành dict {} ---
        # Điều này cho phép lưu trữ chính xác theo cặp từng Key kết nối với mảng các Value tương ứng của nó.
        metatags = {}
        if folder_desc:
            for line in folder_desc.splitlines():
                if ":" in line:
                    key_part, val_part = line.split(":", 1)
                    key_clean = key_part.strip()
                    vals = [v.strip() for v in val_part.split(",") if v.strip()]
                    
                    if key_clean:
                        if key_clean not in metatags:
                            metatags[key_clean] = []
                        # Thực hiện gộp dữ liệu độc bản (không trùng lặp phần tử)
                        for v in vals:
                            if v not in metatags[key_clean]:
                                metatags[key_clean].append(v)
        
        # 3. Quét các item con trực tiếp bên trong folder này
        sub_items = drive_ops.list_folder_contents(folder_id)
        
        images_list = []
        child_dict = {}
        
        for item in sub_items:
            item_id = item.get('id')
            mime_type = item.get('mimeType', '')
            
            if mime_type == "application/vnd.google-apps.folder":
                # Nếu là folder -> Tiếp tục đệ quy xuống tầng dưới và gắn vào dict con theo ID
                child_dict[item_id] = build_json_tree_with_images(item_id, log_area)
            else:
                # Nếu không phải folder -> Chắc chắn là image, tiến hành format link thumbnail
                img_url = f"https://drive.google.com/thumbnail?id={item_id}&sz=s1648"
                images_list.append(img_url)
                
        # Trả về cấu trúc dữ liệu theo đúng định nghĩa yêu cầu của folder
        return {
            "metatag": metatags,
            "image": images_list,
            "child": child_dict
        }
    except Exception as e:
        log_area.error(f"❌ Lỗi khi phân tích JSON Tree tại Folder ID {folder_id}: {e}")
        # CHÚ THÍCH CẬP NHẬT: Đổi giá trị fallback của metatag từ mảng rỗng sang dict rỗng để đồng bộ kiểu dữ liệu
        return {"metatag": {}, "image": [], "child": {}}