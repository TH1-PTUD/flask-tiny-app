@echo off
REM -------------------------------------------------
REM Script cài đặt project trên Windows sử dụng GitHub và Visual Studio Code
REM Mục đích:
REM   - Kiểm tra sự tồn tại của Git và Visual Studio Code (code command phải có trong PATH).
REM   - Clone repository từ GitHub hoặc cập nhật nếu thư mục đã tồn tại.
REM   - Cài đặt dependencies (Node.js: package.json, Python: requirements.txt).
REM   - Mở project trong Visual Studio Code.
REM -------------------------------------------------

echo Bắt đầu cài đặt project...

REM 1. Kiểm tra Git đã được cài đặt chưa
git --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Lỗi: Git chưa được cài đặt. Vui lòng cài đặt Git trước.
    pause
    exit /B 1
)

REM 2. Kiểm tra Visual Studio Code đã được cài đặt chưa (code command)
code --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Lỗi: Visual Studio Code chưa được cài đặt hoặc "code" command chưa được thêm vào PATH.
    pause
    exit /B 1
)

REM 3. Định nghĩa URL repository và tên thư mục đích
SET REPO_URL=https://github.com/TH1-PTUD/flask-tiny-app.git
SET TARGET_DIR=project

REM 4. Clone repository hoặc cập nhật nếu đã có thư mục
if exist %TARGET_DIR% (
    echo Thư mục %TARGET_DIR% đã tồn tại. Cập nhật repository...
    cd %TARGET_DIR%
    git pull
    cd ..
) else (
    echo Đang clone repository từ %REPO_URL% vào thư mục %TARGET_DIR%...
    git clone %REPO_URL% %TARGET_DIR%
    IF ERRORLEVEL 1 (
        echo Lỗi: Không thể clone repository. Kiểm tra URL hoặc kết nối mạng.
        pause
        exit /B 1
    )
)

REM 5. Chuyển vào thư mục project
cd %TARGET_DIR%

REM 6. Cài đặt Node.js dependencies nếu file package.json tồn tại
if exist package.json (
    echo Phát hiện file package.json. Đang cài đặt Node.js dependencies...
    npm install
)

REM 7. Cài đặt Python dependencies nếu file requirements.txt tồn tại
if exist requirements.txt (
    echo Phát hiện file requirements.txt. Đang cài đặt Python dependencies...
    pip install -r requirements.txt
)

REM 8. Mở project trong Visual Studio Code
echo Mở Visual Studio Code...
code .

echo Cài đặt hoàn tất!
pause
