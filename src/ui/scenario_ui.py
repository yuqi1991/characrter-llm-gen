import gradio as gr
import pandas as pd
from src.services import scenario_service, character_service


def create_scenario_ui():
    """创建场景标签管理UI"""
    selected_character_id_state = gr.State(None)
    selected_scenario_name_state = gr.State(None)

    def load_characters():
        """加载所有角色到下拉菜单"""
        characters = character_service.get_all_characters()
        character_names = [c["name"] for c in characters]
        # 创建一个从名称到ID的映射
        character_map = {c["name"]: c["id"] for c in characters}
        return gr.update(choices=character_names), character_map

    def on_select_character(character_name, character_map):
        """当选择一个角色后，加载其场景"""
        if not character_name:
            # 清空并禁用组件
            empty_df = pd.DataFrame(columns=["标签名称", "场景描述"])
            return (
                None,  # character_id
                empty_df,  # scenarios_df
                gr.update(interactive=False),  # scenario_name
                gr.update(interactive=False),  # scenario_prompt
                gr.update(interactive=False),  # add_scenario_btn
                gr.update(interactive=False),  # delete_scenario_btn
                gr.update(interactive=False),  # save_scenario_btn
                gr.update(interactive=False),  # export_scenario_btn
                gr.update(interactive=False),  # import_scenario_btn
            )

        character_id = character_map.get(character_name)
        scenarios = scenario_service.get_scenarios_for_display_by_character(
            character_id
        )
        df = pd.DataFrame(scenarios, columns=["标签名称", "场景描述"])
        # 启用组件
        return (
            character_id,  # character_id
            df,  # scenarios_df
            gr.update(interactive=True),  # scenario_name
            gr.update(interactive=True),  # scenario_prompt
            gr.update(interactive=True),  # add_scenario_btn
            gr.update(interactive=True),  # delete_scenario_btn
            gr.update(interactive=True),  # save_scenario_btn
            gr.update(interactive=True),  # export_scenario_btn
            gr.update(interactive=True),  # import_scenario_btn
        )

    def load_scenarios(character_id):
        """根据角色ID加载场景"""
        if not character_id:
            return pd.DataFrame(columns=["标签名称", "场景描述"])
        scenarios = scenario_service.get_scenarios_for_display_by_character(
            character_id
        )
        return pd.DataFrame(scenarios, columns=["标签名称", "场景描述"])

    def on_select_scenario(evt: gr.SelectData, scenarios_df: pd.DataFrame):
        """Handle scenario selection in the dataframe."""
        if evt.index is not None:
            selected_row_index = evt.index[0]
            if (
                scenarios_df is not None
                and not scenarios_df.empty
                and 0 <= selected_row_index < len(scenarios_df)
            ):
                selected_row = scenarios_df.iloc[selected_row_index]
                name = selected_row["标签名称"]
                description = selected_row["场景描述"]
                return name, name, description
        return None, "", ""

    def on_save_scenario(character_id, original_name, new_name, description):
        """Handle save button click."""
        if not character_id:
            gr.Warning("请先选择一个角色！")
            return gr.update(), gr.update(), gr.update(), gr.update()
        if not new_name:
            gr.Warning("场景名称不能为空！")
            return gr.update(), gr.update(), gr.update(), gr.update()
        try:
            scenario_service.save_scenario(
                character_id=character_id,
                original_name=original_name,
                new_name=new_name,
                description=description,
            )
            gr.Info(f"场景 '{new_name}' 已成功保存！")
            df = load_scenarios(character_id)
            return df, None, "", ""
        except ValueError as e:
            gr.Warning(str(e))
            return gr.update(), gr.update(), gr.update(), gr.update()

    def on_delete_scenario(character_id, selected_name, current_name):
        """Handle delete button click."""
        if not character_id:
            gr.Warning("请先选择一个角色！")
            return gr.update(), gr.update(), gr.update(), gr.update()

        name_to_delete = selected_name if selected_name else current_name
        if not name_to_delete:
            gr.Warning("请先选择一个场景！")
            return gr.update(), gr.update(), gr.update(), gr.update()

        deleted = scenario_service.delete_scenario_by_name(character_id, name_to_delete)
        if deleted:
            gr.Info(f"场景 '{name_to_delete}' 已被删除。")
            df = load_scenarios(character_id)
            return df, None, "", ""
        else:
            gr.Warning(f"删除场景 '{name_to_delete}' 失败。")
            return gr.update(), gr.update(), gr.update(), gr.update()

    def on_add_new_scenario():
        """Clear form to add a new scenario."""
        return None, "", ""

    def on_export_scenarios(character_id):
        """Handle export scenarios button click."""
        if not character_id:
            gr.Warning("请先选择一个角色以导出其场景！")
            return None
        try:
            file_path = scenario_service.export_scenarios_to_json(character_id)
            gr.Info("场景已成功导出！")
            return file_path
        except Exception as e:
            gr.Warning(f"导出失败: {e}")
            return None

    def on_import_scenarios(character_id, file):
        """Handle import scenarios button click."""
        if not character_id:
            gr.Warning("请先选择一个角色以导入场景！")
            return gr.update()
        if file is None:
            gr.Warning("请先上传一个JSON文件！")
            return gr.update()
        try:
            added, skipped = scenario_service.import_scenarios_from_json(
                character_id, file.name
            )
            gr.Info(
                f"导入完成！成功添加 {added} 个新场景，跳过 {skipped} 个已存在的场景。"
            )
            return load_scenarios(character_id)
        except Exception as e:
            gr.Warning(f"导入失败: {e}")
            return gr.update()

    with gr.Blocks(analytics_enabled=False) as scenario_ui:
        gr.Markdown("## 🏞️ 场景标签管理\n创建和管理用于生成语料的场景。")

        character_map_state = gr.State({})

        with gr.Row():
            character_dropdown = gr.Dropdown(label="选择角色", scale=1)

        with gr.Row():
            with gr.Column(scale=2):
                scenario_list = gr.Dataframe(
                    headers=["标签名称", "场景描述"],
                    datatype=["str", "str"],
                    row_count=(8, "dynamic"),
                    col_count=(2, "fixed"),
                    label="场景标签列表",
                    interactive=False,
                )

            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### 场景编辑器")
                    scenario_name = gr.Textbox(
                        label="场景标签名称",
                        placeholder="例如：日常闲聊",
                        interactive=False,
                    )
                    scenario_prompt = gr.Textbox(
                        label="场景描述/提示词模板",
                        lines=10,
                        placeholder="在此输入场景的具体描述...",
                        interactive=False,
                    )
                    with gr.Row():
                        add_scenario_btn = gr.Button("✨ 添加新场景", interactive=False)
                        delete_scenario_btn = gr.Button(
                            "🗑️ 删除选中场景", variant="stop", interactive=False
                        )
                    save_scenario_btn = gr.Button(
                        "💾 保存场景", variant="primary", scale=2, interactive=False
                    )
                    with gr.Row():
                        export_scenario_btn = gr.Button(
                            "📤 导出所有场景", interactive=False
                        )
                        import_scenario_btn = gr.UploadButton("📥 导入场景 (JSON)")
                    download_file = gr.File(label="下载导出的文件", interactive=False)

        # Event Handlers
        scenario_ui.load(
            fn=load_characters, outputs=[character_dropdown, character_map_state]
        )

        character_dropdown.change(
            fn=on_select_character,
            inputs=[character_dropdown, character_map_state],
            outputs=[
                selected_character_id_state,
                scenario_list,
                scenario_name,
                scenario_prompt,
                add_scenario_btn,
                delete_scenario_btn,
                save_scenario_btn,
                export_scenario_btn,
                import_scenario_btn,
            ],
        )

        add_scenario_btn.click(
            fn=on_add_new_scenario,
            outputs=[selected_scenario_name_state, scenario_name, scenario_prompt],
        )

        scenario_list.select(
            fn=on_select_scenario,
            inputs=[scenario_list],
            outputs=[selected_scenario_name_state, scenario_name, scenario_prompt],
        )

        save_scenario_btn.click(
            fn=on_save_scenario,
            inputs=[
                selected_character_id_state,
                selected_scenario_name_state,
                scenario_name,
                scenario_prompt,
            ],
            outputs=[
                scenario_list,
                selected_scenario_name_state,
                scenario_name,
                scenario_prompt,
            ],
        )

        delete_scenario_btn.click(
            fn=on_delete_scenario,
            inputs=[
                selected_character_id_state,
                selected_scenario_name_state,
                scenario_name,
            ],
            outputs=[
                scenario_list,
                selected_scenario_name_state,
                scenario_name,
                scenario_prompt,
            ],
        )

        export_scenario_btn.click(
            fn=on_export_scenarios,
            inputs=[selected_character_id_state],
            outputs=[download_file],
        )

        import_scenario_btn.upload(
            fn=on_import_scenarios,
            inputs=[selected_character_id_state, import_scenario_btn],
            outputs=[scenario_list],
        )

    return scenario_ui
