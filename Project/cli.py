import asyncio
import importlib
import os
import logging
import argparse
from modules.base_runner import BaseTestRunner

async def run_test(service_name: str,log_level:str) -> None:
    """
    根據服務名稱執行對應的測試執行器。
    如果找到對應的客製化執行器就使用它，否則使用基礎執行器。
    
    參數:
    - service_name: 服務名稱
    - log_level: 日誌級別
    """
    # 轉換日誌級別字串為 logging 常數
    level_map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'error': logging.ERROR
    }
    # 檢查是否存在對應的 runner 文件
    runner_path = os.path.join("services", f"{service_name}_runner.py")
    if os.path.exists(runner_path):
        try:
            # 動態導入對應的 runner 模組
            module = importlib.import_module(f"services.{service_name}_runner")
            # 獲取 runner 類別（類別名稱為 {ServiceName}TestRunner）
            runner_class = getattr(module, f"{service_name.title()}TestRunner")
            print(f"使用 {service_name} 的客製化測試執行器")
        except (ImportError, AttributeError) as e:
            print(f"載入 {service_name} 的客製化執行器時發生錯誤: {e}")
            print("使用預設執行器")
            runner_class = BaseTestRunner
    else:
        print(f"使用預設執行器")
        runner_class = BaseTestRunner
    
    # 建立實例並執行測試
    runner = runner_class(service_name, log_level=level_map[log_level])
    await runner.execute_load_test()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='執行 AI 服務負載測試')
    parser.add_argument('service', help='要測試的服務名稱')
    # 日誌級別選項
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'error'],
        default='info',
        help='設定日誌級別 (預設: info)'
    )
    
    args = parser.parse_args()
    asyncio.run(run_test(args.service,args.log_level))