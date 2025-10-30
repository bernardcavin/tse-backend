from app.utils.string import parse_input


def parse_dict(dictionary: dict):
    output = {}
    for key, value in dictionary.items():
        output[key] = parse_input(value)
    return output
