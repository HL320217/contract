"""
配置文件 - 合同生成器配置参数
"""

import os

# 应用程序配置
APP_NAME = "合同批量生成器"
APP_VERSION = "2.0.0"
APP_AUTHOR = "合同批量生成器"

# 文件路径配置
DEFAULT_OUTPUT_DIR = "generated_contracts"
TEMP_DIR = "temp"

# 支持的文件格式
SUPPORTED_TEMPLATE_FORMATS = [".docx"]
SUPPORTED_DATA_FORMATS = [".xlsx", ".xls", ".csv", ".json"]
OUTPUT_FORMATS = ["word"]

# GUI配置
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_MIN_WIDTH = 600
WINDOW_MIN_HEIGHT = 400

# 模板变量配置
VARIABLE_PREFIX = "{{"
VARIABLE_SUFFIX = "}}"
VARIABLE_PATTERN = r'\{\{([^}]+)\}\}'

# 文件大小限制 (MB)
MAX_TEMPLATE_SIZE = 50
MAX_DATA_SIZE = 100

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 错误消息
ERROR_MESSAGES = {
    "file_not_found": "文件未找到",
    "invalid_format": "不支持的文件格式",
    "template_error": "模板处理错误",
    "data_error": "数据源处理错误",
    "generation_error": "合同生成错误",
    "file_too_large": "文件大小超出限制"
}

# 成功消息
SUCCESS_MESSAGES = {
    "generation_complete": "合同生成完成",
    "file_saved": "文件保存成功"
}

def ensure_directories():
    """确保必要的目录存在"""
    directories = [DEFAULT_OUTPUT_DIR, TEMP_DIR]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

def get_output_path(filename, format_type, custom_output_dir=None):
    """获取输出文件路径"""
    output_dir = custom_output_dir if custom_output_dir else DEFAULT_OUTPUT_DIR
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    extension_map = {
        "word": ".docx"
    }
    
    base_name = os.path.splitext(filename)[0]
    extension = extension_map.get(format_type, ".docx")
    
    return os.path.join(output_dir, f"{base_name}{extension}")
