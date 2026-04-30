
# Standalone HTML Report Policy

The final HTML report must be a single-file standalone artifact suitable for opening directly from Telegram.

Required output:

```text
full-report.html
```

Forbidden in final HTML:

```html
<link rel="stylesheet" href="...">
<script src="..."></script>
<img src="local/path.png">
<link href="https://fonts.googleapis.com/...">
```

Allowed:

```text
inline <style>
inline optional <script>
inline SVG icons
embedded report JSON
external outbound source URLs in citations
internal #anchors
```

The renderer may use separate source CSS/JS/templates internally, but the delivered HTML must inline all required assets.
