from ddgs import DDGS

with DDGS() as ddgs:
    results = ddgs.text("What is artificial intelligence?", max_results=3)

    for r in results:
        print(r)