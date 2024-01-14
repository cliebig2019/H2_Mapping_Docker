import json

def write_html(html, path):

    f = open(path, "a")
    f.write(html)
    f.close()

def write_json(data, path):

    with open(path, "w") as file:
        json.dump(data, file, indent=4)

def write_file(data, path):

    with open(path, "w") as file:
        file.write(data)
