import re

def pretty_name(filename):
    match = re.search(r'^chapter-(\d*)-?(.*)\.txt$', filename)
    print(match)
    print(filename)
    if not match:
        return filename
    chapter_num = match.group(1)
    chapter_title = match.group(2).replace("-", " ").title()
    if not (chapter_title == ''):
        name = f"Chapter {chapter_num} - {chapter_title}.md"
    else:
        name = f"Chapter {chapter_num}.md"
    return name

def main():
    filename_nt = 'chapter-334.txt'
    filename_t = 'chapter-426-blacksmith.txt'

    outT = pretty_name(filename_t)
    outNT = pretty_name(filename_nt)

    print(outT)
    print(outNT)

if __name__ == "__main__":
    main()
