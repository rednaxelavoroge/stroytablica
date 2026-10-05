// StroyTablica v30 — P0: Platega payments + subscription lifecycle; prompt caching; fair-use 50/day
// Auth: X-Telegram-Bot-Api-Secret-Token (verify_jwt отключён осознанно)

import * as XLSX from "npm:xlsx@0.18.5";
import postgres from "npm:postgres@3.4.5";

const TG_TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN") ?? "";
const TG_SECRET = Deno.env.get("TG_WEBHOOK_SECRET") ?? "";
const ANTHROPIC_KEY = Deno.env.get("ANTHROPIC_API_KEY") ?? "";
const SUPPORT = Deno.env.get("SUPPORT_CONTACT") ?? "владельцу бота";
const OWNER_ID = 370322339;
const MODELS = (Deno.env.get("ANTHROPIC_MODEL") ?? "claude-sonnet-5,claude-haiku-4-5").split(",").map((s) => s.trim());
const DB_URL = Deno.env.get("SUPABASE_DB_URL") ?? "";

const EXPORT_HARD_CAP = 20000;
const MAX_ITER = 8;
const FAIR_USE_DAILY = 50;

// Platega (приём оплаты). Секреты задаются в Supabase → Edge Functions → Secrets.
const PLATEGA_MERCHANT_ID = Deno.env.get("PLATEGA_MERCHANT_ID") ?? "";
const PLATEGA_SECRET = Deno.env.get("PLATEGA_SECRET") ?? "";
const PLATEGA_BASE = Deno.env.get("PLATEGA_BASE") ?? "https://app.platega.io";
// PaymentMethodInt: 2 = СБП QR (+SberPay), 3 = ЕРИП, 11 = карты, 12 = международная, 13 = крипта
const PLATEGA_METHOD = Number(Deno.env.get("PLATEGA_METHOD") ?? "2");

// Тарифы к оплате — всегда в рублях (Platega принимает RUB), независимо от языка интерфейса.
const PLAN_PRICES_RUB: Record<string, { month: number; year: number }> = {
  start: { month: 990, year: 9900 },
  business: { month: 2990, year: 29900 },
  team: { month: 6900, year: 69000 },
};

function fmtRub(n: number): string {
  return n.toLocaleString("ru-RU");
}

// Демо-видео захостено в репозитории лендинга тремя частями (GitHub web-uploader режет >25МБ,
// а исходный файл ~24МБ был разбит на всякий случай) — при первой отправке склеиваем и кэшируем
// telegram file_id в app.bot_assets, дальше шлём уже по file_id без повторного скачивания.
const DEMO_VIDEO_PARTS = [
  "https://raw.githubusercontent.com/rednaxelavoroge/stroytablica/main/demo_part0",
  "https://raw.githubusercontent.com/rednaxelavoroge/stroytablica/main/demo_part1",
  "https://raw.githubusercontent.com/rednaxelavoroge/stroytablica/main/demo_part2",
];
const DEMO_CAPTION_FALLBACK = "Загрузка файла и вопросы обычным текстом — в реальном времени, без монтажа.";
const PRIVACY_URL = "https://stroytablica.ru/privacy.html";
const TERMS_URL = "https://stroytablica.ru/terms.html";


// ——— i18n ———
const LANGS = ["ru", "uk", "be", "kk", "ka", "hy", "tr"] as const;
type Lang = (typeof LANGS)[number];

const BRAND: Record<Lang, string> = {
  ru: "StroyTablica",
  uk: "StroyTablica",
  be: "StroyTablica",
  kk: "StroyTablica",
  ka: "StroyTablica",
  hy: "StroyTablica",
  tr: "StroyTablica",
};

function isLang(s: string): s is Lang {
  return (LANGS as readonly string[]).includes(s);
}

/** Hardcoded display prices by UI language (cross-rate via USD, 2026-07-15). Not live FX. */
const PRICES: Record<Lang, {
  free: string; start: string; biz: string; team: string;
  yStart: string; yBiz: string; yTeam: string;
  quick: string; full: string; per: string;
}> = {
  ru: {
    free: "0 ₽", start: "990 ₽", biz: "2 990 ₽", team: "6 900 ₽",
    yStart: "9 900 ₽", yBiz: "29 900 ₽", yTeam: "69 000 ₽",
    quick: "15 000 ₽", full: "50 000 ₽", per: "/мес",
  },
  uk: {
    free: "0 ₴", start: "574 ₴", biz: "1 732 ₴", team: "3 998 ₴",
    yStart: "5 736 ₴", yBiz: "17 324 ₴", yTeam: "39 980 ₴",
    quick: "8 691 ₴", full: "28 971 ₴", per: "/міс",
  },
  be: {
    free: "0 Br", start: "37 Br", biz: "111 Br", team: "256 Br",
    yStart: "367 Br", yBiz: "1 107 Br", yTeam: "2 555 Br",
    quick: "556 Br", full: "1 852 Br", per: "/мес",
  },
  kk: {
    free: "0 ₸", start: "5 994 ₸", biz: "18 104 ₸", team: "41 778 ₸",
    yStart: "59 943 ₸", yBiz: "181 043 ₸", yTeam: "417 793 ₸",
    quick: "90 822 ₸", full: "302 740 ₸", per: "/ай",
  },
  ka: {
    free: "0 ₾", start: "34 ₾", biz: "102 ₾", team: "234 ₾",
    yStart: "336 ₾", yBiz: "1 016 ₾", yTeam: "2 343 ₾",
    quick: "509 ₾", full: "1 698 ₾", per: "/თვ",
  },
  hy: {
    free: "0 ֏", start: "4 686 ֏", biz: "14 154 ֏", team: "32 663 ֏",
    yStart: "46 865 ֏", yBiz: "141 543 ֏", yTeam: "326 640 ֏",
    quick: "71 007 ֏", full: "236 691 ֏", per: "/ամիս",
  },
  tr: {
    free: "0 ₺", start: "601 ₺", biz: "1 815 ₺", team: "4 188 ₺",
    yStart: "6 008 ₺", yBiz: "18 147 ₺", yTeam: "41 877 ₺",
    quick: "9 104 ₺", full: "30 346 ₺", per: "/ay",
  },
};

function prices(lang: string) {
  return PRICES[isLang(lang) ? lang : "ru"];
}


function mapTgLang(code?: string | null): Lang {
  if (!code) return "ru";
  const c = code.toLowerCase().split("-")[0];
  return isLang(c) ? c : "ru";
}

function parseStartArg(arg: string): { lang?: Lang; referral?: string | null } {
  const a = (arg ?? "").trim();
  if (!a) return {};
  const m = a.match(/^(?:lang_)?(ru|uk|be|kk|ka|hy|tr)$/i);
  if (m) return { lang: m[1].toLowerCase() as Lang };
  if (/^[A-Za-z0-9_-]{1,32}$/.test(a)) return { referral: a };
  return {};
}

type I18nDict = Record<string, Partial<Record<Lang, string>> & { ru: string }>;

