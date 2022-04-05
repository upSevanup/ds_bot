import json


def load_json(name):
    with open(name, encoding="utf-8") as jf:
        return json.load(jf)


def write_json(name, content):
    with open(name, "w") as fff:
        json.dump(content, fff, ensure_ascii=True, indent=4)