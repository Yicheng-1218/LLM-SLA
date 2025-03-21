import os
import json
import asyncio


async def perform_login(page, config):
    await page.fill(config["username_selector"], config["username"])
    await page.fill(config["password_selector"], config["password"])
    await page.click(config["login_button_selector"])
    await page.wait_for_navigation()
    if page.url == config["login_url"]:
        print("自動登入失敗，請檢查帳號密碼是否正確。")
        return False
    return True

    
async def perform_cookies_login(page,config):
    """
    進行 cookie 登入操作：
    1. 檢查是否存在 cookie 檔案，若存在則讀取並加入到瀏覽器 context 中
    2. 檢查是否需要手動登入，若需要則進行手動登入
    3. 若不需要手動登入，則直接使用 cookie 登入
    """
    cookie_file_path = os.path.join(os.path.dirname(__file__), "..", "cookies", f'{config["name"]}.json')
    await page.goto(config["url"])
    return await load_cookies(page.context,cookie_file_path)
    

async def perform_manual_login(page,config):
    """
    進行手動登入操作：
    1. 先檢查 headless 設定（若 headless 為 True，則無法人工登入）
    2. 導向登入頁面，等待使用者手動操作
    3. 完成登入後，使用者按 Enter 鍵繼續流程
    4. 檢查網址中是否仍包含 "login" 關鍵字，確保登入成功
    """
    # 檢查 headless 設定
    if config.get("headless", True):
        print("警告：若要進行手動登入，請將 headless 設定為 False！")
        return
    login_url = config.get("login_url")
    if not login_url:
        print("配置中未找到 login_url，請檢查配置文件。")
        return
    
    await page.goto(login_url)
    print("請在打開的瀏覽器中手動完成登入，完成後按 Enter 鍵繼續...")
    await asyncio.to_thread(input, "按 Enter 鍵繼續...")
        

# 在 load_cookies 函式中，你可以這樣處理：
async def load_cookies(context, cookie_file_path):
    try:
        with open(cookie_file_path, 'r') as f:
            cookies = json.load(f)
            
        # 確保每個 cookie 都有正確的 sameSite 值
        for cookie in cookies:
            if 'sameSite' not in cookie or cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                cookie['sameSite'] = 'Lax'  # 設定預設值
                
        await context.add_cookies(cookies)
        return True
    except Exception as e:
        print(f"載入 cookies 時發生錯誤：{str(e)}")
        return False

async def save_cookies(context,file_path):
    """將當前 context 的 cookies 儲存到檔案"""
    cookies = await context.cookies()
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)
    print("Cookie 已儲存。")
