def build_slice(toks):
    result = None
    first  = 0
    second = 0
    if 'first' in toks:
        first = toks['first']
        result = first

    if 'second' in toks:
        second = toks['second'][0]
        result = slice(first, second)

    return result
