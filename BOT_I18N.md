# Бот: мультиязычность (RU / KA / HY)

Лендинг уже ведёт на deep-link:
- RU: `https://t.me/stroytablica_bot?start=lang_ru`
- KA: `https://t.me/stroytablica_bot?start=lang_ka`
- HY: `https://t.me/stroytablica_bot?start=lang_hy`

Код бота: Supabase edge function `tg-webhook` (проект `vntklcxszqqwbtcergrl`).  
Перед правкой: скачать текущий код через Supabase MCP / dashboard → не переписывать с нуля.

## 1. Миграция

```sql
alter table app.users
  add column if not exists ui_lang text not null default 'ru'
  check (ui_lang in ('ru','ka','hy'));
```

## 2. Определение языка

Порядок приоритета:

1. Deep-link `/start lang_ka|lang_hy|lang_ru` (и короткие `ka|hy|ru`) → сохранить в `users.ui_lang`.
2. Команда `/lang` (кнопки RU / ქარ / Հայ) → обновить `ui_lang`.
3. Если `ui_lang` ещё default и пришёл текст на другом языке — **отвечать на языке сообщения** (system prompt).
4. Telegram `from.language_code`: `ka`→ka, `hy`→hy, иначе `ru` (только при создании пользователя, не перезаписывать).

Реферальный `/start КОД` не трогать: если payload не `lang_*` / `ka|hy|ru` — это referral_code как сейчас.

## 3. Убрать «только по-русски»

Во всех hardcoded-строках (особенно `/start`, help, лимиты, ошибки):

| Было (идея) | Стало |
|---|---|
| «спрашивайте по-русски» | «спрашивайте обычным текстом» / локализованный эквивалент |
| «понимает русский» | «понимает ваш язык» |
| system: «отвечай по-русски» | «Отвечай на том же языке, на котором задан вопрос пользователя. UI-подсказки — на языке ui_lang.» |

## 4. Словарь UI (минимум)

Ключи, которые точно есть в боте (имена ориентировочные — подставить по фактическому коду):

- `start_welcome` — приветствие /start  
- `file_ok` — «✅ N строк, M колонок. Задавайте вопросы!»  
- `ask_question` / примеры  
- `limit_files` / `limit_questions`  
- `tariffs` / `limits`  
- `no_file` — «Сначала пришлите Excel-файл»  
- `error_generic`  
- `support_ok`  
- `compare_need_two` / paywall  
- `lang_set` — «Язык интерфейса: …»

### RU (пример start, без «по-русски»)

```
СтройТаблица — ИИ-аналитик Excel для стройки.

Пришлите таблицу (.xlsx / .xls / .csv / .ods) и задавайте вопросы обычным текстом:
• где сумма не сходится
• есть ли дубли
• сводка по поставщикам

3 файла в месяц бесплатно. /tariffs · /demo · /support
Язык: /lang
```

### KA

```
СтройТаблица — Excel-ცხრილების AI-ანალიტიკოსი მშენებლობისთვის.

გამოგზავნეთ ცხრილი (.xlsx / .xls / .csv / .ods) და დასვით კითხვები ჩვეულებრივი ტექსტით:
• სად არ ემთხვევა ჯამი
• არის თუ არა დუბლიკატები
• შეჯამება მომწოდებლების მიხედვით

3 ფაილი თვეში უფასოდ. /tariffs · /demo · /support
ენა: /lang
```

### HY

```
СтройТаблица — Excel-աղյուսակների AI-վերլուծաբան շինարարության համար.

Ուղարկեք աղյուսակ (.xlsx / .xls / .csv / .ods) և տվեք հարցեր սովորական տեքստով.
• որտեղ գումարը չի համընկնում
• կա՞ն կրկնօրինակներ
• ամփոփում մատակարարների համաձայն

3 ֆայլ ամսում անվճար. /tariffs · /demo · /support
Լեզու. /lang
```

## 5. System prompt для Claude (вопросы по файлу)

Добавить в system (или user context):

```
Respond in the same language as the user's question.
If the question is in Georgian, answer in Georgian.
If in Armenian, answer in Armenian.
If in Russian, answer in Russian.
Keep numbers, row IDs, and column names exactly as in the data.
UI language preference of the user: {ui_lang}.
```

Не писать «always answer in Russian».

## 6. Команды с regex

Сейчас сверка/команды завязаны на русские слова (`сверь`, `сравни`…).  
Добавить синонимы:

- KA: შეადარე, შედარება, შეჯერება  
- HY: համեմատիր, համադրիր, համեմատություն  

Либо: если intent «сверка» не сработал по regex — пусть LLM-роутер / обычный вопрос.

## 7. Критерии приёмки

1. С лендинга `/ka/` кнопка «ბოტის გახსნა» → `/start lang_ka` → welcome на грузинском.  
2. С `/hy/` → welcome на армянском.  
3. Вопрос на грузинском по загруженному файлу → ответ на грузинском.  
4. В welcome и help нет фразы «по-русски» / «только на русском».  
5. Реферальный `/start PARTNERCODE` по-прежнему работает.

## 8. Деплой

После правок: `deploy_edge_function` tg-webhook, ручной тест с трёх аккаунтов (или смена language_code + deep-link).
