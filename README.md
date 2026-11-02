# Код до навчального посібника «Основи аналізу та моделювання бізнес-процесів в ІТ»

Супровідний код до навчального посібника Я. Ю. Дорогого «Основи аналізу та моделювання бізнес-процесів в ІТ» (Київ : КАІ, 2026) та його англійської версії «Fundamentals of Business Process Analysis and Modelling in IT». Усі приклади побудовано на наскрізному прикладі вигаданого вантажного терміналу ТОВ «АероКарго Сервіс».

| Папка | Зміст |
|---|---|
| [uk/](uk/) | електронний додаток українською: моделі BPMN і DMN, генератор журналу подій, process mining, контрольна карта, імітація, Prozorro, агент на основі мовної моделі, розподіл обов'язків, OCEL, ISO 9001, облік витрат за видами діяльності (ABC), зрілість BPM |
| [uk/listings/](uk/listings/) | усі лістинги з тексту посібника, за номерами розділів |
| [en/](en/) | the same electronic supplement in English (Appendix G practicums) |
| [en/listings/](en/listings/) | all code listings from the English edition, by chapter |

Опис кожної програми і порядок запуску наведено в `uk/README.md` (англійською – `en/README.md`). Потрібен Python 3.10 або новіший:

```
pip install -r uk/requirements.txt
python uk/data/generate_log.py 1000
python uk/analysis/pm_analysis.py
```

Програми перезаписують файли результатів, що постачаються разом з ними; щоб порівняти свій запуск з еталонним, збережіть копію папки до експериментів. Дані журналу АероКарго синтетичні; дані Prozorro є відкритими даними системи публічних закупівель.

---

# Code for the textbook “Fundamentals of Business Process Analysis and Modelling in IT”

Companion code for the textbook by Ya. Dorohyi (Kyiv : KAI, 2026), Ukrainian and English editions. The `en/` folder contains the English electronic supplement and `en/listings/` all code listings from the book; see `en/README.md` for the description of each program and how to run it.

## Ліцензія / License

Код поширюється за ліцензією MIT (див. [LICENSE](LICENSE)). Дані Prozorro – відкриті дані системи публічних закупівель; бібліотека PM4Py, яку використовують програми, має власну ліцензію AGPL v3.

The code is released under the MIT License (see [LICENSE](LICENSE)). Prozorro data are open public procurement data; the PM4Py library used by the programs has its own AGPL v3 licence.
