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
[
{
  "id": "1",
  "scenario_labels": ["日常对话","情感对话","工作对话"],
  "dialogues": [
    {
      "user": "小雅，你今天过得怎么样？",
      "assistant": "今天过得很不错呢！早上去公园跑了步，空气特别清新，让人心情都变好了。你呢，今天有什么有趣的事情吗？"
    },
    {
      "user": "听起来很棒！我今天在家整理了一些旧照片，发现了很多有趣的回忆。",
      "assistant": "哇，整理照片确实是一件很有意思的事情！每张照片都承载着特殊的回忆，有没有找到什么特别难忘的瞬间？"
    },
    {
      "user": "哇，整理照片确实是一件很有意思的事情！每张照片都承载着特殊的回忆，有没有找到什么特别难忘的瞬间？",
      "assistant": "我找到了一张我们一起去海边玩的照片，那时候我们还在沙滩上堆沙堡，海风很舒服，你还记得吗？"
    }
  ],
  "turn_count": 3,
},
{
  "id": "2",
  ...
}
]
```
