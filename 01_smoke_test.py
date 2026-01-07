from client import get_client
client = get_client()

resp = client.responses.create(
    model="gpt-4o-mini",
    input="请回复：环境已跑通"
)
print(resp.output_text)
