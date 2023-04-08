import datetime


def find(obj, key, path=''): 

	ret = []

	if type(obj) == list:
		idx = 0 
		for c in obj: 
			r = find(c, key, path=path + f"['{idx}']")
			idx += 1
			ret.extend(r)

	elif type(obj) == dict: 
		for c in obj.keys():
			if c == key: 
				ret.append((path, obj[c]))
			else: 
				r = find(obj[c], key, path=path + f"['{c}']")
				ret.extend(r)

	return ret


def nownanos():
	return int((datetime.datetime.now() - datetime.datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1e9)


if __name__ == "__main__":
	a = {'a': {'b': {'c': 'hello world'}, 'c': 'nononn'}}
	print(find(a, 'c'))
