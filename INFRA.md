# Инфраструктура

## Supabase
- Аккаунт: e***n1@gmail.com (проект перенесён туда, один проект в аккаунте).
- Проект: `stroy-tablica`, ref `vntklcxszqqwbtcergrl`, регион eu-central-1.
- Статус на 2026-10-05: на паузе (INACTIVE). Бот не отвечает, пока проект не возобновлён.
- Также виден через Supabase MCP в организации "MEM Cash's projects" (Vercel-интеграция), где ещё два активных проекта (Roscash, AIMark Platform).

## Edge Functions
`tg-webhook` (бэкап кода: `supabase/functions/tg-webhook/`), `platega-callback`, `subscription-cron`, `landing`, `setup-storage`.

## Секреты функций (задаются в Supabase → Edge Functions → Secrets)
TELEGRAM_BOT_TOKEN, TG_WEBHOOK_SECRET, ANTHROPIC_API_KEY, ANTHROPIC_MODEL, PLATEGA_MERCHANT_ID, PLATEGA_SECRET, PLATEGA_BASE, PLATEGA_METHOD, SUPPORT_CONTACT.
