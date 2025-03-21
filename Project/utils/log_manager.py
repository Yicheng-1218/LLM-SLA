import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import regex as re

class CustomLogger(logging.Logger):
    """
    自訂 Logger 類別，增加 prettify_logger 方法。
    """
    def __init__(self, name, log_path,level=logging.INFO):
        super().__init__(name, level)
        self.log_path = log_path

    def prettify_logger(self) -> None:
        """
        美化日誌檔案的輸出，主要格式化日誌內容。
        """
        try:
            # 以讀寫模式打開檔案
            with open(self.log_path, 'r+', encoding='utf-8') as f:
                lines = f.read()
                report_matches = re.findall(r"=*\s測試結果\s=*.*", lines, re.MULTILINE|re.DOTALL)
                report = report_matches[0].strip() if report_matches else ""
                
                details_list = []
                index = 1
                while True:
                    details = re.findall(f"^.*測試瀏覽器:{index}"+r"\s.*$", lines, re.MULTILINE)
                    if not details:
                        break
                    details_list.append('\n'.join(details))
                    details_list.append('\n========================================================\n')
                    index += 1

                # 將檔案指標移回檔案開頭，並清空原內容
                f.seek(0)
                f.truncate()

                if report:
                    f.write(report)
                    f.write('\n\n======================= 測試細節 =======================\n')
                    
                if details_list:
                    for details in details_list:
                        f.write(details)
        except Exception as e:
            print(f'日誌美化失敗：{e}')

def setup_logger(
    service_name: str,
    log_dir: str = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> CustomLogger:
    """
    建立一個自訂 CustomLogger 實例，日誌檔案名稱格式：
      serviceX_YYYY-MM-DD-hh-mm-ss.log
    
    參數：
    - service_name: 服務名稱，例如 "service1"
    - log_dir: 儲存日誌的目錄，預設為當前目錄下的 "logs" 資料夾
    - level: 日誌級別，預設為 INFO
    - max_bytes: 每個日誌檔案的最大容量（Bytes），超過此容量會進行輪轉
    - backup_count: 保留的輪轉檔案數量

    回傳：
    - CustomLogger 實例
    """
    if log_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(base_dir, "..", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_filename = f"{service_name}_{timestamp}.log"
    log_path = os.path.join(log_dir, log_filename)

    logger = CustomLogger(service_name,log_path)
    logger.setLevel(level)
    logger.propagate = False  

    if logger.handlers:
        return logger

    # 設定日誌格式
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 檔案日誌處理器
    file_handler = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 控制台日誌處理器
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

# 測試
if __name__ == "__main__":
    logger = setup_logger("service1")
    logger.debug("這是 debug 級別的日誌")
    logger.info("這是 info 級別的日誌")
    logger.warning("這是 warning 級別的日誌")
    logger.error("這是 error 級別的日誌")
    logger.critical("這是 critical 級別的日誌")

    # 測試 prettify_logger()
    