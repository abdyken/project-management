from __future__ import annotations

from app.assistant.schemas import Language

_TEXTS: dict[str, dict[str, str]] = {
    "fallback": {
        "en": "I could not find this information in the official FAQ. Please contact the admissions office: {contact}",
        "ru": "Я не нашёл этой информации в официальных FAQ. Пожалуйста, обратитесь в приёмную комиссию: {contact}",
        "kk": "Бұл ақпарат ресми FAQ-та табылмады. Қабылдау комиссиясына хабарласыңыз: {contact}",
    },
    "english_only": {
        "en": "{answer}",
        "ru": "Этот ответ опубликован только на английском языке:\n{answer}",
        "kk": "Бұл жауап тек ағылшын тілінде жарияланған:\n{answer}",
    },
    "missing_documents": {
        "en": "The document list for this program is not published yet, please contact the admissions office. {contact}",
        "ru": "Список документов для этой программы ещё не опубликован, обратитесь в приёмную комиссию. {contact}",
        "kk": "Бұл бағдарламаның құжаттар тізімі әлі жарияланбаған, қабылдау комиссиясына хабарласыңыз. {contact}",
    },
    "ask_applicant_type": {
        "en": '{label} has separate document lists for local and international applicants. Ask again with "local" or '
        '"international", for example: "Which documents do I need for {title} ({code}) as an international applicant?"',
        "ru": "У программы {label} разные списки документов для местных и иностранных абитуриентов. Спросите ещё раз, "
        "указав «местный» или «иностранный», например: «Какие документы нужны иностранному абитуриенту на {title} ({code})?»",
        "kk": "{label} бағдарламасында отандық және шетелдік талапкерлерге бөлек құжаттар тізімі бар. «Отандық» немесе "
        "«шетелдік» деп қайта сұраңыз, мысалы: «Шетелдік талапкер ретінде {title} ({code}) бағдарламасына қандай құжаттар қажет?»",
    },
    "documents_header": {
        "en": "Required documents for {label}, {kind} applicant:",
        "ru": "Необходимые документы для программы {label}, {kind} абитуриент (названия и сроки — как опубликованы на английском):",
        "kk": "{label} бағдарламасына қажетті құжаттар, {kind} талапкер (атаулары мен мерзімдері ағылшынша жарияланғандай):",
    },
    "document_line": {
        "en": "- {name} ({format}{translation}{notarisation}, deadline {deadline})",
        "ru": "- {name} ({format}{translation}{notarisation}, срок: {deadline})",
        "kk": "- {name} ({format}{translation}{notarisation}, мерзімі: {deadline})",
    },
    "translation_required": {"en": ", translation required", "ru": ", нужен перевод", "kk": ", аударма қажет"},
    "notarisation_required": {
        "en": ", notarisation required",
        "ru": ", нужна нотариальная заверка",
        "kk": ", нотариат куәландыруы қажет",
    },
    "format.original": {"en": "original", "ru": "оригинал", "kk": "түпнұсқа"},
    "format.copy": {"en": "copy", "ru": "копия", "kk": "көшірме"},
    "kind.local": {"en": "local", "ru": "местный", "kk": "отандық"},
    "kind.international": {"en": "international", "ru": "иностранный", "kk": "шетелдік"},
    "choose_program": {
        "en": 'Your question matches several programs: {labels}. Ask again with the program code, for example: "{example}"',
        "ru": "Под ваш вопрос подходят несколько программ: {labels}. Спросите ещё раз с кодом программы, например: «{example}»",
        "kk": "Сұрағыңызға бірнеше бағдарлама сәйкес келеді: {labels}. Бағдарлама кодымен қайта сұраңыз, мысалы: «{example}»",
    },
    "label": {"en": "{title} ({degree}, {code})", "ru": "{title} ({degree}, {code})", "kk": "{title} ({degree}, {code})"},
    "degree.bachelor": {"en": "bachelor", "ru": "бакалавриат", "kk": "бакалавриат"},
    "degree.master": {"en": "master", "ru": "магистратура", "kk": "магистратура"},
    "degree.phd": {"en": "phd", "ru": "докторантура", "kk": "докторантура"},
    "example.documents": {
        "en": "Which documents do I need for {title} ({program_id}) as a local applicant?",
        "ru": "Какие документы нужны местному абитуриенту на {title} ({program_id})?",
        "kk": "Отандық талапкер ретінде {title} ({program_id}) бағдарламасына қандай құжаттар қажет?",
    },
    "example.fee": {
        "en": "How much is tuition for {title} ({program_id})?",
        "ru": "Сколько стоит обучение на {title} ({program_id})?",
        "kk": "{title} ({program_id}) бағдарламасының оқу ақысы қанша?",
    },
    "example.deadline": {
        "en": "When is the application deadline for {title} ({program_id})?",
        "ru": "Какой срок подачи заявления на {title} ({program_id})?",
        "kk": "{title} ({program_id}) бағдарламасына өтінім беру мерзімі қашан?",
    },
    "example.language": {
        "en": "What is the language of instruction for {title} ({program_id})?",
        "ru": "На каком языке обучение на {title} ({program_id})?",
        "kk": "{title} ({program_id}) бағдарламасы қай тілде оқытылады?",
    },
    "example.faculty": {
        "en": "Which faculty offers {title} ({program_id})?",
        "ru": "Какая школа ведёт программу {title} ({program_id})?",
        "kk": "{title} ({program_id}) бағдарламасын қай мектеп ұсынады?",
    },
    "not_published": {"en": "not published yet", "ru": "пока не опубликовано", "kk": "әлі жарияланбаған"},
    "fees.both": {
        "en": "{kzt} KZT (about USD {usd})",
        "ru": "{kzt} тенге (около {usd} USD)",
        "kk": "{kzt} теңге (шамамен {usd} USD)",
    },
    "fees.kzt": {"en": "{kzt} KZT", "ru": "{kzt} тенге", "kk": "{kzt} теңге"},
    "fees.usd": {"en": "about USD {usd}", "ru": "около {usd} USD", "kk": "шамамен {usd} USD"},
    "fee_answer": {
        "en": "{label} costs {fee} per ECTS credit. The total depends on how many ECTS credits you take per semester, so "
        "confirm the final amount with the Admissions Office. {contact}",
        "ru": "Стоимость программы {label} — {fee} за 1 кредит ECTS. Итоговая сумма зависит от количества кредитов ECTS "
        "в семестре, поэтому уточните её в приёмной комиссии. {contact}",
        "kk": "{label} бағдарламасының құны — 1 ECTS кредиті үшін {fee}. Жалпы сома семестрдегі ECTS кредиттерінің "
        "санына байланысты, сондықтан нақты соманы қабылдау комиссиясынан нақтылаңыз. {contact}",
    },
    "fee_missing": {
        "en": "The catalogue does not publish a tuition fee for {label}. {contact}",
        "ru": "В каталоге не опубликована стоимость обучения для программы {label}. {contact}",
        "kk": "Каталогта {label} бағдарламасының оқу ақысы жарияланбаған. {contact}",
    },
    "deadline_one": {
        "en": "The application deadline for {kind} applicants to {label} is {value}.",
        "ru": "Срок подачи заявления на программу {label} ({kind} абитуриенты): {value}.",
        "kk": "{label} бағдарламасына өтінім беру мерзімі ({kind} талапкерлер): {value}.",
    },
    "deadline_both": {
        "en": "Application deadlines for {label}: local applicants {local}, international applicants {international}.",
        "ru": "Сроки подачи заявлений на программу {label}: местные абитуриенты — {local}, иностранные — {international}.",
        "kk": "{label} бағдарламасына өтінім беру мерзімдері: отандық талапкерлер — {local}, шетелдік — {international}.",
    },
    "kinds.local": {"en": "local", "ru": "местные", "kk": "отандық"},
    "kinds.international": {"en": "international", "ru": "иностранные", "kk": "шетелдік"},
    "language_answer": {
        "en": "{label} is taught in {value}.",
        "ru": "Язык обучения на программе {label}: {value}.",
        "kk": "{label} бағдарламасының оқыту тілі: {value}.",
    },
    "language_missing": {
        "en": "The catalogue does not publish the language of instruction of {label} yet. {contact}",
        "ru": "В каталоге пока не опубликован язык обучения программы {label}. {contact}",
        "kk": "Каталогта {label} бағдарламасының оқыту тілі әлі жарияланбаған. {contact}",
    },
    "faculty_answer": {
        "en": "{label} is offered by the {faculty}.",
        "ru": "Программу {label} ведёт {faculty}.",
        "kk": "{label} бағдарламасын {faculty} ұсынады.",
    },
    "field.fee": {"en": "Tuition", "ru": "Стоимость", "kk": "Оқу ақысы"},
    "field.fee_value": {"en": "{fee} per ECTS credit", "ru": "{fee} за 1 кредит ECTS", "kk": "1 ECTS кредиті үшін {fee}"},
    "field.language": {"en": "Language of instruction", "ru": "Язык обучения", "kk": "Оқыту тілі"},
    "field.faculty": {"en": "Faculty", "ru": "Школа", "kk": "Мектеп"},
    "field.deadline": {
        "en": "Application deadline, {kind} applicants",
        "ru": "Срок подачи, {kind} абитуриенты",
        "kk": "Өтінім мерзімі, {kind} талапкерлер",
    },
    "comparison": {"en": "Comparison of {names}:", "ru": "Сравнение программ {names}:", "kk": "Бағдарламаларды салыстыру: {names}:"},
    "and": {"en": " and ", "ru": " и ", "kk": " және "},
    "too_many": {
        "en": 'Your question matches {count} programs: {labels}. Name up to {max} program codes to compare, for example: '
        '"Compare {first} and {second}"',
        "ru": "Под ваш вопрос подходят программы ({count}): {labels}. Назовите до {max} кодов программ для сравнения, "
        "например: «Сравни {first} и {second}»",
        "kk": "Сұрағыңызға {count} бағдарлама сәйкес келеді: {labels}. Салыстыру үшін ең көбі {max} бағдарлама кодын "
        "жазыңыз, мысалы: «{first} және {second} салыстыр»",
    },
    "listing": {
        "en": "The catalogue lists {count} {description}:",
        "ru": "Программы в каталоге ({description}): {count}",
        "kk": "Каталогтағы бағдарламалар ({description}): {count}",
    },
    "listing_empty": {
        "en": "The catalogue has no {description}.",
        "ru": "В каталоге нет программ ({description}).",
        "kk": "Каталогта бағдарлама жоқ ({description}).",
    },
    "contact": {
        "ru": "Приёмная комиссия SDU, ул. Абылай хана, 1/1, 040900 Каскелен. Тел. +7 727 307 95 65",
        "kk": "SDU қабылдау комиссиясы, Абылай хан к-сі, 1/1, 040900 Қаскелең. Тел. +7 727 307 95 65",
    },
    "language.English": {"en": "English", "ru": "английский", "kk": "ағылшын"},
    "language.Kazakh": {"en": "Kazakh", "ru": "казахский", "kk": "қазақ"},
    "language.Russian": {"en": "Russian", "ru": "русский", "kk": "орыс"},
    "language.Korean": {"en": "Korean", "ru": "корейский", "kk": "корей"},
}


def text(language: Language, key: str, **params: object) -> str:
    variants = _TEXTS[key]
    template = variants.get(language) or variants["en"]
    return template.format(**params) if params else template


def contact(language: Language, english: str) -> str:
    return english if language == "en" else _TEXTS["contact"][language]


def language_names(language: Language, value: str) -> str:
    names = [name.strip() for name in value.split(",")]
    return ", ".join(text(language, f"language.{name}") if f"language.{name}" in _TEXTS else name for name in names)
