# 合同批量生成器

一个图形界面的合同批量生成工具，支持从 Excel、CSV、JSON 数据源生成 Word 合同（.docx）。

## 功能特点

- 图形界面操作（tkinter），简单易用
- 模板变量自动提取与映射建议
- 支持数据源：`.xlsx`、`.csv`、`.json`
- 支持模板：`.docx`
- 输出格式：`.docx`

## 环境要求

- Python 3.9 及以上（推荐）
- Windows（已验证），其它平台未完全测试

## 安装与运行

1. 安装依赖（项目根目录）：
   ```bash
   pip install -r app/requirements.txt
   ```

2. 运行程序（项目根目录）：
   ```bash
   python app/main.py
   ```

## 使用方法

- 选择模板文件（`.docx`）
- 选择数据源（`.xlsx`/`.csv`/`.json`）
- 根据建议或手动调整变量映射
- 点击“生成合同”，在 `generated_contracts/` 输出 `.docx`

## 打包为可执行文件（Windows）

在项目根目录执行：
```bash
python app/build.py
```

- 生成的可执行文件位于：`dist/合同批量生成器.exe`
- 打包脚本自动收集依赖与资源（如存在图标会设置 EXE 图标）

## 文档

- `docx/项目结构说明.md`
- `docx/打包说明.md`
- `docx/软件使用说明书.md`

## 项目结构（当前）

```
contract/
├── app/
│   ├── main.py                 # GUI入口
│   ├── contract_generator.py   # 生成器核心逻辑
│   ├── template_processor.py   # 模板处理（仅支持 .docx）
│   ├── data_processor.py       # 数据处理
│   ├── config.py               # 配置
│   ├── build.py                # 打包脚本
│   ├── requirements.txt        # 源码运行依赖
│   └── img/                    # 图标与图片资源
├── docx/                       # 项目文档
│   ├── 项目结构说明.md
│   ├── 打包说明.md
│   └── 软件使用说明书.md
├── dist/                       # 本地打包产物，不纳入 Git
│   └── 合同批量生成器.exe      # 打包生成的可执行文件
├── test_templates/             # 本地合同模板，不纳入 Git
│   ├── employment_contract.docx
│   ├── service_contract.docx
│   └── rental_contract.docx
├── test_data/                  # 本地测试数据，不纳入 Git
│   ├── employee_data.csv
│   ├── service_data.csv
│   └── rental_data.json
├── generated_contracts/        # 程序运行时自动创建
├── temp/                       # 程序运行时自动创建
└── README.md
```

## 仓库收录范围

- 提交源码、依赖清单、打包脚本、项目文档和应用图片资源。
- `test_data/` 中的数据和 `test_templates/` 中的合同模板仅保留在本地，不上传到公开仓库；克隆仓库后请自行准备模板和数据源。
- `dist/`、`build/`、`generated_contracts/`、`temp/`、Python 缓存、虚拟环境和 IDE 配置由 `.gitignore` 排除。
- 可执行文件通过 `python app/build.py` 在本地生成，不纳入源码仓库。

## 模板变量语法

在 Word 模板中使用 `{{变量名}}`：

```
合同编号：{{合同编号}}
甲方：{{甲方名称}}
乙方：{{乙方名称}}
签订日期：{{签订日期}}
```

## 注意事项

- 当前版本仅支持 `.docx` 模板与 `.docx` 输出
- 文本模板（`.txt`）与 PDF 输出暂不支持
- 大文件处理建议先在数据源端（Excel/CSV）做好清洗与格式化

## 版本信息

- 应用版本：2.0.0（参考 `app/config.py`）

## 常见问题

- 程序无法启动：请确认 Python 版本与依赖安装正确
- 模板变量未替换：检查变量名与数据列是否一致（空格/大小写）
- 打包后运行异常：请重试在干净环境打包，并确保依赖完整
