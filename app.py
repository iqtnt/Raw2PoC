from flask import Flask, request, render_template_string, make_response
import uuid

app = Flask(__name__)
POCS = {}

HTML = """
<!doctype html>
<html lang="ar">
<head>
<meta charset="utf-8">
<title>Raw HTTP → PoC</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { box-sizing: border-box; }

body {
  margin: 0;
  background: #0b0b0b;
  color: #00ff9c;
  font-family: monospace;
}

.container {
  width: 900px;
  max-width: 95%;
  margin: 30px auto;
  background: #000;
  border: 1px solid #00ff9c;
  padding: 20px;
}

textarea {
  width: 100%;
  height: 200px;
  background: #000;
  color: #00ff9c;
  border: 1px solid #00ff9c;
  padding: 10px;
  resize: vertical;
}

.box {
  background: #000;
  border: 1px solid #00ff9c;
  padding: 10px;
  max-height: 180px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin-top: 10px;
}

.buttons {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
}

button {
  padding: 10px 20px;
  font-size: 15px;
  cursor: pointer;
  background: #000;
  color: #00ff9c;
  border: 1px solid #00ff9c;
}

button:hover {
  background: #00ff9c;
  color: #000;
}

.error {
  background: #330000;
  border: 1px solid #ff4d4d;
  color: #ffb3b3;
  padding: 10px;
  margin-top: 15px;
}

h2, h3 {
  margin-top: 20px;
}

hr {
  border: 1px solid #00ff9c;
  margin: 25px 0;
}

.msg {
  text-align: center;
  margin-top: 10px;
}
</style>
</head>
<body>

<div class="container">

<h2>🧪 Raw HTTP → Executable PoC</h2>

<form method="POST">
<textarea name="raw" placeholder="POST /path HTTP/1.1
Host: example.com

a=1&b=2">{{ raw or '' }}</textarea>

<div class="buttons">
  <button type="submit">تحليل الطلب</button>
</div>
</form>

{% if error %}
<div class="error">⚠ {{ error }}</div>
{% endif %}

{% if poc_id %}
<hr>

<h3>Target:</h3>
<div class="box">{{ url }}</div>

<h3>Headers:</h3>
{% if headers %}
<div class="box">{% for k,v in headers.items() %}{{ k }}: {{ v }}
{% endfor %}</div>
{% else %}
<div class="box">لا توجد Headers</div>
{% endif %}

<h3>Body:</h3>
<div class="box">{{ body }}</div>

<div class="buttons">
  <button onclick="window.location.href='/run/{{ poc_id }}'">🚀 تنفيذ الطلب</button>
  <button onclick="copyExec()">🔗 نسخ رابط التنفيذ</button>
  <button onclick="window.location.href='/export/{{ poc_id }}'">💾 تحويله إلى ملف</button>
</div>

<div id="msg" class="msg"></div>

<script>
function copyExec() {
  const link = window.location.origin + "/run/{{ poc_id }}";
  navigator.clipboard.writeText(link);
  document.getElementById("msg").innerText = "✔ تم نسخ رابط التنفيذ";
}
</script>
{% endif %}

</div>
</body>
</html>
"""

EXEC_HTML = """
<!doctype html>
<html>
<body onload="document.forms[0].submit()">
<form method="{{ method }}" action="{{ url }}">
{% for k,v in params %}
<input type="hidden" name="{{ k }}" value="{{ v }}">
{% endfor %}
</form>
</body>
</html>
"""

EXPORT_HTML = """
<!doctype html>
<html lang="ar">
<head>
<meta charset="utf-8">
<title>PoC</title>
</head>
<body onload="document.forms[0].submit()">
<form method="{{ method }}" action="{{ url }}">
{% for k,v in params %}
<input type="hidden" name="{{ k }}" value="{{ v }}">
{% endfor %}
</form>
</body>
</html>
"""

def parse_raw(raw):
    if not raw.strip():
        raise ValueError("الرجاء إدخال Raw HTTP Request")

    lines = raw.strip().splitlines()
    first = lines[0].split()

    if len(first) < 3:
        raise ValueError("السطر الأول غير صالح (POST /path HTTP/1.1)")

    method, path = first[0], first[1]
    headers = {}
    host = ""
    i = 1

    for line in lines[1:]:
        if line.strip() == "":
            break
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()
            if k.lower() == "host":
                host = v.strip()
        i += 1

    if not host:
        raise ValueError("الهيدر Host غير موجود")

    body = "\n".join(lines[i+1:]).strip()
    url = f"https://{host}{path}"
    return method.upper(), url, headers, body

@app.route("/", methods=["GET", "POST"])
def index():
    raw = ""
    error = None
    poc_id = None
    url = ""
    headers = {}
    body = ""

    if request.method == "POST":
        raw = request.form.get("raw", "")
        try:
            method, url, headers, body = parse_raw(raw)
            poc_id = str(uuid.uuid4())
            POCS[poc_id] = {
                "method": method,
                "url": url,
                "headers": headers,
                "body": body
            }
        except ValueError as e:
            error = str(e)

    return render_template_string(
        HTML,
        raw=raw,
        error=error,
        poc_id=poc_id,
        url=url,
        headers=headers,
        body=body
    )

@app.route("/run/<poc_id>")
def run(poc_id):
    poc = POCS.get(poc_id)
    if not poc:
        return "Invalid PoC", 404

    params = [
        (p.split("=", 1)[0], p.split("=", 1)[1])
        for p in poc["body"].split("&") if "=" in p
    ]

    return render_template_string(
        EXEC_HTML,
        method=poc["method"],
        url=poc["url"],
        params=params
    )

@app.route("/export/<poc_id>")
def export(poc_id):
    poc = POCS.get(poc_id)
    if not poc:
        return "Invalid PoC", 404

    params = [
        (p.split("=", 1)[0], p.split("=", 1)[1])
        for p in poc["body"].split("&") if "=" in p
    ]

    html = render_template_string(
        EXPORT_HTML,
        method=poc["method"],
        url=poc["url"],
        params=params
    )

    filename = f"poc_{poc_id[:8]}.html"

    resp = make_response(html)
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp

if __name__ == "__main__":
    app.run(debug=True)
