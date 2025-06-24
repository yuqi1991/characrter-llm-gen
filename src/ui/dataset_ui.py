import gradio as gr
import pandas as pd
import json
from src.services import character_service, scenario_service, dataset_service


def create_dataset_ui():
    """Creates the UI for dataset management."""

    selected_dataset_id_state = gr.State(None)

    def load_all_dropdowns():
        datasets = dataset_service.get_all_datasets_for_display()
        dataset_names = [d["name"] for d in datasets]
        characters = character_service.get_all_characters()
        character_names = [c["name"] for c in characters]
        scenarios = scenario_service.get_all_scenarios()
        scenario_names = [s["name"] for s in scenarios]
        return (
            gr.update(choices=dataset_names),
            gr.update(choices=character_names),
            gr.update(choices=scenario_names),
        )

    def format_dialogue(dialogue):
        if isinstance(dialogue, str):
            try:
                dialogue = json.loads(dialogue)
            except json.JSONDecodeError:
                return dialogue
        return json.dumps(dialogue, ensure_ascii=False, indent=2)

    def update_corpus_view(dataset_id, scenario_filters):
        if not dataset_id:
            empty_df = pd.DataFrame(columns=["dialogue", "scenarios"])
            return empty_df, "请先选择一个数据集。", gr.update(choices=[], value=[])

        corpus_data = dataset_service.get_corpus_by_dataset(
            dataset_id, scenario_filters
        )
        if corpus_data:
            for item in corpus_data:
                item["dialogue"] = format_dialogue(item.get("dialogue", "{}"))
        corpus_df = (
            pd.DataFrame(corpus_data)
            if corpus_data
            else pd.DataFrame(columns=["dialogue", "scenarios"])
        )

        stats = dataset_service.get_dataset_stats(dataset_id)
        stats_md = f"**总语料数**: {stats['total_corpus_count']}\n\n**各场景语料数**:\n"
        if stats["scenario_counts"]:
            stats_md += "\n".join(
                f"- {name}: {count}" for name, count in stats["scenario_counts"].items()
            )
        else:
            stats_md += "- 暂无场景统计"

        dataset_details = dataset_service.get_dataset_details_by_id(dataset_id)
        scenario_choices = (
            dataset_details.get("scenario_names", []) if dataset_details else []
        )
        return corpus_df, stats_md, gr.update(choices=scenario_choices)

    def on_select_dataset(dataset_name):
        if not dataset_name:
            return None, "", "", None, [], *update_corpus_view(None, [])

        details = dataset_service.get_dataset_details(dataset_name)
        if details:
            corpus_df, stats_md, scenario_filter_update = update_corpus_view(
                details["id"], []
            )
            return (
                details["id"],
                details["name"],
                details["description"],
                details["character_name"],
                details["scenario_names"],
                corpus_df,
                stats_md,
                scenario_filter_update,
            )
        return None, "", "", None, [], *update_corpus_view(None, [])

    def on_save_dataset(dataset_id, name, description, character, scenarios):
        if not name or not character:
            gr.Warning("数据集名称和绑定角色不能为空！")
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
            )

        try:
            new_id = dataset_service.create_or_update_dataset(
                dataset_id, name, description, character, scenarios
            )
            gr.Info(f"数据集 '{name}' 已成功保存！")
            datasets_dd, _, _ = load_all_dropdowns()
            corpus_df, stats_md, scenario_filter_update = update_corpus_view(new_id, [])
            return (
                datasets_dd,
                new_id,
                name,
                description,
                character,
                scenarios,
                corpus_df,
                stats_md,
                scenario_filter_update,
            )
        except ValueError as e:
            gr.Warning(str(e))
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
            )

    def on_delete_dataset(dataset_id):
        if not dataset_id:
            gr.Warning("请先选择一个要删除的数据集！")
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
            )

        success = dataset_service.delete_dataset(dataset_id)
        if success:
            gr.Info("数据集已成功删除。")
            new_datasets, _, _ = load_all_dropdowns()
            empty_form = (None, "", "", None, [])
            empty_corpus_view = update_corpus_view(None, [])
            return new_datasets, *empty_form, *empty_corpus_view
        else:
            gr.Warning("删除数据集失败！")
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
            )

    def on_export_corpus(dataset_id, export_format):
        """导出语料库数据"""
        if not dataset_id:
            gr.Warning("请先选择一个数据集！")
            return None

        try:
            if export_format == "完整格式 (JSONL)":
                filename = dataset_service.export_dataset_corpus_to_jsonl(dataset_id)
            elif export_format == "训练格式 (JSONL)":
                filename = dataset_service.export_dataset_corpus_to_standard_format(
                    dataset_id
                )
            else:
                gr.Warning("请选择导出格式！")
                return None

            # 检查文件是否存在
            import os

            if os.path.exists(filename):
                gr.Info(
                    "语料库已成功导出！文件已准备好下载。",
                )
                return gr.update(value=filename, visible=True)
            else:
                gr.Warning("文件生成失败，请重试")
                return gr.update(visible=False)
        except Exception as e:
            gr.Warning(f"导出失败: {str(e)}")
            return gr.update(visible=False)

    def on_add_new_dataset():
        return None, "", "", None, []

    with gr.Blocks(analytics_enabled=False) as dataset_ui:
        gr.Markdown("## 📚 语料数据集管理\n管理和配置用于生成任务的数据集。")
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 数据集配置")
                dataset_dropdown = gr.Dropdown(label="选择数据集")
                with gr.Group():
                    dataset_name = gr.Textbox(label="数据集名称")
                    dataset_description = gr.Textbox(label="数据集描述", lines=3)
                    character_dropdown = gr.Dropdown(label="绑定角色")
                    scenario_multiselect = gr.Dropdown(
                        label="绑定场景标签 (可多选)",
                        multiselect=True,
                        interactive=True,
                    )
                with gr.Row():
                    add_btn = gr.Button("✨ 添加新数据集")
                    delete_btn = gr.Button("🗑️ 删除数据集", variant="stop")
                save_btn = gr.Button("💾 保存数据集配置", variant="primary")

                # 添加导出功能区域
                gr.Markdown("### 语料库导出")
                with gr.Group():
                    export_format = gr.Dropdown(
                        label="导出格式",
                        choices=["完整格式 (JSONL)", "训练格式 (JSONL)"],
                        value="完整格式 (JSONL)",
                        info="完整格式包含所有元数据，训练格式适用于模型微调",
                    )
                    export_btn = gr.Button("📥 导出语料库", variant="secondary")
                    export_file = gr.File(label="下载文件", visible=False)

            with gr.Column(scale=2):
                gr.Markdown("### 数据集预览与统计")
                with gr.Row():
                    filter_by_scenario_dropdown = gr.Dropdown(
                        label="按场景筛选预览", multiselect=True
                    )
                corpus_preview_df = gr.Dataframe(
                    headers=["dialogue", "scenarios"],
                    label="语料预览",
                    row_count=(10, "dynamic"),
                    wrap=True,
                )
                stats_display = gr.Markdown(label="数据集统计")

        outputs_left_panel = [
            selected_dataset_id_state,
            dataset_name,
            dataset_description,
            character_dropdown,
            scenario_multiselect,
        ]
        outputs_right_panel = [
            corpus_preview_df,
            stats_display,
            filter_by_scenario_dropdown,
        ]

        dataset_ui.load(
            fn=load_all_dropdowns,
            outputs=[dataset_dropdown, character_dropdown, scenario_multiselect],
        )
        dataset_dropdown.change(
            fn=on_select_dataset,
            inputs=[dataset_dropdown],
            outputs=[*outputs_left_panel, *outputs_right_panel],
        )
        add_btn.click(fn=on_add_new_dataset, outputs=outputs_left_panel)
        save_btn.click(
            fn=on_save_dataset,
            inputs=[
                selected_dataset_id_state,
                dataset_name,
                dataset_description,
                character_dropdown,
                scenario_multiselect,
            ],
            outputs=[dataset_dropdown, *outputs_left_panel, *outputs_right_panel],
        )
        delete_btn.click(
            fn=on_delete_dataset,
            inputs=[selected_dataset_id_state],
            outputs=[dataset_dropdown, *outputs_left_panel, *outputs_right_panel],
        )

        # 添加导出事件处理
        export_btn.click(
            fn=on_export_corpus,
            inputs=[selected_dataset_id_state, export_format],
            outputs=[export_file],
        )

        filter_by_scenario_dropdown.change(
            fn=update_corpus_view,
            inputs=[selected_dataset_id_state, filter_by_scenario_dropdown],
            outputs=outputs_right_panel,
        )

    return dataset_ui