const I18N: I18nDict = {
  demo_caption: {
    ru: "Загрузка файла и вопросы обычным текстом — в реальном времени, без монтажа.",
    uk: "Завантаження файлу та запитання звичайним текстом — у реальному часі, без монтажу.",
    be: "Загрузка файла і пытанні звычайным тэкстам — у рэальным часе, без мантажу.",
    kk: "Файл жүктеу және қарапайым мәтінмен сұрақтар — нақты уақытта, монтажсыз.",
    ka: "ფაილის ატვირთვა და კითხვები ჩვეულებრივი ტექსტით — რეალურ დროში, მონტაჟის გარეშე.",
    hy: "Ֆայլի վերբեռնում և հարցեր սովորական տեքստով — իրական ժամանակում, առանց մոնտաժի։",
    tr: "Dosya yükleme ve düz metin sorular — gerçek zamanlı, montaj yok.",
  },
  start: {
    ru: `Привет! Я — {brand}, аналитик ваших Excel-файлов.

Как это работает:
1. Пришлите файл .xlsx / .csv (учёт материалов, план-факт, прайс, ведомость)
2. Задавайте вопросы обычным текстом

Примеры:
• «Сколько потрачено на арматуру в марте?»
• «Найди строки, где сумма не сходится с кол-во × цена»
• «Сводка по поставщикам»

Пришлите два файла и напишите «сверь файлы» — сопоставлю позиции (тариф «Бизнес»/«Команда»).

Данные не передаются в нейросеть целиком — расчёты выполняет база данных.

/files · /limits · /tariffs · /demo · /lang · /support`,
    uk: `Привіт! Я — {brand}, аналітик ваших Excel-файлів.

Як це працює:
1. Надішліть файл .xlsx / .csv
2. Ставте запитання звичайним текстом

Приклади:
• «Скільки витрачено на арматуру в березні?»
• «Знайди рядки, де сума не збігається»
• «Зведення по постачальниках»

/files · /limits · /tariffs · /demo · /lang · /support`,
    be: `Прывітанне! Я — {brand}, аналітык вашых Excel-файлаў.

Як гэта працуе:
1. Дашліце файл .xlsx / .csv
2. Задавайце пытанні звычайным тэкстам

/files · /limits · /tariffs · /demo · /lang · /support`,
    kk: `Сәлем! Мен — {brand}, Excel файлдарыңыздың талдаушысы.

Қалай жұмыс істейді:
1. .xlsx / .csv файл жіберіңіз
2. Қарапайым мәтінмен сұрақ қойыңыз

/files · /limits · /tariffs · /demo · /lang · /support`,
    ka: `გამარჯობა! მე ვარ {brand} — თქვენი Excel-ფაილების ანალიტიკოსი.

როგორ მუშაობს:
1. გამოგზავნეთ .xlsx / .csv
2. დასვით კითხვები ჩვეულებრივი ტექსტით

/files · /limits · /tariffs · /demo · /lang · /support`,
    hy: `Բարև։ Ես {brand}-ն եմ՝ ձեր Excel-ֆայլերի վերլուծաբանը։

Ինչպես է աշխատում.
1. Ուղարկեք .xlsx / .csv
2. Տվեք հարցեր սովորական տեքստով

/files · /limits · /tariffs · /demo · /lang · /support`,
    tr: `Merhaba! Ben {brand} — Excel dosyalarınızın analisti.

Nasıl çalışır:
1. .xlsx / .csv dosyası gönderin
2. Soruları düz metinle sorun

/files · /limits · /tariffs · /demo · /lang · /support`,
  },
  demo_prompt: {
    ru: "Хотите за 2 минуты увидеть, как это работает на реальном файле?",
    uk: "Хочете за 2 хвилини побачити, як це працює на реальному файлі?",
    be: "Хочаце за 2 хвіліны ўбачыць, як гэта працуе на рэальным файле?",
    kk: "2 минутта нақты файлда қалай жұмыс істейтінін көргіңіз келе ме?",
    ka: "გსურთ 2 წუთში ნახოთ, როგორ მუშაობს რეალურ ფაილზე?",
    hy: "Ուզո՞ւմ եք 2 րոպեում տեսնել, թե ինչպես է աշխատում իրական ֆայլի վրա։",
    tr: "2 dakikada gerçek bir dosyada nasıl çalıştığını görmek ister misiniz?",
  },
  demo_btn: {
    ru: "🎥 Смотреть демо (2 мин)",
    uk: "🎥 Дивитися демо (2 хв)",
    be: "🎥 Глядзець дэма (2 хв)",
    kk: "🎥 Демоны көру (2 мин)",
    ka: "🎥 დემოს ნახვა (2 წთ)",
    hy: "🎥 Դիտել դեմո (2 ր)",
    tr: "🎥 Demoyu izle (2 dk)",
  },
  no_file: {
    ru: "Сначала пришлите файл с таблицей (.xlsx / .csv) — затем задавайте вопросы.",
    uk: "Спочатку надішліть файл таблиці (.xlsx / .csv) — потім ставте запитання.",
    be: "Спачатку дашліце файл табліцы (.xlsx / .csv) — затым задавайце пытанні.",
    kk: "Алдымен кесте файлын жіберіңіз (.xlsx / .csv) — содан кейін сұрақ қойыңыз.",
    ka: "ჯერ გამოგზავნეთ ცხრილის ფაილი (.xlsx / .csv) — შემდეგ დასვით კითხვები.",
    hy: "Նախ ուղարկեք աղյուսակի ֆայլ (.xlsx / .csv) — ապա տվեք հարցեր։",
    tr: "Önce tablo dosyası gönderin (.xlsx / .csv) — sonra soru sorun.",
  },
  bad_format: {
    ru: "Пришлите таблицу файлом: .xlsx, .xls, .csv или .ods",
    uk: "Надішліть таблицю файлом: .xlsx, .xls, .csv або .ods",
    be: "Дашліце табліцу файлам: .xlsx, .xls, .csv або .ods",
    kk: "Кестені файлмен жіберіңіз: .xlsx, .xls, .csv немесе .ods",
    ka: "გამოგზავნეთ ცხრილი ფაილად: .xlsx, .xls, .csv ან .ods",
    hy: "Ուղարկեք աղյուսակը ֆայլով. .xlsx, .xls, .csv կամ .ods",
    tr: "Tabloyu dosya olarak gönderin: .xlsx, .xls, .csv veya .ods",
  },
  file_too_big: {
    ru: "Файл больше 20 МБ — Telegram не даёт ботам скачивать такие. Удалите лишние листы или разбейте файл.",
    uk: "Файл більший за 20 МБ — Telegram не дає ботам завантажувати такі. Видаліть зайві аркуші або розбийте файл.",
    be: "Файл большы за 20 МБ — Telegram не дае ботам спампоўваць такія.",
    kk: "Файл 20 МБ-тан үлкен — Telegram мұндай файлды жүктеуге рұқсат етпейді.",
    ka: "ფაილი 20 მბ-ზე დიდია — Telegram ასეთს ბოტებს არ აძლევს ჩამოტვირთვას.",
    hy: "Ֆայլը 20 ՄԲ-ից մեծ է — Telegram-ը բոտերին չի թույլատրում ներբեռնել։",
    tr: "Dosya 20 MB’dan büyük — Telegram botların indirmesine izin vermiyor.",
  },
  photo: {
    ru: "Пришлите файл документом (.xlsx/.csv), не фотографией — с фото данные прочитать не смогу.",
    uk: "Надішліть файл документом (.xlsx/.csv), не фотографією.",
    be: "Дашліце файл дакументам (.xlsx/.csv), не фотаздымкам.",
    kk: "Файлды құжат ретінде жіберіңіз (.xlsx/.csv), сурет емес.",
    ka: "გამოგზავნეთ ფაილი დოკუმენტად (.xlsx/.csv), არა ფოტოდ.",
    hy: "Ուղարկեք ֆայլը որպես փաստաթուղթ (.xlsx/.csv), ոչ լուսանկար։",
    tr: "Dosyayı belge olarak gönderin (.xlsx/.csv), fotoğraf değil.",
  },
  tech_error: {
    ru: "Техническая ошибка. Попробуйте ещё раз.",
    uk: "Технічна помилка. Спробуйте ще раз.",
    be: "Тэхнічная памылка. Паспрабуйце яшчэ раз.",
    kk: "Техникалық қате. Қайта көріңіз.",
    ka: "ტექნიკური შეცდომა. სცადეთ კიდევ.",
    hy: "Տեխնիկական սխալ։ Կրկին փորձեք։",
    tr: "Teknik hata. Tekrar deneyin.",
  },
  unknown_cmd: {
    ru: "Не знаю такую команду. /start — как пользоваться. /lang — язык.",
    uk: "Не знаю таку команду. /start — як користуватися. /lang — мова.",
    be: "Не ведаю такую каманду. /start — як карыстацца. /lang — мова.",
    kk: "Мұндай команда жоқ. /start — қалай қолдану. /lang — тіл.",
    ka: "ასეთი ბრძანება არ ვიცი. /start — როგორ გამოვიყენოთ. /lang — ენა.",
    hy: "Այդ հրամանը չգիտեմ։ /start — ինչպես օգտվել։ /lang — լեզու։",
    tr: "Böyle bir komut yok. /start — nasıl kullanılır. /lang — dil.",
  },
  support_sent: {
    ru: "Сообщение передано в поддержку, вам ответят в личку.",
    uk: "Повідомлення передано в підтримку, вам відповідять у особисті.",
    be: "Паведамленне перададзена ў падтрымку.",
    kk: "Хабарлама қолдауға жіберілді.",
    ka: "შეტყობინება მხარდაჭერას გადაეგზავნა.",
    hy: "Հաղորդագրությունը փոխանցվել է աջակցությանը։",
    tr: "Mesaj desteğe iletildi, size özelden cevap verecekler.",
  },
  support_ask: {
    ru: "Опишите ваш вопрос следующим сообщением — я перешлю его в поддержку.",
    uk: "Опишіть ваше питання наступним повідомленням — я перешлю його в підтримку.",
    be: "Апішыце ваша пытанне наступным паведамленнем.",
    kk: "Келесі хабарламада сұрағыңызды жазыңыз.",
    ka: "შემდეგ შეტყობინებაში აღწერეთ კითხვა.",
    hy: "Հաջորդ հաղորդագրությամբ նկարագրեք հարցը։",
    tr: "Sonraki mesajda sorunuzu yazın — desteğe ileteceğim.",
  },
  lang_choose: {
    ru: "Выберите язык интерфейса:",
    uk: "Оберіть мову інтерфейсу:",
    be: "Абярыце мову інтэрфейсу:",
    kk: "Интерфейс тілін таңдаңыз:",
    ka: "აირჩიეთ ინტერფეისის ენა:",
    hy: "Ընտրեք միջերեսի լեզուն.",
    tr: "Arayüz dilini seçin:",
  },
  // Fixed multi-language prompt on /start (before user picks a language)
  lang_pick_start: {
    ru: "🌐 Choose language / Выберите язык\n\nSelect your language to continue:",
    uk: "🌐 Choose language / Выберите язык\n\nSelect your language to continue:",
    be: "🌐 Choose language / Выберите язык\n\nSelect your language to continue:",
    kk: "🌐 Choose language / Выберите язык\n\nSelect your language to continue:",
    ka: "🌐 Choose language / Выберите язык\n\nSelect your language to continue:",
    hy: "🌐 Choose language / Выберите язык\n\nSelect your language to continue:",
    tr: "🌐 Choose language / Выберите язык\n\nSelect your language to continue:",
  },
  lang_set: {
    ru: "✅ Язык: русский. Бренд: {brand}\n\n/start — заново",
    uk: "✅ Мова: українська. Бренд: {brand}\n\n/start — знову",
    be: "✅ Мова: беларуская. Брэнд: {brand}\n\n/start — зноў",
    kk: "✅ Тіл: қазақша. Бренд: {brand}\n\n/start — қайта",
    ka: "✅ ენა: ქართული. ბრენდი: {brand}\n\n/start — თავიდან",
    hy: "✅ Լեզու. հայերեն։ Բրենդ. {brand}\n\n/start — նորից",
    tr: "✅ Dil: Türkçe. Marka: {brand}\n\n/start — yeniden",
  },
  lang_btn: {
    ru: "🌐 Язык",
    uk: "🌐 Мова",
    be: "🌐 Мова",
    kk: "🌐 Тіл",
    ka: "🌐 ენა",
    hy: "🌐 Լեզու",
    tr: "🌐 Dil",
  },
  file_ok: {
    ru: "✅ «{name}»{sheet}: {rows}.\n\nКолонки:\n{cols}\n\nЗадавайте вопросы обычным текстом. Например:\n• «Сколько всего по сумме?»\n• «Найди строки, где сумма не сходится»\n• «Сводка по поставщикам»\n\n/files — список файлов.",
    uk: "✅ «{name}»{sheet}: {rows}.\n\nКолонки:\n{cols}\n\nСтавте запитання звичайним текстом.\n\n/files — список файлів.",
    be: "✅ «{name}»{sheet}: {rows}.\n\nКалонкі:\n{cols}\n\nЗадавайце пытанні звычайным тэкстам.\n\n/files",
    kk: "✅ «{name}»{sheet}: {rows}.\n\nБағандар:\n{cols}\n\nҚарапайым мәтінмен сұраңыз.\n\n/files",
    ka: "✅ «{name}»{sheet}: {rows}.\n\nსვეტები:\n{cols}\n\nდასვით კითხვები ჩვეულებრივი ტექსტით.\n\n/files",
    hy: "✅ «{name}»{sheet}: {rows}.\n\nՍյունակներ.\n{cols}\n\nՏվեք հարցեր սովորական տեքստով։\n\n/files",
    tr: "✅ «{name}»{sheet}: {rows}.\n\nSütunlar:\n{cols}\n\nDüz metinle soru sorun.\n\n/files",
  },
  limit_files: {
    ru: "Лимит файлов на тарифе «{plan}» исчерпан ({n}/мес).\n\nТариф «Старт» — {start}{per}. /tariffs",
    uk: "Ліміт файлів на тарифі «{plan}» вичерпано ({n}/міс).\n\nТариф «Старт» — {start}{per}. /tariffs",
    be: "Ліміт файлаў на тарыфе «{plan}» вычарпаны ({n}/мес).\n\nТарыф «Старт» — {start}{per}. /tariffs",
    kk: "«{plan}» тарифінде файл лимиті бітті ({n}/ай).\n\n«Старт» — {start}{per}. /tariffs",
    ka: "ტარიფზე «{plan}» ფაილების ლიმიტი ამოწურულია ({n}/თვ).\n\n«სტარტი» — {start}{per}. /tariffs",
    hy: "«{plan}» սակագնով ֆայլերի սահմանը սպառված է ({n}/ամիս)։\n\n«Ստարտ» — {start}{per}. /tariffs",
    tr: "«{plan}» tarifesinde dosya limiti doldu ({n}/ay).\n\n«Start» — {start}{per}. /tariffs",
  },
  limit_questions: {
    ru: "По этому файлу исчерпан лимит вопросов ({n} на тарифе «{plan}»).\n\n/tariffs",
    uk: "По цьому файлу вичерпано ліміт запитань ({n}, тариф «{plan}»).\n\n/tariffs",
    be: "Па гэтым файле вычарпаны ліміт пытанняў ({n}, «{plan}»).\n\n/tariffs",
    kk: "Бұл файлда сұрақ лимиті бітті ({n}, «{plan}»).\n\n/tariffs",
    ka: "ამ ფაილზე კითხვების ლიმიტი ამოწურულია ({n}, «{plan}»).\n\n/tariffs",
    hy: "Այս ֆայլի հարցերի սահմանը սպառված է ({n}, «{plan}»)։\n\n/tariffs",
    tr: "Bu dosyada soru limiti doldu ({n}, «{plan}»).\n\n/tariffs",
  },
  compare_paywall: {
    ru: "Сверка двух файлов — тариф «Бизнес» ({biz}{per}) и «Команда». /tariffs",
    uk: "Звірка двох файлів — тариф «Бізнес» ({biz}{per}) / «Команда». /tariffs",
    be: "Зверка двух файлаў — тарыф «Бізнес» ({biz}{per}) / «Каманда». /tariffs",
    kk: "Екі файлды салыстыру — «Бизнес» ({biz}{per}) / «Команда». /tariffs",
    ka: "ორი ფაილის შეჯერება — «ბიზნესი» ({biz}{per}) / «გუნდი». /tariffs",
    hy: "Երկու ֆայլի համադրում — «Բիզնես» ({biz}{per}) / «Թիմ». /tariffs",
    tr: "İki dosya mutabakatı — «Business» ({biz}{per}) / «Takım». /tariffs",
  },
  compare_need_two: {
    ru: "Для сверки нужно два файла. Пришлите второй и повторите.\n\n/files",
    uk: "Для звірки потрібно два файли. Надішліть другий.\n\n/files",
    be: "Для зверкі патрэбна два файлы.\n\n/files",
    kk: "Салыстыру үшін екі файл керек.\n\n/files",
    ka: "შეჯერებისთვის საჭიროა ორი ფაილი.\n\n/files",
    hy: "Համադրման համար պետք է երկու ֆայլ։\n\n/files",
    tr: "Mutabakat için iki dosya gerekir.\n\n/files",
  },
  empty_sheet: {
    ru: "Лист пустой — проверьте файл.",
    uk: "Аркуш порожній — перевірте файл.",
    be: "Ліст пусты — праверце файл.",
    kk: "Парақ бос — файлды тексеріңіз.",
    ka: "ფურცელი ცარიელია — შეამოწმეთ ფაილი.",
    hy: "Թերթը դատարկ է — ստուգեք ֆայլը։",
    tr: "Sayfa boş — dosyayı kontrol edin.",
  },
  no_data_rows: {
    ru: "Не нашёл строк с данными после шапки — проверьте файл.",
    uk: "Не знайшов рядків з даними після шапки.",
    be: "Не знайшоў радкоў з дадзенымі пасля шапкі.",
    kk: "Тақырыптан кейін дерек жолы табылмады.",
    ka: "სათაურის შემდეგ მონაცემები ვერ ვიპოვე.",
    hy: "Վերնագրից հետո տվյալների տողեր չգտա։",
    tr: "Başlıktan sonra veri satırı bulunamadı.",
  },
  download_fail: {
    ru: "Не удалось скачать файл, попробуйте ещё раз.",
    uk: "Не вдалося завантажити файл, спробуйте ще раз.",
    be: "Не ўдалося спампаваць файл.",
    kk: "Файлды жүктеу мүмкін болмады.",
    ka: "ფაილის ჩამოტვირთვა ვერ მოხერხდა.",
    hy: "Չհաջողվեց ներբեռնել ֆայլը։",
    tr: "Dosya indirilemedi, tekrar deneyin.",
  },
  limits: {
    ru: "Тариф: «{plan}»\nФайлы в этом месяце: {files}\nВопросов на файл: {q}\nМаксимум строк: {rows}",
    uk: "Тариф: «{plan}»\nФайли цього місяця: {files}\nЗапитань на файл: {q}\nМакс. рядків: {rows}",
    be: "Тарыф: «{plan}»\nФайлы ў гэтым месяцы: {files}\nПытанняў на файл: {q}\nМакс. радкоў: {rows}",
    kk: "Тариф: «{plan}»\nОсы айдағы файлдар: {files}\nФайлға сұрақ: {q}\nМакс. жол: {rows}",
    ka: "ტარიფი: «{plan}»\nფაილები ამ თვეში: {files}\nკითხვები ფაილზე: {q}\nმაქს. სტრიქონი: {rows}",
    hy: "Սակագին. «{plan}»\nՖայլեր այս ամիս. {files}\nՀարցեր ֆայլի վրա. {q}\nԱռավ. տող. {rows}",
    tr: "Tarife: «{plan}»\nBu ay dosyalar: {files}\nDosya başı soru: {q}\nMaks. satır: {rows}",
  },
  tariffs: {
    ru: `Тарифы {brand}:

Бесплатный — {free}: 3 файла/мес, 15 вопросов на файл, до 2 000 строк
Старт — {start}{per} ({yStart}/год): 30 файлов, вопросы без лимита
Бизнес — {biz}{per}: без лимита файлов, сверка, экспорт
Команда — {team}{per}: «Бизнес» + 5 сотрудников

Внедрение:
• Быстрый старт — от {quick}: 1 час созвона + правки файлов
• Под ключ — от {full}: настройка, обучение, 1–2 недели

Оплата (СБП): /pay · Вопросы: {support}`,
    uk: `Тарифи {brand}:

Безкоштовний — {free}: 3 файли/міс, 15 запитань
Старт — {start}{per} ({yStart}/рік)
Бізнес — {biz}{per}
Команда — {team}{per}

Впровадження:
• Швидкий старт — від {quick}: 1 год. дзвінка + правки файлів
• Під ключ — від {full}: налаштування, навчання, 1–2 тижні

Оплата: /pay · Питання: {support}`,
    be: `Тарыфы {brand}:

Бясплатны — {free}
Старт — {start}{per}
Бізнес — {biz}{per}
Каманда — {team}{per}

Укараненне: хуткі старт ад {quick}; пад ключ ад {full}

Аплата: /pay · Пытанні: {support}`,
    kk: `Тарифтер {brand}:

Тегін — {free}
Старт — {start}{per}
Бизнес — {biz}{per}
Команда — {team}{per}

Енгізу: жылдам старт {quick}-ден; кілтпен {full}-ден

Төлем: /pay · Сұрақтар: {support}`,
    ka: `ტარიფები {brand}:

უფასო — {free}
სტარტი — {start}{per}
ბიზნესი — {biz}{per}
გუნდი — {team}{per}

დანერგვა: სწრაფი სტარტი {quick}-დან; გასაღებზე {full}-დან

გადახდა: /pay · კითხვები: {support}`,
    hy: `Սակագներ {brand}.

Անվճար — {free}
Ստարտ — {start}{per}
Բիզնես — {biz}{per}
Թիմ — {team}{per}

Ներդրում. արագ մեկնարկ {quick}-ից; բանալիով {full}-ից

Վճարում՝ /pay · Հարցեր՝ {support}`,
    tr: `Tarifeler {brand}:

Ücretsiz — {free}
Start — {start}{per}
Business — {biz}{per}
Takım — {team}{per}

Kurulum:
• Hızlı başlangıç — {quick}'den: 1 saat + dosya düzeltme
• Anahtar teslim — {full}'den: kurulum, eğitim, 1–2 hafta

Ödeme: /pay · Sorular: {support}`,
  },
  no_files_list: {
    ru: "Файлов пока нет — пришлите .xlsx/.csv.",
    uk: "Файлів поки немає — надішліть .xlsx/.csv.",
    be: "Файлаў пакуль няма.",
    kk: "Файлдар әзірге жоқ.",
    ka: "ფაილები ჯერ არ არის.",
    hy: "Ֆայլեր դեռ չկան։",
    tr: "Henüz dosya yok — .xlsx/.csv gönderin.",
  },
  files_list: {
    ru: "Ваши файлы (последние {n}):\n\n{list}\n\nДля сверки: «сверь #12 и #15» (тариф Бизнес/Команда).",
    uk: "Ваші файли (останні {n}):\n\n{list}",
    be: "Вашы файлы (апошнія {n}):\n\n{list}",
    kk: "Файлдарыңыз (соңғы {n}):\n\n{list}",
    ka: "თქვენი ფაილები (ბოლო {n}):\n\n{list}",
    hy: "Ձեր ֆայլերը (վերջին {n}).\n\n{list}",
    tr: "Dosyalarınız (son {n}):\n\n{list}",
  },
  privacy: {
    ru: "Политика конфиденциальности: {url}",
    uk: "Політика конфіденційності: {url}",
    be: "Палітыка канфідэнцыяльнасці: {url}",
    kk: "Құпиялылық саясаты: {url}",
    ka: "კონფიდენციალურობის პოლიტიკა: {url}",
    hy: "Գաղտնիության քաղաքականություն. {url}",
    tr: "Gizlilik politikası: {url}",
  },
  terms: {
    ru: "Пользовательское соглашение: {url}",
    uk: "Угода користувача: {url}",
    be: "Карыстальніцкае пагадненне: {url}",
    kk: "Пайдаланушы келісімі: {url}",
    ka: "მომხმარებლის შეთანხმება: {url}",
    hy: "Օգտագործման պայմաններ. {url}",
    tr: "Kullanım koşulları: {url}",
  },
  plan_free: { ru: "Бесплатный", uk: "Безкоштовний", be: "Бясплатны", kk: "Тегін", ka: "უფასო", hy: "Անվճար", tr: "Ücretsiz" },
  plan_start: { ru: "Старт", uk: "Старт", be: "Старт", kk: "Старт", ka: "სტარტი", hy: "Ստարտ", tr: "Start" },
  plan_business: { ru: "Бизнес", uk: "Бізнес", be: "Бізнес", kk: "Бизнес", ka: "ბიზნესი", hy: "Բիզնես", tr: "Business" },
  plan_team: { ru: "Команда", uk: "Команда", be: "Каманда", kk: "Команда", ka: "გუნდი", hy: "Թիմ", tr: "Takım" },
  row_one: { ru: "строка", uk: "рядок", be: "радок", kk: "жол", ka: "სტრიქონი", hy: "տող", tr: "satır" },
  row_few: { ru: "строки", uk: "рядки", be: "радкі", kk: "жол", ka: "სტრიქონი", hy: "տող", tr: "satır" },
  row_many: { ru: "строк", uk: "рядків", be: "радкоў", kk: "жол", ka: "სტრიქონი", hy: "տող", tr: "satır" },
  col_num: { ru: "число", uk: "число", be: "лік", kk: "сан", ka: "რიცხვი", hy: "թիվ", tr: "sayı" },
  col_date: { ru: "дата", uk: "дата", be: "дата", kk: "күн", ka: "თარიღი", hy: "ամսաթիվ", tr: "tarih" },
  sheet_word: { ru: "лист", uk: "аркуш", be: "ліст", kk: "парақ", ka: "ფურცელი", hy: "թերթ", tr: "sayfa" },
  truncated: { ru: ", обрезано до лимита тарифа ({n})", uk: ", обрізано до ліміту ({n})", be: ", абрэзана да ліміту ({n})", kk: ", тариф лимитіне дейін ({n})", ka: ", ტარიფის ლიმიტამდე ({n})", hy: ", սահմանափակված ({n})", tr: ", tarife limitine kırpıldı ({n})" },
  fair_use: {
    ru: "Дневной лимит справедливого использования исчерпан ({n} вопросов). Завтра лимит обновится. Нужно больше — напишите /support",
    uk: "Денний ліміт добросовісного використання вичерпано ({n} запитань). Завтра ліміт оновиться. Потрібно більше — /support",
    be: "Дзённы ліміт вычарпаны ({n} пытанняў). Заўтра абновіцца. /support",
    kk: "Күндізгі лимит бітті ({n} сұрақ). Ертең жаңарады. /support",
    ka: "დღიური ლიმიტი ამოწურულია ({n} კითხვა). ხვალ განახლდება. /support",
    hy: "Օրական սահմանը սպառված է ({n} հարց)։ Վաղը կթարմանա։ /support",
    tr: "Günlük adil kullanım limiti doldu ({n} soru). Yarın yenilenir. /support",
  },
  pay_pick: {
    ru: "Выберите тариф — пришлю ссылку на оплату (СБП, в рублях):",
    uk: "Оберіть тариф — надішлю посилання на оплату (СБП, у рублях):",
    be: "Абярыце тарыф — дашлю спасылку на аплату (СБП, у рублях):",
    kk: "Тарифті таңдаңыз — төлем сілтемесін жіберемін (СБП, рубльмен):",
    ka: "აირჩიეთ ტარიფი — გამოგიგზავნით გადახდის ბმულს (СБП, რუბლში):",
    hy: "Ընտրեք սակագինը — կուղարկեմ վճարման հղումը (СБП, ռուբլով):",
    tr: "Tarife seçin — ödeme bağlantısı göndereceğim (SBP, ruble):",
  },
  pay_link: {
    ru: "Оплата тарифа «{plan}» — {amount} ₽. Ссылка действует 15 минут:",
    uk: "Оплата тарифу «{plan}» — {amount} ₽. Посилання діє 15 хвилин:",
    be: "Аплата тарыфу «{plan}» — {amount} ₽. Спасылка дзейнічае 15 хвілін:",
    kk: "«{plan}» тарифін төлеу — {amount} ₽. Сілтеме 15 минут жарамды:",
    ka: "ტარიფის «{plan}» გადახდა — {amount} ₽. ბმული მოქმედებს 15 წუთი:",
    hy: "«{plan}» սակագնի վճարում — {amount} ₽. Հղումը գործում է 15 րոպե:",
    tr: "«{plan}» tarifesi ödemesi — {amount} ₽. Bağlantı 15 dakika geçerli:",
  },
  pay_btn: {
    ru: "💳 Оплатить {amount} ₽",
    uk: "💳 Сплатити {amount} ₽",
    be: "💳 Аплаціць {amount} ₽",
    kk: "💳 {amount} ₽ төлеу",
    ka: "💳 გადახდა {amount} ₽",
    hy: "💳 Վճարել {amount} ₽",
    tr: "💳 {amount} ₽ öde",
  },
  pay_unavailable: {
    ru: "Оплата онлайн временно недоступна — напишите /support, подключим вручную.",
    uk: "Онлайн-оплата тимчасово недоступна — напишіть /support.",
    be: "Анлайн-аплата часова недаступная — /support.",
    kk: "Онлайн төлем уақытша қолжетімсіз — /support.",
    ka: "ონლაინ გადახდა დროებით მიუწვდომელია — /support.",
    hy: "Օնլայն վճարումը ժամանակավորապես անհասանելի է — /support:",
    tr: "Online ödeme geçici olarak kullanılamıyor — /support.",
  },
  pay_error: {
    ru: "Не получилось создать ссылку на оплату. Попробуйте ещё раз или напишите /support.",
    uk: "Не вдалося створити посилання на оплату. Спробуйте ще раз або /support.",
    be: "Не ўдалося стварыць спасылку на аплату. Паспрабуйце яшчэ раз або /support.",
    kk: "Төлем сілтемесін жасау мүмкін болмады. Қайта көріңіз немесе /support.",
    ka: "გადახდის ბმულის შექმნა ვერ მოხერხდა. სცადეთ კიდევ ან /support.",
    hy: "Չհաջողվեց ստեղծել վճարման հղումը։ Կրկին փորձեք կամ /support:",
    tr: "Ödeme bağlantısı oluşturulamadı. Tekrar deneyin veya /support.",
  },
  plan_until: {
    ru: "Тариф действует до {date}.",
    uk: "Тариф діє до {date}.",
    be: "Тарыф дзейнічае да {date}.",
    kk: "Тариф {date} дейін жарамды.",
    ka: "ტარიფი მოქმედებს {date}-მდე.",
    hy: "Սակագինը գործում է մինչև {date}:",
    tr: "Tarife {date} tarihine kadar geçerli.",
  },
  plan_expired: {
    ru: "⚠️ Срок тарифа истёк {date} — лимиты как на «Бесплатном». Продлить: /pay",
    uk: "⚠️ Термін тарифу минув {date} — ліміти як на «Безкоштовному». Продовжити: /pay",
    be: "⚠️ Тэрмін тарыфу скончыўся {date}. Падоўжыць: /pay",
    kk: "⚠️ Тариф мерзімі {date} аяқталды. Ұзарту: /pay",
    ka: "⚠️ ტარიფის ვადა ამოიწურა {date}. განახლება: /pay",
    hy: "⚠️ Սակագնի ժամկետը լրացել է {date}։ Երկարաձգել՝ /pay",
    tr: "⚠️ Tarife süresi {date} doldu. Uzatmak için: /pay",
  },
  per_year: { ru: "/год", uk: "/рік", be: "/год", kk: "/жыл", ka: "/წელ", hy: "/տարի", tr: "/yıl" },
};

