"""Fetch news across configured topics, summarise with Gemini, write a markdown digest."""

import json
import os
import pathlib
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

import feedparser
from google import genai

MODEL = "gemini-flash-latest"
GOOGLE_NEWS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:EN"

config = json.loads(pathlib.Path("config.json").read_text())
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

cutoff = datetime.now(timezone.utc) - timedelta(hours=config["lookback_hours"])


def fetch(topic):
    """Pull recent, deduplicated headlines for one topic."""
    url = GOOGLE_NEWS.format(query=urllib.parse.quote(topic["query"]))
    feed = feedparser.parse(url)

    items, seen = [], set()
    for entry in feed.entries:
        if not getattr(entry, "published_parsed", None):
            continue
        published = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
        if published < cutoff:
            continue

        title = entry.title.strip()
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)

        source = entry.get("source", {}).get("title", "")
        items.append({"title": title, "link": entry.link, "source": source})

        if len(items) >= config["max_items_per_topic"]:
            break

    return items


PROMPT = """You are briefing a deal technology consultant who works IT workstreams in M&A.
They are sharp, time-poor, and allergic to filler.

Topic: {name}
What matters for this topic: {focus}

Below are raw headlines from the last {hours} hours. Write a briefing that:
- Opens with one sentence naming the single most important development, or says plainly
  that nothing significant happened
- Then gives 3-5 bullets, most important first. Each bullet: what happened, and why it
  matters to someone in deal tech or enterprise AI
- Drops anything that is thin, duplicated, promotional, or purely speculative
- Never pads to hit a bullet count. Two strong bullets beat five weak ones
- Uses markdown links in the form [headline](url) so sources are clickable
- Contains no preamble, no heading, and no closing summary

Headlines:
{headlines}"""


def summarise(topic, items):
    headlines = "\n".join(f"- {i['title']} ({i['source']}) — {i['link']}" for i in items)
    response = client.models.generate_content(
        model=MODEL,
        contents=PROMPT.format(
            name=topic["name"],
            focus=topic["focus"],
            hours=config["lookback_hours"],
            headlines=headlines,
        ),
    )
    return response.text.strip()


def main():
    today = datetime.now(timezone.utc)
    sections = [
        f"# Deal Pulse — {today.strftime('%d %B %Y')}",
        "",
        f"_Covering the last {config['lookback_hours']} hours. Generated automatically._",
        "",
    ]

    for topic in config["topics"]:
        print(f"Fetching: {topic['name']}")
        items = fetch(topic)
        sections.append(f"## {topic['name']}")
        sections.append("")

        if not items:
            sections.append("_No coverage in this window._")
        else:
            print(f"  {len(items)} items — summarising")
            try:
                sections.append(summarise(topic, items))
            except Exception as error:
                print(f"  Failed: {error}")
                sections.append(f"_Summary failed: {error}_")
                sections.append("")
                sections.extend(f"- [{i['title']}]({i['link']})" for i in items)

        sections.append("")

    sections.append("---")
    sections.append("")
    sections.append(
        "Built by Ishita Singh. Headlines via Google News, summarised with Gemini. "
        "AI-generated — verify anything you plan to act on."
    )

    body = "\n".join(sections)

    archive = pathlib.Path("digests")
    archive.mkdir(exist_ok=True)
    (archive / f"{today.strftime('%Y-%m-%d')}.md").write_text(body)
    pathlib.Path("latest.md").write_text(body)

    print("Digest written.")


if __name__ == "__main__":
    main()
