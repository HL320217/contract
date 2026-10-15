"""
合同批量生成核心逻辑 - 整合模板处理和数据处理，生成各种格式的合同文档
"""

import os
from typing import List, Dict, Any, Optional, Callable
import logging

# 文档生成库
from docx import Document

# 本地模块
from template_processor import TemplateProcessor
from data_processor import DataProcessor
from config import get_output_path, ensure_directories

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContractGenerator:
    """合同批量生成器"""
    
    def __init__(self):
        self.template_processor = TemplateProcessor()
        self.data_processor = DataProcessor()
        self.progress_callback = None
        
    def set_progress_callback(self, callback: Callable[[int, str], None]):
        """
        设置进度回调函数
        
        Args:
            callback: 回调函数，参数为(progress_percent, status_message)
        """
        self.progress_callback = callback
    
    def _update_progress(self, percent: int, message: str):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(percent, message)
        logger.info(f"进度 {percent}%: {message}")
    
    def load_template(self, template_path: str) -> bool:
        """
        加载模板文件
        
        Args:
            template_path: 模板文件路径
            
        Returns:
            bool: 加载是否成功
        """
        self._update_progress(10, "正在加载模板...")
        success = self.template_processor.load_template(template_path)
        if success:
            self._update_progress(20, "模板加载完成")
        else:
            self._update_progress(0, "模板加载失败")
        return success
    
    def load_data(self, data_path: str) -> bool:
        """
        加载数据源文件
        
        Args:
            data_path: 数据源文件路径
            
        Returns:
            bool: 加载是否成功
        """
        self._update_progress(30, "正在加载数据源...")
        success = self.data_processor.load_data(data_path)
        if success:
            self._update_progress(40, "数据源加载完成")
        else:
            self._update_progress(0, "数据源加载失败")
        return success
    
    def validate_template_data_compatibility(self) -> Dict[str, Any]:
        """
        验证模板和数据源的兼容性
        
        Returns:
            Dict: 验证结果
        """
        template_vars = self.template_processor.get_variables()
        data_columns = self.data_processor.columns
        
        return self.template_processor.validate_data_mapping(data_columns)
    
    def generate_contracts(self, 
                         output_prefix: str = "contract") -> Dict[str, Any]:
        """
        生成所有合同文档
        
        Args:
            output_prefix: 输出文件名前缀
            
        Returns:
            Dict: 生成结果
        """
        try:
            self._update_progress(50, "开始生成合同...")
            
            # 确保输出目录存在
            ensure_directories()
            
            # 获取所有数据行
            all_data = self.data_processor.get_all_data()
            total_contracts = len(all_data)
            
            if total_contracts == 0:
                return {"success": False, "error": "没有数据可生成"}
            
            generated_files = []
            current_progress = 50
            progress_step = 40 / total_contracts  # 剩余40%的进度
            
            for i, row_data in enumerate(all_data):
                self._update_progress(
                    int(current_progress), 
                    f"正在生成第 {i+1}/{len(all_data)} 份合同..."
                )
                
                # 渲染模板内容
                rendered_content = self.template_processor.render_template(row_data)
                
                # 生成文件名（使用行索引或特定字段）
                file_suffix = f"_{i+1:03d}"
                if "姓名" in row_data:
                    file_suffix = f"_{row_data['姓名']}"
                elif "员工姓名" in row_data:
                    file_suffix = f"_{row_data['员工姓名']}"
                
                filename = f"{output_prefix}{file_suffix}"
                
                try:
                    file_path = self._generate_word(rendered_content, filename, row_data)
                    if file_path:
                        generated_files.append(file_path)
                    current_progress += progress_step
                except Exception as e:
                    logger.error(f"生成 Word 格式时发生错误: {str(e)}")
            
            self._update_progress(90, "正在完成...")
            
            result = {
                "success": True,
                "generated_files": generated_files,
                "total_files": len(generated_files),
                "contracts_count": len(all_data)
            }
            
            self._update_progress(100, f"生成完成！共生成 {len(generated_files)} 个文件")
            return result
            
        except Exception as e:
            error_msg = f"生成合同时发生错误: {str(e)}"
            logger.error(error_msg)
            self._update_progress(0, error_msg)
            return {"success": False, "error": error_msg}
    
    def generate_contracts_advanced(self, 
                                  output_prefix: str = "contract",
                                  advanced_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        高级合同生成，支持自定义命名规则和数据筛选
        
        Args:
            output_prefix: 输出文件名前缀
            advanced_options: 高级选项字典
            
        Returns:
            Dict: 生成结果
        """
        try:
            self._update_progress(50, "开始生成合同...")
            
            # 确保输出目录存在
            ensure_directories()
            
            # 获取数据
            all_data = self.data_processor.get_all_data()
            
            # 应用数据筛选
            if advanced_options and advanced_options.get("filter_enabled"):
                all_data = self._apply_data_filter(all_data, advanced_options)
            
            # 应用变量映射
            if advanced_options and advanced_options.get("variable_mapping"):
                all_data = self._apply_variable_mapping(all_data, advanced_options["variable_mapping"])
            
            total_contracts = len(all_data)
            
            if total_contracts == 0:
                return {"success": False, "error": "没有数据可生成"}
            
            generated_files = []
            current_progress = 50
            progress_step = 40 / total_contracts
            
            for i, row_data in enumerate(all_data):
                self._update_progress(
                    int(current_progress), 
                    f"正在生成第 {i+1}/{len(all_data)} 份合同..."
                )
                
                # 渲染模板内容
                rendered_content = self.template_processor.render_template(row_data)
                
                # 生成文件名
                filename = self._generate_filename(output_prefix, i, row_data, advanced_options)
                
                try:
                    file_path = self._generate_word(rendered_content, filename, row_data, advanced_options)
                    if file_path:
                        generated_files.append(file_path)
                    current_progress += progress_step
                except Exception as e:
                    logger.error(f"生成 Word 格式时发生错误: {str(e)}")
            
            self._update_progress(90, "正在完成...")
            
            result = {
                "success": True,
                "generated_files": generated_files,
                "total_files": len(generated_files),
                "contracts_count": len(all_data)
            }
            
            self._update_progress(100, f"生成完成！共生成 {len(generated_files)} 个文件")
            return result
            
        except Exception as e:
            error_msg = f"生成合同时发生错误: {str(e)}"
            logger.error(error_msg)
            self._update_progress(0, error_msg)
            return {"success": False, "error": error_msg}
    
    def _apply_data_filter(self, data: List[Dict[str, Any]], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """应用数据筛选"""
        try:
            filter_column = options.get("filter_column")
            filter_condition = options.get("filter_condition")
            filter_value = options.get("filter_value", "").strip()
            
            if not filter_column or not filter_value:
                return data
            
            filtered_data = []
            
            for row in data:
                cell_value = str(row.get(filter_column, "")).strip()
                
                if filter_condition == "等于":
                    if cell_value == filter_value:
                        filtered_data.append(row)
                elif filter_condition == "不等于":
                    if cell_value != filter_value:
                        filtered_data.append(row)
                elif filter_condition == "包含":
                    if filter_value in cell_value:
                        filtered_data.append(row)
                elif filter_condition == "不包含":
                    if filter_value not in cell_value:
                        filtered_data.append(row)
                elif filter_condition == "大于":
                    try:
                        if float(cell_value) > float(filter_value):
                            filtered_data.append(row)
                    except ValueError:
                        pass
                elif filter_condition == "小于":
                    try:
                        if float(cell_value) < float(filter_value):
                            filtered_data.append(row)
                    except ValueError:
                        pass
            
            logger.info(f"数据筛选: {len(data)} -> {len(filtered_data)} 行")
            return filtered_data
            
        except Exception as e:
            logger.error(f"应用数据筛选时发生错误: {str(e)}")
            return data
    
    def _apply_variable_mapping(self, data: List[Dict[str, Any]], mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """应用变量映射"""
        try:
            if not mapping:
                return data
            
            mapped_data = []
            
            for row in data:
                mapped_row = {}
                
                # 应用映射
                for template_var, data_column in mapping.items():
                    if data_column in row:
                        mapped_row[template_var] = row[data_column]
                    else:
                        mapped_row[template_var] = ""
                
                # 保留未映射的原始数据
                for key, value in row.items():
                    if key not in mapped_row.values():
                        mapped_row[key] = value
                
                mapped_data.append(mapped_row)
            
            return mapped_data
            
        except Exception as e:
            logger.error(f"应用变量映射时发生错误: {str(e)}")
            return data
    
    def _generate_filename(self, prefix: str, index: int, row_data: Dict[str, Any], 
                          options: Dict[str, Any] = None) -> str:
        """生成文件名"""
        try:
            if not options:
                return f"{prefix}_{index+1:03d}"
            
            naming_rule = options.get("naming_rule", "序号")
            naming_column = options.get("naming_column", "")
            naming_columns = options.get("naming_columns", [])
            separator = options.get("separator", "_")
            
            if naming_rule == "序号":
                return f"{index+1:03d}"
            elif naming_rule == "使用数据列" and naming_column:
                column_value = str(row_data.get(naming_column, f"{index+1:03d}"))
                column_value = self._clean_filename(column_value)
                return column_value or f"{index+1:03d}"
            elif naming_rule == "前缀+序号":
                return f"{prefix}_{index+1:03d}"
            elif naming_rule == "前缀+数据列" and naming_column:
                column_value = str(row_data.get(naming_column, f"{index+1:03d}"))
                column_value = self._clean_filename(column_value)
                return f"{prefix}_{column_value}" if column_value else f"{prefix}_{index+1:03d}"
            elif naming_rule == "多列组合" and naming_columns:
                # 多列组合命名
                values = []
                for column in naming_columns:
                    value = str(row_data.get(column, ""))
                    value = self._clean_filename(value)
                    if value:
                        values.append(value)
                
                if values:
                    return separator.join(values)
                else:
                    return f"{prefix}_{index+1:03d}"
            else:
                return f"{prefix}_{index+1:03d}"
                
        except Exception as e:
            logger.error(f"生成文件名时发生错误: {str(e)}")
            return f"{prefix}_{index+1:03d}"
    
    def _clean_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        # 移除或替换Windows文件名中的非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '')
        
        # 只保留字母数字和常用符号
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
        
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename
    
    def _generate_word(self, content: str, filename: str, data: Dict[str, Any], options: Dict[str, Any] = None) -> Optional[str]:
        """生成Word文档 - 基于原模板替换占位符"""
        try:
            custom_output_dir = options.get("output_path") if options else None
            output_path = get_output_path(filename, "word", custom_output_dir)
            
            # 如果原模板是Word格式，直接基于模板替换
            if self.template_processor.template_type == '.docx':
                return self._generate_word_from_template(output_path, data)
            else:
                # 如果原模板是文本格式，创建简单的Word文档
                return self._generate_word_from_text(content, output_path)
            
        except Exception as e:
            logger.error(f"生成Word文档时发生错误: {str(e)}")
            return None
    
    def _generate_word_from_template(self, output_path: str, data: Dict[str, Any]) -> Optional[str]:
        """基于Word模板生成文档，保持原有格式"""
        try:
            from docx import Document
            import shutil
            
            # 复制原模板文件
            shutil.copy2(self.template_processor.template_path, output_path)
            
            # 打开复制的文档
            doc = Document(output_path)
            
            # 替换段落中的占位符，保持格式
            for paragraph in doc.paragraphs:
                self._replace_paragraph_text(paragraph, data)
            
            # 替换表格中的占位符
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            self._replace_paragraph_text(paragraph, data)
            
            # 替换页眉页脚中的占位符
            for section in doc.sections:
                # 页眉
                if section.header:
                    for paragraph in section.header.paragraphs:
                        self._replace_paragraph_text(paragraph, data)
                
                # 页脚
                if section.footer:
                    for paragraph in section.footer.paragraphs:
                        self._replace_paragraph_text(paragraph, data)
            
            # 保存文档
            doc.save(output_path)
            logger.info(f"Word文档生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"基于Word模板生成文档时发生错误: {str(e)}")
            return None
    
    def _replace_paragraph_text(self, paragraph, data: Dict[str, Any]):
        """替换段落中的占位符，保持原有格式"""
        try:
            # 遍历段落中的所有run（文本片段）
            for run in paragraph.runs:
                original_text = run.text
                modified_text = original_text
                
                # 对每个变量进行替换
                for var_name, value in data.items():
                    placeholder = f"{{{{ {var_name} }}}}"
                    placeholder_no_space = f"{{{{{var_name}}}}}"
                    
                    # 替换占位符
                    if placeholder in modified_text:
                        modified_text = modified_text.replace(placeholder, str(value))
                    if placeholder_no_space in modified_text:
                        modified_text = modified_text.replace(placeholder_no_space, str(value))
                
                # 如果文本有变化，更新run的文本（保持原有格式）
                if modified_text != original_text:
                    run.text = modified_text
            
            # 如果上面的方法没有完全替换（可能占位符跨越多个run），使用备用方法
            full_text = paragraph.text
            has_placeholder = False
            
            for var_name in data.keys():
                placeholder = f"{{{{ {var_name} }}}}"
                placeholder_no_space = f"{{{{{var_name}}}}}"
                if placeholder in full_text or placeholder_no_space in full_text:
                    has_placeholder = True
                    break
            
            if has_placeholder:
                # 如果还有占位符，说明占位符可能跨越多个run，需要重建段落
                self._rebuild_paragraph_with_format(paragraph, data)
                
        except Exception as e:
            logger.error(f"替换段落文本时发生错误: {str(e)}")
            # 如果出错，使用最简单的替换方法
            try:
                for var_name, value in data.items():
                    placeholder = f"{{{{ {var_name} }}}}"
                    placeholder_no_space = f"{{{{{var_name}}}}}"
                    if placeholder in paragraph.text:
                        paragraph.text = paragraph.text.replace(placeholder, str(value))
                    if placeholder_no_space in paragraph.text:
                        paragraph.text = paragraph.text.replace(placeholder_no_space, str(value))
            except:
                pass
    
    def _rebuild_paragraph_with_format(self, paragraph, data: Dict[str, Any]):
        """重建段落，保持格式（当占位符跨越多个run时使用）"""
        try:
            # 获取段落的完整文本
            full_text = paragraph.text
            
            # 替换所有占位符
            for var_name, value in data.items():
                placeholder = f"{{{{ {var_name} }}}}"
                placeholder_no_space = f"{{{{{var_name}}}}}"
                
                if placeholder in full_text:
                    full_text = full_text.replace(placeholder, str(value))
                if placeholder_no_space in full_text:
                    full_text = full_text.replace(placeholder_no_space, str(value))
            
            # 保存第一个run的格式作为默认格式
            default_format = None
            if paragraph.runs:
                first_run = paragraph.runs[0]
                default_format = {
                    'font_name': first_run.font.name,
                    'font_size': first_run.font.size,
                    'bold': first_run.font.bold,
                    'italic': first_run.font.italic,
                    'underline': first_run.font.underline,
                    'color': first_run.font.color.rgb if first_run.font.color.rgb else None
                }
            
            # 清空段落
            paragraph.clear()
            
            # 添加新的文本，应用保存的格式
            new_run = paragraph.add_run(full_text)
            
            if default_format:
                if default_format['font_name']:
                    new_run.font.name = default_format['font_name']
                if default_format['font_size']:
                    new_run.font.size = default_format['font_size']
                if default_format['bold'] is not None:
                    new_run.font.bold = default_format['bold']
                if default_format['italic'] is not None:
                    new_run.font.italic = default_format['italic']
                if default_format['underline'] is not None:
                    new_run.font.underline = default_format['underline']
                if default_format['color']:
                    new_run.font.color.rgb = default_format['color']
                    
        except Exception as e:
            logger.error(f"重建段落格式时发生错误: {str(e)}")
            # 最后的备用方案
            paragraph.text = paragraph.text.replace('{{', '').replace('}}', '')
    
    def _generate_word_from_text(self, content: str, output_path: str) -> Optional[str]:
        """基于文本内容生成Word文档"""
        try:
            from docx import Document
            
            doc = Document()
            
            # 直接添加渲染后的内容，不添加额外的标题和时间
            paragraphs = content.split('\n')
            for para in paragraphs:
                doc.add_paragraph(para)
            
            doc.save(output_path)
            logger.info(f"Word文档生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"基于文本生成Word文档时发生错误: {str(e)}")
            return None
    
    
    
    def get_generation_preview(self, row_index: int = 0) -> Dict[str, Any]:
        """
        获取生成预览
        
        Args:
            row_index: 预览的数据行索引
            
        Returns:
            Dict: 预览信息
        """
        try:
            # 获取指定行数据
            row_data = self.data_processor.get_row_data(row_index)
            if not row_data:
                return {"error": "无法获取数据行"}
            
            # 渲染模板
            rendered_content = self.template_processor.render_template(row_data)
            
            return {
                "success": True,
                "data": row_data,
                "rendered_content": rendered_content[:1000] + "..." if len(rendered_content) > 1000 else rendered_content,
                "full_length": len(rendered_content)
            }
            
        except Exception as e:
            logger.error(f"获取生成预览时发生错误: {str(e)}")
            return {"error": str(e)}
    
    def get_status_info(self) -> Dict[str, Any]:
        """
        获取当前状态信息
        
        Returns:
            Dict: 状态信息
        """
        return {
            "template_loaded": self.template_processor.template_path is not None,
            "data_loaded": self.data_processor.data is not None,
            "template_info": self.template_processor.get_template_info() if self.template_processor.template_path else None,
            "data_info": {
                "row_count": self.data_processor.row_count,
                "columns": self.data_processor.columns
            } if self.data_processor.data is not None else None,
            "compatibility": self.validate_template_data_compatibility() if (
                self.template_processor.template_path and self.data_processor.data is not None
            ) else None
        }
