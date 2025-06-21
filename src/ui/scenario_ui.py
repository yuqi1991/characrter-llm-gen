import gradio as gr
import pandas as pd
from src.services import scenario_service


def create_scenario_ui():
    """创建场景标签管理UI"""
    # State to store the original name of the selected scenario for updates
    selected_scenario_name_state = gr.State(None)

    def load_scenarios():
        """Load scenarios and format them for the dataframe."""
        scenarios = scenario_service.get_all_scenarios_for_display()
        # Create a pandas DataFrame for better display control in Gradio
        df = pd.DataFrame(scenarios, columns=["标签名称", "场景描述"])
        return df

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

    def on_save_scenario(original_name, new_name, description):
        """Handle save button click."""
        if not new_name:
            gr.Warning("场景名称不能为空！")
            return gr.update(), gr.update(), gr.update(), gr.update()
        try:
            scenario_service.save_scenario(
                original_name=original_name, new_name=new_name, description=description
            )
            gr.Info(f"场景 '{new_name}' 已成功保存！")
            df = load_scenarios()
            return df, None, "", ""  # Refresh list and clear form
        except ValueError as e:
            gr.Warning(str(e))
            # On error, don't change the UI state, just show a warning.
            return gr.update(), gr.update(), gr.update(), gr.update()

    def on_delete_scenario(selected_name, current_name):
        """Handle delete button click."""
        # Use selected_name if available, otherwise use current_name from the input field
        name_to_delete = selected_name if selected_name else current_name

        if not name_to_delete:
            gr.Warning("请先选择一个场景！")
            return gr.update(), gr.update(), gr.update(), gr.update()

        deleted = scenario_service.delete_scenario_by_name(name_to_delete)
        if deleted:
            gr.Info(f"场景 '{name_to_delete}' 已被删除。")
            df = load_scenarios()
            return df, None, "", ""
        else:
            gr.Warning(f"删除场景 '{name_to_delete}' 失败。")
            # On error, don't change the UI state
            return gr.update(), gr.update(), gr.update(), gr.update()

    def on_add_new_scenario():
        """Clear form to add a new scenario."""
        return None, "", ""

    with gr.Blocks(analytics_enabled=False) as scenario_ui:
        gr.Markdown("## 🏞️ 场景标签管理\n创建和管理用于生成语料的场景。")

        with gr.Row():
            with gr.Column(scale=2):
                scenario_list = gr.Dataframe(
                    headers=["标签名称", "场景描述"],
                    datatype=["str", "str"],
                    row_count=(8, "dynamic"),
                    col_count=(2, "fixed"),
                    label="场景标签列表",
                    interactive=False,  # Selection handled by .select() event
                )

            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### 场景编辑器")
                    scenario_name = gr.Textbox(
                        label="场景标签名称", placeholder="例如：日常闲聊"
                    )
                    scenario_prompt = gr.Textbox(
                        label="场景描述/提示词模板",
                        lines=10,
                        placeholder="在此输入场景的具体描述...",
                    )
                    with gr.Row():
                        add_scenario_btn = gr.Button("✨ 添加新场景")
                        delete_scenario_btn = gr.Button(
                            "🗑️ 删除选中场景", variant="stop"
                        )
                    save_scenario_btn = gr.Button(
                        "💾 保存场景", variant="primary", scale=2
                    )

        # Event Handlers
        scenario_ui.load(fn=load_scenarios, outputs=[scenario_list])

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
            inputs=[selected_scenario_name_state, scenario_name, scenario_prompt],
            outputs=[
                scenario_list,
                selected_scenario_name_state,
                scenario_name,
                scenario_prompt,
            ],
        )

        delete_scenario_btn.click(
            fn=on_delete_scenario,
            inputs=[selected_scenario_name_state, scenario_name],
            outputs=[
                scenario_list,
                selected_scenario_name_state,
                scenario_name,
                scenario_prompt,
            ],
        )

    return scenario_ui
