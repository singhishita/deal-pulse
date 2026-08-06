# Deal Pulse

An automated weekday briefing on M&A, deal technology, AI, and AI policy.
Runs on GitHub Actions, summarises with Gemini, commits itself to this repo.

**Read the latest:** [latest.md](latest.md) · **Archive:** [digests/](digests/)

## Why

Deal tech sits at an intersection — transactions, enterprise technology, and now AI —
and no single publication covers all three. This pulls from across them daily and
compresses it into something readable in three minutes.

## How it works

1. A GitHub Actions cron job runs each weekday morning
2. `digest.py` reads `config.json` and fetches recent headlines per topic via Google News RSS
3. Each topic goes to Gemini separately, with topic-specific instructions on what to
   prioritise and what to ignore
4. The result is written to a dated archive file and committed back to the repo

No server, no hosting, no cost.

## Adding a topic

Add a block to `config.json`:

```json
{
  "name": "Your topic",
  "query": "search terms OR alternatives",
  "focus": "What to prioritise, and what to ignore."
}
```

No code changes needed.

## Design notes

- **One API call per topic, not one for everything.** Separate calls produce noticeably
  sharper summaries than asking the model to handle five unrelated subjects at once.
- **Failures degrade, they don't crash.** If summarisation fails for one topic, that
  section falls back to a raw headline list and the run continues.
- **Google News RSS instead of scraping.** Most consulting firms no longer publish public
  feeds. Search-based retrieval is more robust and doesn't scrape anyone's site.

## Stack

Python · feedparser · Google Gemini API · GitHub Actions

## Caveat


Summaries are AI-generated and may misrepresent sources. Verify anything you plan to
act on.
