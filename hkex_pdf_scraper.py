"""
香港交易所 - 自動搜索和提取 PDF 鏈接
功能：自動下載 ChromeDriver，搜索關鍵詞，提取 PDF 鏈接
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from datetime import datetime
import os
import json

# ==================== 自動下載 ChromeDriver ====================
print("=" * 70)
print("正在準備 ChromeDriver...")
print("=" * 70)

try:
    # webdriver_manager 會自動下載正確版本的 ChromeDriver
    service = Service(ChromeDriverManager().install())
    print("✅ ChromeDriver 已自動下載並準備好")
    print(f"📁 位置：{service.path}")
except Exception as e:
    print(f"❌ ChromeDriver 下載失敗：{e}")
    print("💡 請確認你的網絡連接正常")
    exit()

print()

# ==================== 配置部分（可以隨時修改） ====================
START_DATE = "2025/05/01"      # 開始日期
END_DATE = "2025/12/03"        # 結束日期

# 搜索關鍵詞
KEYWORDS = [
    '供股',      # 供股
    '配股',      # 配股
    '股權集中',  # 股權集中
    '易手',      # 易手
    '全購'       # 全購
]

# 文件夾設定
OUTPUT_FOLDER = 'hkex_search_results'
PDF_LINKS_FILE = f'{OUTPUT_FOLDER}/pdf_links.csv'
SEARCH_LOG_FILE = f'{OUTPUT_FOLDER}/search_log.json'

# 創建輸出文件夾
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
    print(f"✅ 創建輸出文件夾：{OUTPUT_FOLDER}\n")

print("=" * 70)
print("香港交易所 - 關鍵詞搜索和 PDF 鏈接提取")
print("=" * 70)
print(f"⏰ 搜索時間範圍：{START_DATE} 至 {END_DATE}")
print(f"🔍 搜索關鍵詞：{', '.join(KEYWORDS)}")
print(f"📁 輸出文件夾：{OUTPUT_FOLDER}")
print("=" * 70)

# ==================== 初始化瀏覽器 ====================
print("\n⏳ 啟動瀏覽器...")

chrome_options = Options()
# chrome_options.add_argument('--headless')  # 取消註釋可無視窗運行（更快）
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

try:
    # 使用自動下載的 ChromeDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("✅ 瀏覽器已成功啟動")
except Exception as e:
    print(f"❌ 瀏覽器啟動失敗：{e}")
    exit()

# ==================== 訪問網站 ====================
print("\n⏳ 訪問香港交易所網站...")
try:
    driver.get("https://www.hkexnews.hk/index_c.htm")
    time.sleep(5)  # 等待網頁完全加載
    print("✅ 網站已加載")
except Exception as e:
    print(f"❌ 訪問網站失敗：{e}")
    driver.quit()
    exit()

# ==================== 存儲結果 ====================
all_results = []
search_summary = {
    'start_date': START_DATE,
    'end_date': END_DATE,
    'keywords': KEYWORDS,
    'search_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_results': 0,
    'keywords_results': {}
}

# ==================== 搜索每個關鍵詞 ====================
print(f"\n⏳ 開始搜索 {len(KEYWORDS)} 個關鍵詞...\n")

for keyword_idx, keyword in enumerate(KEYWORDS, 1):
    print(f"[{keyword_idx}/{len(KEYWORDS)}] 🔍 搜索關鍵詞：《{keyword}》")
    print("-" * 70)
    
    keyword_results = []
    
    try:
        # ========== 第 1 步：找到搜索框 ==========
        try:
            # 等待並找到公告標題搜索框
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "Title"))  
            )
            search_input.clear()
            search_input.send_keys(keyword)
            print(f"  ✅ 輸入關鍵詞：{keyword}")
        except Exception as e:
            print(f"  ⚠️ 找不到標題搜索框")
            print(f"  💡 可能需要檢查網站結構，詳見錯誤：{e}")
            continue
        
        # ========== 第 2 步：輸入日期範圍 ==========
        try:
            # 開始日期
            begin_date_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "BeginDate"))
            )
            begin_date_input.clear()
            begin_date_input.send_keys(START_DATE)
            print(f"  ✅ 設定開始日期：{START_DATE}")
            
            # 結束日期
            end_date_input = driver.find_element(By.NAME, "EndDate")
            end_date_input.clear()
            end_date_input.send_keys(END_DATE)
            print(f"  ✅ 設定結束日期：{END_DATE}")
        except Exception as e:
            print(f"  ⚠️ 日期設定出現問題：{e}")
        
        # ========== 第 3 步：點擊搜索按鈕 ==========
        try:
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "btnSearch"))
            )
            search_button.click()
            print(f"  ⏳ 執行搜索...")
            time.sleep(5)  # 等待搜索結果加載
        except Exception as e:
            print(f"  ⚠️ 搜索按鈕出現問題：{e}")
            continue
        
        # ========== 第 4 步：提取 PDF 鏈接 ==========
        try:
            # 等待結果表格加載
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
            )
            
            # 尋找所有的表格行
            rows = driver.find_elements(By.TAG_NAME, "tr")
            print(f"  ✅ 找到 {len(rows)} 行搜索結果")
            
            # 遍歷每一行
            row_count = 0
            for row_idx, row in enumerate(rows[1:], 1):  # 跳過表頭
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) >= 4:  # 確保有足夠的列
                        # 提取信息
                        announcement_title = cells[0].get_text(strip=True)
                        announcement_date = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        company_name = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                        
                        # 尋找 PDF 鏈接
                        try:
                            pdf_link_elem = cells[-1].find_element(By.TAG_NAME, "a")
                            pdf_link = pdf_link_elem.get_attribute("href")
                            pdf_filename = pdf_link.split('/')[-1] if pdf_link else ""
                        except:
                            pdf_link = ""
                            pdf_filename = ""
                        
                        # 只保存有 PDF 鏈接的結果
                        if pdf_link:
                            result = {
                                '搜索關鍵詞': keyword,
                                '公告標題': announcement_title,
                                '公告日期': announcement_date,
                                '公司名稱': company_name,
                                'PDF 檔名': pdf_filename,
                                'PDF 鏈接': pdf_link,
                                '搜索時間': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            
                            keyword_results.append(result)
                            all_results.append(result)
                            row_count += 1
                            
                            # 每 5 個結果打印一次
                            if row_count % 5 == 0 or row_count == 1:
                                print(f"    [{row_count}] ✅ {announcement_title[:40]}...")
                
                except Exception as e:
                    pass  # 跳過無法解析的行
            
            print(f"  📊 從《{keyword}》找到 {len(keyword_results)} 個 PDF 結果")
            search_summary['keywords_results'][keyword] = len(keyword_results)
        
        except Exception as e:
            print(f"  ❌ 提取結果失敗：{e}")
    
    except Exception as e:
        print(f"  ❌ 搜索失敗：{e}")
    
    print()  # 空行分隔

# ==================== 關閉瀏覽器 ====================
print("\n⏳ 關閉瀏覽器...")
driver.quit()
print("✅ 瀏覽器已關閉")

# ==================== 保存結果 ====================
print(f"\n⏳ 保存搜索結果...\n")

if all_results:
    # 1. 保存為 CSV
    df = pd.DataFrame(all_results)
    df.to_csv(PDF_LINKS_FILE, index=False, encoding='utf-8-sig')
    print(f"✅ PDF 鏈接列表已保存")
    print(f"   📁 {PDF_LINKS_FILE}")
    
    # 2. 保存搜索摘要
    search_summary['total_results'] = len(all_results)
    with open(SEARCH_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(search_summary, f, ensure_ascii=False, indent=2)
    print(f"✅ 搜索日誌已保存")
    print(f"   📁 {SEARCH_LOG_FILE}")
    
    # 3. 顯示結果摘要
    print("\n" + "=" * 70)
    print("📋 搜索結果摘要")
    print("=" * 70)
    print(f"搜索時間範圍：{START_DATE} 至 {END_DATE}")
    print(f"搜索關鍵詞數量：{len(KEYWORDS)}")
    print(f"找到的 PDF 總數：{len(all_results)} 個")
    print(f"\n各關鍵詞結果數量：")
    for kw, count in search_summary['keywords_results'].items():
        print(f"  • {kw}：{count} 個")
    
    # 4. 顯示前 5 個結果
    if len(df) > 0:
        print(f"\n前 5 個結果預覽：")
        print("-" * 70)
        for idx, result in enumerate(df.head(5).itertuples(index=False), 1):
            print(f"{idx}. 【{result[0]}】 {result[1][:50]}")
            print(f"   日期：{result[2]} | 公司：{result[3]}")
            print(f"   檔名：{result[4]}")
            print()

else:
    print("⚠️ 沒有找到任何結果")
    print("💡 可能原因：")
    print("   - 日期範圍內沒有該關鍵詞的公告")
    print("   - 網站選擇器已改變，需要更新程式")

print("=" * 70)
print("✅ 完成！")
print("=" * 70)
