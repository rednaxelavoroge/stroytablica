# Инфраструктура

## Supabase
- Аккаунт: e***n1@gmail.com (проект перенесён туда, один проект в аккаунте).
- Рабочий проект: ref `kyezzruvogdvehnjvtwi` (ap-northeast-1). Схема и функции пересобраны 2026-10-05 из кода (`supabase/migrations`, `supabase/functions`).
- Старый проект `stroy-tablica` (`vntklcxszqqwbtcergrl`, eu-central-1) остался на паузе в организации "MEM Cash's projects"; данных там были только тесты, его можно удалить.
- Webhook Telegram: `https://kyezzruvogdvehnjvtwi.supabase.co/functions/v1/tg-webhook`.
- Оплата Platega отключена (секреты PLATEGA_* не заданы), бот отвечает «оплата недоступна, /support».

## Edge Functions
`tg-webhook` (бэкап кода: `supabase/functions/tg-webhook/`), `platega-callback`, `subscription-cron`, `landing`, `setup-storage`.

## Секреты функций (задаются в Supabase → Edge Functions → Secrets)
TELEGRAM_BOT_TOKEN, TG_WEBHOOK_SECRET, ANTHROPIC_API_KEY, ANTHROPIC_MODEL, PLATEGA_MERCHANT_ID, PLATEGA_SECRET, PLATEGA_BASE, PLATEGA_METHOD, SUPPORT_CONTACT.