function t(lang: string, key: string, vars?: Record<string, string | number>): string {
  const L: Lang = isLang(lang) ? lang : "ru";
  const entry = I18N[key];
  let s = entry?.[L] ?? entry?.ru ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) s = s.split(`{${k}}`).join(String(v));
  }
  return s;
}

function planNameL(p: string, lang: string): string {
  const map: Record<string, string> = {
    free: t(lang, "plan_free"),
    start: t(lang, "plan_start"),
    business: t(lang, "plan_business"),
    team: t(lang, "plan_team"),
  };
  return map[p] ?? p;
}

function pluralL(n: number, lang: string): string {
  // simple: number + translated "rows" form
  if (lang === "ru" || lang === "uk" || lang === "be") {
    return `${n} ${plural(n, t(lang, "row_one"), t(lang, "row_few"), t(lang, "row_many"))}`;
  }
  return `${n} ${t(lang, "row_many")}`;
}

/** Эффективный план: если срок оплаченного тарифа истёк — лимиты считаем как free.
 *  Планы без plan_expires_at (выданы вручную владельцем) не деградируют. */
function effectivePlan(u: any): string {
  if (u.plan !== "free" && u.plan_expires_at && new Date(u.plan_expires_at).getTime() < Date.now()) return "free";
  return u.plan;
}

