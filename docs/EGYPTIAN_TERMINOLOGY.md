# Egyptian Arabic terminology baseline

This project targets a professional Arabic interface for ERPNext V16 with Egyptian accounting and business usage as its primary baseline.

## Primary references

- Egyptian Financial Regulatory Authority — Egyptian Accounting Standards portal: https://fra.gov.eg/معايير-المحاسبة-المصرية/
- Egyptian Accounting Standard 1 — Presentation of Financial Statements: https://fra.gov.eg/wp-content/uploads/2024/03/معيار-المحاسبة-المصري-رقم-1-عرض-القوائم-المالية.pdf
- Ministerial Decision 69/2019 and amended standards: https://fra.gov.eg/regulations/قرار-وزير-الاستثمار-والتعاون-الدولي-ر/
- FRA accounting-standard regulatory decisions and later amendments: https://fra.gov.eg/القرارات-و-الضوابط-التنظيمية-لمعايير/

These sources establish names such as **قائمة المركز المالي**، **قائمة الدخل**، **قائمة التدفقات النقدية**، **قائمة التغيرات في حقوق الملكية**، and the wider terminology used in Egyptian financial reporting.

## Product-language principles

- Translate business meaning, not the isolated English word.
- Prefer Egyptian operational terms that remain understandable in Modern Standard Arabic.
- Distinguish workflow approval (**اعتماد**) from accounting posting (**ترحيل**).
- Use **سند دفع أو قبض** for ERPNext Payment Entry because the document supports both directions.
- Use **قائمة مكونات الصنف** for BOM; it is not a financial invoice.
- Use **عنصر فرعي/مستند فرعي** for technical “Child”; never the human word **طفل**.
- Use **دور** for Role and **صلاحية** for Permission.
- Use **المخزن** for the user-facing Warehouse label in the Egyptian edition.

## Scope rule

The glossary is authoritative for exact document/report labels. Longer messages must still be reviewed in their screen and business context; global search-and-replace is prohibited.
