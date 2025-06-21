import gradio as gr


def create_scenario_ui():
    """创建场景标签管理UI"""
    with gr.Blocks(analytics_enabled=False) as scenario_ui:
        gr.Markdown("## 🏞️ 场景标签管理\n创建和管理用于生成语料的场景。")

        with gr.Row():
            with gr.Column(scale=1):
                # Using a Dataframe to show both name and description
                scenario_list = gr.Dataframe(
                    headers=["标签名称", "场景描述"],
                    datatype=["str", "str"],
                    row_count=10,
                    col_count=(2, "fixed"),
                    label="场景标签列表",
                    interactive=True,
                )

                with gr.Row():
                    add_scenario_btn = gr.Button("✨ 添加新场景")
                    delete_scenario_btn = gr.Button("🗑️ 删除选中场景", variant="stop")

            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### 场景编辑器")
                    scenario_name = gr.Textbox(
                        label="场景标签名称", placeholder="例如：日常闲聊"
                    )
                    scenario_prompt = gr.Textbox(
                        label="场景描述/提示词模板",
                        lines=10,
                        placeholder="在此输入场景的具体描述，或者一个包含占位符的提示词模板。\n例如：在一个安静的咖啡馆里，{character_name}正在和朋友聊天。",
                    )

                    with gr.Row():
                        save_scenario_btn = gr.Button("💾 保存场景", variant="primary")

    return scenario_ui
