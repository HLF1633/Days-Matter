@echo off
REM ====================================================
REM  Days-Matter - Windows 打包脚本
REM  使用 PyInstaller 打包为单文件 exe 并创建安装包
REM ====================================================
chcp 65001 >nul
setlocal enabledelayedexpansion

echo =========================================
echo  Days-Matter Windows 打包脚本
echo =========================================
echo.

REM 检查 PyInstaller
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] 正在安装 PyInstaller...
    pip install pyinstaller
    if !errorlevel! neq 0 (
        echo [ERROR] PyInstaller 安装失败，请手动安装: pip install pyinstaller
        pause
        exit /b 1
    )
)

REM 检查 NSIS 是否安装
where makensis >nul 2>&1
set NSIS_AVAILABLE=%errorlevel%

set VERSION=1.0.0
set APP_NAME=Days-Matter
set DIST_DIR=dist
set OUTPUT_DIR=output

REM 清理旧的构建文件
echo [1/4] 清理旧的构建文件...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%OUTPUT_DIR%" rmdir /s /q "%OUTPUT_DIR%"
mkdir "%OUTPUT_DIR%" 2>nul

REM 第一步：PyInstaller 打包
echo [2/4] 使用 PyInstaller 打包为 exe...
echo.
echo 正在打包成单个 exe 文件（包含完整运行环境）...
echo 这可能需要 2-5 分钟...

pyinstaller --onefile ^
    --windowed ^
    --name "%APP_NAME%" ^
    --icon "resources\icon.ico" ^
    --add-data "resources;resources" ^
    --noconsole ^
    --clean ^
    main.py

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller 打包失败！
    pause
    exit /b 1
)

echo.
echo [3/4] 准备安装包文件...
mkdir "%OUTPUT_DIR%\installer" 2>nul

REM 复制 exe 到输出目录
copy /y "%DIST_DIR%\%APP_NAME%.exe" "%OUTPUT_DIR%\"

REM 复制其他必要文件
copy /y "README.md" "%OUTPUT_DIR%\" 2>nul
copy /y "LICENSE" "%OUTPUT_DIR%\" 2>nul

REM 第二步：创建 NSIS 安装包（如果 NSIS 可用）
echo [4/4] 创建安装包...

if %NSIS_AVAILABLE% equ 0 (
    echo [INFO] 检测到 NSIS，正在创建安装程序...
    
    REM 生成 NSIS 脚本
    (
        echo !define APP_NAME "Days-Matter"
        echo !define APP_VERSION "%VERSION%"
        echo !define APP_PUBLISHER "Days-Matter"
        echo !define APP_URL "https://github.com/HLF1633/Days-Matter"
        echo !define INSTALL_DIR "$PROGRAMFILES\\${APP_NAME}"
        echo.
        echo Name "${APP_NAME}"
        echo OutFile "%OUTPUT_DIR%\\${APP_NAME}-Setup-${APP_VERSION}.exe"
        echo InstallDir "${INSTALL_DIR}"
        echo RequestExecutionLevel admin
        echo.
        echo Section "Install"
        echo   SetOutPath "$INSTDIR"
        echo   File "%DIST_DIR%\\${APP_NAME}.exe"
        echo   File "README.md"
        echo.
        echo   ; 创建开始菜单快捷方式
        echo   CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
        echo   CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_NAME}.exe"
        echo.
        echo   ; 创建卸载程序入口
        echo   WriteUninstaller "$INSTDIR\\uninstall.exe"
        echo   WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
        echo   WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
        echo SectionEnd
        echo.
        echo Section "Uninstall"
        echo   Delete "$INSTDIR\\${APP_NAME}.exe"
        echo   Delete "$INSTDIR\\README.md"
        echo   Delete "$INSTDIR\\uninstall.exe"
        echo   RMDir "$INSTDIR"
        echo.
        echo   Delete "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk"
        echo   RMDir "$SMPROGRAMS\\${APP_NAME}"
        echo.
        echo   DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
        echo SectionEnd
    ) > "%OUTPUT_DIR%\installer\installer.nsi"
    
    cd "%OUTPUT_DIR%\installer"
    makensis installer.nsi
    cd ..\..
    
    if !errorlevel! equ 0 (
        echo [SUCCESS] NSIS 安装包创建成功！
    ) else (
        echo [WARNING] NSIS 安装包创建失败，但 exe 文件已生成。
    )
) else (
    echo [INFO] 未检测到 NSIS，跳过安装包创建。
    echo [INFO] 如需创建安装包，请安装 NSIS: https://nsis.sourceforge.io/
    echo.
    echo [INFO] 也可以直接使用生成的 exe 文件：
    echo   %DIST_DIR%\%APP_NAME%.exe
)

echo.
echo =========================================
echo  打包完成！
echo =========================================
echo.
echo 生成的文件：
echo   - 单文件 exe:    %DIST_DIR%\%APP_NAME%.exe
echo   - 便携版:        %OUTPUT_DIR%\%APP_NAME%.exe
if exist "%OUTPUT_DIR%\installer\*.exe" (
    for /r "%OUTPUT_DIR%\installer" %%f in (*.exe) do (
        if not "%%~nxf"=="uninstall.exe" (
            echo   - 安装包:          %%f
        )
    )
)
echo.
echo 使用方法：
echo   1. 直接运行 exe 文件即可启动程序
echo   2. 安装包版会在开始菜单创建快捷方式
echo.
echo 注意：exe 文件首次启动可能被 Windows Defender 拦截，请允许运行。
echo.

pause