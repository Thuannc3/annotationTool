@echo off
echo ========================================
echo  Building Contour Annotation Tool...
echo ========================================
call .venv\Scripts\activate

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist tooldraw.spec del /f /q tooldraw.spec

pyinstaller --onefile --windowed --add-data "images;images" tooldraw.py

if exist dist\tooldraw.exe (
    echo  Copying to parent folder...
    copy /Y dist\tooldraw.exe .
) else (
    echo  Build failed, no EXE found!
)

echo ========================================
echo  Build completed!
echo  Output: tooldraw.exe
echo ========================================
pause