from modules.base_test_async import BaseTestAsync
from modules.base_runner import BaseTestRunner
import asyncio

# 你需要更新class的名稱以符合你的服務名稱
# 例如，如果你的服務名稱是"Service"，那麼class名稱應該是"ServiceTestRunner"
# 檔案名稱應確保格式是 "小寫服務名稱_runner.py"，並放在"services"資料夾下
# 你可以實作before_test和after_test方法
# 這兩個方法會在執行測試前後被呼叫
class ServiceTestRunner(BaseTestRunner):
    async def before_test(self, test_instance: BaseTestAsync) -> None:
        # TODO: Implement the before_test method
        pass
    
    async def after_test(self, test_instance: BaseTestAsync) -> None:
        # TODO: Implement the after_test method
        pass