function fmtDate(d: string | Date): string {
  return new Date(d).toLocaleDateString("ru-RU");
}

/** Строка о сроке тарифа для /limits и /tariffs (пустая, если срока нет). */
function planStatusSuffix(u: any, lang: string): string {
  if (!u.plan_expires_at || u.plan === "free") return "";
  const expired = new Date(u.plan_expires_at).getTime() < Date.now();
  return "\n\n" + t(lang, expired ? "plan_expired" : "plan_until", { date: fmtDate(u.plan_expires_at) });
}

function payKeyboard(lang: string) {
  const L: Lang = isLang(lang) ? lang : "ru";
  const perM = PRICES[L].per;
  const perY = t(L, "per_year");
  const btn = (icon: string, plan: string, period: "month" | "year") => ({
    text: `${icon} ${planNameL(plan, L)} — ${fmtRub(PLAN_PRICES_RUB[plan][period])} ₽${period === "month" ? perM : perY}`,
    callback_data: `pay:${plan}:${period}`,
  });
  return {
    inline_keyboard: [
      [btn("⭐", "start", "month"), btn("⭐", "start", "year")],
      [btn("💼", "business", "month"), btn("💼", "business", "year")],
      [btn("👥", "team", "month"), btn("👥", "team", "year")],
    ],
  };
}

/** Fair-use: мягкий дневной лимит вопросов на платных тарифах (free ограничен per-file лимитом). */
async function fairUseExceeded(user: any, chatId: number): Promise<boolean> {
  if (effectivePlan(user) === "free") return false;
  const [{ count }] = await sql`select count(*)::int as count from app.questions
    where user_id = ${user.id} and created_at >= date_trunc('day', now())`;
  if (count < FAIR_USE_DAILY) return false;
  await send(chatId, t(user.ui_lang ?? "ru", "fair_use", { n: FAIR_USE_DAILY }));
  await sql`insert into app.events (user_id, event_type) values (${user.id}, 'limit_daily')`;
  return true;
}

