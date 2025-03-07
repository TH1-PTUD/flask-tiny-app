# Sử dụng image Python chính thức
FROM python:3.9

# Đặt thư mục làm việc trong container
WORKDIR /app

# Copy file requirements.txt vào container và cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Mở cổng 5000 để chạy ứng dụng
EXPOSE 5000

# Chạy ứng dụng khi container khởi động
CMD ["python", "app.py"]
