import os


async def log(out_file: str, *kwargs):
    out = ''
    for kwarg in kwargs:
        out += f' {kwarg}'

    if os.path.exists(out_file):
        mode = 'a'
    else:
        mode = 'w'

    with open(out_file, mode=mode, encoding='utf-8') as f:
        f.write(out+"\n")
