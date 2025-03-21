import os
import json
from typing import Any,Dict
def load_config(service_name)-> Dict[str,Any]:
    """ 根據服務名稱讀取對應的配置文件，配置文件放在 configs/ 目錄下，
        文件名格式: service1.json
    Args:
        service_name (str): 服務名稱
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(base_dir,"..","configs")
    file_path = os.path.join(config_dir, f"{service_name}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到配置文件: {file_path}")
    # 讀取json配置
    with open(file_path,'r',encoding='utf-8') as f:
        config = json.load(f)
    return config