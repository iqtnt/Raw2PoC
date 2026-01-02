from flask import Flask, request, render_template_string, make_response, jsonify
import uuid, requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
POCS = {}

HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Raw2PoC</title>
<style>
body {
  background:#0b0b0b;
  color:#00ff9c;
  font-family: monospace;
  margin:0;
}
.container {
  width:900px;
  max-width:95%;
  margin:25px auto;
  border:1px solid #00ff9c;
  padding:20px;
}
textarea,input {
  width:100%;
  background:#000;
  color:#00ff9c;
  border:1px solid #00ff9c;
  padding:10px;
}
textarea {
  height:200px;
}
.section {
  margin-top:22px;
}
.box {
  border:1px solid #00ff9c;
  padding:10px;
  white-space:pre-wrap;
  max-height:260px;
  overflow:auto;
}
iframe {
  width:100%;
  height:320px;
  border:1px solid #00ff9c;
  background:#fff;
}
.buttons {
  display:flex;
  gap:10px;
  justify-content:center;
  flex-wrap:wrap;
  margin:12px 0;
}
button {
  background:#000;
  color:#00ff9c;
  border:1px solid #00ff9c;
  padding:8px 16px;
  cursor:pointer;
}
button:hover {
  background:#00ff9c;
  color:#000;
}
.highlight {
  background:red;
  color:#fff;
  font-weight:bold;
}
</style>
</head>
<body>

<div class="container">
<h2>🧪 Raw2PoC</h2>

<form method="post">
<textarea name="raw" placeholder="POST /cgi/logout HTTP/1.1
Host: example.com
User-Agent: PoC-Test

param1=value1&param2=value2">{{ raw or '' }}</textarea>

<div class="buttons">
<button type="submit">تحليل الطلب</button>
</div>
</form>

{% if pid %}

<div class="section">
<b>Method:</b>
<div class="box">{{ method }}</div>
</div>

<div class="section">
<b>Target:</b>
<div class="box">{{ url }}</div>
</div>

<div class="section">
<b>Headers:</b>
<div class="box">{% for k,v in headers.items() -%}
{{k}}: {{v}}
{% endfor %}</div>
</div>

<div class="section">
<b>Body:</b>
<div class="box">{{ body or "-" }}</div>
</div>

<div class="buttons">
<button onclick="execReq()">🚀 تنفيذ الطلب</button>
<button onclick="sendReq()">📡 جلب الطلب</button>
<button onclick="copyLink()">🔗 نسخ رابط التنفيذ</button>
<button onclick="exportPoC()">💾 تحويله إلى ملف</button>
</div>

<div class="section">
<b>Response:</b>
</div>

<div id="respText" class="box"></div>
<iframe id="respFrame" style="display:none;"></iframe>

<div class="buttons">
<button onclick="showText()">عرض كنص</button>
<button onclick="showRender()">عرض كمشاهدة</button>
</div>

<input id="search" placeholder="بحث داخل الرسبونس" oninput="searchResp()">
<div id="count"></div>

<script>
let RAW_TEXT="", SAFE_TEXT="", HTML_BODY="";

function execReq(){
  window.open("/run/{{pid}}","_blank");
}

function sendReq(){
  fetch("/send/{{pid}}")
   .then(r=>r.json())
   .then(d=>{
     RAW_TEXT=d.full;
     HTML_BODY=d.body;
     SAFE_TEXT=RAW_TEXT
       .replace(/&/g,"&amp;")
       .replace(/</g,"&lt;")
       .replace(/>/g,"&gt;");
     respText.innerHTML=SAFE_TEXT;
     showText();
   });
}

function copyLink(){
 navigator.clipboard.writeText(location.origin+"/run/{{pid}}");
 alert("✔ تم النسخ");
}

function exportPoC(){
 window.open("/export/{{pid}}","_blank");
}

function showRender(){
 respFrame.srcdoc=HTML_BODY;
 respFrame.style.display="block";
 respText.style.display="none";
}

function showText(){
 respFrame.style.display="none";
 respText.style.display="block";
}

function searchResp(){
 let q=search.value;
 if(!q){
   respText.innerHTML=SAFE_TEXT;
   count.innerText="";
   return;
 }
 let re=new RegExp(q,"gi");
 let m=SAFE_TEXT.match(re);
 respText.innerHTML=SAFE_TEXT.replace(
   re,x=>"<span class='highlight'>"+x+"</span>"
 );
 count.innerText="🔎 عدد النتائج: "+(m?m.length:0);
}
</script>
{% endif %}
</div>
</body>
</html>
"""

def parse_raw(raw):
 lines=raw.splitlines()
 method,path,_=lines[0].split()
 headers={}
 host=""
 i=1
 for l in lines[1:]:
  if not l.strip(): break
  k,v=l.split(":",1)
  headers[k.strip()]=v.strip()
  if k.lower()=="host":
    host=v.strip()
  i+=1
 body="\n".join(lines[i+1:])
 return method.upper(),"https://"+host+path,headers,body

@app.route("/",methods=["GET","POST"])
def index():
 if request.method=="POST":
  raw=request.form["raw"]
  m,u,h,b=parse_raw(raw)
  pid=str(uuid.uuid4())
  POCS[pid]=dict(m=m,u=u,h=h,b=b)
  return render_template_string(
    HTML,
    raw=raw,
    pid=pid,
    url=u,
    headers=h,
    body=b,
    method=m
  )
 return render_template_string(HTML)

@app.route("/run/<pid>")
def run(pid):
 p=POCS[pid]
 return f"""<html><body onload="document.forms[0].submit()">
<form method="{p['m']}" action="{p['u']}"></form></body></html>"""

@app.route("/send/<pid>")
def send(pid):
 p=POCS[pid]
 h=dict(p["h"])
 h.pop("Host",None)
 r=requests.request(p["m"],p["u"],headers=h,data=p["b"],verify=False)
 full=f"Status: {r.status_code}\n\nHeaders:\n"
 for k,v in r.headers.items():
  full+=f"{k}: {v}\n"
 full+=f"\nBody:\n{r.text}"
 return jsonify(full=full, body=r.text)

@app.route("/export/<pid>")
def export(pid):
 p=POCS[pid]
 html=f"""<!doctype html>
<html>
<body>
<p>هذا الملف ينفّذ الطلب تلقائيًا عند الفتح.</p>
<form method="{p['m']}" action="{p['u']}"></form>
<script>document.forms[0].submit()</script>
</body>
</html>"""
 filename=f"poc_{pid}.html"
 r=make_response(html)
 r.headers["Content-Disposition"]=f'attachment; filename="{filename}"'
 r.headers["Content-Type"]="text/html; charset=utf-8"
 return r

if __name__=="__main__":
 app.run(debug=True)
