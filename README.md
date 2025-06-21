
# Character LLM Dataset Generator

一个基于 Gradio WebUI 的智能语料生成和管理工具，专为角色扮演LLM微调数据集制作而设计。

## 🎯 项目简介

本工具通过用户定义的虚拟角色卡片，结合丰富的场景标签系统，利用高级LLM模型（如OpenAI GPT-4、Google Gemini Pro等）自动生成高质量的角色对话语料，为小型LLM微调提供专业的数据集制作解决方案。

## ✨ 核心功能

### 1. 虚拟角色管理
### 2. 场景标签系统
### 3. 语料数据集管理
### 4. 语料生成流程和结果入库
### 5. 数据库导出为可用于微调的jsonl格式

## 🚀 快速开始

### 环境要求
- Python 3.9+
- 8GB+ RAM 推荐
- 稳定的网络连接

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/your-username/character-llm-gen.git
cd character-llm-gen

# 配置虚拟环境
pyenv install 3.9.9
pyenv virtualenv 3.9.9 char_gen
pyenv activate char_gen


# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

### 配置设置

1. **API密钥配置**
   - 在WebUI中进入"配置管理"页面
   - 添加OpenAI、Google等平台的API密钥
   - 测试连接确保配置正确

2. **创建角色卡**
   - 点击"角色管理" → "新建角色"
   - 填写角色的基本信息、性格特征、背景信息、口语风格、对话例子等

3. **配置场景标签**
   - 进入"场景管理"页面
   - 创建或选择所需的场景标签
   - 设置场景描述和对应的提示词模板

4. **开始生成语料**
   - 选择目标角色卡
   - 选择一个或多个场景标签
   - 配置生成参数（数量、格式等）
   - 点击"开始生成"并等待完成

## 📁 项目结构

```
character-llm-gen/
├── app.py                 # 主应用入口
├── requirements.txt       # 依赖包列表
├── config/               # 配置文件目录
│   ├── settings.json     # 应用配置
├── src/                  # 源码目录
│   ├── ui/              # Gradio界面组件
│   │   ├── character_ui.py    # 角色管理界面
│   │   ├── scenario_ui.py     # 场景管理界面
│   │   ├── generation_ui.py   # 语料生成界面
│   │   └── dataset_ui.py      # 数据集管理界面
│   ├── models/          # 数据模型定义, 数据库表结构定义
│   │   ├── character.py       # 角色模型
│   │   ├── scenario.py        # 场景模型
│   │   └── dataset.py         # 数据集模型
│   │   └── api_config.py         # LLM API配置模型
│   ├── services/        # 业务逻辑服务
│   │   ├── llm_service.py     # LLM统一调用服务
│   │   ├── generation_service.py  # 语料生成服务
│   │   └── quality_service.py     # 质量控制服务（预留）
│   ├── utils/           # 工具函数
│   └── database/        # 数据库相关
├── data/                # 数据存储目录
│   ├── data.db          # 默认数据库文件
├── templates/           # 模板文件
│   ├── prompts/         # 提示词模板
│   └── scenarios/       # 场景模板
├── logs/                # 日志文件
└── docs/                # 文档目录
```

## 🔧 功能标签页功能说明

### 角色卡管理
1. **管理角色卡**：增删改查角色卡, 数据库读写更新
2. **编辑角色卡内容**：定义角色的基本属性、性格特征、说话风格，保存到角色卡列表(数据库)

### 场景标签
1. **管理场景标签**：增删改查场景标签, 数据库读写更新
2. **设置场景描述**：为每个场景标签配置场景描述提示词, 保存到数据库

### 语料数据集管理
1. **数据集管理**：增删查改数据集对象, 数据库读写更新
2. **数据集参数配置**：设置数据集参数, 如数据集名称、数据集绑定角色卡、数据集绑定多个场景标签、数据集场景标签、数据集来源、数据集状态(未完成生成/已完成生成)等
3. **数据集内容统计**：查看数据集内语料数量、标签数量分布
4. **按场景筛选**：可按特定场景标签筛选查看语料
5. **数据导出**：选择合适的格式导出，包含完整的场景标签信息

### 语料生成流程
1. **选择数据集**：选择数据集对象
2. **配置生成参数**：设置生成数量、每条语料的对话轮数、每个场景的分配比例、是否并行生成(并行生成请求数量设置)、最终生成提示词预览
3. **配置API调用参数**：设置API调用配置，如LLM API配置(暂时只需支持openai)、可用模型下拉列表、温度、最大长度等
   - 支持API参数保存到数据库, 每次打开自动加载数据库中的API配置(如果数据库中没有API配置，则使用默认配置)
4. **开始生成按钮**：系统自动调用LLM API进行分场景生成, 如果是并行生成, 则自动切分请求, 并行发出异步请求
5. **结果预览/质量审核**：预览生成结果，查看每条语料的场景标签, 如果是并行生成, 可以下拉选择查看不同批次请求的生成结果
6. **确认入库**：将通过审核的语料添加到数据集，保留场景标签信息, 支持自动模式开关(自动入库/人工审核)


### 导出数据格式示例

**JSONL格式**：
```json
{"character": "角色名", "scenario": "日常对话", "conversation": [...], "quality_score": 0.95}
{"character": "角色名", "scenario": "情感交流", "conversation": [...], "quality_score": 0.88}
```

**CSV格式**：
```csv
character,scenario,conversation,quality_score,created_at
角色名,日常对话,"对话内容...",0.95,2024-01-01 10:00:00
角色名,情感交流,"对话内容...",0.88,2024-01-01 10:05:00
```

## 🛠️ 技术栈

- **前端框架**：Gradio WebUI
- **后端语言**：Python 3.8+
- **数据库**：SQLite
- **LLM接口**：OpenAI API（Google AI API、Anthropic API日后支持）



## 语料结构化结果生成格式定义
请参考[RESULT_FORMAT.md](RESULT_FORMAT.md)文件

