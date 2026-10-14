# HTB Academy - Web Fuzzing: Parameter and Value Fuzzing (Optional Exercise 1)

Target: http://154.57.164.79:34341

## POST parameter fuzzing
Endpoint: /post.php  (POST param `y`)
Empty POST -> "Incorrect parameter value y:" (404)

ffuf command:
  ffuf -u http://154.57.164.79:34341/post.php -X POST \
       -H "Content-Type: application/x-www-form-urlencoded" \
       -d "y=FUZZ" -w /usr/share/seclists/Discovery/Web-Content/common.txt -mc 200 -v

Valid value: SUNWmc  (returns HTTP 200)
Verify:
  curl -d "y=SUNWmc" http://154.57.164.79:34341/post.php

### ANSWER (POST): HTB{p0st_fuzz1ng_succ3ss}

## GET parameter fuzzing (related)
  curl "http://154.57.164.79:34341/get.php?x=OA_HTML"
  ANSWER (GET): HTB{g3t_fuzz1ng_succ3ss}

---
# Question 1 (target 154.57.164.74:32459)

Fuzz with DirBuster-2007_directory-list-2.3-medium.txt to find hidden dir,
then read the tar.gz inside and answer with the Content-Length header.

Hidden dir: /ur-hiddenmember/
File:       /ur-hiddenmember/backup.tar.gz

  curl -I http://154.57.164.74:32459/ur-hiddenmember/backup.tar.gz
  # Content-Length: 210

### ANSWER: Content-Length: 210

---
# Question 1 (target 154.57.164.69:32117) - API Fuzzing
Endpoint identified: /czcmdcvt
  curl http://154.57.164.69:32117/czcmdcvt
  -> {"flag":"h1dd3n_r357"}
ANSWER: h1dd3n_r357

---
# Web Fuzzing Skills Assessment (target 154.57.164.75:43303)
/admin/panel.php?accessID=getaccess -> hints fuzzing_fun.htb vhost
vhost hidden.fuzzing_fun.htb -> /godeep/stoneedge/bbclone/typo3/index.php
  curl -H "Host: hidden.fuzzing_fun.htb" http://154.57.164.75:43303/godeep/stoneedge/bbclone/typo3/index.php
  -> HTB{w3b_fuzz1ng_sk1lls}
ANSWER: HTB{w3b_fuzz1ng_sk1lls}

---
# JavaScript Deobfuscation (target 154.57.164.78:38110)
curl http://154.57.164.78:38110/ -> HTML source comment: <!-- HTB{4lw4y5_r34d_7h3_50urc3} -->
ANSWER: HTB{4lw4y5_r34d_7h3_50urc3}
