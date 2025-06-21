import gradio as gr


def create_character_ui():
    """创建角色卡管理UI"""
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
                    "### 说明\n- **角色名称**：角色的唯一标识。\n- **角色简介**：对角色的简短概括。\n- **性格特征**：详细描述角色的性格，例如MBTI、价值观等。\n- **背景故事**：角色的过去和经历。\n- **口语风格**：角色说话的习惯和特点。\n- **对话示例**：提供一些对话范例，帮助LLM模仿。"
                )

            with gr.Column(scale=2):
                with gr.Group():
                    gr.Markdown("### 角色卡编辑器")

                    # Placeholders to avoid long lines
                    desc_placeholder = (
                        "例如：一位来自大阪的网球天才，以其完美的网球风格而闻名。"
                    )
                    pers_placeholder = "例如：冷静、沉着，有时会说出冷笑话。对胜利有强烈的执着，但更享受过程。"
                    bg_placeholder = (
                        "例如：在网球名校四天宝寺中学担任部长，带领队伍挑战全国冠军。"
                    )
                    style_placeholder = (
                        "例如：关西腔，语速平稳，喜欢在句尾加上「んふっ」（嗯哼）。"
                    )
                    ex_placeholder = (
                        "user: 今天天气真好啊。\n"
                        "assistant: 是啊，心情都跟着放晴了呢。んふっ，要不要去打一场网球？"
                    )

                    char_name = gr.Textbox(
                        label="角色名称", placeholder="例如：白石藏之介"
                    )
                    char_description = gr.Textbox(
                        label="角色简介", lines=2, placeholder=desc_placeholder
                    )
                    char_personality = gr.Textbox(
                        label="性格特征", lines=4, placeholder=pers_placeholder
                    )
                    char_background = gr.Textbox(
                        label="背景故事", lines=4, placeholder=bg_placeholder
                    )
                    char_speaking_style = gr.Textbox(
                        label="口语风格", lines=4, placeholder=style_placeholder
                    )
                    char_dialogue_examples = gr.TextArea(
                        label="对话示例 (user/assistant)",
                        lines=5,
                        placeholder=ex_placeholder,
                    )

                    with gr.Row():
                        save_char_btn = gr.Button("💾 保存角色卡", variant="primary")
                        cancel_char_btn = gr.Button("↩️ 取消")

    return character_ui
