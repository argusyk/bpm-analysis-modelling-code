# Електронний додаток до навчального посібника «Основи аналізу та моделювання бізнес-процесів в ІТ»

Файли для практикумів 1–10 додатка Ж посібника. Усе побудовано на наскрізному прикладі ТОВ «АероКарго Сервіс».

| Папка | Файл | Призначення |
|---|---|---|
| models | aerocargo-asis.bpmn | модель «як є» (BPMN 2.0 з діаграмою), відкривається в Camunda Modeler і bpmn.io |
| models | aerocargo-tobe.bpmn | модель «як має бути» з паралельним скринінгом і митним оформленням |
| models | error-deadlock.bpmn | навмисно помилкова модель (глухий кут) для вправ |
| models | make_bpmn.py | генератор моделей (змінюйте й перегенеровуйте) |
| models | check_models.py | перевірка коректності (soundness) моделей через мережі Петрі і метрики складності (розділ 4.11.2) |
| decisions | handling-category.dmn | таблиця рішень DMN «Категорія обробки відправки» |
| decisions | dmn_check.py | навчальний виконавець таблиці рішень з тестами |
| data | generate_log.py | генератор синтетичного журналу подій процесу «як є» |
| data | aerocargo_export_log.csv | журнал на 1000 відправок (роздільник «;», UTF-8) |
| analysis | pm_analysis.py | process mining журналу засобами PM4Py |
| analysis | spc_chart.py | контрольна карта середнього часу обробки (розділ 7.10.2) |
| simulation | screening_sim.py | імітаційна модель черги на скринінг (SimPy), 4 сценарії |
| prozorro | build_log.py | побудова журналу подій з відкритого API Prozorro (потрібен інтернет), розділ 9.1 |
| prozorro | analyze.py | process mining журналу відкритих торгів, результати -> results.json |
| prozorro | prozorro_log.csv, prozorro_tenders.csv | журнал 400 відкритих торгів, використаний у посібнику |
| camunda | README.md, worker.py | практикум розгортання в Camunda 8 (підготовлено за документацією, не запускався) |
| agent | awb_agent.py | агент на основі мовної моделі (Claude API), режим --offline без мережі, розділ 9.4 |
| security | sod_check.py | перевірка розподілу обов'язків (SoD) за журналом подій, розділ 9.5 |
| ocel | build_ocel.py | об'єктно-центричний журнал закупівель (OCEL 2.0), граф OC-DFG і наслідки сплощення (розділ 9.1.5) |
| iso | bpmn_to_procedure.py | генерування чернетки процедури ISO 9001 з BPMN-моделі, розділ 10.2 |
| abc | abc_costing.py | облік витрат за видами діяльності (ABC), розділ 10.3 |
| maturity | assessment.py | самооцінка зрілості процесного управління, розділ 10.4 |

## Встановлення

Потрібен Python 3.10 або новіший.

```
python -m venv .venv
.venv\Scripts\activate          (Windows)   |   source .venv/bin/activate   (Linux, macOS)
pip install -r requirements.txt   # закріплені версії pm4py, simpy, pandas, numpy
pip install anthropic      # лише для реального запуску агента (потрібен ключ ANTHROPIC_API_KEY)
pip install pyzeebe        # лише для практикуму Camunda 8
```

Бібліотека PM4Py поширюється за ліцензією AGPL v3 (безкоштовно для навчання). SimPy: https://simpy.readthedocs.io.

## Порядок роботи

```
python models/make_bpmn.py          # (необов'язково) перегенерувати моделі
python models/check_models.py       # перевірка коректності
python decisions/dmn_check.py       # тести таблиці рішень
python data/generate_log.py 1000    # новий журнал (seed фіксований)
python analysis/pm_analysis.py      # process mining
python analysis/spc_chart.py        # контрольна карта
python simulation/screening_sim.py  # імітація сценаріїв
python prozorro/build_log.py        # (потрібен інтернет) новий журнал з Prozorro
python prozorro/analyze.py          # аналіз журналу відкритих торгів
python agent/awb_agent.py --offline # перевірка циклу агента без мережі
python security/sod_check.py        # перевірка розподілу обов'язків
python ocel/build_ocel.py           # об'єктно-центричний журнал
python iso/bpmn_to_procedure.py models/aerocargo-tobe.bpmn
python abc/abc_costing.py           # розрахунок ABC
python maturity/assessment.py       # самооцінка зрілості
```

Програми перезаписують файли результатів (results.json, CSV, procedure.md), що постачаються з додатком. Щоб порівняти свій запуск з еталонним, збережіть копію папки до експериментів.

У моделі «як має бути» очікування відповіді експедитора показано проміжною подією «Виправлення отримано», а в журналі подій те саме фіксує дія «Отримати виправлення». Під час перевірки відповідності pm_analysis.py враховує лише дії, тому подія з моделі і подія «Вантаж доставлено» з журналу не порівнюються.

Дані журналу синтетичні: їх згенеровано з параметрами, узгодженими з розділом 6 посібника, і вони не описують жодне реальне підприємство.

Дані Prozorro є відкритими даними системи публічних закупівель; результати аналізу залежать від вибірки і часу завантаження. Агент у папці agent використовує модель claude-opus-5 з увімкненими резервними моделями на боці сервера (server-side fallbacks).
