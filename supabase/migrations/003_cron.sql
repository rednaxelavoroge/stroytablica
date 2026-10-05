-- Ежедневный запуск subscription-cron (06:00 UTC). <ANON_KEY> — legacy anon key проекта (Settings → API Keys).
select cron.schedule('subscription-cron-daily', '0 6 * * *', $$select net.http_post(
  url := 'https://kyezzruvogdvehnjvtwi.supabase.co/functions/v1/subscription-cron',
  headers := jsonb_build_object('Content-Type','application/json','Authorization','Bearer <ANON_KEY>'),
  body := '{}'::jsonb)$$);
