import gradio as gr
import pandas as pd
import asyncio
import json
from datetime import datetime
from src.services import api_config_service, dataset_service, llm_service


def create_generation_ui():
    """创建语料生成UI"""

    # --- Helper Functions ---
    def load_form_from_config(config_name):
        if not config_name:
            return "", "", "", 1.0, 0.0, 0.0, "OpenAI", gr.update(visible=True)
        config = api_config_service.get_api_config_by_name(config_name)
        if config:
            is_visible = config["api_type"] in ["OpenAI", "Anthropic"]
            return (
                config["name"],
                config["api_key"],
                config.get("base_url", ""),
                config.get("top_p", 1.0),
                config.get("frequency_penalty", 0.0),
                config.get("presence_penalty", 0.0),
                config["api_type"],
                gr.update(visible=is_visible),
            )
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

    def load_form_and_models(config_name):
        """Load form data and fetch models when config changes"""
        # Get form data
        form_data = load_form_from_config(config_name)

        # Get models
        if config_name:
            try:
                models = api_config_service.get_available_models(config_name)
                model_update = gr.update(
                    choices=models, value=models[0] if models else None
                )
                gr.Info(f"已自动获取 {len(models)} 个可用模型")
            except Exception as e:
                model_update = gr.update(choices=[])

        # Return form data + model update
        return form_data + (model_update,)

    def refresh_all_configs():
        configs = api_config_service.get_all_api_configs()
        names = [c["name"] for c in configs]
        df_data = [
            {
                "配置名称": c["name"],
                "API类型": c["api_type"],
                "Base URL": c.get("base_url", ""),
                "创建时间": c["created_at"],
            }
            for c in configs
        ]
        df = pd.DataFrame(df_data)
        return gr.update(choices=names), df

    def on_save_api_config(name, provider, key, base_url, top_p, freq_p, pres_p):
        if not all([name, provider, key]):
            gr.Warning("配置名称、API提供商和API Key不能为空！")
            return gr.update(), gr.update()
        try:
            api_config_service.save_api_config(
                name, provider, key, base_url, top_p, freq_p, pres_p
            )
            gr.Info(f"API配置 '{name}' 已成功保存。")
            return refresh_all_configs()
        except ValueError as e:
            gr.Warning(str(e))
            return gr.update(), gr.update()

    def on_delete_api_config(config_name_to_delete):
        if not config_name_to_delete:
            gr.Warning("请先从列表中选择一个要删除的配置。")
            return gr.update(), gr.update()
        api_config_service.delete_api_config(config_name_to_delete)
        gr.Info(f"API配置 '{config_name_to_delete}' 已删除。")
        return refresh_all_configs()

    def on_get_models(config_name):
        """Fetches and updates the model dropdown."""
        if not config_name:
            gr.Warning("请先选择一个API配置。")
            return gr.update(choices=[])
        try:
            gr.Info(f"正在从 {config_name} 获取可用模型列表...")
            models = api_config_service.get_available_models(config_name)
            gr.Info(f"成功获取 {len(models)} 个模型。")
            # Update choices, set the first model as default, and ensure it's interactive
            if models:
                return gr.update(choices=models, value=models[0], interactive=True)
            else:
                gr.Warning("未能获取到任何可用模型。")
                return gr.update(choices=[], interactive=True)
        except Exception as e:
            gr.Warning(str(e))
            return gr.update(choices=[], interactive=True)

    def load_datasets():
        datasets = dataset_service.get_all_datasets_for_display()
        return gr.update(choices=[d["name"] for d in datasets], interactive=True)

    def start_generation(
        dataset_name,
        api_config_name,
        model_name,
        num_to_generate,
        conversation_turns,
        parallel_requests,
        temperature,
        max_tokens,
        top_p,
        frequency_penalty,
        presence_penalty,
    ):
        """开始生成语料"""
        if not all([dataset_name, api_config_name, model_name]):
            gr.Warning("请确保已选择数据集、API配置和模型！")
            return "请完善生成配置", gr.update(), None

        try:
            # 显示开始信息
            progress_msg = f"开始生成 {num_to_generate} 条语料...\n"
            progress_msg += f"数据集: {dataset_name}\n"
            progress_msg += f"API配置: {api_config_name}\n"
            progress_msg += f"模型: {model_name}\n"
            progress_msg += f"并行请求数: {parallel_requests}\n"

            # 运行异步生成任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                batch = loop.run_until_complete(
                    llm_service.generate_corpus_batch(
                        dataset_name=dataset_name,
                        api_config_name=api_config_name,
                        model_name=model_name,
                        total_count=num_to_generate,
                        conversation_turns=conversation_turns,
                        parallel_requests=parallel_requests,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty,
                    )
                )

                # 格式化结果
                total_time = (batch.end_time - batch.start_time).total_seconds()
                progress_msg += "\n✅ 生成完成！\n"
                progress_msg += f"成功: {batch.completed}/{batch.total_requested}\n"
                progress_msg += f"失败: {batch.failed}\n"
                progress_msg += f"用时: {total_time:.2f}秒\n"

                # 准备预览数据
                preview_data = []
                for i, conversation in enumerate(batch.results[:10]):  # 只显示前10条
                    scenarios_str = ", ".join(conversation.get("scenarios", []))
                    dialogues = conversation.get("dialogues", [])

                    dialogue_text = ""
                    for turn in dialogues:
                        role = turn.get("role", "unknown")
                        content = turn.get("content", "")
                        dialogue_text += f"{role}: {content}\n"

                    preview_data.append(
                        {
                            "序号": i + 1,
                            "场景标签": scenarios_str,
                            "对话内容": dialogue_text.strip(),
                            "轮数": len(dialogues),
                        }
                    )

                preview_df = pd.DataFrame(preview_data)

                # 存储到全局状态以供确认入库使用
                current_batch_state = {"batch": batch, "dataset_name": dataset_name}

                gr.Info(f"生成完成！成功生成 {batch.completed} 条对话")
                return progress_msg, preview_df, current_batch_state

            finally:
                loop.close()

        except Exception as e:
            error_msg = f"❌ 生成失败: {str(e)}"
            gr.Warning(error_msg)
            return error_msg, gr.update(), None

    def confirm_save_results(current_batch_state):
        """确认保存生成结果到数据库"""
        if not current_batch_state or "batch" not in current_batch_state:
            gr.Warning("没有可保存的生成结果！")
            return "没有可保存的生成结果"

        try:
            batch = current_batch_state["batch"]
            dataset_name = current_batch_state["dataset_name"]

            # 保存到数据库
            saved_count = llm_service.save_generation_results(batch, dataset_name)

            success_msg = f"✅ 成功保存 {saved_count} 条语料到数据集 '{dataset_name}'"
            gr.Info(success_msg)
            return success_msg

        except Exception as e:
            error_msg = f"❌ 保存失败: {str(e)}"
            gr.Warning(error_msg)
            return error_msg

    def export_results_as_json(current_batch_state):
        """导出生成结果为JSON文件"""
        if not current_batch_state or "batch" not in current_batch_state:
            return None

        try:
            batch = current_batch_state["batch"]

            # 准备导出数据
            export_data = {
                "batch_info": {
                    "batch_id": batch.batch_id,
                    "dataset_name": batch.dataset_name,
                    "character_name": batch.character_name,
                    "scenario_names": batch.scenario_names,
                    "total_requested": batch.total_requested,
                    "completed": batch.completed,
                    "failed": batch.failed,
                    "start_time": batch.start_time.isoformat(),
                    "end_time": batch.end_time.isoformat() if batch.end_time else None,
                },
                "conversations": batch.results,
            }

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generation_results_{batch.batch_id}_{timestamp}.json"

            # 写入文件
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            gr.Info(f"结果已导出到文件: {filename}")
            return filename

        except Exception as e:
            gr.Warning(f"导出失败: {str(e)}")
            return None

    # --- UI Definition ---
    with gr.Blocks(analytics_enabled=False) as generation_ui:
        selected_config_name_state = gr.State(None)
        current_batch_state = gr.State(None)  # 存储当前生成批次的状态

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 1. 选择数据集")
                target_dataset = gr.Dropdown(label="选择一个数据集进行生成")

                gr.Markdown("### 2. 配置生成参数")
                with gr.Group():
                    num_to_generate = gr.Slider(
                        label="总生成数量", minimum=1, maximum=1000, step=1, value=10
                    )
                    conversation_turns = gr.Slider(
                        label="每条语料对话轮数", minimum=1, maximum=20, step=1, value=3
                    )
                    parallel_requests = gr.Slider(
                        label="并行请求数",
                        minimum=1,
                        maximum=20,
                        step=1,
                        value=1,
                        info="同时发送给LLM的请求数量",
                    )

                gr.Markdown("### 3. 配置API调用")
                with gr.Group():
                    api_config = gr.Dropdown(label="选择API配置")
                    with gr.Row():
                        model_name = gr.Dropdown(label="选择模型", scale=4)
                        get_models_btn = gr.Button(
                            "🔄 获取可用模型", scale=1, min_width=50
                        )
                    temperature = gr.Slider(
                        label="温度", minimum=0.0, maximum=2.0, step=0.1, value=0.7
                    )
                    max_tokens = gr.Slider(
                        label="最大长度", minimum=8096, maximum=128000, step=64, value=2048
                    )
                    top_p = gr.Slider(
                        label="Top P",
                        minimum=0.0,
                        maximum=1.0,
                        step=0.05,
                        value=1.0,
                    )
                    frequency_penalty = gr.Slider(
                        label="频率惩罚",
                        minimum=-2.0,
                        maximum=2.0,
                        step=0.1,
                        value=0.5,
                    )
                    presence_penalty = gr.Slider(
                        label="存在惩罚",
                        minimum=-2.0,
                        maximum=2.0,
                        step=0.1,
                        value=0.5,
                    )
                    with gr.Accordion("管理API配置", open=False):
                        with gr.Tabs():
                            with gr.TabItem("添加/更新API配置"):
                                api_provider = gr.Dropdown(
                                    label="API提供商",
                                    choices=["OpenAI", "Google", "Anthropic"],
                                    value="OpenAI",
                                )
                                api_name = gr.Textbox(
                                    label="配置名称",
                                    info="为这个API配置起一个唯一的名称。",
                                )
                                api_key = gr.Textbox(label="API Key", type="password")
                                base_url = gr.Textbox(
                                    label="Base URL (可选)", visible=True
                                )
                                with gr.Row():
                                    save_api_btn = gr.Button("💾 保存并测试")

                            with gr.TabItem("已存配置列表"):
                                api_config_list = gr.Dataframe(
                                    headers=[
                                        "配置名称",
                                        "API类型",
                                        "Base URL",
                                        "创建时间",
                                    ],
                                    datatype=["str", "str", "str", "str"],
                                    row_count=5,
                                    label="已保存的API配置列表",
                                    interactive=True,
                                )
                                with gr.Row():
                                    refresh_configs_btn = gr.Button("🔄 刷新列表")
                                    delete_config_btn = gr.Button(
                                        "🗑️ 删除选中配置", variant="stop"
                                    )

            with gr.Column(scale=2):
                gr.Markdown("### 4. 预览与启动")
                with gr.Group():
                    with gr.Tabs():
                        with gr.TabItem("📝 最终提示词预览"):
                            prompt_preview = gr.TextArea(
                                label="生成的提示词将显示在这里",
                                lines=20,
                                interactive=True,
                                placeholder='选择好参数后，点击"生成/刷新提示词"按钮进行预览。',
                            )
                    with gr.Row():
                        generate_prompt_btn = gr.Button("⚙️ 生成/刷新提示词")
                        start_generation_btn = gr.Button(
                            "🚀 开始生成", variant="primary"
                        )

                gr.Markdown("### 5. 结果预览与审核")
                with gr.Group():
                    generation_status = gr.TextArea(
                        label="生成状态",
                        lines=6,
                        placeholder="生成状态信息将在这里显示...",
                        interactive=False,
                    )

                    results_preview = gr.Dataframe(
                        headers=["序号", "场景标签", "对话内容", "轮数"],
                        datatype=["number", "str", "str", "number"],
                        label="生成结果预览 (最多显示前10条)",
                        interactive=False,
                        wrap=True,
                    )

                    with gr.Row():
                        save_results_btn = gr.Button("💾 确认入库", variant="primary")
                        export_json_btn = gr.Button("📄 导出JSON")

        # --- Event Handlers Binding ---
        api_form_outputs = [
            api_name,
            api_key,
            base_url,
            top_p,
            frequency_penalty,
            presence_penalty,
            api_provider,
            base_url,
        ]
        all_sliders = [
            num_to_generate,
            conversation_turns,
            parallel_requests,
            temperature,
            max_tokens,
            top_p,
            frequency_penalty,
            presence_penalty,
        ]

        # On page load, load datasets, configs, and explicitly enable all sliders
        def initial_load():
            datasets_update = load_datasets()
            configs_update, configs_df_update = refresh_all_configs()
            # Return update for each slider to ensure they are interactive
            slider_updates = [gr.update(interactive=True)] * len(all_sliders)
            return datasets_update, configs_update, configs_df_update, *slider_updates

        generation_ui.load(
            initial_load,
            outputs=[target_dataset, api_config, api_config_list, *all_sliders],
        )

        # Main API Config Dropdown Event
        api_config.change(
            load_form_from_config, inputs=api_config, outputs=api_form_outputs
        )

        # --- Events for "添加/更新API配置" Tab ---
        def update_visibility(provider):
            return gr.update(visible=provider in ["OpenAI", "Anthropic"])

        api_provider.change(update_visibility, inputs=api_provider, outputs=base_url)
        save_api_btn.click(
            on_save_api_config,
            inputs=[
                api_name,
                api_provider,
                api_key,
                base_url,
                top_p,
                frequency_penalty,
                presence_penalty,
            ],
            outputs=[api_config, api_config_list],
        )

        get_models_btn.click(on_get_models, inputs=api_config, outputs=model_name)

        # --- Events for "已存配置列表" Tab ---
        refresh_configs_btn.click(
            refresh_all_configs, outputs=[api_config, api_config_list]
        )

        def on_select_config_in_list(df: pd.DataFrame, evt: gr.SelectData):
            if evt.index is None:
                return None
            name = df.iloc[evt.index[0]]["配置名称"]
            return name

        api_config_list.select(
            on_select_config_in_list,
            [api_config_list],
            selected_config_name_state,
            queue=False,
        ).then(load_form_from_config, selected_config_name_state, api_form_outputs)
        delete_config_btn.click(
            on_delete_api_config,
            selected_config_name_state,
            [api_config, api_config_list],
        )

        # Event for the "Generate Preview" button
        generate_prompt_btn.click(
            fn=llm_service.generate_preview_prompt,
            inputs=[target_dataset, conversation_turns, num_to_generate],
            outputs=[prompt_preview],
        )

        # Event for the "Start Generation" button
        start_generation_btn.click(
            fn=start_generation,
            inputs=[
                target_dataset,
                api_config,
                model_name,
                num_to_generate,
                conversation_turns,
                parallel_requests,
                temperature,
                max_tokens,
                top_p,
                frequency_penalty,
                presence_penalty,
            ],
            outputs=[generation_status, results_preview, current_batch_state],
        )

        # Event for the "Save Results" button
        save_results_btn.click(
            fn=confirm_save_results,
            inputs=[current_batch_state],
            outputs=[generation_status],
        )

        # Event for the "Export JSON" button
        export_json_btn.click(
            fn=export_results_as_json,
            inputs=[current_batch_state],
            outputs=None,  # File download handled internally
        )

    return generation_ui
