"""
模板处理模块 - 处理Word、TXT模板文件，提取变量并进行替换
"""

import os
import re
from typing import List, Dict, Any, Optional, Set
import logging
from docx import Document
from jinja2 import Environment, BaseLoader
from config import (
    SUPPORTED_TEMPLATE_FORMATS, 
    MAX_TEMPLATE_SIZE, 
    VARIABLE_PATTERN,
    VARIABLE_PREFIX,
    VARIABLE_SUFFIX
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemplateProcessor:
    """模板处理器"""
    
    def __init__(self):
        self.template_path = None
        self.template_type = None
        self.template_content = ""
        self.variables = set()
        self.jinja_env = Environment(loader=BaseLoader())
        
    def load_template(self, file_path: str) -> bool:
        """
        加载模板文件
        
        Args:
            file_path: 模板文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"模板文件不存在: {file_path}")
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            if file_size > MAX_TEMPLATE_SIZE:
                logger.error(f"模板文件大小超出限制: {file_size:.2f}MB > {MAX_TEMPLATE_SIZE}MB")
                return False
            
            # 获取文件扩展名
            _, ext = os.path.splitext(file_path.lower())
            
            if ext not in SUPPORTED_TEMPLATE_FORMATS:
                logger.error(f"不支持的模板格式: {ext}")
                return False
            
            self.template_path = file_path
            self.template_type = ext
            
            # 根据文件类型加载内容
            if ext == '.docx':
                success = self._load_docx_template(file_path)
            elif ext == '.txt':
                logger.error("不支持的模板格式: .txt")
                return False
            elif ext == '.pdf':
                logger.error("不支持的模板格式: .pdf")
                return False
            else:
                logger.error(f"未实现的模板类型: {ext}")
                return False
            
            if success:
                # 提取模板变量
                self._extract_variables()
                logger.info(f"成功加载模板: {len(self.variables)}个变量")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"加载模板时发生错误: {str(e)}")
            return False
    
    def _load_docx_template(self, file_path: str) -> bool:
        """加载Word模板"""
        try:
            doc = Document(file_path)
            content_parts = []
            
            # 提取段落文本
            for paragraph in doc.paragraphs:
                content_parts.append(paragraph.text)
            
            # 提取表格文本
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        content_parts.append(cell.text)
            
            self.template_content = '\n'.join(content_parts)
            return True
            
        except Exception as e:
            logger.error(f"加载Word模板时发生错误: {str(e)}")
            return False
    
    # 已移除文本模板支持
    
    
    def _extract_variables(self):
        """从模板内容中提取变量"""
        try:
            # 使用正则表达式查找变量
            matches = re.findall(VARIABLE_PATTERN, self.template_content)
            self.variables = set()
            
            for match in matches:
                # 清理变量名（去除空格）
                var_name = match.strip()
                if var_name:
                    self.variables.add(var_name)
            
            logger.info(f"提取到变量: {list(self.variables)}")
            
        except Exception as e:
            logger.error(f"提取变量时发生错误: {str(e)}")
            self.variables = set()
    
    def get_variables(self) -> List[str]:
        """
        获取模板中的所有变量
        
        Returns:
            List[str]: 变量名列表
        """
        return sorted(list(self.variables))
    
    def get_template_preview(self, max_length: int = 500) -> str:
        """
        获取模板内容预览
        
        Args:
            max_length: 最大预览长度
            
        Returns:
            str: 模板内容预览
        """
        if len(self.template_content) <= max_length:
            return self.template_content
        else:
            return self.template_content[:max_length] + "..."
    
    def validate_data_mapping(self, data_columns: List[str]) -> Dict[str, Any]:
        """
        验证数据列是否能满足模板变量需求
        
        Args:
            data_columns: 数据源的列名列表
            
        Returns:
            Dict: 验证结果
        """
        missing_vars = []
        available_vars = []
        
        for var in self.variables:
            if var in data_columns:
                available_vars.append(var)
            else:
                missing_vars.append(var)
        
        return {
            "valid": len(missing_vars) == 0,
            "missing_variables": missing_vars,
            "available_variables": available_vars,
            "total_variables": len(self.variables)
        }
    
    def render_template(self, data: Dict[str, Any]) -> str:
        """
        使用数据渲染模板
        
        Args:
            data: 用于替换的数据字典
            
        Returns:
            str: 渲染后的内容
        """
        try:
            # 使用Jinja2进行模板渲染
            template = self.jinja_env.from_string(self.template_content)
            rendered_content = template.render(**data)
            return rendered_content
            
        except Exception as e:
            logger.error(f"渲染模板时发生错误: {str(e)}")
            # 如果Jinja2渲染失败，尝试简单的字符串替换
            return self._simple_render(data)
    
    def _simple_render(self, data: Dict[str, Any]) -> str:
        """
        简单的字符串替换渲染
        
        Args:
            data: 用于替换的数据字典
            
        Returns:
            str: 渲染后的内容
        """
        try:
            rendered_content = self.template_content
            
            for var_name, value in data.items():
                # 构造变量占位符
                placeholder = f"{VARIABLE_PREFIX}{var_name}{VARIABLE_SUFFIX}"
                # 替换所有出现的占位符
                rendered_content = rendered_content.replace(placeholder, str(value))
            
            return rendered_content
            
        except Exception as e:
            logger.error(f"简单渲染时发生错误: {str(e)}")
            return self.template_content
    
    def get_template_info(self) -> Dict[str, Any]:
        """
        获取模板信息
        
        Returns:
            Dict: 模板信息
        """
        return {
            "path": self.template_path,
            "type": self.template_type,
            "variables": self.get_variables(),
            "variable_count": len(self.variables),
            "content_length": len(self.template_content),
            "preview": self.get_template_preview()
        }
