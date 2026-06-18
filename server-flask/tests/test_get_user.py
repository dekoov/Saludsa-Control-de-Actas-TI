import urllib.request

nombre = input("Ingrese el nombre del usuario a buscar: ")
url = f"http://localhost:5000/api/user?q={nombre}"
# url = f"http://localhost:5000/api/user?q=David%20Correa"
response = urllib.request.urlopen(url)
print(response.read())
