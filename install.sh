#!/bin/bash
# Workdo 自動打卡系統 - 快速安裝腳本

set -e

echo "🚀 開始安裝 Workdo 自動打卡系統..."
echo ""

# 檢查 Python 版本
echo "📌 檢查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤: 未找到 Python 3"
    echo "請先安裝 Python 3.8 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo "✅ Python 版本: $PYTHON_VERSION"
echo ""

# 安裝依賴套件
echo "📦 安裝依賴套件..."
pip3 install -r requirements.txt
echo "✅ 套件安裝完成"
echo ""

# 檢查並建立 .env 檔案
if [ ! -f .env ]; then
    echo "📝 建立環境變數檔案..."
    cp .env.example .env
    echo "✅ 已建立 .env 檔案"
    echo ""
    echo "⚠️  重要: 請編輯 .env 檔案，填入您的 Workdo 帳號資訊"
    echo ""
    echo "執行以下命令編輯："
    echo "  nano .env"
    echo "或"
    echo "  code .env"
    echo ""
else
    echo "✅ .env 檔案已存在"
    echo ""
fi

# 設定執行權限
echo "🔧 設定執行權限..."
chmod +x workdo_auto_clock.py
echo "✅ 權限設定完成"
echo ""

# 顯示使用說明
echo "=========================================="
echo "✅ 安裝完成！"
echo "=========================================="
echo ""
echo "📖 使用說明："
echo ""
echo "1. 編輯 .env 檔案設定您的帳號資訊"
echo "   nano .env"
echo ""
echo "2. 測試上班打卡："
echo "   python3 workdo_auto_clock.py in"
echo ""
echo "3. 測試下班打卡："
echo "   python3 workdo_auto_clock.py out"
echo ""
echo "4. 查詢打卡狀態："
echo "   python3 workdo_auto_clock.py status"
echo ""
echo "5. 智慧自動打卡："
echo "   python3 workdo_auto_clock.py auto"
echo ""
echo "6. 檢查並補缺卡："
echo "   python3 workdo_auto_clock.py check-missing"
echo ""
echo "📚 詳細說明請參考 README.md"
echo "🤖 GitHub Actions 設定請參考 docs/GITHUB_ACTIONS_SETUP.md"
echo ""
