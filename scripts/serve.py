#!/usr/bin/env python3
"""Simplified local web UI for the Google Maps scraper — Python standard library only.

    python scripts/serve.py        ->  http://localhost:8765

The scraper's own UI (port 8080) asks for latitude/longitude/zoom/radius. This one asks for
"what" and "where" (e.g. "São Paulo, Brasil"), geocodes it via OpenStreetMap, runs the job,
and hands back a table + CSV. UI text is pt-BR; the rest of the kit stays in English.

Bound to 127.0.0.1 on purpose: there is no auth and the page shows scraped personal data.
"""
import csv, json, os, sys, threading, time, urllib.error, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Windows consoles default to cp1252 and crash on accents/symbols
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrape import (BASE, LEAD, build_job_body, create_job, download_rows,  # noqa: E402
                    enrich_socials, geocode_full, job_status, req)

PORT = int(os.environ.get("KIT_UI_PORT", "8765"))
HOST = "127.0.0.1"
MAX_TIME = 600

LOCK = threading.Lock()
JOBS = {}
ACTIVE_JOB_ID = None

PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Buscar empresas no Google Maps</title>
<style>
  :root {
    --bg:#f4f6fa; --card:#fff; --text:#0f172a; --muted:#64748b; --line:#e2e8f0;
    --accent:#2563eb; --accent-dk:#1d4ed8; --ok:#047857; --okbg:#ecfdf5;
    --err:#dc2626; --errbg:#fef2f2; --zebra:#fafbfd; --hover:#eff4ff; --head:#f8fafc;
    --shadow:0 1px 2px rgba(15,23,42,.04), 0 10px 30px rgba(15,23,42,.07);
  }
  * { box-sizing:border-box; }
  body { margin:0; padding:40px 20px 72px; background:var(--bg); color:var(--text);
         font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
         -webkit-font-smoothing:antialiased; }
  .wrap { max-width:1440px; margin:0 auto; }
  .narrow { max-width:860px; margin-left:auto; margin-right:auto; }

  .head { display:flex; align-items:center; gap:14px; margin-bottom:26px; }
  .logo { width:44px; height:44px; border-radius:13px; flex:none; display:grid; place-items:center;
          background:linear-gradient(135deg,#3b82f6,#1d4ed8);
          box-shadow:0 4px 14px rgba(37,99,235,.35); }
  .logo svg { width:22px; height:22px; fill:#fff; }
  h1 { font-size:22px; font-weight:700; letter-spacing:-.02em; margin:0; }
  .sub { color:var(--muted); margin:2px 0 0; font-size:14px; }

  .card { background:var(--card); border:1px solid var(--line); border-radius:16px;
          padding:28px; margin-bottom:18px; box-shadow:var(--shadow); }
  label { display:block; font-weight:600; margin-bottom:7px; font-size:14px; }
  input[type=text], select { width:100%; padding:12px 14px; font-size:15px; font-family:inherit;
    border:1px solid var(--line); border-radius:10px; background:#fff; color:var(--text);
    transition:border-color .15s, box-shadow .15s; }
  input[type=text]:hover, select:hover { border-color:#cbd5e1; }
  input[type=text]:focus, select:focus { outline:none; border-color:var(--accent);
    box-shadow:0 0 0 3px rgba(37,99,235,.15); }
  .field { margin-bottom:20px; }
  .hint { font-size:13px; color:var(--muted); margin-top:7px; }
  .hint.ok { color:var(--ok); font-weight:500; }
  .hint.err { color:var(--err); }
  .timer { font-variant-numeric:tabular-nums; font-size:14px; color:var(--muted);
           background:var(--head); border:1px solid var(--line); border-radius:999px;
           padding:3px 12px; }

  button { padding:13px 32px; font-size:15px; font-weight:600; font-family:inherit; border:0;
           border-radius:10px; background:var(--accent); color:#fff; cursor:pointer;
           box-shadow:0 2px 8px rgba(37,99,235,.28); transition:background .15s, transform .05s; }
  button:hover:not(:disabled) { background:var(--accent-dk); }
  button:active:not(:disabled) { transform:translateY(1px); }
  button:disabled { opacity:.4; cursor:not-allowed; box-shadow:none; }

  details { border-top:1px solid var(--line); padding-top:18px; margin-bottom:20px; }
  summary { cursor:pointer; font-weight:600; color:var(--muted); font-size:14px;
            list-style:none; display:flex; align-items:center; gap:7px; }
  summary::-webkit-details-marker { display:none; }
  summary::before { content:"▸"; transition:transform .15s; font-size:11px; }
  details[open] summary::before { transform:rotate(90deg); }
  details .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                  gap:18px; margin-top:18px; }
  .check { display:flex; gap:10px; align-items:flex-start; }
  .check input { margin-top:3px; width:16px; height:16px; accent-color:var(--accent); }
  .check label { font-weight:500; margin:0; }
  .check .hint { margin-top:3px; }

  .banner { padding:14px 18px; border-radius:12px; background:var(--errbg); color:var(--err);
            margin-bottom:18px; font-size:14px; border:1px solid #fecaca; }
  .bar { height:6px; background:var(--line); border-radius:999px; overflow:hidden; margin:16px 0 10px; }
  .bar span { display:block; height:100%; width:35%; border-radius:999px;
              background:linear-gradient(90deg,#60a5fa,var(--accent));
              animation:slide 1.5s cubic-bezier(.4,0,.2,1) infinite; }
  @keyframes slide { 0%{margin-left:-35%} 100%{margin-left:100%} }

  .row-between { display:flex; justify-content:space-between; align-items:center; gap:16px;
                 flex-wrap:wrap; }
  #resultCard { padding:22px 22px 8px; }
  #resultCount { font-size:17px; letter-spacing:-.01em; }
  #resultCount .dim { color:var(--muted); font-weight:400; font-size:15px; }
  a.dl { display:inline-block; padding:11px 22px; border-radius:10px; background:var(--accent);
         color:#fff; text-decoration:none; font-weight:600; font-size:14px;
         box-shadow:0 2px 8px rgba(37,99,235,.28); }
  a.dl:hover { background:var(--accent-dk); }

  /* ── results table ─────────────────────────────────────────────── */
  .scroll { overflow:auto; max-height:72vh; margin-top:16px;
            border:1px solid var(--line); border-radius:12px; }
  table { width:100%; border-collapse:separate; border-spacing:0; font-size:13.5px; }
  th, td { text-align:left; padding:11px 14px; border-bottom:1px solid var(--line);
           vertical-align:top; }
  thead th { position:sticky; top:0; z-index:2; background:var(--head); white-space:nowrap;
             font-size:11.5px; text-transform:uppercase; letter-spacing:.5px;
             color:var(--muted); font-weight:600; }
  tbody tr:last-child td { border-bottom:0; }
  tbody tr:nth-child(even) td { background:var(--zebra); }
  tbody tr:hover td { background:var(--hover); }
  td a { color:var(--accent); text-decoration:none; }
  td a:hover { text-decoration:underline; }
  .dim { color:#cbd5e1; }

  /* keep the company name in view while scrolling sideways */
  .c-name { position:sticky; left:0; z-index:1; font-weight:600; background:#fff;
            min-width:210px; max-width:260px; border-right:1px solid var(--line); }
  thead .c-name { z-index:3; background:var(--head); }
  tbody tr:nth-child(even) .c-name { background:var(--zebra); }
  tbody tr:hover .c-name { background:var(--hover); }

  .c-phone { white-space:nowrap; }
  .c-cat { min-width:130px; max-width:170px; }
  .c-addr { min-width:240px; max-width:320px; color:var(--muted); font-size:13px; }
  .c-num { text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }
  .c-email, .c-site, .c-soc { max-width:190px; white-space:nowrap;
                              overflow:hidden; text-overflow:ellipsis; }
  .rating { font-weight:600; }
  .rating::before { content:"★ "; color:#f59e0b; font-weight:400; }

  .hide { display:none; }
  footer { color:var(--muted); font-size:12.5px; text-align:center; margin-top:32px; }

  @media (max-width:640px) {
    body { padding:24px 14px 56px; }
    .card { padding:20px; border-radius:14px; }
    .scroll { max-height:66vh; }
  }
</style>
</head>
<body>
<div class="wrap">
  <div class="head narrow">
    <div class="logo">
      <svg viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>
    </div>
    <div>
      <h1>Buscar empresas no Google Maps</h1>
      <p class="sub">Diga o que você procura e em que cidade. O resto a gente resolve.</p>
    </div>
  </div>

  <div id="offline" class="banner hide narrow"></div>

  <div class="card narrow" id="formCard">
    <div class="field">
      <label for="what">O que você procura?</label>
      <input type="text" id="what" placeholder="restaurantes, academias, dentistas…" autocomplete="off">
    </div>

    <div class="field">
      <label for="where">Onde?</label>
      <input type="text" id="where" placeholder="São Paulo, Brasil" autocomplete="off">
      <div class="hint" id="whereHint">Cidade e país. Ex.: "São Paulo, Brasil" ou "Lisboa, Portugal".</div>
    </div>

    <details>
      <summary>Opções avançadas</summary>
      <div class="grid">
        <div>
          <label for="depth">Resultados por busca</label>
          <select id="depth">
            <option value="3">Poucos — mais rápido</option>
            <option value="5" selected>Padrão — recomendado</option>
            <option value="10">Muitos — mais lento</option>
            <option value="20">Máximo — bem lento</option>
          </select>
        </div>
        <div>
          <label for="lang">Idioma dos resultados</label>
          <select id="lang">
            <option value="pt" selected>Português</option>
            <option value="en">Inglês</option>
            <option value="es">Espanhol</option>
          </select>
        </div>
      </div>
      <div class="grid">
        <div class="check">
          <input type="checkbox" id="email" checked>
          <label for="email">Buscar e-mails<br><span class="hint">Visita o site de cada empresa. Deixa a busca um pouco mais lenta.</span></label>
        </div>
        <div class="check">
          <input type="checkbox" id="socials">
          <label for="socials">Buscar redes sociais<br><span class="hint">Instagram, Facebook e LinkedIn. Bem mais lento e nem toda empresa tem.</span></label>
        </div>
      </div>
    </details>

    <button id="go" disabled>Buscar</button>
    <div class="hint" id="formErr"></div>
  </div>

  <div class="card narrow hide" id="progressCard">
    <div class="row-between">
      <strong id="phaseText">Criando a busca…</strong>
      <span class="timer" id="elapsed">0s</span>
    </div>
    <div class="bar"><span></span></div>
    <div class="hint">Pode deixar esta aba aberta. Buscas grandes levam alguns minutos.</div>
  </div>

  <div class="card hide" id="resultCard">
    <div class="row-between">
      <strong id="resultCount"></strong>
      <a class="dl hide" id="download" href="#">Baixar CSV</a>
    </div>
    <div class="scroll"><table id="table"></table></div>
  </div>

  <footer>
    Dados do Google Maps. Telefones e e-mails são dados pessoais — use conforme a LGPD/GDPR.
  </footer>
</div>

<script>
const $ = id => document.getElementById(id);

function esc(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
}
const dim = () => '<span class="dim">\\u2014</span>';

// scraped values are untrusted — never let a non-http scheme reach an href
function safeUrl(v) {
  let u = String(v || "").trim();
  if (!u) return "";
  if (!/^https?:\\/\\//i.test(u)) {
    if (/^[a-z][a-z0-9+.\\-]*:/i.test(u)) return "";
    u = "https://" + u;
  }
  return u;
}
function link(url, text) {
  return '<a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer" title="'
       + esc(url) + '">' + esc(text) + '</a>';
}
function fmtSite(v) {
  const u = safeUrl(v);
  if (!u) return dim();
  return link(u, u.replace(/^https?:\\/\\//i, "").replace(/^www\\./i, "").replace(/\\/.*$/, ""));
}
function fmtEmail(v) {
  const all = String(v || "").split(/[,;\\s]+/).filter(Boolean);
  if (!all.length) return dim();
  const extra = all.length > 1 ? ' +' + (all.length - 1) : '';
  return '<a href="mailto:' + esc(all[0]) + '" title="' + esc(all.join(", ")) + '">'
       + esc(all[0]) + '</a>' + extra;
}
function fmtSocial(v) {
  const u = safeUrl(v);
  if (!u) return dim();
  const handle = u.replace(/\\/+$/, "").split("/").pop().split("?")[0];
  return link(u, handle ? "@" + handle : "abrir");
}
function fmtRating(v) {
  const n = parseFloat(v);
  return n ? '<span class="rating">' + n.toFixed(1).replace(".", ",") + '</span>' : dim();
}
function fmtCount(v) {
  const n = parseInt(v, 10);
  return n ? n.toLocaleString("pt-BR") : dim();
}

const COLS = {
  title:         { label:"Empresa",    cls:"c-name" },
  phone:         { label:"Telefone",   cls:"c-phone" },
  emails:        { label:"E-mail",     cls:"c-email", fmt:fmtEmail },
  website:       { label:"Site",       cls:"c-site",  fmt:fmtSite },
  category:      { label:"Categoria",  cls:"c-cat" },
  address:       { label:"Endereço",   cls:"c-addr" },
  review_rating: { label:"Nota",       cls:"c-num",   fmt:fmtRating },
  review_count:  { label:"Avaliações", cls:"c-num",   fmt:fmtCount },
  instagram:     { label:"Instagram",  cls:"c-soc",   fmt:fmtSocial },
  facebook:      { label:"Facebook",   cls:"c-soc",   fmt:fmtSocial },
  linkedin:      { label:"LinkedIn",   cls:"c-soc",   fmt:fmtSocial },
};

let coords = null, lastPlace = "", timer = null, ticker = null, startedAt = 0;

function fmt(s) {
  s = Math.max(0, Math.round(s));
  const m = Math.floor(s / 60);
  return m ? m + "m " + String(s % 60).padStart(2, "0") + "s" : s + "s";
}

function stopTimers() { clearInterval(timer); clearInterval(ticker); }

async function api(path, opts) {
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({ ok:false, error:"resposta inválida do servidor" }));
  return { status:r.status, data };
}

function setGo() { $("go").disabled = !(coords && $("what").value.trim()); }

(async function health() {
  const { data } = await api("/api/health");
  if (!data.ok) {
    $("offline").textContent = "O scraper não está respondendo. Rode  docker compose up -d  na pasta do projeto e recarregue esta página.";
    $("offline").classList.remove("hide");
    $("formCard").style.opacity = .5;
    $("formCard").style.pointerEvents = "none";
  }
})();

$("what").addEventListener("input", setGo);

$("where").addEventListener("blur", async () => {
  const place = $("where").value.trim();
  if (!place || place === lastPlace) return;
  lastPlace = place; coords = null; setGo();
  $("whereHint").className = "hint";
  $("whereHint").textContent = "Procurando esse lugar…";
  const { data } = await api("/api/geocode", {
    method:"POST", headers:{ "Content-Type":"application/json" },
    body: JSON.stringify({ place })
  });
  if (data.ok) {
    coords = { lat:data.lat, lon:data.lon };
    $("whereHint").className = "hint ok";
    $("whereHint").textContent = "\\u2713 " + data.display_name;
  } else {
    $("whereHint").className = "hint err";
    $("whereHint").textContent = data.error;
  }
  setGo();
});

$("go").addEventListener("click", async () => {
  $("go").disabled = true;
  $("formErr").className = "hint";
  $("formErr").textContent = "";
  $("resultCard").classList.add("hide");
  $("progressCard").classList.remove("hide");
  $("phaseText").textContent = "Criando a busca…";

  const { status, data } = await api("/api/job", {
    method:"POST", headers:{ "Content-Type":"application/json" },
    body: JSON.stringify({
      what: $("what").value.trim(), where: $("where").value.trim(),
      lat: coords.lat, lon: coords.lon, depth: Number($("depth").value),
      lang: $("lang").value, email: $("email").checked, socials: $("socials").checked
    })
  });
  if (!data.ok) {
    $("progressCard").classList.add("hide");
    $("formErr").className = "hint err";
    $("formErr").textContent = data.error + (status === 409 ? " Espere ela terminar." : "");
    setGo();
    return;
  }
  $("phaseText").textContent = "Buscando no Google Maps…";
  startedAt = Date.now();
  $("elapsed").textContent = "0s";
  ticker = setInterval(() => {
    $("elapsed").textContent = fmt((Date.now() - startedAt) / 1000);
  }, 1000);
  timer = setInterval(() => poll(data.id), 3000);
});

async function poll(id) {
  const { data } = await api("/api/status?id=" + encodeURIComponent(id));
  if (data.phase === "working") {
    $("phaseText").textContent = "Buscando no Google Maps…";
  } else if (data.phase === "processing") {
    const s = data.socials;
    $("phaseText").textContent = s && s.total
      ? "Buscando redes sociais… " + s.done + "/" + s.total + " sites"
      : "Organizando os resultados…";
  } else if (data.phase === "done") {
    stopTimers();
    show(id, data.count, data.elapsed);
  } else if (data.phase === "failed") {
    stopTimers();
    $("progressCard").classList.add("hide");
    $("formErr").className = "hint err";
    $("formErr").textContent = data.error + " (após " + fmt(data.elapsed) + ")";
    setGo();
  }
}

async function show(id, count, elapsed) {
  $("progressCard").classList.add("hide");
  $("resultCard").classList.remove("hide");
  setGo();
  if (!count) {
    $("resultCount").textContent = "Nenhuma empresa encontrada em " + fmt(elapsed)
      + ". Tente um termo mais amplo ou outra cidade.";
    $("download").classList.add("hide");
    $("table").innerHTML = "";
    return;
  }
  $("resultCount").innerHTML = "<strong>" + count + "</strong> "
    + (count === 1 ? "empresa encontrada" : "empresas encontradas")
    + ' <span class="dim">\\u00b7 ' + esc(fmt(elapsed)) + "</span>";
  $("download").href = "/api/download?id=" + encodeURIComponent(id);
  $("download").classList.remove("hide");

  const { data } = await api("/api/results?id=" + encodeURIComponent(id));
  const cols = data.fields.map(f => COLS[f] || { label:f, cls:"" });
  const head = "<thead><tr>" + cols.map(c =>
    '<th class="' + c.cls + '">' + esc(c.label) + "</th>").join("") + "</tr></thead>";
  const body = "<tbody>" + data.rows.map(r => "<tr>" + data.fields.map((f, i) => {
    const c = cols[i], v = r[f] || "";
    return '<td class="' + c.cls + '">' + (c.fmt ? c.fmt(v) : (v ? esc(v) : dim())) + "</td>";
  }).join("") + "</tr>").join("") + "</tbody>";
  $("table").innerHTML = head + body;
}
</script>
</body>
</html>"""


def finalize(job_id):
    """Runs in a background thread once the scraper reports the job is done."""
    job = JOBS[job_id]
    try:
        fields = list(LEAD)
        rows = [{k: r.get(k, "") for k in fields} for r in download_rows(job_id)]
        if job["socials"]:
            with LOCK:
                job["stotal"] = sum(1 for r in rows if r.get("website"))

            def tick(done, total):
                with LOCK:
                    job["sdone"], job["stotal"] = done, total

            enrich_socials(rows, progress=tick)
            fields += ["instagram", "facebook", "linkedin"]

        path = os.path.abspath(f"resultados-{job_id[:8]}.csv")
        # utf-8-sig so Excel opens accented Portuguese correctly
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        with LOCK:
            job.update(fields=fields, rows=rows, csv_path=path, phase="done",
                       elapsed=time.time() - job["started"])
        print(f"  {len(rows)} resultados em {job['elapsed']:.0f}s -> {path}")
    except Exception as e:
        with LOCK:
            job.update(phase="failed", error=f"Erro ao baixar os resultados: {e}",
                       elapsed=time.time() - job["started"])


class UIHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the console readable; we print the events that matter

    # ── plumbing ─────────────────────────────────────────────────────────────
    def _send(self, code, body, ctype, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode(),
                   "application/json; charset=utf-8")

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def _query(self, key):
        return urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get(key, [""])[0]

    # ── routes ───────────────────────────────────────────────────────────────
    def do_GET(self):
        route = urllib.parse.urlparse(self.path).path
        try:
            if route == "/":
                self._send(200, PAGE.encode(), "text/html; charset=utf-8")
            elif route == "/favicon.ico":
                self._send(204, b"", "image/x-icon")
            elif route == "/api/health":
                self._json({"ok": self._scraper_up()})
            elif route == "/api/status":
                self._status()
            elif route == "/api/results":
                self._results()
            elif route == "/api/download":
                self._download()
            else:
                self._json({"ok": False, "error": "rota não encontrada"}, 404)
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    def do_POST(self):
        route = urllib.parse.urlparse(self.path).path
        try:
            if route == "/api/geocode":
                self._geocode()
            elif route == "/api/job":
                self._create()
            else:
                self._json({"ok": False, "error": "rota não encontrada"}, 404)
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    # ── handlers ─────────────────────────────────────────────────────────────
    def _scraper_up(self):
        try:
            req("GET", "/api/v1/jobs")
            return True
        except Exception:
            return False

    def _geocode(self):
        place = (self._body().get("place") or "").strip()
        if not place:
            return self._json({"ok": False, "error": "Digite uma cidade."})
        hit = geocode_full(place)
        if not hit:
            return self._json({"ok": False,
                               "error": "Não encontramos esse lugar. Tente \"Cidade, Estado, País\"."})
        self._json({"ok": True, **hit})

    def _create(self):
        global ACTIVE_JOB_ID
        b = self._body()
        what, where = (b.get("what") or "").strip(), (b.get("where") or "").strip()
        if not what or not b.get("lat") or not b.get("lon"):
            return self._json({"ok": False, "error": "Preencha o que você procura e onde."})

        with LOCK:
            running = JOBS.get(ACTIVE_JOB_ID, {}).get("phase") in ("working", "processing")
        if running:
            return self._json({"ok": False, "error": "Já existe uma busca rodando."}, 409)

        # lat/lon only centres the map — the term is what actually steers the search
        keyword = f"{what} {where}"
        body = build_job_body([keyword], b["lat"], b["lon"], depth=b.get("depth", 5),
                              email=bool(b.get("email", True)), max_time=MAX_TIME,
                              lang=b.get("lang", "pt"), name="scrape-ui")
        try:
            job_id = create_job(body)
        except urllib.error.HTTPError as e:
            return self._json({"ok": False,
                               "error": f"O scraper recusou a busca (HTTP {e.code})."}, 502)
        except Exception:
            return self._json({"ok": False,
                               "error": "Scraper fora do ar. Rode  docker compose up -d  e tente de novo."}, 502)

        with LOCK:
            JOBS[job_id] = {"phase": "working", "socials": bool(b.get("socials")),
                            "fields": [], "rows": [], "csv_path": "", "started": time.time(),
                            "elapsed": 0, "sdone": 0, "stotal": 0, "error": ""}
            ACTIVE_JOB_ID = job_id
        print(f"▶ busca criada: \"{keyword}\" (job {job_id[:8]})")
        self._json({"ok": True, "id": job_id})

    def _status(self):
        job_id = self._query("id")
        with LOCK:
            job = JOBS.get(job_id)
            phase = job and job["phase"]
        if not job:
            return self._json({"phase": "failed", "error": "Busca desconhecida."}, 404)

        if phase == "working":
            gone = False
            try:
                st = job_status(job_id)
            except urllib.error.HTTPError as e:
                st, gone = None, e.code == 404
            except Exception:
                st = None  # scraper momentarily unreachable — keep waiting
            if gone:
                with LOCK:
                    job.update(phase="failed", error="Essa busca não existe mais no scraper.")
            elif st == "failed":
                with LOCK:
                    job.update(phase="failed", error="A busca falhou. Isso costuma ser bloqueio "
                               "temporário do Google — espere alguns minutos e tente de novo.")
            elif st != "ok" and time.time() - job["started"] > MAX_TIME + 120:
                # the scraper leaves crashed jobs in "working" forever; don't spin with it
                with LOCK:
                    job.update(phase="failed", error="A busca estourou o tempo limite sem retornar "
                               "nada. Veja o que houve com:  docker compose logs --tail 30")
            elif st == "ok":
                with LOCK:
                    start = job["phase"] == "working"
                    if start:
                        job["phase"] = "processing"
                if start:
                    threading.Thread(target=finalize, args=(job_id,), daemon=True).start()

        with LOCK:
            # the failure branches above ran in this same request, so freezing here is accurate
            if job["phase"] in ("done", "failed") and not job["elapsed"]:
                job["elapsed"] = time.time() - job["started"]
            self._json({"phase": job["phase"], "count": len(job["rows"]),
                        "socials": {"done": job["sdone"], "total": job["stotal"]},
                        "elapsed": job["elapsed"] or time.time() - job["started"],
                        "error": job["error"]})

    def _results(self):
        with LOCK:
            job = JOBS.get(self._query("id"))
            if not job or job["phase"] != "done":
                return self._json({"fields": [], "rows": []}, 404)
            self._json({"fields": job["fields"], "rows": job["rows"]})

    def _download(self):
        with LOCK:
            job = JOBS.get(self._query("id"))
            path = job and job["csv_path"]
        if not path or not os.path.exists(path):
            return self._json({"ok": False, "error": "arquivo não encontrado"}, 404)
        with open(path, "rb") as f:
            data = f.read()
        self._send(200, data, "text/csv; charset=utf-8",
                   {"Content-Disposition": f'attachment; filename="{os.path.basename(path)}"'})


def main():
    print(f"▶ Interface simplificada em  http://localhost:{PORT}")
    print(f"  scraper: {BASE}   (Ctrl+C para parar)")
    try:
        ThreadingHTTPServer((HOST, PORT), UIHandler).serve_forever()
    except KeyboardInterrupt:
        print("\n  encerrado.")
    except OSError as e:
        sys.exit(f"✗ Não consegui abrir a porta {PORT}: {e}\n"
                 f"  Use outra porta com  KIT_UI_PORT=8766 python scripts/serve.py")


if __name__ == "__main__":
    main()
