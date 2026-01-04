from flask import Flask, request, render_template_string, make_response, jsonify
import uuid, requests, urllib3

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
  direction:ltr;
}
.container {
  width:900px;
  max-width:95%;
  margin:25px auto;
  border:1px solid #00ff9c;
  padding:20px;
}
textarea,input,select {
  width:100%;
  background:#000;
  color:#00ff9c;
  border:1px solid #00ff9c;
  padding:8px;
  box-sizing:border-box;
}
textarea { height:200px; }
.section { margin-top:18px; }
.box {
  border:1px solid #00ff9c;
  padding:10px;
  white-space:pre;
  overflow:auto;
  max-height:260px;
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
.row {
  display:flex;
  gap:15px;
  margin-bottom:12px;
}
.col { flex:1; }
.highlight {
  background:red;
  color:#fff;
}
</style>
</head>
<body>

<div class="container">
<h2>🧪 Raw2PoC</h2>

<form method="post">

<div class="row">
  <div class="col">
    <label>Scheme</label>
    <select name="scheme">
      <option value="https" {% if scheme=='https' %}selected{% endif %}>https</option>
      <option value="http" {% if scheme=='http' %}selected{% endif %}>http</option>
    </select>
  </div>
</div>

<textarea name="raw" placeholder="GET / HTTP/2
Host: example.com
X-Forwarded-Host: //interact.sh

param=value">{{ raw or '' }}</textarea>

<div class="buttons">
<button type="submit">Analyze</button>
</div>
</form>

{% if pid %}

<div class="section">
<b>Method</b>
<div class="box">{{ method }}</div>
</div>

<div class="section">
<b>Target</b>
<div class="box">{{ url }}</div>
</div>

<div class="section">
<b>Headers</b>
<div class="box">{% for k,v in headers.items() -%}
{{k}}: {{v}}
{% endfor %}</div>
</div>

<div class="section">
<b>Body</b>
<div class="box">{{ body or "-" }}</div>
</div>

<div class="buttons">
<button onclick="execReq()">🚀 Execute</button>
<button onclick="sendReq()">📡 Send</button>
<button onclick="copyLink()">🔗 Copy link</button>
<button onclick="exportPoC()">💾 Export</button>
</div>

<div class="section"><b>Response</b></div>
<div id="respText" class="box"></div>
<iframe id="respFrame" style="display:none;"></iframe>

<div class="buttons">
<button onclick="showText()">Text</button>
<button onclick="showRender()">Render</button>
</div>

<input id="search" placeholder="Search response" oninput="searchResp()">
<div id="count"></div>

<script>
let RAW="", SAFE="", HTMLB="";

function execReq(){ window.open("/run/{{pid}}","_blank"); }

function sendReq(){
 fetch("/send/{{pid}}")
  .then(r=>r.json())
  .then(d=>{
    if(d.error){ respText.innerText=d.error; return; }
    RAW=d.full;
    HTMLB=d.body;
    SAFE=RAW.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
    respText.innerHTML=SAFE;
  });
}

function copyLink(){
 navigator.clipboard.writeText(location.origin+"/run/{{pid}}");
 alert("Copied");
}

function exportPoC(){ window.open("/export/{{pid}}","_blank"); }

function showRender(){
 respFrame.srcdoc=HTMLB;
 respFrame.style.display="block";
 respText.style.display="none";
}

function showText(){
 respFrame.style.display="none";
 respText.style.display="block";
}

function searchResp(){
 let q=search.value;
 if(!q){ respText.innerHTML=SAFE; count.innerText=""; return; }
 let re=new RegExp(q,"gi");
 let m=SAFE.match(re);
 respText.innerHTML=SAFE.replace(re,x=>"<span class='highlight'>"+x+"</span>");
 count.innerText="Matches: "+(m?m.length:0);
}
</script>

{% endif %}
</div>
</body>
</html>
"""

def parse_raw(raw):
    lines = raw.splitlines()
    if not lines:
        raise ValueError("Empty request")

    # Parse request line
    method, path, _ = lines[0].split()

    headers = {}
    host = None
    i = 1
    for l in lines[1:]:
        if not l.strip():
            break
        if ":" in l:
            k, v = l.split(":", 1)
            headers[k.strip()] = v.strip()
            if k.lower() == "host":
                host = v.strip()
        i += 1

    body = "\n".join(lines[i+1:])
    return method.upper(), path, headers, body, host

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        raw = request.form["raw"]
        scheme = request.form["scheme"]

        method, path, headers, body, host = parse_raw(raw)
        if not host:
            return "Host header missing", 400

        url = f"{scheme}://{host}{path}"

        pid = str(uuid.uuid4())
        POCS[pid] = dict(m=method, u=url, h=headers, b=body)

        return render_template_string(
            HTML,
            raw=raw,
            pid=pid,
            method=method,
            url=url,
            headers=headers,
            body=body,
            scheme=scheme
        )

    return render_template_string(HTML, scheme="https")

@app.route("/run/<pid>")
def run(pid):
    p = POCS[pid]
    return f"<html><body onload='document.forms[0].submit()'><form method='{p['m']}' action='{p['u']}'></form></body></html>"

@app.route("/send/<pid>")
def send(pid):
    p = POCS[pid]
    h = dict(p["h"])
    h.pop("Host", None)

    try:
        r = requests.request(
            p["m"],
            p["u"],
            headers=h,
            data=p["b"],
            verify=False,
            timeout=10,
            allow_redirects=False
        )
        r.encoding = r.apparent_encoding
    except requests.RequestException as e:
        return jsonify(error=str(e))

    full = f"Status: {r.status_code}\n\nHeaders:\n"
    for k, v in r.headers.items():
        full += f"{k}: {v}\n"
    full += f"\nBody:\n{r.text}"

    return jsonify(full=full, body=r.text)

@app.route("/export/<pid>")
def export(pid):
    p = POCS[pid]
    html = f"""<!doctype html>
<html><body>
<form method="{p['m']}" action="{p['u']}"></form>
<script>document.forms[0].submit()</script>
</body></html>"""
    r = make_response(html)
    r.headers["Content-Disposition"] = 'attachment; filename="poc.html"'
    r.headers["Content-Type"] = "text/html; charset=utf-8"
    return r

if __name__ == "__main__":
    app.run(debug=True)
