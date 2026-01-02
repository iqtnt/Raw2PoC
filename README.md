# 🧪 Raw2PoC

Raw2PoC is a lightweight web tool designed for security researchers and bug bounty hunters to transform raw HTTP requests into executable Proof‑of‑Concepts (PoCs).

The tool allows you to paste a raw HTTP request and instantly analyze, execute, replay, and export it as a standalone PoC.

Raw2PoC focuses on simplicity, clarity, and real‑world vulnerability reproduction workflows.

---

## Features

- Parse raw HTTP requests (GET, POST, and more)
- Extract target URL, headers, and request body
- Execute requests directly from the interface
- Generate executable PoC links
- Export PoCs as standalone auto‑submitting HTML files
- Replay requests and inspect full server responses
- Minimal, fast, and bug‑bounty friendly

---

## Use Cases

- Open Redirect validation
- Host Header Injection testing
- SSRF and request replay
- Vulnerability reproduction
- Sharing reproducible PoCs with program owners
- Converting Burp Suite raw requests into live PoCs

---

## Example Workflow

1. Capture a raw HTTP request from Burp Suite
2. Paste it into Raw2PoC
3. Analyze the request
4. Execute or export the PoC
5. Share the generated PoC link or file

---

## Disclaimer

This tool is intended for educational and authorized security testing purposes only.

Use Raw2PoC only on systems you own or have explicit permission to test.
The author is not responsible for any misuse or illegal activity.

## 🚀 Install

```bash
git clone https://github.com/iqtnt/Raw2PoC.git
cd Raw2PoC
python3 app.py
```
