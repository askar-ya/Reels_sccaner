def get_accounts_cookies(from_f: str):
    with open(from_f, 'r') as f:
        raw = f.read()

    out = []

    raw = raw.split('\n')
    for i in raw:
        cookies = i.split('||')[1].split('||')[0].split(';')
        acc = []
        for cookie in cookies[:-1]:
            cook = {
                "domain": ".instagram.com",
                "path": "/",
            }
            data = cookie.split('=')
            name = data[0]
            value = data[1]
            cook['name'] = name
            cook['value'] = value
            acc.append(cook)
        out.append(acc)
    #print(out)
    return out

#get_accounts_cookies('cookies.txt')