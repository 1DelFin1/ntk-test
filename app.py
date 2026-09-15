import streamlit as st

from app.parsers import extract_text_from_file
from app.extractor import extract, is_mock_mode
from app.validator import validate


st.set_page_config(page_title="AI-разбор заявки", layout="wide")
st.title("AI-обработка входящей заявки")

if is_mock_mode():
    st.info(
        "Работает в **демо-режиме** (без OPENAI_API_KEY). "
        "Результаты — захардкоженные примеры, не реальное извлечение."
    )

uploaded_files = st.file_uploader(
    "Загрузите файлы заявки",
    type=["txt", "md", "eml", "pdf", "docx", "xlsx"],
    accept_multiple_files=True,
)

text = st.text_area("Или вставьте текст заявки", height=200)


if st.button("Разобрать заявку"):
    parts = []
    parse_errors = []

    if text.strip():
        parts.append(text.strip())

    for f in uploaded_files or []:
        try:
            parsed = extract_text_from_file(f.name, f.getvalue())
            if not parsed.strip():
                parse_errors.append(f"{f.name}: файл пуст или не содержит текста")
            else:
                parts.append(f"--- {f.name} ---")
                parts.append(parsed)
        except Exception as e:
            parse_errors.append(f"{f.name}: {e}")

    for err in parse_errors:
        st.warning(f"Ошибка чтения файла: {err}")

    if not parts:
        st.warning("Добавьте текст или файл.")
        st.stop()

    full_text = "\n\n".join(parts)

    with st.spinner("Извлекаю данные..."):
        try:
            extraction = extract(full_text)
        except Exception as e:
            st.error(f"Ошибка извлечения: {e}")
            st.stop()

    questions = validate(extraction)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Исходный текст")
        st.text_area(
            "Исходный текст",
            full_text,
            height=400,
            label_visibility="collapsed",
        )

    with col2:
        st.subheader("Извлечённые поля")

        fields = [
            ("Компания", extraction.company),
            ("Станция отправления", extraction.origin_station),
            ("Станция назначения", extraction.destination_station),
            ("Груз", extraction.cargo),
            ("Вагоны", extraction.wagons_count),
            ("Тоннаж", extraction.tonnage),
            ("Период с", extraction.period_from),
            ("Период по", extraction.period_to),
            ("Погрузка", extraction.loading_conditions),
            ("Выгрузка", extraction.unloading_conditions),
            ("Ставка", extraction.rate),
        ]

        for label, f in fields:
            if f.status == "present":
                st.success(f"{label}: {f.value}")
            elif f.status == "ambiguous":
                opts = ", ".join(f.options) if f.options else "—"
                st.warning(
                    f"{label}: неоднозначно — {f.evidence or '—'} | "
                    f"варианты: {opts}"
                )
            else:
                st.info(f"{label}: не найдено")

    st.subheader("Вопросы пользователю")

    if questions:
        for q in questions:
            st.write("—", q)
    else:
        st.success("Все обязательные данные заполнены. Можно создавать сделку.")

    with st.expander("JSON для создания сделки"):
        st.json(extraction.model_dump())