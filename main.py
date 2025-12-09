from lib import scraper
import lmstudio as lms
from typing import Dict, Generator, Type, TypeVar, get_type_hints, cast

SERVER_API_HOST = "localhost:1234"

T = TypeVar("T", bound=lms.Chat)


def validate_LMSDataDict(data: Dict, target_type: Type[T]) -> T:
    expected_structure = get_type_hints(target_type)
    for key, expected_type in expected_structure.items():
        if key not in data:
            raise KeyError(f"Missing required key '{key}'.")
        actual_value = data[key]
        if not isinstance(actual_value, type(expected_type)):
            raise TypeError(
                f"Key '{key}' has an incorrect type. Expected {expected_type}, but got {type(actual_value).__name__}."
            )
    return cast(T, data)


def call_llm(shared: Dict) -> Generator:
    try:
        LMSDataDict = validate_LMSDataDict(shared, lms.Chat)
        with lms.Client(SERVER_API_HOST) as client:
            model = client.llm.model()
            for fragment in model.respond_stream(LMSDataDict):
                yield fragment.content
    except (TypeError, KeyError) as e:
        print(f"Shared dictionary was not a valid LM Studio Dictionary: {e}")
        return None


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
