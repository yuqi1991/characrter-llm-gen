import gradio as gr
from src.services import prompt_service


def on_select_prompt(filename: str):
    """
    当从下拉菜单选择提示词时触发。
    """
    content = prompt_service.read_prompt_file(filename)
    return filename, content


def on_save_prompt(filename: str, content: str):
    """
    处理保存提示词的逻辑。
    """
    if not filename:
        return gr.Dropdown(), "❌ 错误：文件名不能为空"
    message = prompt_service.save_prompt_file(filename, content)

    if not filename.endswith(".txt"):
        filename += ".txt"

    # 刷新提示词列表
    new_choices = prompt_service.get_prompt_files()
    return gr.Dropdown(choices=new_choices, value=filename), message


def on_delete_prompt(filename: str):
    """
    处理删除提示词的逻辑。
    """
    message = prompt_service.delete_prompt_file(filename)
    new_choices = prompt_service.get_prompt_files()
    return gr.Dropdown(choices=new_choices, value=None), "", "", message


def on_new_prompt():
    """
    清空输入框以创建新的提示词。
    """
    return "", ""


def create_prompt_ui():
    """
    创建提示词管理的Gradio UI组件。
    """
    with gr.Blocks() as prompt_ui:
        gr.Markdown(
            "## 📝 提示词模板管理\n在这里，您可以直接管理 `templates/prompts/` 目录下的 `.txt` 文件。"
        )

        status_message = gr.Markdown("")

        with gr.Row():
            prompt_files_dd = gr.Dropdown(
                label="选择或搜索提示词模板",
                choices=prompt_service.get_prompt_files(),
                interactive=True,
                allow_custom_value=True,
            )
            new_button = gr.Button("➕ 新建模板")

        with gr.Group():
            prompt_filename_txt = gr.Textbox(
                label="文件名 (例如: my_prompt.txt)",
                info="如果文件已存在，则会覆盖保存。",
            )
            prompt_content_txt = gr.Textbox(
                label="模板内容", lines=20, show_copy_button=True
            )

        with gr.Row():
            save_button = gr.Button("💾 保存", variant="primary")
            delete_button = gr.Button("🗑️ 删除", variant="stop")

        # --- Event Handlers ---

        # 选择一个文件
        prompt_files_dd.select(
            fn=on_select_prompt,
            inputs=[prompt_files_dd],
            outputs=[prompt_filename_txt, prompt_content_txt],
        )

        # "新建"按钮
        new_button.click(
            fn=on_new_prompt,
            inputs=[],
            outputs=[prompt_filename_txt, prompt_content_txt, status_message],
        )

        # "保存"按钮
        save_button.click(
            fn=on_save_prompt,
            inputs=[prompt_filename_txt, prompt_content_txt],
            outputs=[prompt_files_dd, status_message],
        )

        # "删除"按钮
        delete_button.click(
            fn=on_delete_prompt,
            inputs=[prompt_filename_txt],
            outputs=[
                prompt_files_dd,
                prompt_filename_txt,
                prompt_content_txt,
                status_message,
            ],
            # 添加确认提示
            js="() => confirm('您确定要删除这个提示词模板吗？')",
        )

    return prompt_ui
