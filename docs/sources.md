# Sources

Clippings fetches articles from configurable sources. Each source has a `type`, `name`, and `max_articles`.

## Hacker News

Fetches top stories from the [HN API](https://hacker-news.firebaseio.com/v0/).

```yaml
sources:
  - type: hackernews
    name: Hacker News
    max_articles: 10
```

No URL needed — uses the official HN API.

## RSS Feeds

Any RSS/Atom feed works.

```yaml
sources:
  - type: rss
    name: BBC News
    url: http://feeds.bbci.co.uk/news/rss.xml
    max_articles: 10
```

Popular feeds:
- Ars Technica: `https://arstechnica.com/feed/`
- The Verge: `https://www.theverge.com/rss/index.xml`
- TechCrunch: `https://techcrunch.com/feed/`
- Wired: `https://www.wired.com/feed/rss`

## BBC News

A preset for BBC News RSS feeds.

```yaml
sources:
  - type: bbc
    name: BBC News
    url: http://feeds.bbci.co.uk/news/rss.xml
    max_articles: 10
```

## Adding Custom Sources

Just add another entry to the `sources` list:

```yaml
sources:
  - type: hackernews
    name: Hacker News
    max_articles: 10
  - type: rss
    name: Ars Technica
    url: https://arstechnica.com/feed/
    max_articles: 10
  - type: rss
    name: The Verge
    url: https://www.theverge.com/rss/index.xml
    max_articles: 10
```

Each source's `max_articles` controls how many articles it fetches. The `schedule.max_articles` setting then caps the final output after scoring/ranking.
