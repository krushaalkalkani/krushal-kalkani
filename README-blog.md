# Blog — how it works & how to add a post

The blog is plain static HTML/CSS/JS, matching the rest of the site (same
tokens in `assets/css/style.css`, same nav, same dark/light toggle). There is
**no build step** — edit files, refresh, done.

## Project structure

```
/  index.html  blog.html  ml-roadmap.html  ai-skill.html   ← pages (live at root)
├── assets/
│   ├── css/style.css        ← all styles
│   ├── img/                 ← images (favicon, feature images, photo)
│   └── docs/                ← résumé PDF
├── data/
│   ├── portrait.json        ← ASCII jelly-portrait data (index hero)
│   └── posts.json           ← blog source of truth
└── posts/
    └── _template.html       ← copy this to create a post
```

## Files

| File | Role |
| --- | --- |
| `data/posts.json` | **Source of truth.** The list of posts the index renders. |
| `blog.html` | The blog index — header + featured post + responsive card grid. Reads `data/posts.json`. |
| `posts/<slug>.html` | One file per article. |
| `posts/_template.html` | Starting point — copy it to create a new post. |
| `assets/css/style.css` | All blog styles live in the `Blog` section at the bottom. |

## Add a new post (2 steps)

### 1. Add one entry to `data/posts.json`

Add an object to the `posts` array:

```json
{
  "slug": "my-new-post",
  "title": "My New Post",
  "date": "2026-07-01",
  "readingTime": "4 min read",
  "tags": ["Machine Learning"],
  "excerpt": "One or two sentences that show up on the card.",
  "featureImage": "",
  "featured": false
}
```

Field reference:

- **slug** — must match the file name `posts/<slug>.html` and the URL. Use
  lowercase-with-hyphens.
- **title** — post title (card + page).
- **date** — `YYYY-MM-DD`. The index sorts newest-first by this.
- **readingTime** — free text like `"4 min read"`. Optional; omit to hide it.
- **tags** — array of 1–2 short strings, rendered as pills. (Only the first 2 show on a card.)
- **excerpt** — 1–2 sentences for the card.
- **featureImage** — `""` for the designed placeholder, or a path like
  `"assets/img/my-new-post.jpg"` (relative to the **site root**, because
  `blog.html` lives at the root).
- **featured** — `true` makes it the one large post at the top. Keep **at most
  one** `true`; if several are `true`, the newest wins.
- **url** *(optional)* — set this when the post is its **own standalone page**
  rather than a `posts/<slug>.html` article. The card links straight to that
  path. This is how the **ML Engineer Roadmap** (`ml-roadmap.html`) and
  **Agentic AI Builder** (`ai-skill.html`) pages appear in the blog — they keep
  their own rich layouts and just show up as cards here. When `url` is set you
  do **not** need to create a file in `posts/`.

### 2. Create one post file

> Skip this step for a `url`-based post (its page already exists).

```bash
cp posts/_template.html posts/my-new-post.html
```

Open it and replace every `{{PLACEHOLDER}}` (title, tags, date, body…). The
body supports styled headings (`h2`/`h3`), paragraphs, lists, blockquotes,
inline `<code>`, and `<pre><code>` blocks — all themed to match the site.

That's it. Open `blog.html` and the new card appears.

## Feature images & the empty state

When `featureImage` is empty, both the card and the article banner render a
**designed placeholder** — a soft accent gradient with the site's dot texture
and a faint `K` monogram — so nothing ever looks broken.

To add a real image later:

- **Index card:** just set `featureImage` in `data/posts.json` (e.g.
  `"assets/img/my-post.png"`). It swaps in automatically (lazy-loaded), with the
  title as alt text.
- **Article banner:** in `posts/<slug>.html`, replace the placeholder
  `<figure class="feature-media">…</figure>` with the `<img>` version shown in
  the HTML comment right above it. Paths there use `../assets/img/...` (because
  post files live in `posts/`). **Write real, descriptive alt text.**

Recommended image ratio: **16:9** (e.g. 1280×720). Keep files small (≈150–300 KB)
so the blog stays fast.

## Running locally

Because the index fetches `data/posts.json`, open the site through a local
server (not `file://`):

```bash
python3 -m http.server 8123
# then visit http://localhost:8123/blog.html
```

## Notes

- Works in **both themes** and is fully **responsive**; hover/transitions
  respect `prefers-reduced-motion`; images **lazy-load**; cards are keyboard
  accessible (real links, visible focus).
- The `_howToAddAPost` key at the top of `data/posts.json` is a quick inline
  reminder — it's ignored by the renderer (only the `posts` array is read).
