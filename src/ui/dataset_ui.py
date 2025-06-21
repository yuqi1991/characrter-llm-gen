import gradio as gr


def create_dataset_ui():
    """创建语料数据集管理UI"""
    with gr.Blocks(analytics_enabled=False) as dataset_ui:
        gr.Markdown("## 📚 语料数据集管理\n管理、查看和导出您的语料数据集。")

        with gr.Row():
            with gr.Column(scale=1):
                dataset_list = gr.Dropdown(
                    label="选择数据集", info="选择一个数据集以查看其内容或进行管理。"
                )
                with gr.Row():
                    new_dataset_btn = gr.Button("✨ 新建数据集")
                    delete_dataset_btn = gr.Button("🗑️ 删除数据集", variant="stop")

                gr.Markdown("---")
                gr.Markdown("### 数据集设置")
                with gr.Group():
                    dataset_name = gr.Textbox(
                        label="数据集名称",
                        placeholder="例如：白石藏之介-日常对话-第一批",
                    )
                    dataset_character = gr.Dropdown(
                        label="绑定角色卡", info="选择此数据集关联的角色。"
                    )
                    dataset_scenarios = gr.CheckboxGroup(
                        label="绑定场景标签", info="选择此数据集包含的场景。"
                    )
                    save_dataset_btn = gr.Button("💾 保存设置", variant="primary")

            with gr.Column(scale=2):
                gr.Markdown("### 数据集内容")
                with gr.Tabs():
                    with gr.TabItem("📖 内容预览"):
                        filter_scenario = gr.Dropdown(
                            label="按场景筛选", info="只看特定场景下的语料。"
                        )
                        dataset_content_display = gr.Dataframe(
                            headers=["角色", "场景", "对话内容摘要", "质量分"],
                            datatype=["str", "str", "str", "number"],
                            row_count=8,
                            col_count=(4, "fixed"),
                        )
                        view_content_btn = gr.Button("查看完整对话")

                    with gr.TabItem("📊 统计与导出"):
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("#### 数据统计")
                                stats_display = gr.Textbox(
                                    label="统计信息",
                                    lines=8,
                                    interactive=False,
                                    placeholder="数据集总数：\n语料条数：\n场景分布：\n...",
                                )
                            with gr.Column():
                                gr.Markdown("#### 导出数据")
                                gr.Markdown("将数据集导出为常见的微调格式。")
                                export_format = gr.Radio(
                                    ["jsonl"], label="选择导出格式", value="jsonl"
                                )
                                export_btn = gr.Button(
                                    "🚀 导出数据集", variant="primary"
                                )

    return dataset_ui