function isCompareIntent(text: string): boolean {
  // Explicit file refs + compare-ish → compare route only if also compare words? Audit: #id alone not enough
  const hasFileRef = /#\d+/.test(text) || /(файл|file|ფაილ|ֆայլ|dosya)/i.test(text);
  if (/(сверь|сверка|сверить|сверьте|сопостав)/i.test(text)) return true;
  if (/(сравни|сравнение)/i.test(text) && hasFileRef) return true;
  if (/(порівня|звір|параўн|салыстыр|შეადარე|შედარებ|შეჯერ|համեմատ|համադր|karşılaştır|kıyasla|compare\b)/i.test(text) && hasFileRef) return true;
  if (/(сверь|сравни).{0,20}#\d+/i.test(text)) return true;
  return false;
}



const sql: any = postgres(DB_URL, { prepare: false, max: 2, idle_timeout: 20 });
const TG = `https://api.telegram.org/bot${TG_TOKEN}`;

async function tg(method: string, payload: Record<string, unknown>): Promise<any> {
  const r = await fetch(`${TG}/${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return await r.json().catch(() => ({}));
}

function chunks(s: string, n = 3900): string[] {
  const out: string[] = [];
  for (let i = 0; i < s.length; i += n) out.push(s.slice(i, i + n));
  return out.length ? out : [""];
}

async function send(chatId: number, text: string) {
  if (!chatId) return;
  for (const part of chunks(text)) {
    const r = await tg("sendMessage", { chat_id: chatId, text: part });
    if (!r.ok) console.error("sendMessage failed", JSON.stringify(r).slice(0, 300));
  }
}
const typing = (chatId: number) => tg("sendChatAction", { chat_id: chatId, action: "typing" });

async function sendDocument(chatId: number, filename: string, bytes: Uint8Array, caption?: string): Promise<any> {
  const form = new FormData();
  form.append("chat_id", String(chatId));
  if (caption) form.append("caption", caption.slice(0, 1024));
  form.append(
    "document",
    new Blob([bytes], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }),
    filename,
  );
  const r = await fetch(`${TG}/sendDocument`, { method: "POST", body: form });
  return await r.json().catch(() => ({}));
}

function rowsToXlsxBuffer(rows: Record<string, unknown>[], sheetName = "Данные"): Uint8Array {
  const ws = XLSX.utils.json_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, sheetName.slice(0, 31));
  return XLSX.write(wb, { type: "array", bookType: "xlsx" }) as Uint8Array;
}

function notifyOwner(actorTgId: number, text: string) {
  if (!OWNER_ID || actorTgId === OWNER_ID) return;
  tg("sendMessage", { chat_id: OWNER_ID, text }).catch(() => {});
}

function userLabel(from: any): string {
  const name = [from.first_name, from.last_name].filter(Boolean).join(" ");
  return from.username ? `@${from.username}${name ? ` (${name})` : ""}` : (name || `id${from.id}`);
}

function plural(n: number, one: string, few: string, many: string): string {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}

function ruToNumber(v: unknown): number | null {
  if (typeof v === "number" && isFinite(v)) return v;
  if (typeof v !== "string") return null;
  const s = v.replace(/[\s ]/g, "").replace("₽", "").replace(/руб\.?$/i, "").replace(",", ".");
  if (!s || !/^-?\d+(\.\d+)?$/.test(s)) return null;
  return parseFloat(s);
}

type ColType = "numeric" | "date" | "text";

function detectType(values: unknown[]): ColType {
  const nonEmpty = values.filter((v) => v !== null && v !== undefined && v !== "");
  if (!nonEmpty.length) return "text";
  const dates = nonEmpty.filter((v) => v instanceof Date).length;
  if (dates / nonEmpty.length > 0.8) return "date";
  const nums = nonEmpty.filter((v) => ruToNumber(v) !== null).length;
  if (nums / nonEmpty.length > 0.8) return "numeric";
  return "text";
}

function pickHeaderRows(rows: unknown[][]): { headers: string[]; dataStart: number } {
  const filled = (r: unknown[]) => (r ?? []).filter((c) => c !== null && c !== undefined && String(c).trim() !== "").length;
  let h = 0;
  while (h < Math.min(rows.length, 10) && filled(rows[h]) === 0) h++;
  const r1 = rows[h] ?? [], r2 = rows[h + 1] ?? [];
  const width = Math.max(r1.length, r2.length);
  const twoRow = filled(r1) < width * 0.6 && filled(r2) > filled(r1);
  let headers: string[] = [];
  for (let i = 0; i < width; i++) {
    const a = String(r1[i] ?? "").trim(), b = String(r2[i] ?? "").trim();
    let name = twoRow ? [a, b].filter(Boolean).join(" / ") : a;
    if (!name) name = `Колонка ${i + 1}`;
    headers.push(name.slice(0, 80));
  }
  if (headers.length > 60) headers = headers.slice(0, 60);
  return { headers, dataStart: h + (twoRow ? 2 : 1) };
}

async function getCachedFileId(name: string): Promise<string | null> {
  try {
    const [row] = await sql`select telegram_file_id from app.bot_assets where name = ${name}`;
    return row?.telegram_file_id ?? null;
  } catch (e) {
    console.error("getCachedFileId error", e);
    return null;
  }
}

async function cacheFileId(name: string, fileId: string) {
  await sql`insert into app.bot_assets (name, telegram_file_id) values (${name}, ${fileId})
    on conflict (name) do update set telegram_file_id = excluded.telegram_file_id, updated_at = now()`;
}

async function sendDemoVideo(chatId: number, lang: string = "ru") {
  const caption = t(lang, "demo_caption");
  const cached = await getCachedFileId("demo_video");
  if (cached) {
    const r = await tg("sendVideo", { chat_id: chatId, video: cached, caption });
    if (r.ok) return;
    console.error("cached sendVideo failed, re-uploading", JSON.stringify(r).slice(0, 300));
  }

  await typing(chatId);
  let bytes: Uint8Array;
  try {
    const buffers: ArrayBuffer[] = [];
    for (const url of DEMO_VIDEO_PARTS) {
      const r = await fetch(url);
      if (!r.ok) throw new Error(`part fetch failed: ${url} (${r.status})`);
      buffers.push(await r.arrayBuffer());
    }
    const total = buffers.reduce((n, b) => n + b.byteLength, 0);
    bytes = new Uint8Array(total);
    let offset = 0;
    for (const b of buffers) { bytes.set(new Uint8Array(b), offset); offset += b.byteLength; }
  } catch (e) {
    console.error("demo video fetch error", e);
    await send(chatId, t(lang, "tech_error"));
    return;
  }

  const form = new FormData();
  form.append("chat_id", String(chatId));
  form.append("caption", caption);
  form.append("video", new Blob([bytes], { type: "video/mp4" }), "demo.mp4");
  const r = await fetch(`${TG}/sendVideo`, { method: "POST", body: form });
  const data = await r.json().catch(() => ({}));
  if (data.ok && data.result?.video?.file_id) {
    await cacheFileId("demo_video", data.result.video.file_id).catch((e: unknown) => console.error("cacheFileId error", e));
  } else {
    console.error("sendVideo failed", JSON.stringify(data).slice(0, 300));
    await send(chatId, "Не получилось отправить видео, попробуйте ещё раз чуть позже.");
  }
}

const PLAN_ICON: Record<string, string> = { free: "🆓", start: "⭐", business: "💼", team: "👥" };
const PLANS = ["free", "start", "business", "team"];

function dbUserLabel(u: { tg_username: string | null; first_name: string | null; tg_user_id: number }): string {
  return u.tg_username ? `@${u.tg_username}` : (u.first_name ?? `id${u.tg_user_id}`);
}

async function sendClientsList(chatId: number, messageId?: number) {
  const users = await sql`select id, tg_user_id, tg_username, first_name, plan from app.users
    order by created_at desc limit 25`;
  const payload: Record<string, unknown> = { chat_id: chatId };
  if (!users.length) {
    payload.text = "Пользователей пока нет.";
  } else {
    payload.text = `Клиенты (последние ${users.length}). Нажмите на клиента — откроется смена тарифа.`;
    payload.reply_markup = {
      inline_keyboard: users.map((u: any) => [{
        text: `${PLAN_ICON[u.plan] ?? "•"} ${dbUserLabel(u)} — ${planName(u.plan)}`,
        callback_data: `cl:${u.id}`,
      }]),
    };
  }
  if (messageId) await tg("editMessageText", { ...payload, message_id: messageId });
  else await tg("sendMessage", payload);
}

async function sendPlanPicker(chatId: number, messageId: number, userId: number) {
  const [u] = await sql`select id, tg_user_id, tg_username, first_name, plan from app.users where id = ${userId}`;
  if (!u) {
    await tg("editMessageText", { chat_id: chatId, message_id: messageId, text: "Пользователь не найден — возможно, список устарел. /clients — обновить." });
    return;
  }
  const keyboard = PLANS.map((p) => [{ text: `${p === u.plan ? "✅ " : ""}${planName(p)}`, callback_data: `sp:${userId}:${p}` }]);
  keyboard.push([{ text: "⬅️ Назад к списку", callback_data: "cl:list" }]);
  await tg("editMessageText", {
    chat_id: chatId,
    message_id: messageId,
    text: `Тариф для ${dbUserLabel(u)} (сейчас: «${planName(u.plan)}»):`,
    reply_markup: { inline_keyboard: keyboard },
  });
}

async function setUserPlan(chatId: number, messageId: number, userId: number, plan: string) {
  if (!PLANS.includes(plan)) return;
  const [u] = await sql`update app.users set plan = ${plan} where id = ${userId}
    returning tg_user_id, tg_username, first_name`;
  if (!u) {
    await tg("editMessageText", { chat_id: chatId, message_id: messageId, text: "Пользователь не найден — возможно, список устарел. /clients — обновить." });
    return;
  }
  await tg("editMessageText", {
    chat_id: chatId,
    message_id: messageId,
    text: `✅ Тариф обновлён: ${dbUserLabel(u)} → «${planName(plan)}»`,
  });
}

async function onCallback(cq: any) {
  try {
    await tg("answerCallbackQuery", { callback_query_id: cq.id });
    const chatId = cq.message?.chat?.id;
    const messageId = cq.message?.message_id;
    if (!chatId) return;

    if (typeof cq.data !== "string") return;

    if (cq.data === "watch_demo") {
      const user = await ensureUser(cq.from);
      await sendDemoVideo(chatId, user.ui_lang ?? "ru");
      return;
    }

    if (cq.data === "langmenu") {
      const user = await ensureUser(cq.from);
      const L = user.ui_lang ?? "ru";
      await tg("sendMessage", {
        chat_id: chatId,
        text: t(L, "lang_choose"),
        reply_markup: langKeyboard("lang"),
      });
      return;
    }

    // Оплата тарифа: pay:<plan>:<month|year> → создаём платёж в Platega, шлём ссылку
    if (cq.data.startsWith("pay:")) {
      const [, planKey, period] = cq.data.split(":");
      if (!PLAN_PRICES_RUB[planKey] || (period !== "month" && period !== "year")) return;
      const user = await ensureUser(cq.from);
      const L = user.ui_lang ?? "ru";
      if (!PLATEGA_MERCHANT_ID || !PLATEGA_SECRET) {
        await send(chatId, t(L, "pay_unavailable"));
        notifyOwner(cq.from.id, `⚠️ ${userLabel(cq.from)} нажал оплату (${planKey}/${period}), но секреты PLATEGA_* не заданы.`);
        return;
      }
      const amount = PLAN_PRICES_RUB[planKey][period as "month" | "year"];
      const [payment] = await sql`insert into app.payments (user_id, plan, period, amount)
        values (${user.id}, ${planKey}, ${period}, ${amount}) returning id`;
      try {
        const resp = await fetch(`${PLATEGA_BASE}/transaction/process`, {
          method: "POST",
          headers: {
            "X-MerchantId": PLATEGA_MERCHANT_ID,
            "X-Secret": PLATEGA_SECRET,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            paymentMethod: PLATEGA_METHOD,
            paymentDetails: { amount, currency: "RUB" },
            description: `СтройТаблица: тариф «${planName(planKey)}», ${period === "year" ? "12 мес" : "1 мес"}`,
            return: "https://t.me/stroytablica_bot",
            failedUrl: "https://t.me/stroytablica_bot",
            payload: payment.id,
            metadata: { userId: String(cq.from.id), userName: cq.from.username ? `@${cq.from.username}` : "" },
          }),
        });
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok || !data.redirect || !data.transactionId) {
          console.error("platega create error", resp.status, JSON.stringify(data).slice(0, 500));
          await sql`update app.payments set status = 'error' where id = ${payment.id}`;
          await send(chatId, t(L, "pay_error"));
          notifyOwner(cq.from.id, `⚠️ Ошибка создания платёжной ссылки (${resp.status}) для ${userLabel(cq.from)}: ${JSON.stringify(data).slice(0, 300)}`);
          return;
        }
        await sql`update app.payments set platega_tx_id = ${data.transactionId} where id = ${payment.id}`;
        await tg("sendMessage", {
          chat_id: chatId,
          text: t(L, "pay_link", { plan: planNameL(planKey, L), amount: fmtRub(amount) }),
          reply_markup: { inline_keyboard: [[{ text: t(L, "pay_btn", { amount: fmtRub(amount) }), url: data.redirect }]] },
        });
        notifyOwner(cq.from.id, `💳 ${userLabel(cq.from)} создал платёж: «${planName(planKey)}» / ${period}, ${amount} ₽ (ожидает оплаты)`);
      } catch (e) {
        console.error("platega error", e);
        await sql`update app.payments set status = 'error' where id = ${payment.id}`.catch(() => {});
        await send(chatId, t(L, "pay_error"));
      }
      return;
    }

    // From /start → language then full welcome
    if (cq.data.startsWith("langstart:")) {
      const langCode = cq.data.slice(10);
      if (!isLang(langCode)) return;
      const user = await ensureUser(cq.from, { forceLang: langCode });
      await setUserLang(user.id, langCode);
      if (messageId) {
        await tg("editMessageText", {
          chat_id: chatId,
          message_id: messageId,
          text: t(langCode, "lang_set", { brand: BRAND[langCode] }),
        }).catch(() => {});
      }
      await sendWelcomeFlow(chatId, user, langCode);
      return;
    }

    // From /lang → only confirm language
    if (cq.data.startsWith("lang:")) {
      const langCode = cq.data.slice(5);
      if (!isLang(langCode)) return;
      const user = await ensureUser(cq.from, { forceLang: langCode });
      await setUserLang(user.id, langCode);
      await tg("editMessageText", {
        chat_id: chatId,
        message_id: messageId,
        text: t(langCode, "lang_set", { brand: BRAND[langCode] }),
      }).catch(() => send(chatId, t(langCode, "lang_set", { brand: BRAND[langCode] })));
      return;
    }

    if (!(cq.data === "cl:list" || cq.data.startsWith("cl:") || cq.data.startsWith("sp:"))) return;
    if (cq.from?.id !== OWNER_ID) return; // управление клиентами — только владелец

    if (cq.data === "cl:list") {
      await sendClientsList(chatId, messageId);
    } else if (cq.data.startsWith("cl:")) {
      const userId = Number(cq.data.slice(3));
      if (messageId && Number.isFinite(userId)) await sendPlanPicker(chatId, messageId, userId);
    } else if (cq.data.startsWith("sp:")) {
      const [, userIdStr, plan] = cq.data.split(":");
      if (messageId && plan) await setUserPlan(chatId, messageId, Number(userIdStr), plan);
    }
  } catch (e) {
    console.error("callback error", e);
  }
}

async function ensureUser(from: any, opts: { referral?: string | null; forceLang?: Lang | null } = {}) {
  const referralCode = opts.referral ?? null;
  const forceLang = opts.forceLang ?? null;
  const insertLang = forceLang ?? mapTgLang(from?.language_code);
  let u: any;
  if (forceLang) {
    [u] = await sql`insert into app.users (tg_user_id, tg_username, first_name, referral_code, ui_lang)
      values (${from.id}, ${from.username ?? null}, ${from.first_name ?? null}, ${referralCode}, ${forceLang})
      on conflict (tg_user_id) do update set tg_username = excluded.tg_username, ui_lang = ${forceLang}
      returning id, plan, plan_expires_at, referral_code, awaiting_support, ui_lang, (xmax = 0) as is_new`;
  } else {
    [u] = await sql`insert into app.users (tg_user_id, tg_username, first_name, referral_code, ui_lang)
      values (${from.id}, ${from.username ?? null}, ${from.first_name ?? null}, ${referralCode}, ${insertLang})
      on conflict (tg_user_id) do update set tg_username = excluded.tg_username
      returning id, plan, plan_expires_at, referral_code, awaiting_support, ui_lang, (xmax = 0) as is_new`;
  }
  if (u.is_new) {
    const refSuffix = referralCode ? ` — пришёл по коду ${referralCode}` : "";
    notifyOwner(from.id, `👤 Новый пользователь: ${userLabel(from)}${refSuffix} [${u.ui_lang ?? "ru"}]`);
  }
  if (!u.ui_lang) u.ui_lang = "ru";
  return u;
}

async function setUserLang(userId: number, lang: Lang) {
  await sql`update app.users set ui_lang = ${lang} where id = ${userId}`;
}

function langKeyboard(prefix: "lang" | "langstart") {
  return {
    inline_keyboard: [
      [
        { text: "🇷🇺 RU", callback_data: `${prefix}:ru` },
        { text: "🇺🇦 UK", callback_data: `${prefix}:uk` },
        { text: "🇧🇾 BE", callback_data: `${prefix}:be` },
      ],
      [
        { text: "🇰🇿 KK", callback_data: `${prefix}:kk` },
        { text: "🇬🇪 KA", callback_data: `${prefix}:ka` },
        { text: "🇦🇲 HY", callback_data: `${prefix}:hy` },
      ],
      [{ text: "🇹🇷 TR", callback_data: `${prefix}:tr` }],
    ],
  };
}

/** Full onboarding after language is known: welcome + demo buttons. */
async function sendWelcomeFlow(chatId: number, user: any, lang: string) {
  const L: Lang = isLang(lang) ? lang : "ru";
  const brand = BRAND[L];
  await send(chatId, t(L, "start", { brand }));

  const promptResp = await tg("sendMessage", {
    chat_id: chatId,
    text: t(L, "demo_prompt"),
    reply_markup: {
      inline_keyboard: [
        [{ text: t(L, "demo_btn"), callback_data: "watch_demo" }],
        [{ text: t(L, "lang_btn"), callback_data: "langmenu" }],
        [{ text: "📄 Privacy", url: PRIVACY_URL }, { text: "📄 Terms", url: TERMS_URL }],
      ],
    },
  });
  if (user?.is_new && promptResp.ok && promptResp.result?.message_id) {
    await tg("pinChatMessage", {
      chat_id: chatId,
      message_id: promptResp.result.message_id,
      disable_notification: true,
    }).catch(() => {});
  }
}

async function planLimits(plan: string) {
  const [l] = await sql`select files_per_month, questions_per_file, max_rows from app.plan_limits where plan = ${plan}`;
  return l ?? { files_per_month: 3, questions_per_file: 15, max_rows: 2000 };
}

function planName(p: string): string {
  return ({ free: "Бесплатный", start: "Старт", business: "Бизнес", team: "Команда" } as Record<string, string>)[p] ?? p;
}

async function onDocument(msg: any) {
  const chatId = msg.chat.id;
  const user = await ensureUser(msg.from);
  const plan = effectivePlan(user);
  const limits = await planLimits(plan);

  if (limits.files_per_month !== null) {
    const [{ count }] = await sql`select count(*)::int as count from app.files
      where user_id = ${user.id} and uploaded_at >= date_trunc('month', now())`;
    if (count >= limits.files_per_month) {
      const lang = user.ui_lang ?? "ru";
      {
        const pr = prices(lang);
        await send(chatId, t(lang, "limit_files", {
          plan: planNameL(plan, lang), n: limits.files_per_month,
          start: pr.start, per: pr.per,
        }));
      }
      await sql`insert into app.events (user_id, event_type) values (${user.id}, 'limit_files')`;
      notifyOwner(msg.from.id, `🔥 ГОРЯЧИЙ ЛИД: ${userLabel(msg.from)} упёрся в лимит файлов (${limits.files_per_month}/мес). Пора предлагать тариф.`);
      return;
    }
  }

  const doc = msg.document;
  const name: string = doc.file_name ?? "file.xlsx";
  if (!/\.(xlsx|xls|csv|ods)$/i.test(name)) {
    await send(chatId, t(user.ui_lang ?? "ru", "bad_format"));
    return;
  }
  if ((doc.file_size ?? 0) > 19_000_000) {
    await send(chatId, t(user.ui_lang ?? "ru", "file_too_big"));
    return;
  }
  await typing(chatId);

  const info = await tg("getFile", { file_id: doc.file_id });
  if (!info.ok) { await send(chatId, t(user.ui_lang ?? "ru", "download_fail")); return; }
  const bin = await (await fetch(`https://api.telegram.org/file/bot${TG_TOKEN}/${info.result.file_path}`)).arrayBuffer();

  const wb = XLSX.read(new Uint8Array(bin), { type: "array", cellDates: true });
  let best = wb.SheetNames[0], bestRows = -1;
  for (const sn of wb.SheetNames) {
    const ref = wb.Sheets[sn]["!ref"];
    const r = ref ? XLSX.utils.decode_range(ref).e.r : 0;
    if (r > bestRows) { bestRows = r; best = sn; }
  }
  const rows: unknown[][] = XLSX.utils.sheet_to_json(wb.Sheets[best], { header: 1, defval: null });
  if (!rows.length) { await send(chatId, t(user.ui_lang ?? "ru", "empty_sheet")); return; }

  const { headers, dataStart } = pickHeaderRows(rows);
  let data = rows.slice(dataStart).filter((r) => (r ?? []).some((c) => c !== null && String(c).trim() !== ""));
  let truncated = false;
  if (data.length > limits.max_rows) { data = data.slice(0, limits.max_rows); truncated = true; }
  if (!data.length) { await send(chatId, t(user.ui_lang ?? "ru", "no_data_rows")); return; }

  const sample = data.slice(0, 500);
  const types: ColType[] = headers.map((_, i) => detectType(sample.map((r) => r[i])));
  const colsMeta = headers.map((h, i) => ({ col: `c${i + 1}`, header: h, type: types[i] }));

  const [file] = await sql`insert into app.files (user_id, tg_file_id, file_name, sheet_name, columns_map, row_count)
    values (${user.id}, ${doc.file_id}, ${name}, ${best}, ${sql.json(colsMeta)}, ${data.length})
    returning id`;
  const tableName = `userdata.f_${file.id}`;
  await sql`update app.files set table_name = ${tableName} where id = ${file.id}`;

  const colDefs = types.map((t, i) => `c${i + 1} ${t === "numeric" ? "double precision" : t === "date" ? "timestamptz" : "text"}`).join(", ");
  await sql.unsafe(`create table ${tableName} (row_num int, ${colDefs})`);

  const colNames = types.map((_, i) => `c${i + 1}`);
  for (let off = 0; off < data.length; off += 200) {
    const batch = data.slice(off, off + 200);
    const params: unknown[] = [];
    const tuples = batch.map((r, j) => {
      const vals = [off + j + 1, ...types.map((t, i) => {
        const v = r[i];
        if (v === null || v === undefined || v === "") return null;
        if (t === "numeric") return ruToNumber(v);
        if (t === "date") return v instanceof Date ? v.toISOString() : null;
        return v instanceof Date ? v.toISOString().slice(0, 10) : String(v);
      })];
      const base = params.length;
      params.push(...vals);
      return `(${vals.map((_, k) => `$${base + k + 1}`).join(",")})`;
    }).join(",");
    await sql.unsafe(`insert into ${tableName} (row_num, ${colNames.join(",")}) values ${tuples}`, params);
  }

  await sql`update app.files set is_active = false where user_id = ${user.id} and id <> ${file.id}`;
  await sql`update app.files set is_active = true where id = ${file.id}`;

  const lang = user.ui_lang ?? "ru";
  const colList = headers.map((h, i) => `${i + 1}. ${h}${types[i] !== "text" ? ` (${types[i] === "numeric" ? t(lang, "col_num") : t(lang, "col_date")})` : ""}`).join("\n");
  const rowsWord = pluralL(data.length, lang);
  notifyOwner(msg.from.id, `📄 ${userLabel(msg.from)} загрузил файл «${name}» — ${rowsWord}`);
  const sheet = wb.SheetNames.length > 1 ? ` (${t(lang, "sheet_word")} «${best}»)` : "";
  const trunc = truncated ? t(lang, "truncated", { n: limits.max_rows }) : "";
  await send(chatId, t(lang, "file_ok", { name, sheet, rows: rowsWord + trunc, cols: colList }));
}

const SQL_FORBIDDEN = /\b(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|vacuum|call|do|execute|listen|notify|set|reset|comment|security|pg_sleep|pg_read|pg_write|lo_import|lo_export)\b/i;
const SCHEMA_BLOCKLIST = /\b(app|auth|storage|extensions|pg_catalog|information_schema|pg_toast|vault|graphql|graphql_public|pgsodium|realtime|supabase_functions|supabase_migrations|net|cron)\s*\./i;

function checkSql(q: string, allowedTables: string[]): { ok: true; query: string } | { ok: false; error: string } {
  const query = (q ?? "").trim().replace(/;+\s*$/, "");
  if (query.includes(";")) return { ok: false, error: "разрешён один запрос без точек с запятой." };
  if (!/^\s*(select|with)\b/i.test(query)) return { ok: false, error: "разрешён только SELECT/WITH." };
  if (SQL_FORBIDDEN.test(query)) return { ok: false, error: "запрос содержит запрещённые операции." };
  if (SCHEMA_BLOCKLIST.test(query)) return { ok: false, error: "доступ к системным схемам запрещён." };
  const refs = query.match(/userdata\.\w+/gi) ?? [];
  if (!refs.length) return { ok: false, error: `запрашивайте данные из: ${allowedTables.join(", ")}.` };
  const allowedSet = new Set(allowedTables.map((t) => t.toLowerCase()));
  if (refs.some((r) => !allowedSet.has(r.toLowerCase()))) {
    return { ok: false, error: `доступны только таблицы: ${allowedTables.join(", ")}.` };
  }
  return { ok: true, query };
}

async function safeRunSql(q: string, allowedTables: string[]): Promise<string> {
  const check = checkSql(q, allowedTables);
  if (!check.ok) return `ОШИБКА: ${check.error}`;
  try {
    const rows = await sql.begin(async (tx: any) => {
      await tx.unsafe("set transaction read only");
      await tx.unsafe("set local statement_timeout = 8000");
      return await tx.unsafe(`select * from (${check.query}) _q limit 200`);
    });
    const out = JSON.stringify(rows);
    return out.length > 12000 ? out.slice(0, 12000) + "…(обрезано)" : out;
  } catch (e) {
    return `ОШИБКА SQL: ${String((e as Error).message).slice(0, 300)}`;
  }
}

async function runExportXlsx(
  q: string,
  allowedTables: string[],
  maxRows: number,
): Promise<{ ok: true; rows: any[]; truncated: boolean } | { ok: false; error: string }> {
  const check = checkSql(q, allowedTables);
  if (!check.ok) return { ok: false, error: check.error };
  try {
    const rows = await sql.begin(async (tx: any) => {
      await tx.unsafe("set transaction read only");
      await tx.unsafe("set local statement_timeout = 15000");
      return await tx.unsafe(`select * from (${check.query}) _q limit ${maxRows + 1}`);
    });
    const truncated = rows.length > maxRows;
    return { ok: true, rows: truncated ? rows.slice(0, maxRows) : rows, truncated };
  } catch (e) {
    return { ok: false, error: String((e as Error).message).slice(0, 300) };
  }
}

async function anthropic(body: Record<string, unknown>): Promise<{ model: string; resp: any }> {
  let lastErr = "";
  for (const model of MODELS) {
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model, ...body }),
    });
    if (r.ok) return { model, resp: await r.json() };
    const err = await r.text();
    lastErr = `${r.status}: ${err.slice(0, 300)}`;
    if (r.status !== 404 && !/model/i.test(err)) throw new Error(lastErr);
  }
  throw new Error(`Все модели недоступны. ${lastErr}`);
}

