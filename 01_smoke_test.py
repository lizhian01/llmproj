from client import get_client


def main() -> None:
    client = get_client()
    resp = client.responses.create(
        model="gpt-4o-mini",
        input="请回复：环境已跑通",
    )
    print(resp.output_text)


if __name__ == "__main__":
    main()
