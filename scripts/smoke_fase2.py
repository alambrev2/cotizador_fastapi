import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

BASE = os.getenv("SMOKE_BASE", "http://127.0.0.1:8765/api/v1")
USER = os.getenv("SMOKE_USER", "admin")
PASS = os.getenv("SMOKE_PASS", "")

passed = 0
failed = 0


def req(method, path, data=None, token=None, form=False):
    url = BASE + path
    body = None
    headers = {}
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8"))
        except Exception:
            detail = {}
        return e.code, detail


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name} {extra}")


if not PASS:
    print("Define SMOKE_PASS con la contraseña del usuario de prueba (ver scripts/create_initial_users.py).")
    sys.exit(1)

# 1) Health
try:
    with urllib.request.urlopen("http://127.0.0.1:8765/health") as resp:
        print(f"health -> {resp.status}")
except Exception as e:
    print(f"FAIL health: {e}")
    sys.exit(1)

# 2) Login (el token viaja en cookie httpOnly)
login_body = urllib.parse.urlencode({"username": USER, "password": PASS}).encode("utf-8")
try:
    resp = urllib.request.urlopen(urllib.request.Request(
        BASE + "/auth/login", data=login_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    ))
    code = resp.status
    set_cookie = resp.headers.get("Set-Cookie", "")
    resp.read()
except urllib.error.HTTPError as e:
    code = e.code
    set_cookie = e.headers.get("Set-Cookie", "") if e.headers else ""
check("login admin 200", code == 200, f"(got {code})")
token = None
for part in set_cookie.split(";"):
    part = part.strip()
    if part.startswith("access_token="):
        token = part[len("access_token="):]
        break
check("token presente en cookie", bool(token), f"(cookie: {set_cookie[:80]})")
if not token:
    sys.exit(1)

# 3) Coherencia quote: quote_id=1 (cliente 56) con cliente_id=55 -> 400
code, body = req("POST", "/payments/", {"quote_id": 1, "cliente_id": 55, "monto": "100"}, token)
check("quote coherencia -> 400", code == 400, f"(got {code}: {body})")

# 4) 404 quote inexistente
code, body = req("POST", "/payments/", {"quote_id": 9999, "monto": "100"}, token)
check("quote 404", code == 404, f"(got {code})")

# 5) Coherencia cargo: cargo_id=1 (cliente 56) con cliente_id=55 -> 400
code, body = req("POST", "/payments/", {"cargo_id": 1, "cliente_id": 55, "monto": "100"}, token)
check("cargo coherencia -> 400", code == 400, f"(got {code}: {body})")

# 6) Sobrepago cargo: cargo_id=1 saldo 1200, monto 5000 -> 400
code, body = req("POST", "/payments/", {"cargo_id": 1, "monto": "5000"}, token)
check("cargo sobrepago -> 400", code == 400, f"(got {code}: {body})")

# 7) Monto negativo -> rechazado (400 por regla propia o 422 por schema)
code, body = req("POST", "/payments/", {"quote_id": 1, "monto": "-50"}, token)
check("monto negativo -> rechazado", code in (400, 422), f"(got {code}: {body})")

# 8) Abono global sin cliente -> 400 (ningún vinculo)
code, body = req("POST", "/payments/", {"monto": "100"}, token)
check("sin vinculo -> 400", code == 400, f"(got {code}: {body})")

# 9) Abono global cliente inexistente -> 404
code, body = req("POST", "/payments/", {"cliente_id": 9999, "monto": "100"}, token)
check("abono global cliente 404", code == 404, f"(got {code}: {body})")

# 10) Sin datos insertados: lista de pagos sigue vacía
code, body = req("GET", "/payments/", token=token)
count = len(body) if isinstance(body, list) else -1
check("sin pagos insertados", count == 0, f"(got {count})")

print(f"\nRESULTADO: {passed} pass, {failed} fail")
sys.exit(1 if failed else 0)