function buildSystem(fileName: string, tableName: string, columnsMap: any[], samples: any[]): string {
  const cols = columnsMap.map((c: any) => `${c.col} — «${c.header}» (${c.type})`).join("\n");
  return `Ты — аналитик данных строительной компании, работаешь внутри Telegram-бота «StroyTablica».
Пользователь загрузил файл «${fileName}». Данные лежат в PostgreSQL-таблице ${tableName}.
Служебная колонка row_num — номер строки исходного файла.

Колонки:
${cols}

Первые строки данных (JSON):
${JSON.stringify(samples).slice(0, 4000)}

Правила:
1. Отвечай, выполняя SQL через инструмент run_sql. Только SELECT/WITH, только таблица ${tableName}. Инструмент возвращает максимум 200 строк — для больших данных используй агрегаты.
2. Не выдумывай числа: каждое число в ответе должно приходить из результата SQL. Если нужна сумма по нескольким категориям/статусам сразу (например «не оплачено + оплачено частично»), делай это отдельным SQL-запросом (where с in(...) или sum с фильтром) — НЕ складывай числа вручную в тексте ответа: арифметика в уме часто ошибочна на больших числах.
3. Текстовые колонки могут содержать опечатки и разные регистры — используй ilike и trim.
4. Отвечай на том же языке, на котором задан вопрос пользователя (русский, украинский, белорусский, казахский, грузинский, армянский, турецкий и др.). Кратко и по делу. Числа — с разделителями тысяч, деньги — с «₽», где уместно.
5. ФОРМАТ ОТВЕТА — только простой текст. Telegram НЕ отображает markdown: запрещены таблицы из «|», звёздочки «**», решётки «#». Списки оформляй через «•», каждый элемент с новой строки: «• Строка 376: Арматура А500С d16 — в файле 4 550 856 ₽, по расчёту 3 374 728 ₽, расхождение +1 176 128 ₽». Блоки разделяй пустой строкой. Заголовок можно выделить эмодзи (📊, ⚠️, ✅).
6. При указании конкретных строк ссылайся на row_num (номер строки файла).
7. Если вопрос не про данные файла — вежливо скажи, что отвечаешь только по загруженной таблице.
8. Если результат пуст или данных не хватает — скажи прямо и предложи, как переформулировать.
9. Если пользователь просит выгрузить/скачать/экспортировать данные файлом (а не текстом) — используй инструмент export_xlsx вместо текстового ответа. Давай колонкам в SELECT понятные алиасы на языке пользователя (as "Наименование") — они станут заголовками в Excel.`;
}

function buildCompareSystem(older: any, samplesA: any[], newer: any, samplesB: any[]): string {
  const colsA = older.columns_map.map((c: any) => `${c.col} — «${c.header}» (${c.type})`).join("\n");
  const colsB = newer.columns_map.map((c: any) => `${c.col} — «${c.header}» (${c.type})`).join("\n");
  return `Ты — аналитик данных строительной компании, работаешь внутри Telegram-бота «StroyTablica», режим СВЕРКИ ДВУХ ФАЙЛОВ.

Файл А (старее) «${older.file_name}» — таблица ${older.table_name}. Служебная колонка row_num — номер строки исходного файла.
Колонки файла А:
${colsA}
Первые строки файла А (JSON): ${JSON.stringify(samplesA).slice(0, 2500)}

Файл Б (новее) «${newer.file_name}» — таблица ${newer.table_name}.
Колонки файла Б:
${colsB}
Первые строки файла Б (JSON): ${JSON.stringify(samplesB).slice(0, 2500)}

Задача — сопоставить строки между файлами (например, заявка/накладная vs счёт поставщика) и найти расхождения (по сумме, количеству, цене, наличию позиции только в одном файле).

СТРАТЕГИЯ СОПОСТАВЛЕНИЯ СТРОК (ошибка здесь хуже, чем в арифметике — деньги на кону):
1. Сначала проверь, есть ли в обоих файлах колонка-ключ (артикул, код, номер позиции) по названиям колонок и образцам данных. Если да — сопоставляй по точному равенству (trim, нижний регистр).
2. Если ключа нет — сопоставляй по наименованию нечётким сравнением. В базе доступно расширение pg_trgm: функция similarity(lower(trim(a.название)), lower(trim(b.название))) и оператор %.
3. Для каждой строки файла А находи топ-2 кандидата в файле Б по similarity — удобно через row_number() over (partition by ... order by similarity(...) desc).
4. ВАЖНО (проверено эмпирически на реальных данных снабжения): в файлах учёта материалов наименования часто ПОВТОРЯЮТСЯ (одна и та же позиция закупается много раз в разные даты) — поэтому по одному только имени у строки почти всегда будет несколько кандидатов с одинаковой максимальной similarity, и правило «маленький разрыв → неоднозначно» без уточнения пометит НЕОДНОЗНАЧНЫМИ практически все строки, хотя на самом деле однозначное совпадение есть. Прежде чем объявлять неоднозначность, дожимай ранжирование дополнительными полями, которые есть почти всегда: order by similarity(...) desc, abs(цена_за_ед_а - цена_за_ед_б) asc [, abs(количество_а - количество_б) asc] — среди кандидатов с одинаковым именем совпадение с ближайшей ценой за единицу почти всегда верное. Если в данных есть дата/объект — тоже используй как доп. признак.
5. Только если ПОСЛЕ такого дожатия у строки всё ещё остаётся несколько кандидатов-твинов (одинаковое имя И одинаковая цена/кол-во у двух и более позиций Б) — это настоящая НЕОДНОЗНАЧНОСТЬ. НЕ выбирай в этом случае молча. Вынеси такие позиции отдельным списком «❓ не нашёл однозначного соответствия» с указанием 2-3 кандидатов и их similarity — пусть пользователь решает сам.
6. Никогда не подгоняй числа вручную в тексте ответа — расхождения по сумме/количеству/цене всегда должны быть результатом SQL (JOIN + разница), не устного счёта.
7. Позиции, которые есть только в одном из файлов (пары вообще не нашлось), выводи отдельными списками «только в файле А» / «только в файле Б».

Доступные инструменты:
- run_sql — только SELECT/WITH к таблицам ${older.table_name} и ${newer.table_name} (JOIN между ними разрешён), не более 200 строк результата — для показа текстом в чате.
- export_xlsx — то же самое, но результат уходит пользователю файлом .xlsx вместо текста — используй по явной просьбе выгрузить/экспортировать результат сверки.

ФОРМАТ ОТВЕТА — простой текст, без markdown (никаких «|», «**», «#»). Списки через «•», каждая позиция с новой строки, где уместно — с указанием row_num обоих файлов. Блоки разделяй пустой строкой. Заголовки можно выделить эмодзи (📊 сходится, ⚠️ расхождение, ❓ не сопоставлено).

Отвечай на том же языке, на котором задан вопрос пользователя. Кратко и по делу.`;
}

