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
        # 初始时场景选择框为空，需要先选择角色
        return (
            gr.update(choices=dataset_names),
            gr.update(choices=character_names),
            gr.update(choices=[], value=[]),  # 空的场景选择框
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

    def on_character_change_in_dataset(character_name):
        """当角色下拉菜单变化时，更新场景多选框的选项"""
        if not character_name:
            return gr.update(choices=[], value=[])

        # NOTE: 这耦合了两个服务，但为了UI的响应性是值得的
        character = character_service.get_character_by_name(character_name)
        if character:
            scenarios = scenario_service.get_scenarios_by_character(character["id"])
            scenario_names = [s["name"] for s in scenarios]
            return gr.update(choices=scenario_names, value=[])
        return gr.update(choices=[], value=[])

    def on_delete_corpus_by_scenario(dataset_id, scenarios_to_delete):
        """处理按场景删除语料的按钮点击事件"""
        if not dataset_id:
            gr.Warning("请先选择一个数据集！")
            return gr.update(), gr.update(), gr.update()
        if not scenarios_to_delete:
            gr.Warning("请至少选择一个要删除语料的场景！")
            return gr.update(), gr.update(), gr.update()

        try:
            deleted_count = dataset_service.delete_corpus_by_scenarios(
                dataset_id, scenarios_to_delete
            )
            gr.Info(f"成功删除了 {deleted_count} 条语料。")
            # Refresh corpus view and stats
            return update_corpus_view(dataset_id, [])
        except Exception as e:
            gr.Warning(f"删除语料失败: {e}")
            return gr.update(), gr.update(), gr.update()

    def on_detect_invalid_data(dataset_id):
        """检测不合规范的数据"""
        if not dataset_id:
            # 检测所有数据集
            try:
                result = dataset_service.detect_invalid_corpus_data()
                total_checked = result["total_checked"]
                invalid_count = len(result["invalid_entries"])

                if invalid_count == 0:
                    detection_info = f"✅ 检测完成：总共检查了 {total_checked} 条语料，**未发现**不合规范数据"
                    detection_details = "所有数据格式正确！"
                    return detection_info, detection_details, gr.update(visible=False)
                else:
                    detection_info = f"⚠️ 检测完成：总共检查了 {total_checked} 条语料，发现 **{invalid_count}** 条不合规范数据"

                    # 构建详细信息
                    details_lines = ["### 不合规范数据详情：\n"]
                    for i, entry in enumerate(
                        result["invalid_entries"][:10]
                    ):  # 只显示前10条
                        details_lines.append(f"**{i+1}. 语料ID: {entry['corpus_id']}**")
                        details_lines.append(f"- 数据集: {entry['dataset_name']}")
                        details_lines.append(f"- 问题: {', '.join(entry['issues'])}")
                        details_lines.append(
                            f"- 数据样本: `{entry['dialogue_sample'][:100]}...`"
                        )
                        details_lines.append("")

                    if len(result["invalid_entries"]) > 10:
                        details_lines.append(
                            f"*...还有 {len(result['invalid_entries']) - 10} 条数据未显示*"
                        )

                    detection_details = "\n".join(details_lines)
                    return detection_info, detection_details, gr.update(visible=True)

            except Exception as e:
                error_msg = f"❌ 检测失败: {str(e)}"
                return error_msg, "", gr.update(visible=False)
        else:
            # 检测特定数据集
            try:
                result = dataset_service.detect_invalid_corpus_data(dataset_id)
                total_checked = result["total_checked"]
                invalid_count = len(result["invalid_entries"])

                dataset_details = dataset_service.get_dataset_details_by_id(dataset_id)
                dataset_name = (
                    dataset_details["name"] if dataset_details else f"ID {dataset_id}"
                )

                if invalid_count == 0:
                    detection_info = (
                        f"✅ 数据集 '{dataset_name}' 检测完成：检查了 {total_checked} 条语料，"
                        f"**未发现**不合规范数据"
                    )
                    detection_details = "该数据集所有数据格式正确！"
                    return detection_info, detection_details, gr.update(visible=False)
                else:
                    detection_info = (
                        f"⚠️ 数据集 '{dataset_name}' 检测完成：检查了 {total_checked} 条语料，"
                        f"发现 **{invalid_count}** 条不合规范数据"
                    )

                    # 构建详细信息
                    details_lines = ["### 不合规范数据详情：\n"]
                    for i, entry in enumerate(
                        result["invalid_entries"][:10]
                    ):  # 只显示前10条
                        details_lines.append(f"**{i+1}. 语料ID: {entry['corpus_id']}**")
                        details_lines.append(f"- 问题: {', '.join(entry['issues'])}")
                        details_lines.append(
                            f"- 数据样本: `{entry['dialogue_sample'][:100]}...`"
                        )
                        details_lines.append("")

                    if len(result["invalid_entries"]) > 10:
                        details_lines.append(
                            f"*...还有 {len(result['invalid_entries']) - 10} 条数据未显示*"
                        )

                    detection_details = "\n".join(details_lines)
                    return detection_info, detection_details, gr.update(visible=True)

            except Exception as e:
                error_msg = f"❌ 检测失败: {str(e)}"
                return error_msg, "", gr.update(visible=False)

    def on_clean_invalid_data(dataset_id, dry_run):
        """清理不合规范的数据"""
        try:
            result = dataset_service.clean_invalid_corpus_data(dataset_id, dry_run)
            detected_count = result["detected_count"]
            deleted_count = result["deleted_count"]

            if detected_count == 0:
                gr.Info("未发现需要清理的不合规范数据")
                return "未发现需要清理的数据", gr.update(), gr.update(), gr.update()

            if dry_run:
                cleanup_info = f"🔍 试运行模式：发现 {detected_count} 条不合规范数据，如需删除请点击'确认清理'"
                gr.Info(f"试运行完成：发现 {detected_count} 条不合规范数据")
                return cleanup_info, gr.update(), gr.update(), gr.update()
            else:
                cleanup_info = f"✅ 清理完成：成功删除 {deleted_count}/{detected_count} 条不合规范数据"
                gr.Info(f"清理完成：成功删除 {deleted_count} 条数据")

                # 刷新语料预览和统计
                if dataset_id:
                    corpus_df, stats_md, scenario_filter_update = update_corpus_view(
                        dataset_id, []
                    )
                    return cleanup_info, corpus_df, stats_md, scenario_filter_update
                else:
                    return cleanup_info, gr.update(), gr.update(), gr.update()

        except Exception as e:
            error_msg = f"❌ 清理失败: {str(e)}"
            gr.Warning(f"清理失败: {str(e)}")
            return error_msg, gr.update(), gr.update(), gr.update()

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

                # 添加数据清理功能区域
                gr.Markdown("### 数据质量管理")
                with gr.Group():
                    gr.Markdown("**检测和清理不合规范的语料数据**")
                    with gr.Row():
                        detect_btn = gr.Button("🔍 检测问题数据", variant="secondary")
                        clean_dry_run_btn = gr.Button(
                            "🧪 试运行清理", variant="secondary"
                        )
                        clean_confirm_btn = gr.Button("🗑️ 确认清理", variant="stop")

                        # 检测结果显示
                    detection_result = gr.Markdown(visible=True)
                    detection_details = gr.Markdown(visible=True)

                    # 清理结果显示
                    cleanup_result = gr.Markdown(visible=True)

            with gr.Column(scale=2):
                gr.Markdown("### 数据集预览与统计")
                with gr.Row():
                    filter_by_scenario_dropdown = gr.Dropdown(
                        label="按场景筛选预览", multiselect=True, scale=4
                    )
                    delete_corpus_by_scenario_btn = gr.Button(
                        "🗑️ 删除选中场景的语料", variant="stop", scale=1
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

        character_dropdown.change(
            fn=on_character_change_in_dataset,
            inputs=[character_dropdown],
            outputs=[scenario_multiselect],
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

        delete_corpus_by_scenario_btn.click(
            fn=on_delete_corpus_by_scenario,
            inputs=[selected_dataset_id_state, filter_by_scenario_dropdown],
            outputs=[
                corpus_preview_df,
                stats_display,
                filter_by_scenario_dropdown,
            ],
        )

        # 添加数据清理事件处理
        detect_btn.click(
            fn=on_detect_invalid_data,
            inputs=[selected_dataset_id_state],
            outputs=[detection_result, detection_details, cleanup_result],
        )

        clean_dry_run_btn.click(
            fn=lambda dataset_id: on_clean_invalid_data(dataset_id, dry_run=True),
            inputs=[selected_dataset_id_state],
            outputs=[
                cleanup_result,
                corpus_preview_df,
                stats_display,
                filter_by_scenario_dropdown,
            ],
        )

        clean_confirm_btn.click(
            fn=lambda dataset_id: on_clean_invalid_data(dataset_id, dry_run=False),
            inputs=[selected_dataset_id_state],
            outputs=[
                cleanup_result,
                corpus_preview_df,
                stats_display,
                filter_by_scenario_dropdown,
            ],
        )

    return dataset_ui
