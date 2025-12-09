from lib import scraper

def main():
    start_url = "https://novelfull.net/chronicles-of-primordial-wars/chapter-1-the-person-in-front-your-pants-are-slipping.html"
    base_url = "https://novelfull.net/chronicles-of-primordial-wars/"
    output_dir = "RePhraseData"
    delay = 5 
    max_requests = 1
    print("Welcome to RePhrase!")
    scraper.crawl(start_url=start_url,
                  delay=delay,
                  max_requests=max_requests,
                  output_dir=output_dir,
                  base_url=base_url)

if __name__ == "__main__":
    main()
