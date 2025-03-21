import logging
import asyncio
import statistics
import numpy as np
from playwright.async_api import async_playwright
from modules.base_test_async import BaseTestAsync,ResponseMetrics
from utils.config_loader import load_config
from utils.log_manager import setup_logger
from typing import Any, Dict
import time

class BaseTestRunner:
    def __init__(self, service_name: str,log_level: int = logging.INFO) -> None:
        self.service_name = service_name
        self.logger = setup_logger(service_name,level=log_level)
        self.config = load_config(service_name)

    async def before_test(self, test_instance: BaseTestAsync) -> None:
        pass
    
    async def after_test(self, test_instance: BaseTestAsync) -> None:
        pass

    async def run_test(self, playwright=None, browser_idx=None, **kwargs) -> ResponseMetrics:
        """
        執行測試，可以是單次測試或持續測試。
        
        參數：
        - playwright: PlaywrightContextManager 實例
        - browser_idx: 瀏覽器索引
        - **kwargs: 額外參數
            - verbose: 是否紀錄AI的回應
            - browser_name: 測試器的名稱，預設為 `測試瀏覽器:{idx}`
        
        回傳：
        - dict: 包含測試結果的字典
        """
        test_instance = BaseTestAsync(
            self.service_name,
            playwright_instance=playwright,
            browser_name=f"測試瀏覽器:{browser_idx+1}",
            logger=self.logger,
            verbose=kwargs.get('verbose', False))
        
        try:
            await test_instance.setup()
            await self.before_test(test_instance)
            
            # 根據是否設定測試時間決定執行模式
            if self.config.get("test_duration"):
                result = await self._run_continuous(test_instance)
            else:
                result = await test_instance.run_test()
                
            await self.after_test(test_instance)
            return result
        finally:
            await test_instance.teardown()
            

    async def _run_continuous(self, test_instance: BaseTestAsync) -> ResponseMetrics:
        """內部方法：執行持續測試"""
        loop = asyncio.get_running_loop()
        start_time = loop.time()
        results:list[ResponseMetrics] = []
        _failed_transactions = 0
        
        while loop.time() - start_time < self.config["test_duration"]:
            r = await test_instance.run_test()
            _failed_transactions += r.failed_transactions
            if _failed_transactions>self.config['concurrency']*3:
                self.logger.error('錯誤次數過多，提前中斷')
                break
            results.append(r)
        
        return ResponseMetrics(
            total_transactions=sum(r.total_transactions for r in results),
            failed_transactions=sum(r.failed_transactions for r in results),
            total_response_time=[t for r in results for t in r.total_response_time or []],
            ai_response_token_count=[t for r in results for t in r.ai_response_token_count or []],
            first_token_latency=[t for r in results for t in r.first_token_latency or []],
            generation_time=[t for r in results for t in r.generation_time or []]
        )

    def _calculate_statistics(self, results: list[ResponseMetrics]) -> Dict[str, Any]:
        """內部方法：計算測試統計數據"""
        # 合併所有測試結果
        generated_time = [t for r in results for t in (r.generation_time or [])]
        ai_response_token_count = [t for r in results for t in (r.ai_response_token_count or [])]
        first_token_latency = [t for r in results for t in (r.first_token_latency or [])]
        total_transactions = sum(r.total_transactions for r in results)
        failed_transactions = sum(r.failed_transactions for r in results)
        
        # 計算 tokens per second
        total_generated_time = sum(generated_time)
        total_tokens = sum(ai_response_token_count)
        tokens_per_second = total_tokens / total_generated_time if total_generated_time > 0 else 0.0
        
        return {
            "concurrency": self.config.get("concurrency", 1),
            "total_transactions": total_transactions,
            "failed_transactions": failed_transactions,
            "failed_rate": (failed_transactions/total_transactions)*100 if total_transactions else 100.0,
            "tokens_per_second": tokens_per_second,
            "p95_first_token_time": np.percentile(first_token_latency, 95) if first_token_latency else None,
            "p99_first_token_time": np.percentile(first_token_latency, 99) if first_token_latency else None,
            "median_first_token_time": statistics.median(first_token_latency) if first_token_latency else None
        }

    def _log_test_results(self, results: list[Dict], total_time: float) -> str:
        """內部方法：記錄測試結果"""
        stats = self._calculate_statistics(results)
        
        # 準備日誌訊息
        log_message = "\r\n=========== 測試結果 ===========\n" \
                     f"併發數量：{stats['concurrency']}\n" \
                     f"總測試時間：{total_time:.2f} 秒\n" \
                     f"錯誤率：{stats['failed_rate']:.2f} %\n" \
                     f"總交易次數：{stats['total_transactions']}\n"

        # 只有在有成功的測試結果時才顯示這些統計數據
        if stats['tokens_per_second'] is not None:
            log_message += f"每秒多少token：{stats['tokens_per_second']:.2f} 個\n" \
                          f"95% 的回應時間低於：{stats['p95_first_token_time']:.2f} 秒\n" \
                          f"99% 的回應時間低於：{stats['p99_first_token_time']:.2f} 秒\n" \
                          f"中位數第一個 token 延遲：{stats['median_first_token_time']:.2f} 秒"
        else:
            log_message += "所有測試都失敗，無法計算回應時間統計數據"

        self.logger.info(log_message)
        self.logger.prettify_logger()
        return log_message

    async def execute_load_test(self) -> str:
        """執行負載測試，依照設定的併發數量執行多個測試"""
        try:
            concurrency = self.config.get("concurrency", 1)
            
            self.logger.info("開始執行服務測試...")
            async with async_playwright() as playwright:
                tasks = [
                    asyncio.create_task(
                        self.run_test(playwright, idx)
                    ) for idx in range(concurrency)
                ]
                
                start_time = time.time()
                results = await asyncio.gather(*tasks)
                total_time = time.time() - start_time
                
                return self._log_test_results(results, total_time)
        finally:
            # 清理資源，關閉文件句柄
            if self.logger:
                for handler in self.logger.handlers[:]:
                    handler.close()
                    self.logger.removeHandler(handler)
        
if __name__ == '__main__':
    runner = BaseTestRunner("service")
    asyncio.run(runner.execute_load_test())