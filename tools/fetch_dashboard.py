import urllib.request
print(urllib.request.urlopen('http://127.0.0.1:8000/users/dashboard/').read().decode('utf-8'))
