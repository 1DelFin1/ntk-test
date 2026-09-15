import os

from dotenv import load_dotenv
from openai import OpenAI

from app.models import Extraction, ExtractedField
from app.prompts import SYSTEM_PROMPT

load_dotenv()

MOCK_HINT = "ООО Ромашка"


def is_mock_mode() -> bool:
    return not (os.getenv("OPENAI_API_KEY") or "").strip()


def extract(text: str) -> Extraction:
    if is_mock_mode():
        return mock_extraction(text)

    model = (os.getenv("OPENAI_MODEL") or "").strip() or "gpt-4o-mini"

    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Текущий год: 2026.\n\nЗаявка:\n{text}"},
        ],
        response_format={"type": "json_object"},
        timeout=120,
    )

    content = response.choices[0].message.content

    if not content or not content.strip():
        raise RuntimeError("LLM вернул пустой ответ.")

    try:
        return Extraction.model_validate_json(content)
    except Exception:
        raise


def mock_extraction(text: str) -> Extraction:
    """Демо-режим без OpenAI API key."""
    lower = text.lower()

    if MOCK_HINT in lower or any(w in lower for w in ("уголь", "угля", "углём", "угли")):
        return Extraction(
            company=ExtractedField(
                value="ООО Ромашка",
                status="present",
                confidence=0.98,
                evidence="ООО Ромашка",
            ),
            origin_station=ExtractedField(
                value="Новокузнецк-Восточный",
                status="present",
                confidence=0.97,
                evidence="со ст. Новокузнецк-Восточный",
            ),
            destination_station=ExtractedField(
                value="Находкинский-Восточный",
                status="present",
                confidence=0.97,
                evidence="до ст. Находкинский-Восточный",
            ),
            cargo=ExtractedField(
                value="уголь",
                status="present",
                confidence=0.95,
                evidence="перевозка угля",
            ),
            wagons_count=ExtractedField(
                value=10,
                status="present",
                confidence=0.99,
                evidence="10 вагонов",
            ),
            tonnage=ExtractedField(status="missing"),
            period_from=ExtractedField(
                status="ambiguous",
                confidence=0.6,
                evidence="15-20 июля",
                options=["2026-07-15", "2027-07-15"],
            ),
            period_to=ExtractedField(
                status="ambiguous",
                confidence=0.6,
                evidence="15-20 июля",
                options=["2026-07-20", "2027-07-20"],
            ),
            loading_conditions=ExtractedField(
                value="навалом",
                status="present",
                confidence=0.9,
                evidence="Погрузка навалом",
            ),
            unloading_conditions=ExtractedField(status="missing"),
            rate=ExtractedField(
                value="1500 RUB / вагон, без НДС",
                status="present",
                confidence=0.95,
                evidence="1500 руб/вагон без НДС",
            ),
            raw_summary=(
                "Заявка на перевозку угля со ст. Новокузнецк-Восточный "
                "до ст. Находкинский-Восточный, 10 вагонов, 15-20 июля, "
                "1500 руб/вагон без НДС."
            ),
        )

    if any(w in lower for w in ("добрый", "тест", "алеан", "кокс", "железо")):
        return Extraction(
            company=ExtractedField(
                value="ООО Альянс-Транс",
                status="present",
                confidence=0.95,
                evidence="ООО Альянс-Транс",
            ),
            origin_station=ExtractedField(
                value="Кемерово",
                status="present",
                confidence=0.93,
                evidence="ст. Кемерово",
            ),
            destination_station=ExtractedField(status="missing"),
            cargo=ExtractedField(
                value="кокс",
                status="present",
                confidence=0.92,
                evidence="перевозка кокса",
            ),
            wagons_count=ExtractedField(status="missing"),
            tonnage=ExtractedField(status="missing"),
            period_from=ExtractedField(status="missing"),
            period_to=ExtractedField(status="missing"),
            loading_conditions=ExtractedField(status="missing"),
            unloading_conditions=ExtractedField(status="missing"),
            rate=ExtractedField(status="missing"),
            raw_summary=(
                "Заявка ООО Альянс-Транс на перевозку кокса со ст. Кемерово. "
                "Станция назначения, объём, период и ставка не указаны."
            ),
        )

    return Extraction(raw_summary=text[:300])