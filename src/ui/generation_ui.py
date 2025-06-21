import gradio as gr


def create_generation_ui():
    """创建语料生成UI"""
    with gr.Blocks(analytics_enabled=False) as generation_ui:
        gr.Markdown("## 🚀 语料生成\n配置并启动语料生成任务。")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 1. 选择数据集")
                with gr.Group():
                    target_dataset = gr.Dropdown(
                        label="选择一个数据集进行生成",
                        info="生成的语料将添加到此数据集中。",
                    )

                gr.Markdown("### 2. 配置生成参数")
                with gr.Group():
                    num_to_generate = gr.Slider(
                        label="总生成数量",
                        minimum=1,
                        maximum=1000,
                        step=1,
                        value=10,
                        info="为所有选定场景生成的语料总数。",
                    )
                    conversation_turns = gr.Slider(
                        label="每条语料对话轮数",
                        minimum=1,
                        maximum=20,
                        step=1,
                        value=3,
                        info="一次对话包含的用户和AI的交互次数。",
                    )

                    gr.Markdown("##### 场景分配")
                    # This part can be complex. For now, a placeholder or a simple interface.
                    # A more advanced implementation might use gr.Dataframe or dynamic components.
                    scenario_distribution = gr.Textbox(
                        label="场景分配比例",
                        info="（暂未实现）指定每个场景的生成比例。",
                        interactive=False,
                    )

                gr.Markdown("### 3. 配置API调用")
                with gr.Group():
                    api_config = gr.Dropdown(
                        label="选择API配置", info="选择一个已保存的API配置。"
                    )
                    model_name = gr.Dropdown(
                        label="选择模型", info="根据API配置自动加载可用模型。"
                    )
                    temperature = gr.Slider(
                        label="温度 (temperature)",
                        minimum=0.0,
                        maximum=2.0,
                        step=0.1,
                        value=0.7,
                    )
                    max_tokens = gr.Slider(
                        label="最大长度 (max_tokens)",
                        minimum=64,
                        maximum=8192,
                        step=64,
                        value=2048,
                    )

                    with gr.Accordion("管理API配置", open=False):
                        with gr.Tabs():
                            with gr.TabItem("添加/更新API配置"):
                                gr.Markdown(
                                    "统一管理和测试你的大语言模型API连接。配置将会被加密保存在本地数据库中。"
                                )
                                with gr.Group():
                                    api_provider = gr.Dropdown(
                                        label="选择API提供商",
                                        choices=["OpenAI", "Google", "Anthropic"],
                                        value="OpenAI",
                                    )
                                    api_name = gr.Textbox(
                                        label="配置名称",
                                        info="为这个API配置起一个唯一的名称。",
                                        placeholder="例如：my-openai-key",
                                    )
                                    api_key = gr.Textbox(
                                        label="API Key",
                                        type="password",
                                        placeholder="输入你的API Key",
                                    )
                                    # This will be visible for OpenAI and Anthropic
                                    base_url = gr.Textbox(
                                        label="Base URL (可选)",
                                        placeholder="留空则使用官方默认地址",
                                        visible=True,  # Initially visible for OpenAI
                                    )

                                    with gr.Row():
                                        save_api_btn = gr.Button("💾 保存并测试")
                                        api_test_status = gr.Label(label="连接状态")

                                # Add event listener for the dropdown to control visibility of base_url
                                def update_visibility(provider):
                                    if provider in ["OpenAI", "Anthropic"]:
                                        return gr.update(visible=True)
                                    else:  # Google
                                        return gr.update(visible=False, value="")

                                api_provider.change(
                                    fn=update_visibility,
                                    inputs=[api_provider],
                                    outputs=[base_url],
                                )

                            with gr.TabItem("已存配置列表"):
                                gr.Markdown("管理所有已保存的API配置。")
                                api_config_list = gr.Dataframe(
                                    headers=[
                                        "配置名称",
                                        "API类型",
                                        "Base URL",
                                        "创建时间",
                                    ],
                                    datatype=["str", "str", "str", "str"],
                                    row_count=5,
                                    col_count=(4, "fixed"),
                                    label="已保存的API配置列表",
                                )
                                with gr.Row():
                                    refresh_configs_btn = gr.Button("🔄 刷新列表")
                                    delete_config_btn = gr.Button(
                                        "🗑️ 删除选中配置", variant="stop"
                                    )

            with gr.Column(scale=2):
                gr.Markdown("### 4. 预览与启动")
                with gr.Tabs():
                    with gr.TabItem("📝 最终提示词预览"):
                        prompt_preview = gr.TextArea(
                            label="生成的提示词将显示在这里",
                            lines=20,
                            interactive=False,
                            placeholder="选择好参数后，此处将展示发送给LLM的最终提示词。",
                        )

                with gr.Row(equal_height=True):
                    start_generation_btn = gr.Button(
                        "🚀 开始生成", variant="primary", scale=3
                    )
                    auto_save = gr.Checkbox(
                        label="自动审核并入库", value=True, scale=1, min_width=50
                    )

                gr.Markdown("### 5. 结果预览与审核")
                with gr.Group():
                    with gr.Tabs():
                        with gr.TabItem("表格视图"):
                            batch_result_table = gr.Dataframe(
                                headers=["角色", "场景", "对话摘要", "质量分"],
                                datatype=["str", "str", "str", "number"],
                                row_count=5,
                                col_count=(4, "fixed"),
                                label="单批次生成结果预览",
                            )
                        with gr.TabItem("JSON 原始数据"):
                            generation_result = gr.Json(label="生成结果JSON")

                    with gr.Row():
                        save_to_db_btn = gr.Button("👍 确认入库")
                        discard_btn = gr.Button("👎 丢弃本批", variant="secondary")

    return generation_ui
