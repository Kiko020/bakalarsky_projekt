from ...common.parser import clean


def parse_qa(response):
    
    
    title = clean(" ".join(response.css("h1 ::text").getall()))
    if not title:
        raise ValueError("Chýba nadpis otázky (h1)")


    question_node = response.css("div.pw_bc")
    if not question_node:
        raise ValueError("Nenašiel sa text otázky (div.pw_bc)")
    question = clean(" ".join(question_node[0].css("p ::text, p::text").getall()))
    if not question:
        question = clean(" ".join(question_node[0].css("::text").getall()))


    answer_node = response.css('[id^="comment-"]')
    if not answer_node:
        raise ValueError("Nenašla sa odpoveď (id^=comment-)")
    answer = clean(" ".join(answer_node[0].css("div.ic_l p ::text, div.ic_l p::text").getall()))
    if not answer:
        answer = clean(" ".join(answer_node[0].css("div.ic_l ::text").getall()))

    if len(question) < 10 or len(answer) < 20:
        raise ValueError(f"Príliš krátke: otázka={len(question)}, odpoveď={len(answer)}")

    return {
        "title": title,
        "question": question,
        "answer": answer,
    }


def parse_forum(response):
    title = clean(" ".join(response.css("h1 ::text").getall()))

    posts = []
    for node in response.css('[id^="comment-"]'):
        text = clean(" ".join(node.css("div.ic_l p ::text, div.ic_l p::text").getall()))
        if not text:
            text = clean(" ".join(node.css("div.ic_l ::text").getall()))
        if text and len(text) > 30:
            posts.append(text)

    if len(posts) < 2:
        raise ValueError(f"Málo príspevkov vo vlákne: {len(posts)}")

    question = posts[0]
    pairs = []
    for answer in posts[1:]:
        pairs.append((question, answer))
    return title, pairs