import gradio as gr
import logging

# Import UI creation functions from the ui directory
from src.ui.character_ui import create_character_ui
from src.ui.scenario_ui import create_scenario_ui
from src.ui.dataset_ui import create_dataset_ui
from src.ui.generation_ui import create_generation_ui

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Custom CSS for a more polished look
css = """
/* Add some breathing room */
.gradio-container {
    padding: 20px;
}

/* Style the main title */
#main_title {
    text-align: center;
    font-size: 2.5em;
    font-weight: bold;
    color: #2E86C1;
    margin-bottom: 5px;
}

#main_subtitle {
    text-align: center;
    font-size: 1.1em;
    color: #5D6D7E;
    margin-bottom: 25px;
}

/* Fix transparent background for info/warning/error messages */
.toast-wrap {
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
}

.toast-body {
    background: transparent !important;
    color: #333 !important;
    font-weight: 500 !important;
}

/* Info messages */
.toast-wrap.toast-info {
    background: rgba(59, 130, 246, 0.1) !important;
    border-color: rgba(59, 130, 246, 0.3) !important;
}

.toast-wrap.toast-info .toast-body {
    color: #1e40af !important;
}

/* Success messages */
.toast-wrap.toast-success {
    background: rgba(34, 197, 94, 0.1) !important;
    border-color: rgba(34, 197, 94, 0.3) !important;
}

.toast-wrap.toast-success .toast-body {
    color: #166534 !important;
}

/* Warning messages */
.toast-wrap.toast-warning {
    background: rgba(245, 158, 11, 0.1) !important;
    border-color: rgba(245, 158, 11, 0.3) !important;
}

.toast-wrap.toast-warning .toast-body {
    color: #92400e !important;
}

/* Error messages */
.toast-wrap.toast-error {
    background: rgba(239, 68, 68, 0.1) !important;
    border-color: rgba(239, 68, 68, 0.3) !important;
}

.toast-wrap.toast-error .toast-body {
    color: #dc2626 !important;
}

/* Alternative approach for older Gradio versions */
.gr-form {
    background: white !important;
}

/* Ensure toast notifications are visible */
.toast-container {
    z-index: 9999 !important;
}

/* Fix notification positioning */
.toast {
    background: rgba(255, 255, 255, 0.95) !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    border-radius: 8px !important;
    color: #333 !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
}
"""


def main():
    """Main function to launch the Gradio app."""
    logger.info("启动角色LLM数据集生成器...")

    with gr.Blocks(
        theme=gr.themes.Soft(
            primary_hue=gr.themes.colors.blue, secondary_hue=gr.themes.colors.sky
        ),
        title="Character LLM Dataset Generator",
        css=css,
    ) as demo:

        gr.Markdown("# 🎭 Character LLM Dataset Generator", elem_id="main_title")
        gr.Markdown(
            "一个为角色扮演LLM微调而设计的智能语料生成和管理工具。",
            elem_id="main_subtitle",
        )

        with gr.Tabs():
            with gr.TabItem("✍️ 角色卡管理", id="character_tab"):
                create_character_ui()

            with gr.TabItem("🏞️ 场景标签管理", id="scenario_tab"):
                create_scenario_ui()

            with gr.TabItem("📚 语料数据集管理", id="dataset_tab"):
                create_dataset_ui()

            with gr.TabItem("🚀 语料生成", id="generation_tab"):
                create_generation_ui()

    # Use queue() for handling multiple users or long-running tasks
    demo.queue()

    # Launch the app
    demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False)


if __name__ == "__main__":
    main()
