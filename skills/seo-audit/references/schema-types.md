# Which structured-data type fits which page

Only add a schema the page genuinely is. A `Product` schema on a blog post is worse than
no schema: it is a validation error, and repeated it costs trust in the whole domain.

| Page | Type | Required fields | Gets a rich result |
|------|------|-----------------|--------------------|
| Blog post, news article | `Article` / `NewsArticle` | `headline`, `datePublished`, `author`, `image` | Top stories, date in snippet |
| Question-and-answer block | `FAQPage` | `mainEntity[].name`, `mainEntity[].acceptedAnswer.text` | Expandable answers |
| Step-by-step instructions | `HowTo` | `name`, `step[].name`, `step[].text` | Numbered steps |
| Software, app, agent skill | `SoftwareApplication` | `name`, `applicationCategory`, `operatingSystem`, `offers` | Rating stars, price |
| Any page nested under a section | `BreadcrumbList` | `itemListElement[].position`, `.name`, `.item` | Breadcrumb path instead of URL |
| Collection / index page | `CollectionPage` + `ItemList` | `itemListElement[].position`, `.url` | Carousel eligibility |
| Company, personal brand | `Organization` / `Person` | `name`, `url`, `logo` | Knowledge panel input |
| Physical or digital product | `Product` | `name`, `image`, `offers.price`, `offers.priceCurrency` | Price, availability |

## Rules that catch most mistakes

1. **The schema must describe what a visitor sees.** Marking up an FAQ that is not
   rendered on the page is a guidelines violation, not a shortcut.
2. **One primary type per page**, plus `BreadcrumbList` and `Organization` as companions.
   Three competing primary types is a signal of copy-paste, and validators flag it.
3. **`@id` everything you reference more than once**, then point at it. Repeating a full
   `Organization` block in five schemas creates five entities, not one.
4. **Dates are ISO 8601 with an offset.** `2026-07-31T09:00:00+02:00`, not `31-07-2026`.
5. **`image` wants an absolute URL.** A root-relative path silently resolves to nothing.

## Validating

```bash
# Extract every JSON-LD block and check that each one parses
python3 - "$URL" <<'PY'
import json, re, sys, urllib.request
html = urllib.request.urlopen(sys.argv[1]).read().decode()
for i, m in enumerate(re.findall(
        r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S)):
    try:
        data = json.loads(m)
        print(f"[{i}] ok   {data.get('@type')}")
    except json.JSONDecodeError as e:
        print(f"[{i}] FAIL {e}")
PY
```

Parsing is necessary, not sufficient. Run the result through Google's Rich Results Test
before claiming a page is eligible for anything.
