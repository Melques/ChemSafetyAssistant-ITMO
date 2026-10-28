"""UI для демо: вопрос → ответ со ссылками на SDS.

Если агент предложил запись в журнал хранения (PendingAction), UI показывает её и кнопку «Подтвердить».
Только эта кнопка вызывает chemsafety.tools.storage_log.confirm_storage_entry.

Streamlit или Gradio добавьте через `uv add`. Запуск Streamlit: uv run streamlit run src/chemsafety/app.py
"""


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
