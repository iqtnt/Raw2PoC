# 🧪 Raw2PoC

Raw2PoC is a lightweight Flask-based tool that converts **raw HTTP requests** into:

- 🚀 Executable PoC URLs  
- 🔗 Shareable execution links  
- 💾 Auto-submitting HTML PoC files  

Designed for **bug bounty hunters** and **security researchers**.

---

## ✨ Features

- Paste full raw HTTP request (Burp / Proxy style)
- Automatically parses:
  - Method
  - Target URL
  - Headers
  - Body
- Generate:
  - One-click execution link
  - Downloadable HTML PoC
- Clean RTL-friendly UI
- No external dependencies

---

## 📥 Example Input

```bash
POST /cgi/logout HTTP/1.1
Host: example.com
User-Agent: PoC-Test

param1=value1&param2=value2
```

## 🚀 Usage

```bash
git clone https://github.com/iqtnt/Raw2PoC.git
cd Raw2PoC
python3 app.py
```
