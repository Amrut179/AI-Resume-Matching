def print_pipeline(doc):
    tokens = []
    for token in doc:
        tokens.append(token.text)
    print("=================== tokenization =========================")
    print(tokens)
    print("")

    tags = []
    for token in doc:
        tags.append(f"{token.text}:{token.pos_}  ")
    print("=================== part-of-speech tagging =========================")
    print(tags)
    print("")

    deps = []
    for token in doc:
        deps.append(f"{token.text}:{token.dep_}  ")
    print("=================== Parsing Dependency Labels =========================")
    print(deps)
    print("")

    lemmas = []
    for ent in doc:
        lemmas.append(f"{ent.text}:{ent.lemma_}  ")
    print("=================== lemmatizing =========================")
    print(lemmas)
    print("")

    labels = []
    for ent in doc.ents:
        labels.append(f"{ent.text}:{ent.label_}  ")
    print("=================== custom named entity recognition =========================")
    print(labels)
    print("")

    stops = []
    for ent in doc:
        if ent.is_stop or ent.is_punct:
            stops.append(ent.text)
    print("=================== step 6: stop words removal =========================")
    print(stops)
    print("")