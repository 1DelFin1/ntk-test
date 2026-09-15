from app.models import Extraction, ExtractedField


REQUIRED = {
    "company": "Укажите компанию, от которой пришла заявка.",
    "origin_station": "Уточните станцию отправления.",
    "destination_station": "Уточните станцию назначения.",
    "cargo": "Уточните груз.",
}


def _ambiguous_question(field: ExtractedField, question: str) -> str:
    evidence = field.evidence or "—"
    options = ", ".join(field.options) if field.options else "—"
    return f"{question} В заявке: {evidence}. Варианты: {options}"


def validate(extraction: Extraction) -> list[str]:
    questions = []

    for field, question in REQUIRED.items():
        f = getattr(extraction, field)

        if f.status == "missing":
            questions.append(question)
        elif f.status == "ambiguous":
            questions.append(_ambiguous_question(f, question))

    # Объём: вагоны или тоннаж
    wagons = extraction.wagons_count
    tonnage = extraction.tonnage

    if wagons.status == "ambiguous":
        questions.append(
            _ambiguous_question(wagons, "Уточните количество вагонов.")
        )
    elif tonnage.status == "ambiguous" and wagons.status == "missing":
        questions.append(_ambiguous_question(tonnage, "Уточните тоннаж."))
    elif (
        wagons.status == "missing"
        and tonnage.status == "missing"
    ):
        questions.append("Уточните объём: количество вагонов или тоннаж.")

    # Период: диапазон дат
    period_from = extraction.period_from
    period_to = extraction.period_to

    if period_from.status == "missing" and period_to.status == "missing":
        questions.append("Уточните период перевозки: даты с ... по ...")
    else:
        if period_from.status == "missing":
            questions.append("Уточните дату начала периода перевозки.")
        elif period_from.status == "ambiguous":
            questions.append(
                _ambiguous_question(period_from, "Уточните дату начала.")
            )
        if period_to.status == "missing":
            questions.append("Уточните дату окончания периода перевозки.")
        elif period_to.status == "ambiguous":
            questions.append(
                _ambiguous_question(period_to, "Уточните дату окончания.")
            )

    # Ставка (если присутствует в заявке, но неоднозначна)
    rate = extraction.rate
    if rate.status == "ambiguous":
        questions.append(
            _ambiguous_question(rate, "Уточните ставку: валюта, за вагон/тонну, с НДС или без.")
        )

    # Погрузка/выгрузка: если упомянуты, но непонятны
    loading = extraction.loading_conditions
    unloading = extraction.unloading_conditions

    if loading.status == "ambiguous":
        questions.append(
            _ambiguous_question(loading, "Уточните условия погрузки.")
        )
    if unloading.status == "ambiguous":
        questions.append(
            _ambiguous_question(unloading, "Уточните условия выгрузки.")
        )

    return questions