async function runAgentLoop(opts: {
  chatId: number;
  system: string;
  userText: string;
  allowedTables: string[];
  exportMaxRows: number;
}): Promise<{ answer: string; sqlLog: string[]; inTok: number; outTok: number; cacheTok: number; usedModel: string }> {
  const { chatId, system, userText, allowedTables, exportMaxRows } = opts;
  const tools = [
    {
      name: "run_sql",
      description: `Выполняет читающий SQL-запрос (SELECT/WITH) к таблицам ${allowedTables.join(", ")} в PostgreSQL, возвращает строки в JSON (не более 200). Для показа результата текстом в чате.`,
      input_schema: { type: "object", properties: { query: { type: "string", description: "SQL-запрос" } }, required: ["query"] },
    },
    {
      name: "export_xlsx",
      description: `Выполняет SQL-запрос (SELECT/WITH) к таблицам ${allowedTables.join(", ")} и отправляет результат пользователю как файл .xlsx (до ${exportMaxRows} строк) — используй, когда пользователь просит выгрузить/экспортировать/скачать данные файлом, а не текстом. Названия колонок в SELECT указывай через понятные alias на языке пользователя (as "Наименование") — они станут заголовками в Excel.`,
      input_schema: {
        type: "object",
        properties: {
          query: { type: "string", description: "SQL-запрос" },
          filename: { type: "string", description: "Имя файла без расширения, коротко" },
        },
        required: ["query"],
      },
      // Кэш-брейкпоинт на последнем инструменте: tools кэшируются между итерациями и вопросами
      cache_control: { type: "ephemeral" },
    },
  ];

  // system блоком с cache_control: system+tools читаются из кэша (TTL 5 мин) — минус 60–80% input-стоимости
  const systemBlocks = [{ type: "text", text: system, cache_control: { type: "ephemeral" } }];

  const messages: any[] = [{ role: "user", content: userText }];
  let inTok = 0, outTok = 0, cacheTok = 0, usedModel = "", answer = "";
  const sqlLog: string[] = [];

  try {
    for (let i = 0; i < MAX_ITER; i++) {
      const { model, resp } = await anthropic({ system: systemBlocks, messages, tools, max_tokens: 4096 });
      usedModel = model;
      inTok += resp.usage?.input_tokens ?? 0;
      outTok += resp.usage?.output_tokens ?? 0;
      cacheTok += resp.usage?.cache_read_input_tokens ?? 0;
      const toolUses = (resp.content ?? []).filter((b: any) => b.type === "tool_use");
      if (resp.stop_reason === "tool_use" && toolUses.length) {
        await typing(chatId);
        messages.push({ role: "assistant", content: resp.content });

        const toolResults: any[] = [];
        for (const toolUse of toolUses) {
          if (toolUse.name === "export_xlsx") {
            sqlLog.push(`[export] ${toolUse.input.query}`);
            const res = await runExportXlsx(toolUse.input.query, allowedTables, exportMaxRows);
            let toolResultText: string;
            if (!res.ok) {
              toolResultText = `ОШИБКА: ${res.error}`;
            } else if (!res.rows.length) {
              toolResultText = "Запрос вернул 0 строк — файл не отправлен.";
            } else {
              const rawName = String(toolUse.input.filename ?? "").replace(/[^\p{L}\p{N}_\- ]/gu, "").trim().slice(0, 60);
              const filename = `${rawName || "выгрузка"}.xlsx`;
              const buf = rowsToXlsxBuffer(res.rows);
              const sendRes = await sendDocument(
                chatId,
                filename,
                buf,
                res.truncated ? `Показаны первые ${res.rows.length} строк — лимит выгрузки на вашем тарифе.` : undefined,
              );
              toolResultText = sendRes.ok
                ? `Файл «${filename}» отправлен пользователю, ${res.rows.length} строк${res.truncated ? " (обрезано по лимиту тарифа)" : ""}.`
                : `ОШИБКА при отправке файла в Telegram: ${JSON.stringify(sendRes).slice(0, 200)}`;
            }
            toolResults.push({ type: "tool_result", tool_use_id: toolUse.id, content: toolResultText });
          } else {
            sqlLog.push(toolUse.input.query);
            const result = await safeRunSql(toolUse.input.query, allowedTables);
            toolResults.push({ type: "tool_result", tool_use_id: toolUse.id, content: result });
          }
        }
        messages.push({ role: "user", content: toolResults });
      } else if (resp.stop_reason === "max_tokens") {
        answer = "Ответ получился слишком длинным и был обрезан. Попробуйте сузить вопрос (например, укажите конкретные позиции или колонки) — так проще уложиться в лимит.";
        break;
      } else {
        answer = (resp.content ?? []).filter((b: any) => b.type === "text").map((b: any) => b.text).join("\n").trim();
        break;
      }
    }
    if (!answer) answer = "Не удалось построить ответ за разумное число шагов — попробуйте переформулировать вопрос.";
  } catch (e) {
    console.error("agent error", e);
    answer = "Техническая ошибка при обработке вопроса. Попробуйте ещё раз через минуту.";
  }

  answer = answer.replace(/\*\*(.+?)\*\*/g, "$1").replace(/^#{1,4}\s*/gm, "");
  return { answer, sqlLog, inTok, outTok, cacheTok, usedModel };
}

async function onCompare(chatId: number, from: any, user: any, text: string) {
  const plan = effectivePlan(user);
  if (plan !== "business" && plan !== "team") {
    {
      const L = user.ui_lang ?? "ru";
      const pr = prices(L);
      await send(chatId, t(L, "compare_paywall", { biz: pr.biz, per: pr.per }));
    }
    await sql`insert into app.events (user_id, event_type) values (${user.id}, 'compare_upsell')`;
    notifyOwner(from.id, `🔥 ГОРЯЧИЙ ЛИД: ${userLabel(from)} запросил сверку файлов на тарифе «${planName(plan)}». Пора предлагать «Бизнес».`);
    return;
  }

  const explicitIds = [...text.matchAll(/#(\d+)/g)].map((m) => Number(m[1])).slice(0, 2);
  let files: any[];
  if (explicitIds.length === 2) {
    files = await sql`select id, file_name, table_name, columns_map, uploaded_at from app.files
      where user_id = ${user.id} and id in ${sql(explicitIds)}`;
  } else {
    files = await sql`select id, file_name, table_name, columns_map, uploaded_at from app.files
      where user_id = ${user.id} order by uploaded_at desc limit 2`;
  }
  if (files.length < 2) {
    await send(chatId, t(user.ui_lang ?? "ru", "compare_need_two"));
    return;
  }
  files.sort((a: any, b: any) => new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime());
  const [newer, older] = files;

  await typing(chatId);
  const t0 = Date.now();
  const [samplesA, samplesB] = await Promise.all([
    sql.unsafe(`select * from ${older.table_name} order by row_num limit 10`),
    sql.unsafe(`select * from ${newer.table_name} order by row_num limit 10`),
  ]);
  const system = buildCompareSystem(older, samplesA, newer, samplesB);
  const limits = await planLimits(plan);
  const exportMaxRows = Math.min(limits.max_rows, EXPORT_HARD_CAP);

  await send(chatId, `📎 Сверяю: «${older.file_name}» (загружен ${new Date(older.uploaded_at).toLocaleDateString("ru-RU")}, #${older.id}) ↔ «${newer.file_name}» (загружен ${new Date(newer.uploaded_at).toLocaleDateString("ru-RU")}, #${newer.id})`);

  const { answer, sqlLog, inTok, outTok, cacheTok, usedModel } = await runAgentLoop({
    chatId, system, userText: text, allowedTables: [older.table_name, newer.table_name], exportMaxRows,
  });

  await send(chatId, answer);
  await sql`insert into app.questions (user_id, file_id, question, answer, sql_queries, input_tokens, output_tokens, cache_read_tokens, model, latency_ms)
    values (${user.id}, ${newer.id}, ${"[сверка] " + text}, ${answer}, ${sql.json(sqlLog)}, ${inTok}, ${outTok}, ${cacheTok}, ${usedModel}, ${Date.now() - t0})`;
}

async function onText(msg: any) {
  const chatId = msg.chat.id;
  const text: string = (msg.text ?? "").trim();
  if (!text) return;
  if (text.startsWith("/")) { await onCommand(chatId, text, msg.from); return; }

  const user = await ensureUser(msg.from);

  if (user.awaiting_support) {
    await sql`update app.users set awaiting_support = false where id = ${user.id}`;
    tg("sendMessage", { chat_id: OWNER_ID, text: `✉️ Обращение от ${userLabel(msg.from)}:\n${text}` }).catch(() => {});
    await send(chatId, t(user.ui_lang ?? "ru", "support_sent"));
    return;
  }

  if (await fairUseExceeded(user, chatId)) return;

  if (isCompareIntent(text)) {
    await onCompare(chatId, msg.from, user, text);
    return;
  }

  const [file] = await sql`select id, file_name, table_name, columns_map from app.files
    where user_id = ${user.id} and is_active order by uploaded_at desc limit 1`;
  if (!file) { await send(chatId, t(user.ui_lang ?? "ru", "no_file")); return; }

  const plan = effectivePlan(user);
  const limits = await planLimits(plan);
  if (limits.questions_per_file !== null) {
    const [{ count }] = await sql`select count(*)::int as count from app.questions where file_id = ${file.id}`;
    if (count >= limits.questions_per_file) {
      await send(chatId, t(user.ui_lang ?? "ru", "limit_questions", { n: limits.questions_per_file, plan: planNameL(plan, user.ui_lang ?? "ru") }));
      await sql`insert into app.events (user_id, event_type) values (${user.id}, 'limit_questions')`;
      notifyOwner(msg.from.id, `🔥 ГОРЯЧИЙ ЛИД: ${userLabel(msg.from)} упёрся в лимит вопросов по файлу «${file.file_name}». Пора предлагать тариф.`);
      return;
    }
  }

  await typing(chatId);
  const t0 = Date.now();
  const samples = await sql.unsafe(`select * from ${file.table_name} order by row_num limit 15`);
  const system = buildSystem(file.file_name, file.table_name, file.columns_map, samples);
  const exportMaxRows = Math.min(limits.max_rows, EXPORT_HARD_CAP);

  const { answer, sqlLog, inTok, outTok, cacheTok, usedModel } = await runAgentLoop({
    chatId, system, userText: text, allowedTables: [file.table_name], exportMaxRows,
  });

  await send(chatId, answer);
  await sql`insert into app.questions (user_id, file_id, question, answer, sql_queries, input_tokens, output_tokens, cache_read_tokens, model, latency_ms)
    values (${user.id}, ${file.id}, ${text}, ${answer}, ${sql.json(sqlLog)}, ${inTok}, ${outTok}, ${cacheTok}, ${usedModel}, ${Date.now() - t0})`;
}

async function onCommand(chatId: number, cmd: string, from: any) {
  const rawStartArg = cmd.startsWith("/start") ? cmd.slice(6).trim() : "";
  const parsed = parseStartArg(rawStartArg);
  const user = await ensureUser(from, { referral: parsed.referral ?? null, forceLang: parsed.lang ?? null });
  const lang = (user.ui_lang as string) ?? "ru";
  const brand = BRAND[isLang(lang) ? lang : "ru"];

  if (cmd.startsWith("/start")) {
    // Deep-link with language (from landing /ka /uk …) → skip picker
    if (parsed.lang) {
      await sendWelcomeFlow(chatId, user, parsed.lang);
    } else {
      // Always ask language first, then welcome after button
      await tg("sendMessage", {
        chat_id: chatId,
        text: "🌐 Choose language / Выберите язык\n\nSelect your language:",
        reply_markup: langKeyboard("langstart"),
      });
    }
  } else if (cmd.startsWith("/lang")) {
    await tg("sendMessage", {
      chat_id: chatId,
      text: t(lang, "lang_choose"),
      reply_markup: langKeyboard("lang"),
    });
  } else if (cmd.startsWith("/demo")) {
    await sendDemoVideo(chatId, lang);
  } else if (cmd.startsWith("/privacy")) {
    await send(chatId, t(lang, "privacy", { url: PRIVACY_URL }));
  } else if (cmd.startsWith("/terms")) {
    await send(chatId, t(lang, "terms", { url: TERMS_URL }));
  } else if (cmd.startsWith("/limits")) {
    const plan = effectivePlan(user);
    const limits = await planLimits(plan);
    const [{ count: filesUsed }] = await sql`select count(*)::int as count from app.files where user_id = ${user.id} and uploaded_at >= date_trunc('month', now())`;
    const filesStr = limits.files_per_month !== null ? `${filesUsed} / ${limits.files_per_month}` : `${filesUsed}`;
    await send(chatId, t(lang, "limits", {
      plan: planNameL(plan, lang),
      files: filesStr,
      q: limits.questions_per_file ?? "∞",
      rows: limits.max_rows,
    }) + planStatusSuffix(user, lang));
  } else if (cmd.startsWith("/tariffs")) {
    {
      const pr = prices(lang);
      await send(chatId, t(lang, "tariffs", {
        brand, support: SUPPORT,
        free: pr.free, start: pr.start, biz: pr.biz, team: pr.team,
        yStart: pr.yStart, yBiz: pr.yBiz, yTeam: pr.yTeam,
        quick: pr.quick, full: pr.full, per: pr.per,
      }) + planStatusSuffix(user, lang));
    }
    await tg("sendMessage", { chat_id: chatId, text: t(lang, "pay_pick"), reply_markup: payKeyboard(lang) });
  } else if (cmd.startsWith("/pay")) {
    await tg("sendMessage", { chat_id: chatId, text: t(lang, "pay_pick") + planStatusSuffix(user, lang), reply_markup: payKeyboard(lang) });
  } else if (cmd.startsWith("/files")) {
    const files = await sql`select id, file_name, row_count, uploaded_at, is_active from app.files where user_id = ${user.id} order by uploaded_at desc limit 8`;
    if (!files.length) { await send(chatId, t(lang, "no_files_list")); return; }
    const list = files.map((f: any) => `${f.is_active ? "▶️" : "•"} #${f.id} «${f.file_name}» — ${f.row_count}, ${new Date(f.uploaded_at).toLocaleDateString("ru-RU")}`).join("\n");
    await send(chatId, t(lang, "files_list", { n: files.length, list }));
  } else if (cmd.startsWith("/compare")) {
    if (await fairUseExceeded(user, chatId)) return;
    const argText = cmd.slice(8).trim();
    await onCompare(chatId, from, user, argText || "сверь последние два файла, найди расхождения");
  } else if (cmd.startsWith("/support")) {
    const supportText = cmd.slice(8).trim();
    if (supportText) {
      tg("sendMessage", { chat_id: OWNER_ID, text: `✉️ Обращение от ${userLabel(from)}:\n${supportText}` }).catch(() => {});
      await send(chatId, t(lang, "support_sent"));
    } else {
      await sql`update app.users set awaiting_support = true where id = ${user.id}`;
      await send(chatId, t(lang, "support_ask"));
    }
  } else if (cmd.startsWith("/admin")) {
    if (from.id !== OWNER_ID) { await send(chatId, "Команда недоступна."); return; }
    const [{ new_users }] = await sql`select count(*)::int as new_users from app.users where created_at >= now() - interval '30 days'`;
    const [{ total_users }] = await sql`select count(*)::int as total_users from app.users`;
    const paying = await sql`select tg_username, first_name, plan from app.users where plan <> 'free' order by plan, tg_username`;
    const [{ q_count, in_tok, out_tok }] = await sql`select count(*)::int as q_count, coalesce(sum(input_tokens),0)::bigint as in_tok, coalesce(sum(output_tokens),0)::bigint as out_tok from app.questions where created_at >= now() - interval '30 days'`;
    const hot = await sql`select coalesce(u.tg_username, u.first_name, 'id'||u.tg_user_id) as label, count(*)::int as hits
      from app.events e join app.users u on u.id = e.user_id
      where e.created_at >= now() - interval '7 days' and e.event_type in ('limit_files','limit_questions','compare_upsell')
      group by u.id, u.tg_username, u.first_name, u.tg_user_id
      order by hits desc limit 15`;

    const payingList = paying.length
      ? paying.map((p: any) => `• ${p.tg_username ? "@" + p.tg_username : (p.first_name ?? "без ника")} — ${planName(p.plan)}`).join("\n")
      : "нет";
    const hotList = hot.length
      ? hot.map((h: any) => `• ${h.label} — ${h.hits} раз(а)`).join("\n")
      : "нет";

    await send(chatId, `📊 Статистика за 30 дней

Новые пользователи: ${new_users}
Всего пользователей: ${total_users}
Вопросов: ${q_count}
Токены: ${in_tok} вход / ${out_tok} выход

Платящие:
${payingList}

🔥 Горячие (упирались в лимиты/спрашивали сверку за 7 дней):
${hotList}

Список клиентов и смена тарифа кнопкой (без SQL): /clients`);
  } else if (cmd.startsWith("/clients")) {
    if (from.id !== OWNER_ID) { await send(chatId, "Команда недоступна."); return; }
    await sendClientsList(chatId);
  } else if (cmd.startsWith("/setup_menu")) {
    if (from.id !== OWNER_ID) { await send(chatId, "Команда недоступна."); return; }

    const userCommands = [
      { command: "start", description: "Start / Начать" },
      { command: "lang", description: "Language / Мова / ენა / Тіл" },
      { command: "tariffs", description: "Tariffs / Тарифы" },
      { command: "pay", description: "Pay / Оплата" },
      { command: "files", description: "Files / Файлы" },
      { command: "limits", description: "Limits / Лимиты" },
      { command: "demo", description: "Demo / Демо" },
      { command: "support", description: "Support / Поддержка" },
      { command: "privacy", description: "Privacy" },
      { command: "terms", description: "Terms" },
    ];
    const ownerCommands = [
      ...userCommands,
      { command: "admin", description: "Статистика по боту" },
      { command: "clients", description: "Список клиентов, смена тарифа" },
    ];

    // Per Telegram client language_code — menu labels localized
    const menusByLang: Record<string, { command: string; description: string }[]> = {
      ru: [
        { command: "start", description: "Начать" },
        { command: "lang", description: "Язык" },
        { command: "tariffs", description: "Тарифы" },
        { command: "pay", description: "Оплата тарифа" },
        { command: "files", description: "Файлы" },
        { command: "limits", description: "Лимиты" },
        { command: "demo", description: "Видео-демо" },
        { command: "support", description: "Поддержка" },
        { command: "privacy", description: "Конфиденциальность" },
        { command: "terms", description: "Условия" },
      ],
      uk: [
        { command: "start", description: "Почати" },
        { command: "lang", description: "Мова" },
        { command: "tariffs", description: "Тарифи" },
        { command: "pay", description: "Оплата тарифу" },
        { command: "files", description: "Файли" },
        { command: "limits", description: "Ліміти" },
        { command: "demo", description: "Відео-демо" },
        { command: "support", description: "Підтримка" },
        { command: "privacy", description: "Конфіденційність" },
        { command: "terms", description: "Умови" },
      ],
      be: [
        { command: "start", description: "Пачаць" },
        { command: "lang", description: "Мова" },
        { command: "tariffs", description: "Тарыфы" },
        { command: "pay", description: "Аплата тарыфу" },
        { command: "files", description: "Файлы" },
        { command: "limits", description: "Ліміты" },
        { command: "demo", description: "Відэа-дэма" },
        { command: "support", description: "Падтрымка" },
        { command: "privacy", description: "Канфідэнцыяльнасць" },
        { command: "terms", description: "Умовы" },
      ],
      kk: [
        { command: "start", description: "Бастау" },
        { command: "lang", description: "Тіл" },
        { command: "tariffs", description: "Тарифтер" },
        { command: "pay", description: "Тариф төлемі" },
        { command: "files", description: "Файлдар" },
        { command: "limits", description: "Лимиттер" },
        { command: "demo", description: "Демо-видео" },
        { command: "support", description: "Қолдау" },
        { command: "privacy", description: "Құпиялылық" },
        { command: "terms", description: "Шарттар" },
      ],
      ka: [
        { command: "start", description: "დაწყება" },
        { command: "lang", description: "ენა" },
        { command: "tariffs", description: "ტარიფები" },
        { command: "pay", description: "გადახდა" },
        { command: "files", description: "ფაილები" },
        { command: "limits", description: "ლიმიტები" },
        { command: "demo", description: "დემო-ვიდეო" },
        { command: "support", description: "მხარდაჭერა" },
        { command: "privacy", description: "კონფიდენციალურობა" },
        { command: "terms", description: "პირობები" },
      ],
      hy: [
        { command: "start", description: "Սկսել" },
        { command: "lang", description: "Լեզու" },
        { command: "tariffs", description: "Սակագներ" },
        { command: "pay", description: "Վճարում" },
        { command: "files", description: "Ֆայլեր" },
        { command: "limits", description: "Սահմաններ" },
        { command: "demo", description: "Դեմո" },
        { command: "support", description: "Աջակցություն" },
        { command: "privacy", description: "Գաղտնիություն" },
        { command: "terms", description: "Պայմաններ" },
      ],
      tr: [
        { command: "start", description: "Başla" },
        { command: "lang", description: "Dil" },
        { command: "tariffs", description: "Tarifeler" },
        { command: "pay", description: "Ödeme" },
        { command: "files", description: "Dosyalar" },
        { command: "limits", description: "Limitler" },
        { command: "demo", description: "Demo" },
        { command: "support", description: "Destek" },
        { command: "privacy", description: "Gizlilik" },
        { command: "terms", description: "Koşullar" },
      ],
    };

    const r1 = await tg("setMyCommands", { commands: userCommands, scope: { type: "default" } });
    const r2 = await tg("setMyCommands", { commands: ownerCommands, scope: { type: "chat", chat_id: OWNER_ID } });
    const r3 = await tg("setChatMenuButton", { menu_button: { type: "commands" } });
    const langResults: Record<string, boolean> = {};
    for (const [code, commands] of Object.entries(menusByLang)) {
      const r = await tg("setMyCommands", { commands, scope: { type: "default" }, language_code: code });
      langResults[code] = !!r.ok;
    }

    const ok = r1.ok && r2.ok && r3.ok && Object.values(langResults).every(Boolean);
    await send(chatId, ok
      ? "✅ Меню обновлено.\n\nОбычным пользователям — команды в кнопке «Меню»: /start /lang /tariffs /pay /files /limits /demo /support /privacy /terms.\n\nВам (владельцу) — те же плюс /admin и /clients.\n\nКнопка «Меню» теперь явно открывает список команд."
      : `⚠️ Ошибка при обновлении меню: ${JSON.stringify({ r1, r2, r3 }).slice(0, 600)}`);
  } else {
    await send(chatId, t(lang, "unknown_cmd"));
  }
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return new Response("ok");
  if (TG_SECRET && req.headers.get("x-telegram-bot-api-secret-token") !== TG_SECRET) {
    return new Response("forbidden", { status: 403 });
  }
  let update: any;
  try { update = await req.json(); } catch { return new Response("bad request", { status: 400 }); }

  const work = (async () => {
    if (update.callback_query) { await onCallback(update.callback_query); return; }
    const msg = update.message ?? update.edited_message;
    try {
      if (!msg) return;
      if (msg.document) await onDocument(msg);
      else if (typeof msg.text === "string") await onText(msg);
      else if (msg.photo) {
        const u = msg.from ? await ensureUser(msg.from) : null;
        await send(msg.chat.id, t(u?.ui_lang ?? "ru", "photo"));
      }
    } catch (e) {
      console.error("update error", e);
      try { await send(msg?.chat?.id, t("ru", "tech_error")); } catch { /* ignore */ }
    }
  })();

  const rt = (globalThis as any).EdgeRuntime;
  if (rt?.waitUntil) rt.waitUntil(work); else await work;
  return new Response("ok");
});
