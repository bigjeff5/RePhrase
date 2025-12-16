from types import ClassMethodDescriptorType
from lib import scraper
from pathlib import Path
import re
import argparse
import lmstudio as lms
from typing import Dict, Generator, Type, TypeVar, get_type_hints, cast
import json

SERVER_API_HOST = "localhost:1234"
REPHRASE_DATA = Path("./RePhraseData")
RAW_CHAPTERS = Path(f"{REPHRASE_DATA}/RawChapters")
CLEANED_CHAPTERS = Path(f"{REPHRASE_DATA}/CleanedChapters")
START_URL = "https://novelfull.net/chronicles-of-primordial-wars/chapter-1-the-person-in-front-your-pants-are-slipping.html"
BASE_URL = "https://novelfull.net/chronicles-of-primordial-wars/" 
CRAWL_DELAY = 1
MAX_REQUESTS = 600
PROMPT = '''
    You are an Editor for a Chinese to English Xianxia Web Novel translation project.
    Your job is to take the text of a specific chapter and improve the phrasing of the text so that it flows nicely in for an English reader who is familiar with classic Xianxia Web Novel tropes.
    The following are your guiding principles:
    * You make the minimum changes necessary to improve the flow of the text.
    * You do not add content. You are not the author or the translator, you're supporting their efforts to improve the reader's experience.
    * You maintain tropes English readers of Xianxia will be familiar with, e.g.: "You have eyes but cannot see Mt Tai", "You're seeking death", Face, etc.
    * You work English idiom where appropriate for the time period represented in a way that complements any Chinese idioms.

    Rewrite the following chapter in natural, fluent English. Do not embelish the end of the chapter, the author wants it to end exactly as described:

'''

T = TypeVar("T", bound=lms.Chat)


def call_llm(message):
    with lms.Client(SERVER_API_HOST) as client:
        model = client.llm.model()
        response = model.respond(message).content
    return response 

def load_state(output_dir):
    STATE_FILE = Path(f"{output_dir}/state.json")
    if not STATE_FILE.exists():
        return set()
    data = json.loads(STATE_FILE.read_text())
    processed = set(data.get("processed"))
    return processed

def save_state(processed, output_dir):
    STATE_FILE = Path(f"{output_dir}/state.json")
    data = {"processed": list(processed)}
    STATE_FILE.write_text(json.dumps(data, indent=2))

def natural_key(name):
    # extract the first number in the filename
    num = re.search(r'\d+', name)
    return int(num.group()) if num else float('inf')

def pretty_name(filename):
    match = re.search(r'^chapter-(\d*)-?(.*)$', filename)
    if not match:
        return filename
    chapter_num = match.group(1)
    chapter_title = match.group(2).replace("-", " ").title()
    if not (chapter_title == ''):
        name = f"Chapter {chapter_num} - {chapter_title}.md"
    else:
        name = f"Chapter {chapter_num}.md"
    return name

def format_chapter(text):
    # basic formatting - strips tabs and adds # to first line for the chapter heading
    lines = text.splitlines()
    if not lines:
        return text
    first = lines[0].lstrip()
    formatted_lines = []
    if not first.startswith("#"):
        first = f"# {first}"
    for line in lines[1:]:
        text = line.replace("—", " - ")
        text = text.replace("\t", "")
        formatted_lines.append(text)
    return "\n".join([first] + formatted_lines)

def process_chapters(input_dir, output_dir):
    """
    Check each file in the input_dir to see if it has been processed yet. If not,
    load the file and combine the Prompt with the text and send to the llm for 
    processing. Save the file in the output_dir as 0001 - <chapter1 tite>.md
    """
    chapters = sorted(Path(input_dir).glob("chapter-*"), key=lambda p: natural_key(p.name))
    processed = load_state(output_dir)
    chapters_processed = 0
    for chapter in chapters:
        if chapter.name in processed:
            print(f"[INFO] Already processed {chapter}, skipping to Next Chapter.")
        else:
            processed.add(chapter.name)
            print(f"[INFO] Processing {chapter}")
            new_name = pretty_name(chapter.stem)
            content_text = chapter.read_text("utf-8")
            message = f"{PROMPT}\n{content_text}"
            cleaned_text = format_chapter(call_llm(message))
            cleaned_chapter = Path(f"{output_dir}/{new_name}")
            cleaned_chapter.write_text(cleaned_text, "utf-8")
        chapters_processed += 1
        save_state(processed, output_dir)

    print(f"[INFO] Crawl finished. Pages fetched: {chapters_processed}")



def main():
    parser = argparse.ArgumentParser(
        description="Simple chapter archiver that follows next_chapter links."
    )
    parser.add_argument(
        "-s",
        "--scrape",
        action='store_true',
        help="Flag to scrape urls before processing. Off by default.",
    )

    print("Welcome to RePhrase!") 
    args = parser.parse_args()
    if args.scrape: 
        scraper.crawl(start_url=START_URL,
                  delay=CRAWL_DELAY,
                  max_requests=MAX_REQUESTS,
                  output_dir=RAW_CHAPTERS,
                  base_url=BASE_URL)
    process_chapters(RAW_CHAPTERS, CLEANED_CHAPTERS)
    print("Finished Cleaning all Chapters")


if __name__ == "__main__":
    main()
