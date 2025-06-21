import gradio as gr
from src.services import character_service


def create_character_ui():
    """创建角色卡管理UI"""
    character_id_state = gr.State(None)

    def get_character_names():
        """Helper to fetch character names for the dropdown."""
        return character_service.get_all_character_names()

    def on_load_data():
        """Function to run when the tab is loaded."""
        return gr.update(choices=get_character_names())

    def on_select_character(char_name: str):
        """Handle character selection from the dropdown."""
        if not char_name:
            return None, "", "", "", "", "", ""

        char_dict = character_service.get_character_by_name(char_name)
        if char_dict:
            return (
                char_dict.get("id"),
                char_dict.get("name", ""),
                char_dict.get("description", ""),
                char_dict.get("personality", ""),
                char_dict.get("background", ""),
                char_dict.get("speaking_style", ""),
                char_dict.get("dialogue_examples", ""),
            )
        return None, "", "", "", "", "", ""

    def on_save_character(
        char_id,
        name,
        description,
        personality,
        background,
        speaking_style,
        dialogue_examples,
    ):
        """Handle the save button click."""
        if not name:
            gr.Warning("角色名称不能为空！")
            return gr.update(), gr.update()
        try:
            character_service.save_character(
                id=char_id,
                name=name,
                description=description,
                personality=personality,
                background=background,
                speaking_style=speaking_style,
                dialogue_examples=dialogue_examples,
            )
            gr.Info(f"角色 '{name}' 已成功保存！")
            return gr.update(choices=get_character_names(), value=name)
        except ValueError as e:
            gr.Warning(str(e))
            return gr.update()

    def on_delete_character(char_name: str):
        """Handle character deletion."""
        if not char_name:
            gr.Warning("请先选择一个角色！")
            return gr.update()

        deleted = character_service.delete_character_by_name(char_name)
        if deleted:
            gr.Info(f"角色 '{char_name}' 已被删除。")
            return gr.update(choices=get_character_names(), value=None)
        else:
            gr.Warning(f"删除角色 '{char_name}' 失败。")
            return gr.update()

    def on_new_character():
        """Clear the form to create a new character."""
        return None, "", "", "", "", "", ""

    with gr.Blocks(analytics_enabled=False) as character_ui:
        gr.Markdown("## ✍️ 角色卡管理\n在此创建、编辑和管理您的角色卡。")

        with gr.Row():
            with gr.Column(scale=1):
                character_list = gr.Dropdown(
                    label="选择角色卡", info="选择一个已有的角色进行编辑或查看。"
                )
                with gr.Row():
                    new_char_btn = gr.Button("✨ 新建角色")
                    delete_char_btn = gr.Button("🗑️ 删除角色", variant="stop")

                gr.Markdown("---")
                gr.Markdown(
                    "### 说明\n- **角色名称**：角色的唯一标识。\n- **角色简介**：对角色的简短概括。\n- **性格特征**：详细描述角色的性格。\n- **背景故事**：角色的过去和经历。\n- **口语风格**：角色说话的习惯和特点。\n- **对话示例**：提供一些对话范例。"
                )

            with gr.Column(scale=2):
                with gr.Group():
                    gr.Markdown("### 角色卡编辑器")
                    char_name = gr.Textbox(
                        label="角色名称", placeholder="例如：白石藏之介"
                    )
                    char_description = gr.Textbox(label="角色简介", lines=2)
                    char_personality = gr.Textbox(label="性格特征", lines=4)
                    char_background = gr.Textbox(label="背景故事", lines=4)
                    char_speaking_style = gr.Textbox(label="口语风格", lines=4)
                    char_dialogue_examples = gr.TextArea(
                        label="对话示例 (user/assistant)", lines=5
                    )
                    with gr.Row():
                        save_char_btn = gr.Button("💾 保存角色卡", variant="primary")

        # Event handlers
        character_list.select(
            fn=on_select_character,
            inputs=[character_list],
            outputs=[
                character_id_state,
                char_name,
                char_description,
                char_personality,
                char_background,
                char_speaking_style,
                char_dialogue_examples,
            ],
        )

        save_char_btn.click(
            fn=on_save_character,
            inputs=[
                character_id_state,
                char_name,
                char_description,
                char_personality,
                char_background,
                char_speaking_style,
                char_dialogue_examples,
            ],
            outputs=[character_list],
        )

        delete_char_btn.click(
            fn=on_delete_character, inputs=[character_list], outputs=[character_list]
        )

        new_char_btn.click(
            fn=on_new_character,
            inputs=[],
            outputs=[
                character_id_state,
                char_name,
                char_description,
                char_personality,
                char_background,
                char_speaking_style,
                char_dialogue_examples,
            ],
        )

        character_ui.load(fn=on_load_data, outputs=[character_list])

    return character_ui
