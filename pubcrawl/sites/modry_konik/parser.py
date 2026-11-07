from ...common.parser import clean
import re


def extract_text_from_ast(ast_node):
    if not ast_node:
        return ""
    text = ""
    if isinstance(ast_node, dict) and "text" in ast_node:
        text += ast_node["text"] + " "
    if isinstance(ast_node, dict) and "elements" in ast_node:
        for el in ast_node["elements"]:
            text += extract_text_from_ast(el) + " "
    return clean(text)


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
        if not text or len(text) <= 30:
            continue

        likes = 0
        like_button = node.css('button.bhs_b')
        if like_button:
            count_str = clean(like_button[0].css('span:last-child::text').get())
            if count_str and count_str.isdigit():
                likes = int(count_str)

        posts.append({
            "text": text,
            "likes": likes
        })

    if len(posts) < 2:
        raise ValueError(f"Málo príspevkov vo vlákne: {len(posts)}")

    question = posts[0]["text"]
    pairs = []
    for post in posts[1:]:
        pairs.append({
            "question": question,
            "answer": post["text"],
            "likes": post["likes"]
        })
    return title, pairs


def parse_blog(response):
    title = clean(" ".join(response.css("h1 ::text").getall()))

    body = ""
    for selector in (".article-body", ".article__body", ".post-content", ".message", "article"):
        node = response.css(selector)
        if node:
            body = clean(" ".join(node[0].css("p ::text, p::text").getall()))
            if body:
                break

    if not body:
        raise ValueError("Chýba text blogového príspevku")

    match = re.search(r'"postId":\s*(\d+)', response.text)
    post_id = match.group(1) if match else None

    if not post_id:
        raise ValueError("Nepodarilo sa nájsť ID blogového príspevku")

    return {
        "title": title,
        "question": body,
        "post_id": post_id
    }