import json

with open('account.txt', 'r') as f:
    raw = f.read()

out = []

raw = raw.split('\n')
for i in raw:
    cookies = i.split('|||')[1].split('||')[0].split(';')
    cook = {}
    for cookie in cookies[:-1]:
        data = cookie.split('=')
        name = data[0]
        value = data[1]

        cook[name] = value
    out.append(cook)

with open('accounts_by.json', 'w') as f:
    json.dump(out, f, indent=4)
