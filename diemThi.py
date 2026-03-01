import httpx
import time

# Điền thông tin đăng nhập
username = "" 
password = "" 

# URL đăng nhập và lấy bảng điểm
login_url = 'https://sinhvien1.tlu.edu.vn/education/oauth/token'  # URL đăng nhập
grades_url = 'https://sinhvien1.tlu.edu.vn/education/api/studentsubjectmark/getListStudentMarkBySemesterByLoginUser/0'  # URL lấy bảng điểm

# Dữ liệu đăng nhập
login_data = {
    'client_id': 'education_client',
    'grant_type': 'password',
    'username': username,
    'password': password,
    'client_secret': 'password' 
}

def safe_get(value):
    """Trả về giá trị hoặc 'N/A' nếu giá trị là None."""
    return value if value is not None else "N/A"

MAX_RETRIES = 50
RETRY_DELAY = 2  # giây
access_token = None

# Thực hiện yêu cầu đăng nhập
with httpx.Client(verify=False, timeout=15) as client:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.post(login_url, data=login_data)

            if response.status_code == 200:
                token_info = response.json()
                access_token = token_info.get('access_token')  # Lấy access token từ phản hồi
                print("Đăng nhập thành công")
                break

            elif response.status_code == 400:
                print("Sai tên đăng nhập hoặc mật khẩu. Dừng lại.")
                break
            else:
                print(f"Lỗi máy chủ ({response.status_code}). Thử lại lần {attempt}/{MAX_RETRIES} sau {RETRY_DELAY} giây...")
                time.sleep(RETRY_DELAY)

        except httpx.RequestError as e:
            print(f"Lỗi kết nối: {e}. Thử lại lần {attempt}/{MAX_RETRIES} sau {RETRY_DELAY} giây...")
            time.sleep(RETRY_DELAY)

    # Nếu vẫn không đăng nhập được sau nhiều lần
    if not access_token:
        print("Không thể đăng nhập sau nhiều lần thử.")
        exit()

    # Sử dụng token để lấy bảng điểm
    headers = {
        'Authorization': f'Bearer {access_token}'  # Thêm token vào header
    }
    grades_response = client.get(grades_url, headers=headers)

    if grades_response.status_code == 200:
        grades_data = grades_response.json()  # Lấy dữ liệu bảng điểm
        
        # Lấy thông tin sinh viên
        if grades_data:
            student_info = grades_data[0]['student']  # Giả sử thông tin sinh viên nằm trong phần tử đầu tiên
            student_name = f"{student_info['lastName']} {student_info['firstName']}"
            student_id = student_info['studentCode']  # Lấy mã sinh viên từ trường 'studentCode'
            class_name = safe_get(student_info['className'])  # Lấy tên lớp
            
            # In ra thông tin sinh viên
            print(f"\nHọ tên: {student_name}")
            print(f"Mã sinh viên: {student_id}")
            print(f"Tên lớp: {class_name}")
            print("Bảng điểm:")
            print(f"{'Mã môn':<10} {'Tên môn':<38} {'Số tín':<10} {'ĐQT':<10} {'Thi':<8} {'Thang 10':<10} {'Thang 4':<8} {'Điểm chữ':<9} {'Đánh giá':<8}")
            print("=" * 119)

            total_credits = 0
            weighted_points_10 = 0
            weighted_points_4 = 0
            
            for entry in grades_data:  # Duyệt qua tất cả các môn học
                subject_code = safe_get(entry['subject']['subjectCode'])
                subject_name = safe_get(entry['subject']['subjectName'])
                mark = safe_get(entry['mark'])
                markQT = safe_get(entry.get('markQT'))
                markTHI = safe_get(entry.get('markTHI'))
                number_of_credit = safe_get(entry['subject']['numberOfCredit'])
                mark4 = safe_get(entry.get('mark4'))
                char_mark = safe_get(entry.get('charMark'))
                subject_type = safe_get(entry['subject']['subjectType'])
                status = "Đạt" if mark4 >= 1 else "Không đạt"
                
                print(f"{subject_code:<10} {subject_name:<40} {number_of_credit:<8} {markQT:<10} {markTHI:<10} {mark:<10} {mark4:<9} {char_mark:<8} {status:<10}")
                # Cộng dồn số tín chỉ và điểm
                if subject_type != 2:
                    # Cộng dồn số tín chỉ và điểm theo công thức trung bình trọng số
                    total_credits += number_of_credit
                    weighted_points_10 += mark * number_of_credit  # Calculating weighted points for thang 10
                    weighted_points_4 += mark4 * number_of_credit    # Calculating weighted points for thang 4

            # Tính trung bình
            average_points_10 = weighted_points_10 / total_credits if total_credits > 0 else 0
            average_points_4 = weighted_points_4 / total_credits if total_credits > 0 else 0

            # In ra tổng số tín chỉ và trung bình
            print("=" * 119)
            print(f"Tổng số tín chỉ: {total_credits}")
            print(f"Trung bình thang 10: {average_points_10:.2f}")
            print(f"GPA: {average_points_4:.2f}")
        else:
            print("Không có dữ liệu bảng điểm.")
    else:
        print("Không thể lấy thông tin điểm thi:", grades_response.status_code, grades_response.text)

