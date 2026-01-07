from client import get_client
client = get_client()

text = "苹果公司发布了一款新手机，主打影像与续航。发布会在加州举行，媒体反响积极，但也有人认为定价偏高。"

bad = client.responses.create(
    model="gpt-4o-mini",
    input=f"总结一下：{text}"
)

good = client.responses.create(
    model="gpt-4o-mini",
    input=[
        {"role":"developer","content":"你是一个严格按要求输出的助手。"},
        {"role":"user","content":(
            "请对下面文本做摘要。\n"
            "要求：1) 不超过40字；2) 必须包含'地点'信息；3) 只输出一句话。\n\n"
            f"文本：{text}"
        )}
    ],
)

print("BAD:", bad.output_text)
print("GOOD:", good.output_text)
