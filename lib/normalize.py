
from pathlib import Path
from charset_normalizer import from_bytes

def normalizeChapters(directory):
    chapter_dir = Path(directory)
    print(chapter_dir)
    for md_file in chapter_dir.glob("Chapter*.md"):
        print(md_file)
        raw = md_file.read_bytes()

        result = from_bytes(raw).best()
        if result is None:
            print(f"Could not detect encoding: {md_file.name}")
            continue

        text = str(result)
        text.replace("\n\n\n", "\n")

        # Write back as UTF-8 (no BOM)
        md_file.write_text(text, encoding="utf-8")

        print(f"{md_file.name}: {result.encoding} → utf-8")


def main():
    print("Successfully Launched Script")
    normalizeChapters("RephraseData\\CleanedChapters")

if __name__ == "__main__":
    main()
