## 语料结构化结果生成格式定义

### 1. 核心数据结构 (Python数据模型)

```python
from typing import List, Dict, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class DialogueTurn(BaseModel):
    """单轮对话结构"""
    speaker: str = Field(description="发言者：'user' 或角色名")
    content: str = Field(description="对话内容")
    turn_id: int = Field(description="对话轮次ID，从1开始")

class QualityMetrics(BaseModel):
    """质量评估指标"""
    overall_score: float = Field(ge=0.0, le=1.0, description="整体质量得分 0-1")
    scenario_consistency: float = Field(ge=0.0, le=1.0, description="场景一致性得分")
    character_consistency: float = Field(ge=0.0, le=1.0, description="角色一致性得分")
    dialogue_naturalness: float = Field(ge=0.0, le=1.0, description="对话自然度得分")
    content_safety: float = Field(ge=0.0, le=1.0, description="内容安全性得分")

class GenerationMetadata(BaseModel):
    """生成元数据"""
    model_name: str = Field(description="使用的LLM模型名称")
    model_version: Optional[str] = Field(description="模型版本")
    temperature: float = Field(description="生成温度参数")
    max_tokens: int = Field(description="最大token数")
    generation_time: float = Field(description="生成耗时(秒)")
    api_cost: Optional[float] = Field(description="API调用成本")

class CorpusItem(BaseModel):
    """单条语料项目 - 核心结构"""
    # 基本信息
    id: str = Field(description="语料唯一ID，格式：{character_id}_{scenario_id}_{timestamp}_{random}")
    character_id: str = Field(description="角色ID")
    character_name: str = Field(description="角色名称")
    scenario_id: str = Field(description="场景标签ID")
    scenario_name: str = Field(description="场景标签名称")
    scenario_description: str = Field(description="场景详细描述")
    
    # 对话内容
    dialogue_turns: List[DialogueTurn] = Field(description="多轮对话列表")
    turn_count: int = Field(description="对话轮数")
    
    # 质量控制
    quality_metrics: QualityMetrics = Field(description="质量评估指标")
    manual_reviewed: bool = Field(default=False, description="是否经过人工审核")
    
    # 生成信息
    generation_metadata: GenerationMetadata = Field(description="生成相关元数据")
    
    # 时间戳
    created_at: datetime = Field(description="创建时间")
    updated_at: Optional[datetime] = Field(description="最后更新时间")
    
    # 扩展字段
    tags: List[str] = Field(default=[], description="额外标签")
    notes: Optional[str] = Field(description="备注信息")

class BatchGenerationResult(BaseModel):
    """批次生成结果"""
    batch_id: str = Field(description="批次ID")
    character_id: str = Field(description="角色ID")
    selected_scenarios: List[str] = Field(description="选中的场景标签ID列表")
    total_requested: int = Field(description="请求生成的总数量")
    successfully_generated: int = Field(description="成功生成的数量")
    failed_count: int = Field(description="生成失败的数量")
    corpus_items: List[CorpusItem] = Field(description="生成的语料项目列表")
    generation_summary: Dict[str, int] = Field(description="各场景生成数量统计")
    total_cost: Optional[float] = Field(description="总API成本")
    total_time: float = Field(description="总生成时间")
    created_at: datetime = Field(description="批次创建时间")
```

### 2. JSON输出格式示例

#### 单条语料项目格式：
```json
{
  "id": "char_001_scenario_daily_20241201_143052_abc123",
  "character_id": "char_001",
  "character_name": "小雅",
  "scenario_id": "scenario_daily",
  "scenario_name": "日常对话",
  "scenario_description": "轻松的日常生活对话场景，包含问候、闲聊、分享等内容",
  "dialogue_turns": [
    {
      "speaker": "user",
      "content": "小雅，你今天过得怎么样？",
      "turn_id": 1
    },
    {
      "speaker": "小雅",
      "content": "今天过得很不错呢！早上去公园跑了步，空气特别清新，让人心情都变好了。你呢，今天有什么有趣的事情吗？",
      "turn_id": 2
    },
    {
      "speaker": "user",
      "content": "听起来很棒！我今天在家整理了一些旧照片，发现了很多有趣的回忆。",
      "turn_id": 3
    },
    {
      "speaker": "小雅",
      "content": "哇，整理照片确实是一件很有意思的事情！每张照片都承载着特殊的回忆，有没有找到什么特别难忘的瞬间？",
      "turn_id": 4
    }
  ],
  "turn_count": 4,
  "quality_metrics": {
    "overall_score": 0.92,
    "scenario_consistency": 0.95,
    "character_consistency": 0.89,
    "dialogue_naturalness": 0.94,
    "content_safety": 1.0
  },
  "manual_reviewed": false,
  "generation_metadata": {
    "model_name": "gpt-4",
    "model_version": "gpt-4-1106-preview",
    "temperature": 0.8,
    "max_tokens": 2048,
    "generation_time": 3.45,
    "api_cost": 0.025
  },
  "created_at": "2024-12-01T14:30:52.123456Z",
  "updated_at": null,
  "tags": ["高质量", "自然对话"],
  "notes": null
}
```

