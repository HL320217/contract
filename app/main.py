"""
主程序 - 合同生成器GUI界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from typing import Optional
import logging
from PIL import Image, ImageTk, ImageDraw
import sys

from contract_generator import ContractGenerator
from config import (
    APP_NAME, APP_VERSION, 
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    SUPPORTED_TEMPLATE_FORMATS, SUPPORTED_DATA_FORMATS
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContractGeneratorGUI:
    """合同生成器GUI应用"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.generator = ContractGenerator()
        self.template_path = None
        self.data_path = None
        self._create_app_icon()
        self.root.iconphoto(True, self.app_icon)
        
        self.setup_ui()
        self.setup_generator_callback()
    
    def _create_app_icon(self):
        size = (64, 64)
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        color = (135, 206, 235, 255)
        d.rounded_rectangle([14, 10, 22, 54], radius=3, fill=color)
        d.rounded_rectangle([42, 10, 50, 54], radius=3, fill=color)
        d.rounded_rectangle([14, 28, 50, 36], radius=3, fill=color)
        self.app_icon = ImageTk.PhotoImage(img)
        try:
            os.makedirs('img', exist_ok=True)
            img.save('img/logo.png', format='PNG')
            img.save('img/favicon.ico', format='ICO', sizes=[(64, 64), (32, 32), (16, 16)])
        except Exception:
            pass
        
    def setup_ui(self):
        """设置用户界面"""
        self.apply_modern_theme()
        # 窗口配置
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("900x650")   # 增加窗口宽度以适应居中布局
        self.root.minsize(800, 550)     # 增加最小窗口宽度
        
        # 配置主窗口网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 创建主滚动框架
        self.create_scrollable_main_frame()
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))

    def _get_img_path(self, filename: str) -> Optional[str]:
        try:
            candidates = []
            if hasattr(sys, '_MEIPASS'):
                candidates.append(os.path.join(sys._MEIPASS, 'img', filename))
            candidates.append(os.path.join(os.path.dirname(__file__), 'img', filename))
            candidates.append(os.path.join('img', filename))
            for p in candidates:
                if os.path.exists(p):
                    return p
            return None
        except Exception:
            return None
    
    def create_scrollable_main_frame(self):
        """创建可滚动的主框架"""
        # 创建Canvas和滚动条
        self.canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # 配置滚动
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # 绑定Canvas大小变化事件，确保内容居中
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局Canvas和滚动条
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 绑定鼠标滚轮事件到Canvas和所有子组件
        self._bind_mousewheel(self.canvas)
        self._bind_mousewheel(self.scrollable_frame)
        
        # 延迟绑定滚轮事件到所有子组件
        self.root.after(100, self._bind_all_mousewheel)
        
        # 配置scrollable_frame的网格权重，实现居中布局
        self.scrollable_frame.columnconfigure(0, weight=1)  # 左侧空白
        self.scrollable_frame.columnconfigure(1, weight=0)  # 主内容区域
        self.scrollable_frame.columnconfigure(2, weight=1)  # 右侧空白
        
        # 创建主内容框架，限制最大宽度并居中
        main_frame = ttk.Frame(self.scrollable_frame, padding="20")
        main_frame.grid(row=0, column=1, sticky=(tk.N, tk.S), padx=40, pady=10)
        
        # 配置主内容框架的网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=0)  # 标签列不扩展
        main_frame.columnconfigure(2, weight=1)  # 输入列扩展
        
        # 创建界面组件
        self.create_file_selection_section(main_frame)
        self.create_options_section(main_frame)
        self.create_output_path_section(main_frame)  # 新增输出路径选择
        self.create_advanced_options_section(main_frame)  # 高级选项
        self.create_mapping_section(main_frame)  # 变量映射
        self.create_progress_section(main_frame)
        self.create_action_buttons(main_frame)
    
    def _bind_mousewheel(self, widget):
        """递归绑定鼠标滚轮事件到所有子组件"""
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)  # Linux
        widget.bind("<Button-5>", self._on_mousewheel)  # Linux
        
        # 递归绑定到所有子组件
        for child in widget.winfo_children():
            self._bind_mousewheel(child)
    
    def _bind_all_mousewheel(self):
        """延迟绑定所有子组件的鼠标滚轮事件"""
        self._bind_mousewheel(self.scrollable_frame)
    
    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        # Windows和MacOS
        if event.delta:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        # Linux
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
    
    def _on_canvas_configure(self, event):
        """处理Canvas大小变化事件"""
        # 更新scrollable_frame的宽度以匹配Canvas宽度
        canvas_width = event.width
        # 确保Canvas中有窗口项目再进行配置
        if self.canvas.find_all():
            self.canvas.itemconfig(self.canvas.find_all()[0], width=canvas_width)
        
    def create_file_selection_section(self, parent):
        """创建文件选择区域"""
        # 文件选择框架
        file_frame = ttk.LabelFrame(parent, text="文件选择", padding="10", style="Section.TLabelframe")
        file_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        file_frame.columnconfigure(1, weight=1)
        
        # 设置框架的最小宽度
        file_frame.configure(width=600)
        
        ttk.Label(file_frame, text="合同模板:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.template_var = tk.StringVar()
        template_entry = ttk.Entry(file_frame, textvariable=self.template_var, state="readonly", width=60)
        template_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(file_frame, text="浏览", command=self.select_template_file, width=8).grid(row=0, column=2)
        ttk.Button(file_frame, text="清空", command=self.clear_template, width=8).grid(row=0, column=3)
        
        ttk.Label(file_frame, text="数据源:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.data_var = tk.StringVar()
        data_entry = ttk.Entry(file_frame, textvariable=self.data_var, state="readonly", width=60)
        data_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))
        ttk.Button(file_frame, text="浏览", command=self.select_data_file, width=8).grid(row=1, column=2, pady=(10, 0))
        ttk.Button(file_frame, text="清空", command=self.clear_data, width=8).grid(row=1, column=3, pady=(10, 0))
        
    def create_options_section(self, parent):
        """创建选项设置区域"""
        options_frame = ttk.LabelFrame(parent, text="生成选项", padding="10", style="Section.TLabelframe")
        options_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        options_frame.configure(width=600)

        ttk.Label(options_frame, text="输出格式:").grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Label(options_frame, text=".docx").grid(row=0, column=1, sticky=tk.W)

        ttk.Label(options_frame, text="文件名前缀:").grid(row=1, column=0, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        self.prefix_var = tk.StringVar(value="contract")
        ttk.Entry(options_frame, textvariable=self.prefix_var, width=20).grid(
            row=1, column=1, sticky=tk.W, pady=(10, 0)
        )
    
    def create_output_path_section(self, parent):
        """创建输出路径选择区域"""
        # 输出路径框架
        path_frame = ttk.LabelFrame(parent, text="输出设置", padding="10", style="Section.TLabelframe")
        path_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        path_frame.columnconfigure(1, weight=1)
        path_frame.configure(width=600)
        
        # 输出路径选择
        ttk.Label(path_frame, text="保存路径:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.output_path_var = tk.StringVar(value="默认路径 (generated_contracts)")
        self.output_path_entry = ttk.Entry(path_frame, textvariable=self.output_path_var, state="readonly")
        self.output_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(path_frame, text="选择路径", command=self.select_output_path).grid(row=0, column=2, sticky=tk.W)
        ttk.Button(path_frame, text="重置", command=self.reset_output_path).grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # 存储实际路径
        self.actual_output_path = None
    
    def select_output_path(self):
        """选择输出路径"""
        from tkinter import filedialog
        
        path = filedialog.askdirectory(
            title="选择合同输出目录",
            initialdir=os.getcwd()
        )
        
        if path:
            self.actual_output_path = path
            # 显示简化的路径
            if len(path) > 50:
                display_path = "..." + path[-47:]
            else:
                display_path = path
            self.output_path_var.set(display_path)
    
    def reset_output_path(self):
        """重置为默认路径"""
        self.actual_output_path = None
        self.output_path_var.set("默认路径 (generated_contracts)")
    
    def clear_template(self):
        self.template_path = None
        self.template_var.set("")
    
    def clear_data(self):
        self.data_path = None
        self.data_var.set("")
    
    def create_advanced_options_section(self, parent):
        """创建高级选项区域"""
        # 高级选项框架
        advanced_frame = ttk.LabelFrame(parent, text="高级选项", padding="10", style="Section.TLabelframe")
        advanced_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        advanced_frame.columnconfigure(1, weight=1)
        advanced_frame.configure(width=600)
        
        # 文件命名规则
        ttk.Label(advanced_frame, text="文件命名规则:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.naming_var = tk.StringVar(value="序号")
        naming_combo = ttk.Combobox(advanced_frame, textvariable=self.naming_var, width=18, state="readonly")
        naming_combo['values'] = ("序号", "使用数据列", "前缀+序号", "前缀+数据列", "多列组合")
        naming_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 命名数据列选择框架
        naming_columns_frame = ttk.Frame(advanced_frame)
        naming_columns_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        naming_columns_frame.columnconfigure(1, weight=1)
        
        ttk.Label(naming_columns_frame, text="命名列:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # 单列选择
        self.naming_column_var = tk.StringVar()
        self.naming_column_combo = ttk.Combobox(naming_columns_frame, textvariable=self.naming_column_var, width=18, state="readonly")
        self.naming_column_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 多列选择框架
        self.multi_columns_frame = ttk.Frame(naming_columns_frame)
        self.multi_columns_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 多列选择区域
        multi_columns_list_frame = ttk.Frame(self.multi_columns_frame)
        multi_columns_list_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        multi_columns_list_frame.columnconfigure(0, weight=1)
        multi_columns_list_frame.columnconfigure(1, weight=1)
        
        # 可选列复选框区域
        available_frame = ttk.LabelFrame(multi_columns_list_frame, text="可选列", padding="5", style="Section.TLabelframe")
        available_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # 创建滚动框架用于复选框
        self.available_canvas = tk.Canvas(available_frame, height=80)
        available_scrollbar = ttk.Scrollbar(available_frame, orient="vertical", command=self.available_canvas.yview)
        self.available_scrollable_frame = ttk.Frame(self.available_canvas)
        
        self.available_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.available_canvas.configure(scrollregion=self.available_canvas.bbox("all"))
        )
        
        self.available_canvas.create_window((0, 0), window=self.available_scrollable_frame, anchor="nw")
        self.available_canvas.configure(yscrollcommand=available_scrollbar.set)
        
        self.available_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        available_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 已选列显示区域
        selected_frame = ttk.LabelFrame(multi_columns_list_frame, text="已选列（按顺序）", padding="5", style="Section.TLabelframe")
        selected_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        self.selected_columns_listbox = tk.Listbox(selected_frame, height=4, width=20)
        selected_scrollbar = ttk.Scrollbar(selected_frame, orient="vertical", command=self.selected_columns_listbox.yview)
        self.selected_columns_listbox.configure(yscrollcommand=selected_scrollbar.set)
        
        self.selected_columns_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        selected_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 操作按钮
        buttons_frame = ttk.Frame(selected_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        ttk.Button(buttons_frame, text="↑ 上移", command=self.move_naming_column_up, width=8).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(buttons_frame, text="↓ 下移", command=self.move_naming_column_down, width=8).grid(row=0, column=1, padx=(5, 0))
        
        # 存储复选框变量
        self.column_checkboxes = {}
        self.column_vars = {}
        
        # 分隔符设置
        separator_frame = ttk.Frame(self.multi_columns_frame)
        separator_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Label(separator_frame, text="分隔符:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.separator_var = tk.StringVar(value="_")
        separator_combo = ttk.Combobox(separator_frame, textvariable=self.separator_var, width=10, state="readonly")
        separator_combo['values'] = ("_", "-", " ", ".", "")
        separator_combo.grid(row=0, column=1, sticky=tk.W)
        
        # 初始状态下隐藏多列选择
        self.multi_columns_frame.grid_remove()
        
        # 数据筛选
        ttk.Label(advanced_frame, text="数据筛选:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(20, 0))
        self.filter_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(advanced_frame, text="启用筛选", variable=self.filter_enabled_var, 
                       command=self.toggle_filter_options).grid(row=2, column=1, sticky=tk.W, pady=(20, 0))
        
        # 筛选条件框架
        self.filter_frame = ttk.Frame(advanced_frame)
        self.filter_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        self.filter_frame.columnconfigure(1, weight=1)
        
        # 筛选列
        ttk.Label(self.filter_frame, text="筛选列:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.filter_column_var = tk.StringVar()
        self.filter_column_combo = ttk.Combobox(self.filter_frame, textvariable=self.filter_column_var, width=15, state="readonly")
        self.filter_column_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # 筛选条件
        ttk.Label(self.filter_frame, text="条件:").grid(row=0, column=2, sticky=tk.W, padx=(10, 10))
        self.filter_condition_var = tk.StringVar(value="等于")
        filter_condition_combo = ttk.Combobox(self.filter_frame, textvariable=self.filter_condition_var, width=8, state="readonly")
        filter_condition_combo['values'] = ("等于", "不等于", "包含", "不包含", "大于", "小于")
        filter_condition_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        # 筛选值
        ttk.Label(self.filter_frame, text="值:").grid(row=0, column=4, sticky=tk.W, padx=(10, 10))
        self.filter_value_var = tk.StringVar()
        ttk.Entry(self.filter_frame, textvariable=self.filter_value_var, width=12).grid(row=0, column=5, sticky=tk.W)
        
        # 初始状态下隐藏筛选选项
        self.toggle_filter_options()
        
        # 绑定命名规则变化事件
        naming_combo.bind('<<ComboboxSelected>>', self.on_naming_rule_changed)
    
    def toggle_filter_options(self):
        """切换筛选选项的显示/隐藏"""
        if self.filter_enabled_var.get():
            self.filter_frame.grid()
        else:
            self.filter_frame.grid_remove()
    
    def on_naming_rule_changed(self, event=None):
        """命名规则改变时的处理"""
        rule = self.naming_var.get()
        if rule == "多列组合":
            self.naming_column_combo.grid_remove()
            self.multi_columns_frame.grid()
        else:
            self.multi_columns_frame.grid_remove()
            self.naming_column_combo.grid()
            if "数据列" in rule:
                self.naming_column_combo.config(state="readonly")
            else:
                self.naming_column_combo.config(state="disabled")
    
    def on_column_checkbox_changed(self, column):
        """复选框状态改变时的处理"""
        if self.column_vars[column].get():
            # 添加到已选列表
            if column not in [self.selected_columns_listbox.get(i) for i in range(self.selected_columns_listbox.size())]:
                self.selected_columns_listbox.insert(tk.END, column)
        else:
            # 从已选列表中移除
            for i in range(self.selected_columns_listbox.size()):
                if self.selected_columns_listbox.get(i) == column:
                    self.selected_columns_listbox.delete(i)
                    break
    
    def move_naming_column_up(self):
        """上移命名列"""
        selected_indices = self.selected_columns_listbox.curselection()
        if selected_indices and selected_indices[0] > 0:
            index = selected_indices[0]
            column = self.selected_columns_listbox.get(index)
            self.selected_columns_listbox.delete(index)
            self.selected_columns_listbox.insert(index - 1, column)
            self.selected_columns_listbox.selection_set(index - 1)
    
    def move_naming_column_down(self):
        """下移命名列"""
        selected_indices = self.selected_columns_listbox.curselection()
        if selected_indices and selected_indices[0] < self.selected_columns_listbox.size() - 1:
            index = selected_indices[0]
            column = self.selected_columns_listbox.get(index)
            self.selected_columns_listbox.delete(index)
            self.selected_columns_listbox.insert(index + 1, column)
            self.selected_columns_listbox.selection_set(index + 1)

    def update_combo_options(self):
        """更新下拉框选项"""
        if hasattr(self, 'generator') and self.generator.data_processor.data is not None:
            columns = self.generator.data_processor.columns

            # 更新命名数据列选项
            self.naming_column_combo['values'] = columns
            if columns:
                if '员工姓名' in columns:
                    self.naming_column_var.set('员工姓名')
                elif not self.naming_column_var.get():
                    self.naming_column_var.set(columns[0])

            # 更新多列选择复选框
            self.create_column_checkboxes(columns)

            # 更新筛选列选项
            self.filter_column_combo['values'] = columns
            if columns and not self.filter_column_var.get():
                self.filter_column_var.set(columns[0])
    
    def create_column_checkboxes(self, columns):
        """创建列选择复选框"""
        # 清除现有复选框
        for widget in self.available_scrollable_frame.winfo_children():
            widget.destroy()
        
        self.column_checkboxes.clear()
        self.column_vars.clear()
        
        # 创建新的复选框
        for i, column in enumerate(columns):
            var = tk.BooleanVar()
            checkbox = ttk.Checkbutton(
                self.available_scrollable_frame,
                text=column,
                variable=var,
                command=lambda col=column: self.on_column_checkbox_changed(col)
            )
            checkbox.grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            
            self.column_vars[column] = var
            self.column_checkboxes[column] = checkbox
        
        # 绑定鼠标滚轮到复选框区域
        self._bind_mousewheel(self.available_canvas)
        self._bind_mousewheel(self.available_scrollable_frame)
        
    def create_mapping_section(self, parent):
        """创建变量映射区域"""
        # 映射框架
        mapping_frame = ttk.LabelFrame(parent, text="变量映射", padding="10", style="Section.TLabelframe")
        mapping_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        mapping_frame.columnconfigure(0, weight=1)
        mapping_frame.rowconfigure(1, weight=1)
        mapping_frame.configure(width=600)
        
        # 控制按钮
        control_frame = ttk.Frame(mapping_frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(control_frame, text="自动匹配", command=self.auto_match_variables).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="清除映射", command=self.clear_mapping).pack(side=tk.LEFT, padx=(10, 0))
        
        # 映射表格框架
        table_frame = ttk.Frame(mapping_frame)
        table_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # 创建Treeview表格
        columns = ("template_var", "data_column", "sample_data")
        self.mapping_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        
        # 设置列标题
        self.mapping_tree.heading("template_var", text="模板变量")
        self.mapping_tree.heading("data_column", text="数据列")
        self.mapping_tree.heading("sample_data", text="示例数据")
        
        # 设置列宽
        self.mapping_tree.column("template_var", width=150)
        self.mapping_tree.column("data_column", width=150)
        self.mapping_tree.column("sample_data", width=200)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.mapping_tree.yview)
        self.mapping_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.mapping_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 绑定双击事件
        self.mapping_tree.bind("<Double-1>", self.on_mapping_double_click)
        
    def create_progress_section(self, parent):
        """创建进度显示区域"""
        # 进度框架
        progress_frame = ttk.LabelFrame(parent, text="进度", padding="10", style="Section.TLabelframe")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.configure(width=600)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100,
            length=400
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 进度文本
        self.progress_text_var = tk.StringVar(value="就绪")
        ttk.Label(progress_frame, textvariable=self.progress_text_var).grid(row=1, column=0, sticky=tk.W)
        
    def create_action_buttons(self, parent):
        """创建操作按钮"""
        # 按钮框架
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(0, 15))
        
        # 居中按钮容器
        center_frame = ttk.Frame(button_frame)
        center_frame.pack(expand=True)
        
        # 生成按钮
        self.generate_button = ttk.Button(
            center_frame, 
            text="生成合同", 
            command=self.start_generation,
            width=12,
            style="Accent.TButton"
        )
        self.generate_button.grid(row=0, column=0, padx=(0, 15))
        
        # 打开输出目录按钮
        ttk.Button(
            center_frame, 
            text="打开输出目录", 
            command=self.open_output_directory,
            width=12
        ).grid(row=0, column=1, padx=(15, 15))
        
        # 反馈按钮
        ttk.Button(
            center_frame, 
            text="反馈", 
            command=self.show_feedback,
            width=8
        ).grid(row=0, column=2, padx=(15, 15))
        
        # 关于按钮
        ttk.Button(
            center_frame, 
            text="关于", 
            command=self.show_about,
            width=8
        ).grid(row=0, column=3, padx=(15, 0))
        
    def setup_generator_callback(self):
        """设置生成器回调"""
        def progress_callback(percent, message):
            # 在主线程中更新UI
            self.root.after(0, lambda: self.update_progress(percent, message))
        
        self.generator.set_progress_callback(progress_callback)

    def apply_modern_theme(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Section.TLabelframe", background="#FFFFFF")
        style.configure("Section.TLabelframe.Label", background="#FFFFFF", foreground="#111827", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("TLabel", background="#FFFFFF", foreground="#374151", font=("Microsoft YaHei UI", 10))
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=6)
        style.configure("Accent.TButton", foreground="#FFFFFF", background="#38BDF8", font=("Microsoft YaHei UI", 10, "bold"), padding=6)
        style.map("Accent.TButton", background=[("active", "#0EA5E9"), ("pressed", "#0284C7"), ("!disabled", "#38BDF8")])
        style.configure("Horizontal.TProgressbar", troughcolor="#E5E7EB", background="#38BDF8")
        style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", rowheight=26, font=("Microsoft YaHei UI", 10))
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"), foreground="#111827")
        
    def select_template_file(self):
        """选择模板文件"""
        filetypes = [
            ("支持的模板文件", " ".join([f"*{ext}" for ext in SUPPORTED_TEMPLATE_FORMATS])),
            ("Word文档", "*.docx"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择合同模板文件",
            filetypes=filetypes
        )
        
        if filename:
            self.template_path = filename
            self.template_var.set(filename)
            self.load_template()
            
    def select_data_file(self):
        """选择数据源文件"""
        filetypes = [
            ("支持的数据文件", " ".join([f"*{ext}" for ext in SUPPORTED_DATA_FORMATS])),
            ("Excel文件", "*.xlsx"),
            ("CSV文件", "*.csv"),
            ("JSON文件", "*.json"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择数据源文件",
            filetypes=filetypes
        )
        
        if filename:
            self.data_path = filename
            self.data_var.set(filename)
            self.load_data()
            
    def load_template(self):
        """加载模板文件"""
        if not self.template_path:
            return
            
        self.status_var.set("正在加载模板...")
        
        def load_thread():
            success = self.generator.load_template(self.template_path)
            self.root.after(0, lambda: self.on_template_loaded(success))
        
        threading.Thread(target=load_thread, daemon=True).start()
        
    def on_template_loaded(self, success):
        """模板加载完成回调"""
        if success:
            self.status_var.set("模板加载成功")
            self.check_compatibility()
        else:
            self.status_var.set("模板加载失败")
            messagebox.showerror("错误", "模板文件加载失败，请检查文件格式")
            
    def load_data(self):
        """加载数据源文件"""
        if not self.data_path:
            return
            
        self.status_var.set("正在加载数据源...")
        
        def load_thread():
            success = self.generator.load_data(self.data_path)
            self.root.after(0, lambda: self.on_data_loaded(success))
        
        threading.Thread(target=load_thread, daemon=True).start()
        
    def on_data_loaded(self, success):
        """数据源加载完成回调"""
        if success:
            self.status_var.set("数据源加载成功")
            self.update_combo_options()  # 更新下拉框选项
            self.check_compatibility()
        else:
            self.status_var.set("数据源加载失败")
            err = self.generator.data_processor.last_error if hasattr(self.generator.data_processor, 'last_error') else ''
            detail = f"\n\n{err}" if err else ""
            messagebox.showerror("错误", f"数据源文件加载失败，请检查文件格式{detail}")
            
    def check_compatibility(self):
        """检查模板和数据源兼容性"""
        if not (self.template_path and self.data_path):
            return
            
        compatibility = self.generator.validate_template_data_compatibility()
        
        if not compatibility["valid"]:
            missing_vars = compatibility["missing_variables"]
            messagebox.showwarning(
                "兼容性警告", 
                f"数据源中缺少以下模板变量：\n{', '.join(missing_vars)}\n\n"
                f"可用的数据列：\n{', '.join(self.generator.data_processor.columns)}"
            )
        else:
            self.status_var.set("模板和数据源兼容")
            # 自动更新变量映射
            self.update_variable_mapping()
            
    def update_variable_mapping(self):
        """更新变量映射表格"""
        if not (self.template_path and self.data_path):
            return
            
        try:
            # 清空现有映射
            for item in self.mapping_tree.get_children():
                self.mapping_tree.delete(item)
            
            # 获取模板变量和数据列
            template_vars = self.generator.template_processor.get_variables()
            data_columns = self.generator.data_processor.columns
            
            # 获取示例数据
            sample_data = self.generator.data_processor.get_row_data(0) or {}
            
            # 自动匹配变量
            suggestions = self.generator.data_processor.get_column_mapping_suggestions(template_vars)
            
            # 填充映射表格
            for var in template_vars:
                suggested_column = suggestions.get(var, "")
                sample_value = sample_data.get(suggested_column, "") if suggested_column else ""
                
                self.mapping_tree.insert("", "end", values=(
                    var,
                    suggested_column,
                    str(sample_value)[:50] + "..." if len(str(sample_value)) > 50 else str(sample_value)
                ))
                
        except Exception as e:
            logger.error(f"更新变量映射时发生错误: {str(e)}")
    
    def auto_match_variables(self):
        """自动匹配变量"""
        if not (self.template_path and self.data_path):
            messagebox.showwarning("警告", "请先选择模板文件和数据源文件")
            return
        
        self.update_variable_mapping()
        self.status_var.set("变量自动匹配完成")
    
    def clear_mapping(self):
        """清除映射"""
        for item in self.mapping_tree.get_children():
            self.mapping_tree.delete(item)
        self.status_var.set("映射已清除")
    
    def on_mapping_double_click(self, event):
        """处理映射表格双击事件"""
        item = self.mapping_tree.selection()[0] if self.mapping_tree.selection() else None
        if not item:
            return
        
        # 获取当前选中的变量
        values = self.mapping_tree.item(item, "values")
        if not values:
            return
        
        template_var = values[0]
        current_column = values[1]
        
        # 创建选择对话框
        self.show_column_selection_dialog(item, template_var, current_column)
    
    def show_column_selection_dialog(self, tree_item, template_var, current_column):
        """显示列选择对话框"""
        if not self.data_path:
            return
        
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title(f"为变量 '{template_var}' 选择数据列")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        # 创建列表框
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"为模板变量 '{template_var}' 选择对应的数据列:").pack(pady=(0, 10))
        
        # 列表框和滚动条
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        listbox = tk.Listbox(listbox_frame)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # 添加数据列
        data_columns = self.generator.data_processor.columns
        for i, column in enumerate(data_columns):
            listbox.insert(tk.END, column)
            if column == current_column:
                listbox.selection_set(i)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def on_ok():
            selection = listbox.curselection()
            if selection:
                selected_column = data_columns[selection[0]]
                # 获取示例数据
                sample_data = self.generator.data_processor.get_row_data(0) or {}
                sample_value = str(sample_data.get(selected_column, ""))
                sample_display = sample_value[:50] + "..." if len(sample_value) > 50 else sample_value
                
                # 更新树形控件
                self.mapping_tree.item(tree_item, values=(template_var, selected_column, sample_display))
                self.status_var.set(f"已将变量 '{template_var}' 映射到列 '{selected_column}'")
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=on_cancel).pack(side=tk.RIGHT)
        
    def start_generation(self):
        """开始生成合同"""
        if not (self.template_path and self.data_path):
            messagebox.showwarning("警告", "请先选择模板文件和数据源文件")
            return
            
        # 获取文件名前缀
        prefix = self.prefix_var.get().strip()
        if not prefix:
            prefix = "contract"
            
        # 禁用生成按钮
        self.generate_button.config(state=tk.DISABLED)
        
        def generation_thread():
            # 获取高级选项
            advanced_options = self.get_advanced_options()
            result = self.generator.generate_contracts_advanced(prefix, advanced_options)
            self.root.after(0, lambda: self.on_generation_complete(result))
        
        threading.Thread(target=generation_thread, daemon=True).start()
    
    def get_advanced_options(self):
        """获取高级选项设置"""
        # 获取命名列信息
        naming_columns = []
        if self.naming_var.get() == "多列组合":
            naming_columns = [self.selected_columns_listbox.get(i) for i in range(self.selected_columns_listbox.size())]
        
        return {
            "naming_rule": self.naming_var.get(),
            "naming_column": self.naming_column_var.get(),
            "naming_columns": naming_columns,
            "separator": self.separator_var.get(),
            "filter_enabled": self.filter_enabled_var.get(),
            "filter_column": self.filter_column_var.get(),
            "filter_condition": self.filter_condition_var.get(),
            "filter_value": self.filter_value_var.get(),
            "variable_mapping": self.get_variable_mapping(),
            "output_path": self.actual_output_path
        }
    
    def get_variable_mapping(self):
        """获取当前的变量映射"""
        mapping = {}
        for item in self.mapping_tree.get_children():
            values = self.mapping_tree.item(item, "values")
            if len(values) >= 2 and values[1]:  # 确保有映射的数据列
                mapping[values[0]] = values[1]  # 模板变量 -> 数据列
        return mapping
        
    def on_generation_complete(self, result):
        """生成完成回调"""
        # 重新启用生成按钮
        self.generate_button.config(state=tk.NORMAL)
        
        if result["success"]:
            messagebox.showinfo(
                "生成完成", 
                f"合同生成成功！\n\n"
                f"生成了 {result['contracts_count']} 份合同\n"
                f"共 {result['total_files']} 个文件\n\n"
                f"文件保存在 generated_contracts 目录中"
            )
        else:
            messagebox.showerror("生成失败", f"合同生成失败：\n{result['error']}")
            
    def update_progress(self, percent, message):
        """更新进度显示"""
        self.progress_var.set(percent)
        self.progress_text_var.set(message)
        
    def open_output_directory(self):
        """打开输出目录"""
        from config import DEFAULT_OUTPUT_DIR, ensure_directories
        
        ensure_directories()
        
        if os.path.exists(DEFAULT_OUTPUT_DIR):
            os.startfile(DEFAULT_OUTPUT_DIR)  # Windows
        else:
            messagebox.showinfo("提示", f"输出目录不存在：{DEFAULT_OUTPUT_DIR}")
    
    def show_feedback(self):
        """显示反馈对话框"""
        # 创建反馈对话框
        feedback_dialog = tk.Toplevel(self.root)
        feedback_dialog.title("问题反馈")
        feedback_dialog.geometry("500x700")
        feedback_dialog.transient(self.root)
        feedback_dialog.grab_set()
        feedback_dialog.resizable(False, False)
        
        # 居中显示
        feedback_dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 100,
            self.root.winfo_rooty() + 50
        ))
        
        # 创建主框架
        main_frame = ttk.Frame(feedback_dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="问题反馈", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 联系方式信息
        contact_frame = ttk.LabelFrame(main_frame, text="联系方式", padding="15")
        contact_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 邮箱信息
        email_frame = ttk.Frame(contact_frame)
        email_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(email_frame, text="📧 邮箱：", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        email_label = ttk.Label(email_frame, text="2221873757@qq.com", foreground="blue", cursor="hand2")
        email_label.pack(side=tk.LEFT)
        
        # 绑定邮箱点击事件
        def copy_email(event):
            feedback_dialog.clipboard_clear()
            feedback_dialog.clipboard_append("2221873757@qq.com")
            messagebox.showinfo("提示", "邮箱地址已复制到剪贴板")
        
        email_label.bind("<Button-1>", copy_email)
        
        # 微信二维码
        wechat_frame = ttk.LabelFrame(contact_frame, text="微信联系", padding="10")
        wechat_frame.pack(fill=tk.X)
        
        # 尝试加载微信二维码图片
        try:
            img_path = self._get_img_path('vx.jpg')
            if img_path:
                pil_image = Image.open(img_path)
                # 调整图片大小，保持宽高比
                pil_image.thumbnail((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(pil_image)
                
                image_label = ttk.Label(wechat_frame, image=photo)
                image_label.image = photo  # 保持引用
                image_label.pack(pady=10)
                
                ttk.Label(wechat_frame, text="扫描上方二维码添加微信", font=("Arial", 9)).pack()
            else:
                ttk.Label(wechat_frame, text="微信二维码图片未找到\n请联系邮箱获取微信", 
                         font=("Arial", 9), foreground="red").pack(pady=20)
        except ImportError:
            ttk.Label(wechat_frame, text="需要安装PIL库来显示二维码\npip install Pillow", 
                     font=("Arial", 9), foreground="orange").pack(pady=20)
        except Exception as e:
            ttk.Label(wechat_frame, text=f"加载微信二维码失败\n{str(e)}", 
                     font=("Arial", 9), foreground="red").pack(pady=20)
        
        # 反馈说明
        feedback_info_frame = ttk.LabelFrame(main_frame, text="反馈说明", padding="15")
        feedback_info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        feedback_text = """🎉 欢迎您使用合同批量生成器！

📞 联系方式：
如果您在使用过程中遇到任何问题，或者有改进建议，请通过以下方式联系我：

📧 邮件反馈：
• 发送邮件到上述邮箱地址
• 请详细描述遇到的问题或建议
• 可以附上截图或错误日志

💬 微信沟通：
• 扫描上方二维码添加微信
• 支持实时沟通和远程协助
• 可以发送文件和截图

🐛 常见问题类型：
• 软件运行错误或崩溃
• 模板格式不兼容
• 数据导入失败
• 生成结果不符合预期
• 功能使用疑问

💡 改进建议：
• 新功能需求
• 界面优化建议
• 性能改进意见
• 用户体验反馈

⏰ 响应时间：
我会在24小时内回复您的邮件，微信消息通常会更快回复。

🙏 感谢您的使用和宝贵反馈！您的意见是我们持续改进的动力！"""
        
        # 创建滚动文本框
        text_frame = ttk.Frame(feedback_info_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = scrolledtext.ScrolledText(
            text_frame, 
            height=18, 
            wrap=tk.WORD, 
            font=("Arial", 10),
            padx=10,
            pady=5
        )
        text_widget.insert(tk.END, feedback_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # 关闭按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="关闭", command=feedback_dialog.destroy).pack(side=tk.RIGHT)
            
    def show_about(self):
        """显示关于对话框"""
        about_text = f"""{APP_NAME} v{APP_VERSION}

概述
- 批量生成 Word 合同，保留模板版式
- 支持 Excel/CSV/JSON 数据源

核心功能
- 仅支持 Word(.docx) 模板
- 自动变量映射与命名规则
- 数据筛选与自定义输出路径
- 进度显示与错误提示

使用流程
1. 选择包含占位符的模板文件
2. 选择数据文件（Excel/CSV/JSON）
3. 配置文件名前缀与高级选项
4. 自动匹配变量映射关系（可手动调整）
5. 点击生成，批量输出 Word 文件

模板变量格式
- 使用单大括号：{{姓名}}、{{职位}}、{{薪资}}

适用场景
- 人力资源、销售、法务的批量合同生成
- 其他需要批量文档生成的场景

技术说明
- Python + Tkinter
- 中文友好、跨平台（安装 Python 后运行）

版权所有 © 2025 {APP_NAME}
如需帮助，请使用“反馈”按钮联系开发者"""
        
        # 创建关于对话框
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("关于合同批量生成器")
        about_dialog.geometry("600x700")
        about_dialog.transient(self.root)
        about_dialog.grab_set()
        about_dialog.resizable(False, False)
        
        # 居中显示
        about_dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 25
        ))
        
        # 创建滚动文本框
        frame = ttk.Frame(about_dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动文本区域
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = scrolledtext.ScrolledText(
            text_frame, 
            wrap=tk.WORD, 
            font=("Arial", 10),
            height=35,
            width=70
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, about_text)
        try:
            about_dialog.iconphoto(True, self.app_icon)
        except Exception:
            pass
        text_widget.config(state=tk.DISABLED)
        
        # 关闭按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(button_frame, text="关闭", command=about_dialog.destroy).pack(side=tk.RIGHT)
        
    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("用户中断程序")
        except Exception as e:
            logger.error(f"程序运行时发生错误: {str(e)}")
            messagebox.showerror("错误", f"程序发生错误：{str(e)}")

def main():
    """主函数"""
    try:
        app = ContractGeneratorGUI()
        app.run()
    except Exception as e:
        logger.error(f"启动程序时发生错误: {str(e)}")
        messagebox.showerror("启动错误", f"程序启动失败：{str(e)}")

if __name__ == "__main__":
    main()
