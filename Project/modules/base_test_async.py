from playwright.async_api import async_playwright, ElementHandle
from utils.config_loader import load_config
from utils.log_manager import setup_logger
from dataclasses import dataclass
import tiktoken
from typing import Any
import asyncio
import logging
import time

@dataclass
class ResponseMetrics:
    total_transactions: int
    failed_transactions: int
    first_token_latency:list[float]
    total_response_time: list[float]
    ai_response_token_count: list[int]
    generation_time: list[float]

@dataclass
class TestResult:
    is_successful: bool = False             # 測試是否成功
    total_response_time: float = 0.0        # 按下 enter 到回應穩定的時間（秒）
    first_token_latency: float = 0.0        # 按下 enter 到第一個 token 出現的延遲（秒）
    token_count: int = 0                    # 回應 token 數
    generation_time: float = 0.0            # 第一個 token 到回應穩定的生成時間（秒）

def count_tokens(text: str):
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    return len(tokens)

class BaseTestAsync:
    def __init__(self,
                 service_name:str,
                 playwright_instance=None,
                 browser_name:str="",
                 logger=None,
                 verbose=False,
                 headless=None,
                 ) -> None:
        """ 初始化 BaseTestAsync

        參數:
            - service_name (str): 測試的服務名稱
            - playwright_instance (PlaywrightContextManager, optional): playwright的物件實例，預設為 None。若為 None，則會在 setup() 時初始化。
            - browser_name (str, optional): 瀏覽器名稱，預設為空字串。
            - logger (Logger, optional): Logger管理器，預設為 None。若為 None，則會在 setup() 時初始化。
            - verbose (bool, optional): 是否顯示詳細AI的回應，預設為 False。
            - headless (bool, optional): 單獨控制 headless 模式或使用config設定，預設為None。
        """
        # 根據服務名稱讀取配置
        self.config = load_config(service_name)
        self.browser = None
        self.page = None
        # LoggerAdapter 包裝
        self.logger = logging.LoggerAdapter(logger if logger else setup_logger(service_name), {'browser_name': browser_name})
        self.logger.process = lambda msg, kwargs: (f"{browser_name} {msg}".strip(), kwargs)
        
        if playwright_instance is not None:
            self.playwright = playwright_instance
            self._external_playwright = True  # 標記這個 playwright 實例是外部傳入的
        else:
            self.playwright = None
        
        self.verbose = verbose
        self._headless = headless
        
    
    async def setup(self,**kargs) -> None:
        """ 初始化 Playwright 
        1. 啟動Async Playwright
        2. 創建新的瀏覽器實例，並設定是否 headless
        3. 創建新的頁面實例
        
        kwargs:
        - test_prompts (List[str], optional): 測試的 prompt 列表，預設使用配置文件中的 test_prompts。
        """
        # 如果已經有 Playwright 實例，就不需要再初始化
        if not self.playwright:
            self.playwright = await async_playwright().start()
        
        # 是否 headless 模式
        headless = self._headless if self._headless is not None else self.config.get("headless",False)
        self.browser = await self.playwright.chromium.launch(headless=headless)
        context = await self.browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        self.page = await context.new_page()
        await self.page.evaluate("() => { Object.defineProperty(navigator, 'webdriver', {get: () => undefined}) }")
        
        # 如果有傳入 test_prompts，就使用傳入的，否則使用配置文件中的 test_prompts
        if "test_prompts" in kargs:
            self.prompts = kargs["test_prompts"]
            assert isinstance(self.prompts, list), "test_prompts 必須是一個列表"
        else:
            self.prompts = self.config.get("test_prompts")


    async def teardown(self) -> None:
        """ 關閉 Playwright """
        if self.browser:
            await self.browser.close()
        # 注意：如果 Playwright 是由外部傳入，就不要關閉它，否則會影響其他測試
        if self.playwright and not getattr(self, '_external_playwright', False):
            await self.playwright.stop()
        
    async def run_test(self) -> ResponseMetrics:
        """
        執行基礎測試：
        1. 記錄開始時間 (performance.now())
        2. 送出 prompt
        3. 等待 AI 回應區域的內容變化並穩定
        4. 記錄結束時間 (performance.now())
        5. 計算反應時間
        6. 返回測試結果
        
        回傳：
        - ResponseMetrics: 包含測試結果的dataclass
        
        dataclass內容：
        - total_transactions: int
        - failed_transactions: int
        - first_token_latency:list[float]
        - total_response_time: list[float]
        - ai_response_token_count: list[int]
        - generation_time: list[float]
        """
        
        
        # 紀錄每次測試結果的list，一次結果為一個TestResult
        _test_results:list[TestResult] = [TestResult() for _ in range(len(self.prompts))]
        total_transactions = 0
        failed_transactions = 0
        
        # 前往測試 URL
        if self.page.url == "about:blank":
            await self.page.goto(self.config["url"])
        
        for index,prompt in enumerate(self.prompts):
            try:
                self.logger.info(f"測試 Prompt{index+1}")
                
                # --------------以下為 UI 交互邏輯--------------
                
                # TODO 若有需要這裡可能需要處理input_selector不是唯一的情況
                # 先等待至少有一個匹配的輸入框出現
                # await self.page.wait_for_selector(input_selector, timeout=10000)
                # # 取得所有匹配的元素
                # textareas = await self.page.query_selector_all(input_selector)
                # # 過濾出所有可見的輸入框
                # visible_textareas:list[ElementHandle] = []
                # for ta in textareas:
                #     if await ta.is_visible():
                #         visible_textareas.append(ta)
                # if not visible_textareas:
                #     raise Exception("No visible input element found")
                # # 根據需求選擇目標：例如選取第一個或最後一個
                # input_area = visible_textareas[-1]  # 或 visible_textareas[-1]
                
                input_area = await self.page.wait_for_selector(self.config['input_selector'],timeout=10000)
                await input_area.scroll_into_view_if_needed()
                # 高亮輸入框
                await input_area.evaluate("(el)=>el.style.backgroundColor='yellow'")
                
                # 輸入 prompt
                await input_area.fill(prompt)
                await input_area.press("Enter")
                
                # 記錄送出時間
                start_time = await self.page.evaluate("performance.now()")
                total_transactions += 1
                
                # FIX 如果AI回應太快，可能會跳過一些回應
                ai_output=None
                found_new_response = False
                for _ in range(30): # 最多等待 15 秒
                    ai_output = await self.page.query_selector(self.config['response_selector'])
                    is_counted = await ai_output.get_attribute('data-counted')
                    if is_counted is None:
                        await ai_output.evaluate("""(el) => {
                            el.dataset.counted = 'true';
                            el.style.backgroundColor = 'yellow';
                        }""")
                        await ai_output.scroll_into_view_if_needed()
                        found_new_response = True
                        break
                    await asyncio.sleep(0.5)
                if not found_new_response:
                    raise TimeoutError("找不到新回應")
                
                # --------------以上為 UI 交互邏輯--------------
                
                

                # --------------以下為計時器--------------
                # 等待輸出區域穩定（避免回應還在逐步輸出）
                stable_duration = 0      # 穩定持續時間
                poll_interval = 0.5      # 每隔 0.5 秒檢查一次
                required_stable_time = 2 # 需要連續穩定 2 秒
                prev_text = ""
                first_token_time = None
                final_token_time = None  # 記錄真正的回應完成時間

                for _ in range(60):
                    current_text = await ai_output.inner_text()
                    current_time = await self.page.evaluate("performance.now()")

                    # 記錄第一個 token 出現的時間
                    if (first_token_time is None) and current_text.strip():
                        first_token_time = current_time

                    if current_text == prev_text and current_text.strip():  # 確保有內容且穩定
                        stable_duration += poll_interval
                        if final_token_time is None:  # 第一次達到穩定狀態
                            final_token_time = current_time
                    else:
                        stable_duration = 0
                        prev_text = current_text
                        final_token_time = None  # 重新等待新的穩定狀態

                    if stable_duration >= required_stable_time:
                        break
                    await asyncio.sleep(poll_interval)
                # --------------以上為計時器--------------
                
                
                
                # --------------以下為結果儲存--------------
                current_result = _test_results[index]
                current_result.is_successful = True
                current_result.total_response_time = (final_token_time - start_time)/1000 if final_token_time is not None else (current_time - start_time)/1000
                current_result.first_token_latency = (first_token_time - start_time)/1000 if first_token_time is not None else 0
                current_result.token_count = count_tokens(await ai_output.inner_text())
                current_result.generation_time = (final_token_time - first_token_time)/1000 if final_token_time is not None else 0
                
                # 紀錄回應內容
                if self.verbose:
                    self.logger.info(f"Prompt{index+1} 回應內容：{await ai_output.inner_text()}")
                
                self.logger.info(
                    f"Prompt{index+1} 測試完成，總回應時間: {current_result.total_response_time:.2f} 秒，第一個 token 延遲: {current_result.first_token_latency:.2f} 秒，回應token數: {current_result.token_count}，生成時間: {current_result.generation_time:.2f} 秒")
                
                # --------------以上為結果儲存--------------
            except Exception as e:
                self.logger.error(f"測試 Prompt{index+1} 發生錯誤：{e}")
                failed_transactions+=1
            if failed_transactions>=5:
                break
                

        successful_results = [t for t in _test_results if t.is_successful]

        return ResponseMetrics(
            total_transactions=total_transactions,
            failed_transactions=failed_transactions,
            first_token_latency=[t.first_token_latency for t in successful_results],
            total_response_time=[t.total_response_time for t in successful_results],
            ai_response_token_count=[t.token_count for t in successful_results],
            generation_time=[t.generation_time for t in successful_results],
        )


        