#### 批次生成结果格式：
```json
{
  "batch_id": "batch_20241201_143000_xyz789",
  "character_id": "char_001",
  "selected_scenarios": ["scenario_daily", "scenario_emotion", "scenario_work"],
  "total_requested": 30,
  "successfully_generated": 28,
  "failed_count": 2,
  "corpus_items": [
    // ... 28个CorpusItem对象
  ],
  "generation_summary": {
    "scenario_daily": 10,
    "scenario_emotion": 9,
    "scenario_work": 9
  },
  "total_cost": 0.75,
  "total_time": 125.6,
  "created_at": "2024-12-01T14:30:00.000000Z"
}
```

### 3. 数据库存储格式

```sql
-- 语料主表
CREATE TABLE corpus_items (
    id VARCHAR(255) PRIMARY KEY,
    character_id VARCHAR(100) NOT NULL,
    character_name VARCHAR(255) NOT NULL,
    scenario_id VARCHAR(100) NOT NULL,
    scenario_name VARCHAR(255) NOT NULL,
    scenario_description TEXT,
    turn_count INTEGER NOT NULL,
    manual_reviewed BOOLEAN DEFAULT FALSE,
    overall_quality_score DECIMAL(3,2),
    scenario_consistency_score DECIMAL(3,2),
    character_consistency_score DECIMAL(3,2),
    dialogue_naturalness_score DECIMAL(3,2),
    content_safety_score DECIMAL(3,2),
    model_name VARCHAR(100),
    generation_time DECIMAL(8,3),
    api_cost DECIMAL(10,6),
    created_at DATETIME NOT NULL,
    updated_at DATETIME,
    tags JSON,
    notes TEXT
);

-- 对话轮次表
CREATE TABLE dialogue_turns (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    corpus_item_id VARCHAR(255) NOT NULL,
    turn_id INTEGER NOT NULL,
    speaker VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    FOREIGN KEY (corpus_item_id) REFERENCES corpus_items(id)
);

-- 批次记录表
CREATE TABLE generation_batches (
    batch_id VARCHAR(255) PRIMARY KEY,
    character_id VARCHAR(100) NOT NULL,
    selected_scenarios JSON NOT NULL,
    total_requested INTEGER NOT NULL,
    successfully_generated INTEGER NOT NULL,
    failed_count INTEGER NOT NULL,
    generation_summary JSON,
    total_cost DECIMAL(10,6),
    total_time DECIMAL(8,3),
    created_at DATETIME NOT NULL
);
```

### 4. 导出格式示例

#### JSONL格式 (用于LLM微调)：
```jsonl
{"messages": [{"role": "user", "content": "小雅，你今天过得怎么样？"}, {"role": "assistant", "content": "今天过得很不错呢！早上去公园跑了步，空气特别清新，让人心情都变好了。你呢，今天有什么有趣的事情吗？"}], "character": "小雅", "scenario": "日常对话", "quality_score": 0.92}
```

#### CSV格式：
```csv
id,character_name,scenario_name,dialogue_content,turn_count,quality_score,created_at
char_001_scenario_daily_20241201_143052_abc123,小雅,日常对话,"用户: 小雅，你今天过得怎么样？\n小雅: 今天过得很不错呢！...",4,0.92,2024-12-01 14:30:52
```

这个结构化格式设计考虑了：
- **完整的场景标签信息**：包含ID、名称和描述
- **灵活的多轮对话支持**：可扩展到任意轮数
- **全面的质量评估**：多维度质量指标
- **详细的生成元数据**：便于成本控制和性能分析
- **批次管理**：支持批量生成和统计
- **数据库友好**：便于存储和查询
- **导出兼容**：支持多种下游使用格式
