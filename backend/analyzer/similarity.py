from sentence_transformers import SentenceTransformer, util

# Load once when server starts — takes ~20 seconds first time
model = SentenceTransformer("all-MiniLM-L6-v2")

SIMILARITY_THRESHOLD = 0.75

def group_similar_questions(all_questions):
    """
    all_questions = list of dicts:
    [
        {"text": "Explain OSI Model", "source": "2022.pdf"},
        {"text": "Describe OSI layers", "source": "2023.pdf"},
        ...
    ]
    Returns ranked list of groups.
    """
    if not all_questions:
        return []

    texts = [q["text"] for q in all_questions]

    # Convert every question to a vector (number representation)
    embeddings = model.encode(texts, convert_to_tensor=True)

    visited = [False] * len(texts)
    groups = []

    for i in range(len(texts)):
        if visited[i]:
            continue

        # Start a new group with this question
        group = {
            "representative": texts[i],
            "variants": [texts[i]],
            "sources": [all_questions[i]["source"]],
            "count": 1,
        }
        visited[i] = True

        # Compare with every other unvisited question
        cos_scores = util.cos_sim(embeddings[i], embeddings)[0]

        for j in range(i + 1, len(texts)):
            if not visited[j] and cos_scores[j].item() >= SIMILARITY_THRESHOLD:
                group["variants"].append(texts[j])
                group["sources"].append(all_questions[j]["source"])
                group["count"] += 1
                visited[j] = True

        groups.append(group)

    # Sort by frequency — most repeated first
    groups.sort(key=lambda g: g["count"], reverse=True)

    # Assign priority based on frequency
    max_count = groups[0]["count"] if groups else 1
    for g in groups:
        ratio = g["count"] / max_count
        if ratio >= 0.6:
            g["priority"] = "High"
        elif ratio >= 0.3:
            g["priority"] = "Medium"
        else:
            g["priority"] = "Low"

    return groups
