
# Telegram Plain Text Policy

Telegram delivery must use plain text by default.

Do not rely on:

```text
Telegram HTML parse_mode
Telegram Markdown
Telegram MarkdownV2
```

Allowed formatting:

```text
plain Unicode
emoji/status markers
numbered lists
short separators
source markers [1], [2]
message numbering [1/5]
```

Forbidden in Telegram messages:

```html
<b>...</b>
<i>...</i>
<a href="...">...</a>
<pre>...</pre>
```

Forbidden markdown patterns:

```text
**bold**
__underline__
[link](url)
large markdown tables
```
