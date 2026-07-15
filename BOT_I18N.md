# Бот: мультиязычность (RU / UK / BE / KK / KA / HY / TR)

## Стандартный подход (как у нормальных Telegram-ботов)

**Приоритет определения `ui_lang`:**

1. **Явный выбор** — `/lang` или deep-link `?start=lang_XX` (с лендинга) → сохранить в `app.users.ui_lang`, больше не трогать автоматически.
2. **Telegram `from.language_code`** при **первом** `/start` (создание пользователя):
   - `ru` → ru  
   - `uk` → uk  
   - `be` → be  
   - `kk` → kk  
   - `ka` → ka  
   - `hy` → hy  
   - `tr` → tr  
   - `en` / прочее → **ru** (дефолт продукта; ответы LLM всё равно на языке вопроса)
3. **Язык сообщения** — system prompt Claude: *всегда отвечать на языке текущего вопроса пользователя* (даже если UI на другом).
4. OS/телефон **напрямую не читаем** — у Telegram-бота единственный надёжный сигнал языка клиента это `language_code` профиля TG + текст сообщения. Это и есть «как обычно».

Лендинг deep-links:
- RU (Русский): `https://t.me/stroytablica_bot?start=lang_ru`
- UK (Українська): `https://t.me/stroytablica_bot?start=lang_uk`
- BE (Беларуская): `https://t.me/stroytablica_bot?start=lang_be`
- KK (Қазақша): `https://t.me/stroytablica_bot?start=lang_kk`
- KA (ქართული): `https://t.me/stroytablica_bot?start=lang_ka`
- HY (Հայերեն): `https://t.me/stroytablica_bot?start=lang_hy`
- TR (Türkçe): `https://t.me/stroytablica_bot?start=lang_tr`

## Миграция

```sql
alter table app.users
  add column if not exists ui_lang text not null default 'ru';
-- при необходимости ослабить check:
-- alter table app.users drop constraint if exists users_ui_lang_check;
-- alter table app.users add constraint users_ui_lang_check check (ui_lang in ('ru', 'uk', 'be', 'kk', 'ka', 'hy', 'tr'));
```

## UI-строки

Все hardcoded-сообщения (`/start`, лимиты, ошибки, /tariffs, /support) — словарь `I18N[ui_lang][key]` с fallback на `ru`.

**Бренд в UI** (как на лендинге):
- ru: СтройТаблица
- uk: БудТаблиця
- be: БудаўнТабліца
- kk: ҚұрылысКесте
- ka: მშენცხრილი
- hy: ՇինԱղյուսակ
- tr: İnşaatTablo

Убрать «по-русски» / «только на русском» из всех локалей.

## System prompt (вопросы по файлу)

```
Respond in the same language as the user's current question
(Russian, Ukrainian, Belarusian, Kazakh, Georgian, Armenian, Turkish, etc.).
Keep numbers, row IDs and column names exactly as in the data.
UI language preference: {ui_lang} — use it only for fixed UI templates, not for forcing answer language.
```

## Команды / regex

Русские триггеры сверки + синонимы (uk/be/kk/ka/hy/tr) или роутинг через LLM.

## Критерии

1. Новый user с TG language_code=uk → welcome на украинском (бренд БудТаблиця).
2. `/start lang_kk` с лендинга → казахский UI.
3. Вопрос на грузинском → ответ на грузинском, даже если ui_lang=ru.
4. `/lang` позволяет сменить вручную.
5. Реферальный `/start CODE` не ломается.
