from flask import Flask, render_template, request, jsonify
import json
import os
import asyncio
from modules.base_runner import BaseTestRunner
from modules.detect_selector import detect_input_selector
import importlib
import sys

app = Flask(__name__)

def format_selector(config: dict) -> dict:
    new_config = config.copy()
     # 如果 selector 是 xpath，則加上 "xpath=" 前綴
    new_config['input_selector'] = f"xpath={new_config['input_selector']}" if any(
        new_config["input_selector"].startswith(p) for p in ("//", "(//")
    ) else new_config["input_selector"]
    
    new_config['response_selector'] = f"xpath={new_config['response_selector']}" if any(
        new_config["response_selector"].startswith(p) for p in ("//", "(//")
    ) else new_config["response_selector"]
    return new_config

@app.route('/')
def index():
    # 讀取現有的配置檔案列表
    config_dir = os.path.join(os.path.dirname(__file__), "configs")
    configs = [f.replace('.json', '') for f in os.listdir(config_dir) if f.endswith('.json')]
    return render_template('index.html', configs=configs)

@app.route('/create_config', methods=['POST'])
def create_config():
    try:
        data = request.json
        config_name = data['name']
        required_fields = {
            'name': 'AI 服務名稱','url': 'AI 服務網址', 'input_selector': '輸入框選擇器','response_selector': '回應選擇器',
            'test_prompts': '測試提示詞', 'concurrency': '同時使用人數', 'test_duration': '測試持續時間(秒)'}
        for field in required_fields.keys():
            if field not in data or not data[field]:
                raise ValueError(f"缺少必填項目: {required_fields[field]}")
            
        # 修正選擇器的格式
        data = format_selector(data)
        
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "configs", 
            f"{config_name}.json"
        )
        if os.path.exists(config_path):
            raise ValueError(f"名為 {config_name} 的配置文件已存在")
        
        # 寫入檔案
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        return jsonify({"status": "success"})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_config/<config_name>')
def get_config(config_name):
    try:
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "configs", 
            f"{config_name}.json"
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/update_config', methods=['POST'])
def update_config():
    try:
        data = request.json
        config_name = data['name']
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "configs", 
            f"{config_name}.json"
        )
        data = format_selector(data)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/delete_config/<config_name>', methods=['DELETE'])
def delete_config(config_name):
    try:
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "configs", 
            f"{config_name}.json"
        )
        os.remove(config_path)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/detect_selector', methods=['POST'])
def detect_selector():
    try:
        print('執行自動偵測輸入框選擇器')
        url = request.form['url']
        result = detect_input_selector(url)
        return jsonify({"status": "success", "selector": result})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "error", "message": "偵測失敗，請手動輸入"}), 500

@app.route('/run_test', methods=['POST'])
def run_test():
    try:
        service_name = request.form['service']
        os.chdir(os.path.dirname(__file__))
        config_path = os.path.join("configs",f"{service_name}.json")
        if not os.path.exists(config_path):
            raise ValueError(f"找不到名為 {service_name} 的配置文件")

        # 檢查是否存在對應的 runner 文件
        runner_name = service_name.lower().split('_')[0].strip()
        runner_path = os.path.join("services", f"{runner_name}_runner.py")
        if os.path.exists(runner_path):
            try:
                # 動態導入對應的 runner 模組
                module = importlib.import_module(f"services.{runner_name}_runner")
                # 獲取 runner 類別（類別名稱為 {runner_name}TestRunner）
                runner_class = getattr(module, f"{runner_name.title()}TestRunner")
                print(f"使用 {runner_name} 的客製化測試執行器")
            except (ImportError, AttributeError) as e:
                print(f"載入 {runner_name} 的客製化執行器時發生錯誤: {e}")
                print("使用預設執行器")
                runner_class = BaseTestRunner
        else:
            print(f"使用預設執行器")
            runner_class = BaseTestRunner
        
        # 建立實例並執行測試
        runner = runner_class(service_name)
        result = asyncio.run(runner.execute_load_test())
        return jsonify({"status": "success", "results": result})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"status": "error", "message": "測試失敗"}), 500

if __name__ == '__main__':
    app.run(debug=True)