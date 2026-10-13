/**
 * Cloudflare Worker — SSP3-Forte order handler
 *
 * Bindings required (set in Cloudflare dashboard → Worker → Settings):
 *   KV namespace:  ORDER_COUNTER  (for daily order sequence)
 *   Secret:        RESEND_API_KEY (from resend.com dashboard)
 *
 * Allowed origin: https://ssp3forte.com
 */

const RESEND_API = 'https://api.resend.com/emails';

// ── Payment / shipping label helpers ────────────────────────────────────────
function paymentLabel(val, lang) {
  const map = {
    'deposito':    { pt: 'Depósito ou Transferência bancária',             en: 'Bank deposit or transfer' },
    'ctt':         { pt: 'CTT à cobrança postal',                        en: 'CTT cash on delivery (postal)' },
    'mbway':       { pt: 'MBway (sem portes)',                            en: 'MBway (no shipping fee)' },
    'deposito-br': { pt: 'Depósito ou transferência bancária',            en: 'Bank deposit or transfer' },
  };
  return map[val]?.[lang] ?? (lang === 'en' ? 'To be confirmed' : 'A confirmar');
}
function shippingLabel(val, lang) {
  const map = {
    'portugal':      { pt: 'Correios registado à cobrança — Portugal (+€4,99)', en: 'Registered mail COD — Portugal (+€4.99)' },
    'europa':        { pt: 'Correios registado — Europa (+€9,00)',               en: 'Registered mail — Europe (+€9.00)' },
    'correio-aereo': { pt: 'Correio aéreo — Entrega em mão',                    en: 'Air mail — Home delivery' },
  };
  return map[val]?.[lang] ?? (lang === 'en' ? 'To be confirmed' : 'A confirmar');
}

// ── Product catalogue ────────────────────────────────────────────────────────
const PRODUCTS = {
  '1x':    { namePT: 'SSP3-Forte · 1 frasco',       nameEN: 'SSP3-Forte · 1 bottle',       qty: 1, pricePT: '€29,95', priceEN: '€29.95', code: 'SSP3-1X'    },
  '3x':    { namePT: 'SSP3-Forte · Kit 3 frascos',  nameEN: 'SSP3-Forte · 3-bottle kit',   qty: 3, pricePT: '€80,86', priceEN: '€80.86', code: 'SSP3-3X'    },
  '1x-br': { namePT: 'SSP3-Forte · 1 frasco',       nameEN: 'SSP3-Forte · 1 bottle',       qty: 1, pricePT: 'R$210',  priceEN: 'R$210',  code: 'SSP3-1X-BR' },
  '3x-br': { namePT: 'SSP3-Forte · Kit 3 frascos',  nameEN: 'SSP3-Forte · 3-bottle kit',   qty: 3, pricePT: 'R$567',  priceEN: 'R$567',  code: 'SSP3-3X-BR' },
};

// ── Country code helper ──────────────────────────────────────────────────────
function countryCode(country, lang) {
  const c = (country || '').toLowerCase();
  if (c.includes('brasil') || c.includes('brazil'))         return 'BR';
  if (c.includes('portugal'))                                return 'PT';
  if (c.includes('angola'))                                  return 'AO';
  if (c.includes('moçambique') || c.includes('mozambique')) return 'MZ';
  if (c.includes('cabo verde') || c.includes('cape verde')) return 'CV';
  if (c.includes('timor'))                                   return 'TL';
  if (lang === 'en')                                         return 'EU';
  return (c.trim().slice(0, 2) || 'XX').toUpperCase();
}

// ── Order number generator ───────────────────────────────────────────────────
// Format: YYYYMMDDnn SSP3-Forte(CC)  e.g. 2026061801 SSP3-Forte(PT)
async function generateOrderNumber(cc) {
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  try {
    const res  = await fetch(`https://api.counterapi.dev/v1/ssp3forte-orders/${date}/up`);
    const data = await res.json();
    const seq  = String(data.count).padStart(2, '0');
    return `${date}${seq} SSP3-Forte(${cc})`;
  } catch {
    const seq = String(Math.floor(Math.random() * 90) + 10);
    return `${date}${seq} SSP3-Forte(${cc})`;
  }
}

// ── Shared email chrome ──────────────────────────────────────────────────────
const headerHTML = `
<div style="background:#0d3d2b;padding:24px 32px;">
  <div style="float:right;margin-left:16px;">
    <img src="https://ssp3forte.com/frasco.jpg" alt="SSP3-Forte" style="height:56px;display:block;">
  </div>
  <div style="color:#c9a84c;font-size:11px;letter-spacing:.15em;text-transform:uppercase;margin-bottom:4px;">Naturalfarma</div>
  <div style="color:#fff;font-family:Georgia,serif;font-size:22px;font-weight:bold;">SSP3-Forte</div>
  <div style="clear:both;"></div>
</div>`;

const footerPT = `
<div style="margin-top:32px;padding-top:16px;border-top:1px solid #e8f4ee;color:#7a7d72;font-size:13px;">
  <p style="margin:0 0 8px;">Com os melhores cumprimentos,<br>
  <strong style="color:#0d3d2b;">Naturalfarma</strong></p>
  <p style="margin:0;font-size:11px;">
    <a href="https://www.ssp3forte.com" style="color:#1a6645;">ssp3forte.com</a> ·
    encomendas@ssp3forte.com
  </p>
</div>`;

const footerEN = `
<div style="margin-top:32px;padding-top:16px;border-top:1px solid #e8f4ee;color:#7a7d72;font-size:13px;">
  <p style="margin:0 0 8px;">Kind regards,<br>
  <strong style="color:#0d3d2b;">Naturalfarma</strong></p>
  <p style="margin:0;font-size:11px;">
    <a href="https://www.ssp3forte.com" style="color:#1a6645;">ssp3forte.com</a> ·
    orders@ssp3forte.com
  </p>
</div>`;

function addressBlock(d) {
  return [d.name, d.address,
    [d.postal, d.city].filter(Boolean).join(', '),
    d.state, d.country, d.email, d.phone || '—']
    .filter(Boolean).join('<br>');
}

// ── PT / BR confirmation email ───────────────────────────────────────────────
function buildEmailPT(d, orderNum, p) {
  const isBR = d.product.endsWith('-br') || (d.country || '').toLowerCase().includes('brasil');
  const addrLabel = isBR ? 'Endereço de entrega' : 'Morada para entrega';
  return `<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="margin:0;padding:0;background:#f5f5f0;font-family:Georgia,serif;">
<div style="max-width:600px;margin:32px auto;background:#fff;">
  ${headerHTML}
  <div style="padding:32px;">
    <p style="margin-top:0;">Caro ${d.name},</p>
    <p>Recebemos o seu pedido e entraremos em contacto brevemente para confirmar os detalhes de pagamento e envio.</p>

    <div style="background:#e8f4ee;border-left:3px solid #1a6645;padding:14px 18px;margin:24px 0;">
      <strong>Pedido n.º ${orderNum}</strong>
    </div>

    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px;margin-bottom:24px;">
      <tr style="background:#0d3d2b;color:#fff;">
        <th align="left"  style="padding:8px 12px;">Produto</th>
        <th align="center" style="padding:8px 12px;">Qtd.</th>
        <th align="right"  style="padding:8px 12px;">Preço unit.</th>
        <th align="right"  style="padding:8px 12px;">Total</th>
      </tr>
      <tr style="border-bottom:1px solid #e0ddd5;">
        <td style="padding:10px 12px;">${p.namePT}<br><span style="font-size:11px;color:#7a7d72;">Ref: ${p.code}</span></td>
        <td align="center" style="padding:10px 12px;">${p.qty}</td>
        <td align="right"  style="padding:10px 12px;">${p.pricePT}</td>
        <td align="right"  style="padding:10px 12px;">${p.pricePT}</td>
      </tr>
      <tr>
        <td colspan="3" align="right" style="padding:8px 12px;font-weight:bold;">Envio:</td>
        <td align="right" style="padding:8px 12px;">A confirmar</td>
      </tr>
      <tr style="background:#e8f4ee;font-weight:bold;">
        <td colspan="3" align="right" style="padding:8px 12px;">Total:</td>
        <td align="right" style="padding:8px 12px;">${p.pricePT} + envio</td>
      </tr>
    </table>

    <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;margin-bottom:24px;">
      <tr><td style="padding:3px 0;color:#7a7d72;width:170px;">Forma de pagamento:</td><td>${paymentLabel(d.paymentMethod, 'pt')}</td></tr>
      <tr><td style="padding:3px 0;color:#7a7d72;">Método de envio:</td><td>${shippingLabel(d.shippingMethod, 'pt')}</td></tr>
    </table>

    <div style="font-size:14px;margin-bottom:24px;">
      <div style="font-weight:bold;color:#0d3d2b;border-bottom:1px solid #e8f4ee;padding-bottom:6px;margin-bottom:10px;">${addrLabel}</div>
      ${addressBlock(d)}
    </div>

    ${d.notes ? `<div style="font-size:14px;margin-bottom:16px;"><strong>Comentários adicionais:</strong><br>${d.notes}</div>` : ''}
    ${footerPT}
  </div>
</div></body></html>`;
}

// ── EN confirmation email ────────────────────────────────────────────────────
function buildEmailEN(d, orderNum, p) {
  return `<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="margin:0;padding:0;background:#f5f5f0;font-family:Georgia,serif;">
<div style="max-width:600px;margin:32px auto;background:#fff;">
  ${headerHTML}
  <div style="padding:32px;">
    <p style="margin-top:0;">Dear ${d.name},</p>
    <p>We have received your order and will be in touch shortly to confirm payment and shipping details.</p>

    <div style="background:#e8f4ee;border-left:3px solid #1a6645;padding:14px 18px;margin:24px 0;">
      <strong>Order no. ${orderNum}</strong>
    </div>

    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px;margin-bottom:24px;">
      <tr style="background:#0d3d2b;color:#fff;">
        <th align="left"  style="padding:8px 12px;">Product</th>
        <th align="center" style="padding:8px 12px;">Qty</th>
        <th align="right"  style="padding:8px 12px;">Unit price</th>
        <th align="right"  style="padding:8px 12px;">Total</th>
      </tr>
      <tr style="border-bottom:1px solid #e0ddd5;">
        <td style="padding:10px 12px;">${p.nameEN}<br><span style="font-size:11px;color:#7a7d72;">Ref: ${p.code}</span></td>
        <td align="center" style="padding:10px 12px;">${p.qty}</td>
        <td align="right"  style="padding:10px 12px;">${p.priceEN}</td>
        <td align="right"  style="padding:10px 12px;">${p.priceEN}</td>
      </tr>
      <tr>
        <td colspan="3" align="right" style="padding:8px 12px;font-weight:bold;">Shipping:</td>
        <td align="right" style="padding:8px 12px;">To be confirmed</td>
      </tr>
      <tr style="background:#e8f4ee;font-weight:bold;">
        <td colspan="3" align="right" style="padding:8px 12px;">Total:</td>
        <td align="right" style="padding:8px 12px;">${p.priceEN} + shipping</td>
      </tr>
    </table>

    <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;margin-bottom:24px;">
      <tr><td style="padding:3px 0;color:#7a7d72;width:170px;">Payment method:</td><td>${paymentLabel(d.paymentMethod, 'en')}</td></tr>
      <tr><td style="padding:3px 0;color:#7a7d72;">Shipping method:</td><td>${shippingLabel(d.shippingMethod, 'en')}</td></tr>
    </table>

    <div style="font-size:14px;margin-bottom:24px;">
      <div style="font-weight:bold;color:#0d3d2b;border-bottom:1px solid #e8f4ee;padding-bottom:6px;margin-bottom:10px;">Delivery address</div>
      ${addressBlock(d)}
    </div>

    ${d.notes ? `<div style="font-size:14px;margin-bottom:16px;"><strong>Additional comments:</strong><br>${d.notes}</div>` : ''}
    ${footerEN}
  </div>
</div></body></html>`;
}

// ── Internal notification to business ───────────────────────────────────────
function buildInternalEmail(d, orderNum, p, clientEmailError) {
  const rows = [
    ['Order', orderNum], ['Name', d.name], ['Email', d.email], ['Phone', d.phone || '—'],
    ['DOB', d.dob || '—'], ['Country', d.country], ['Product', `${p.namePT} (${p.code})`],
    ['Address', d.address], ['Postal', d.postal], ['City', d.city],
    ['State', d.state || '—'], ['Notes', d.notes || '—'],
    ['Payment', paymentLabel(d.paymentMethod, 'pt')], ['Shipping', shippingLabel(d.shippingMethod, 'pt')],
  ].map(([k, v]) => `<tr><td style="padding:4px 12px;color:#555;width:140px;">${k}</td><td style="padding:4px 12px;">${v}</td></tr>`).join('');

  // O cliente nao recebeu a confirmacao -- normalmente porque escreveu mal o
  // email. A encomenda e valida; falta e contactar a pessoa, por telefone se
  // houver numero. Antes destes avisos, um caso destes perdia a encomenda toda.
  const aviso = clientEmailError ? `
  <div style="border:2px solid #b00020;background:#fff4f4;padding:12px 16px;margin-bottom:16px;">
    <div style="color:#b00020;font-weight:bold;margin-bottom:6px;">
      A confirmação não chegou ao cliente — é preciso contactá-lo
    </div>
    <div style="font-size:13px;line-height:1.6;color:#333;">
      O pedido foi registado, mas o email de confirmação para
      <b>${d.email}</b> falhou. O endereço pode estar mal escrito.
      ${d.phone ? `Telefone indicado: <b>${d.phone}</b>.` : 'Não foi indicado telefone.'}
      <div style="color:#777;font-size:12px;margin-top:6px;">Erro: ${clientEmailError}</div>
    </div>
  </div>` : '';

  return `<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="font-family:sans-serif;font-size:14px;">
<div style="max-width:560px;margin:24px auto;">
  ${aviso}
  <h2 style="color:#0d3d2b;margin-bottom:4px;">Novo pedido: ${orderNum}</h2>
  <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;border:1px solid #e0e0e0;">
    ${rows}
  </table>
</div></body></html>`;
}

// ── Resend API call ──────────────────────────────────────────────────────────
async function sendEmail(apiKey, { from, to, subject, html }) {
  const res = await fetch(RESEND_API, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from, to: [to], subject, html }),
  });
  if (!res.ok) throw new Error(`Resend ${res.status}: ${await res.text()}`);
  return res.json();
}

// ── CORS headers ─────────────────────────────────────────────────────────────
const CORS = {
  'Access-Control-Allow-Origin':  'https://ssp3forte.com',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', ...CORS } });

// ── Funil: registo de eventos ────────────────────────────────────────────────
// Guarda uma linha por passo do funil, para se poder ver ONDE as pessoas param
// em vez de so saber quantas encomendaram. A Cloudflare Web Analytics conta
// paginas e o site e uma pagina so, logo nao serve para isto.
//
// Nunca pode estragar uma encomenda: todas as escritas passam por aqui e
// engolem o erro. Sem base de dados ligada, o site funciona exactamente como
// antes e isto nao faz nada.
const EVENTOS_DO_CLIENTE = ['view', 'order_view', 'form_start', 'submit'];

async function registar(env, { name, lang, session, detail }) {
  if (!env.FUNNEL) return false;              // D1 ainda nao ligada
  const agora = new Date().toISOString();
  try {
    await env.FUNNEL.prepare(
      'INSERT INTO events (ts, day, name, lang, session, detail) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(agora, agora.slice(0, 10), name,
           (lang || '').slice(0, 8) || null,
           (session || '').slice(0, 40) || null,
           detail ? String(detail).slice(0, 300) : null).run();
    return true;
  } catch (err) {
    console.error('registo de evento falhou:', err);
    return false;
  }
}

// ── Funil: pagina de estatisticas ────────────────────────────────────────────
// Protegida por um token, porque sao numeros de negocio num endereco publico:
//     npx wrangler secret put STATS_TOKEN
const PASSOS = [
  ['view',        'Abriu o site'],
  ['order_view',  'Chegou ao formulário'],
  ['form_start',  'Começou a preencher'],
  ['submit',      'Carregou em enviar'],
  ['order_ok',    'Encomenda registada'],
  ['order_fail',  'Falhou no envio'],
];

function statsHTML(linhas, porDia, falhas, dias) {
  const base = linhas.view || 0;
  const pct = n => base ? (100 * n / base).toFixed(1) + '%' : '—';

  const funil = PASSOS.map(([k, rotulo], i) => {
    const n = linhas[k] || 0;
    const anterior = i > 0 ? (linhas[PASSOS[i - 1][0]] || 0) : null;
    const queda = (i > 0 && anterior) ? (100 * (anterior - n) / anterior).toFixed(0) + '%' : '';
    const largura = base ? Math.max(1, Math.round(240 * n / base)) : 1;
    const cor = k === 'order_fail' ? '#b00020' : '#1a6645';
    return `<tr>
      <td>${rotulo}</td>
      <td style="text-align:right;font-variant-numeric:tabular-nums;"><b>${n}</b></td>
      <td style="text-align:right;color:#777;">${pct(n)}</td>
      <td style="text-align:right;color:#b00020;">${k === 'order_fail' ? '' : queda}</td>
      <td><div style="width:${largura}px;height:11px;background:${cor};"></div></td>
    </tr>`;
  }).join('');

  const tabelaDias = porDia.length ? porDia.map(d => `<tr>
      <td>${d.day}</td>
      ${PASSOS.map(([k]) => `<td style="text-align:right;font-variant-numeric:tabular-nums;">${d[k] || 0}</td>`).join('')}
    </tr>`).join('') : `<tr><td colspan="7" style="color:#777;">ainda sem dados</td></tr>`;

  const listaFalhas = falhas.length ? falhas.map(f =>
    `<tr><td>${f.n}×</td><td style="color:#555;">${f.detail || '—'}</td></tr>`).join('')
    : `<tr><td colspan="2" style="color:#777;">nenhuma falha registada</td></tr>`;

  return `<!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Funil — SSP3-Forte</title>
<style>
  body { font-family: system-ui, sans-serif; font-size: 14px; color: #222;
         max-width: 820px; margin: 2rem auto; padding: 0 1rem; }
  h1 { font-size: 1.3rem; color: #0d3d2b; margin-bottom: .2rem; }
  h2 { font-size: 1rem; color: #0d3d2b; margin-top: 2rem; }
  p.sub { color: #777; margin-top: 0; }
  table { border-collapse: collapse; width: 100%; margin-top: .6rem; }
  th, td { padding: 5px 9px; border-bottom: 1px solid #eee; text-align: left; }
  th { font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: #777; }
  .nota { color: #777; font-size: 12px; line-height: 1.6; margin-top: 2rem;
          border-top: 1px solid #eee; padding-top: 1rem; }
</style></head><body>
<h1>Funil de encomendas</h1>
<p class="sub">Últimos ${dias} dias. A coluna "queda" é a percentagem que se perde do passo anterior.</p>

<table>
  <tr><th>Passo</th><th style="text-align:right">Visitas</th><th style="text-align:right">Do total</th>
      <th style="text-align:right">Queda</th><th></th></tr>
  ${funil}
</table>

<h2>Por dia</h2>
<table>
  <tr><th>Dia</th>${PASSOS.map(([, r]) => `<th style="text-align:right">${r.split(' ')[0]}</th>`).join('')}</tr>
  ${tabelaDias}
</table>

<h2>Falhas de envio</h2>
<table><tr><th>Quantas</th><th>Motivo</th></tr>${listaFalhas}</table>

<p class="nota">
  Cada número é o total de <b>visitas distintas</b> que chegaram ao passo, não de cliques.<br>
  Não se guarda IP, user-agent, email nem nada no dispositivo de quem visita: o
  identificador de visita é aleatório, vive na memória do browser e desaparece ao
  fechar a página. Por isso isto não precisa de aviso de cookies.<br>
  Uma pessoa que abra o site duas vezes conta como duas visitas.
</p>
</body></html>`;
}

/* Conta VISITAS DISTINTAS por passo numa janela de dias, nao numero de eventos:
   quem carrega duas vezes em enviar nao pode aparecer como duas pessoas. */
async function contarPassos(env, desde, ate) {
  const r = await env.FUNNEL.prepare(
    `SELECT name, COUNT(DISTINCT COALESCE(session, CAST(id AS TEXT))) AS n
       FROM events WHERE day >= ? AND day <= ? GROUP BY name`).bind(desde, ate).all();
  const out = {};
  for (const linha of r.results || []) out[linha.name] = linha.n;
  return out;
}

const diaISO = ms => new Date(ms).toISOString().slice(0, 10);

async function servirStats(env, url) {
  if (!env.STATS_TOKEN)
    return new Response('STATS_TOKEN nao definido. Correr: npx wrangler secret put STATS_TOKEN',
                        { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
  if (url.searchParams.get('t') !== env.STATS_TOKEN)
    return new Response('Not found', { status: 404 });
  if (!env.FUNNEL)
    return new Response('Base de dados FUNNEL nao ligada. Ver worker/schema.sql.',
                        { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });

  const dias = Math.min(Math.max(parseInt(url.searchParams.get('dias') || '30', 10) || 30, 1), 365);
  const desde = diaISO(Date.now() - dias * 86400000);
  const hoje = diaISO(Date.now());

  const linhas = await contarPassos(env, desde, hoje);

  const diario = await env.FUNNEL.prepare(
    `SELECT day, name, COUNT(DISTINCT COALESCE(session, CAST(id AS TEXT))) AS n
       FROM events WHERE day >= ? GROUP BY day, name ORDER BY day DESC`).bind(desde).all();
  const mapa = new Map();
  for (const r of diario.results || []) {
    if (!mapa.has(r.day)) mapa.set(r.day, { day: r.day });
    mapa.get(r.day)[r.name] = r.n;
  }

  const falhas = await env.FUNNEL.prepare(
    `SELECT detail, COUNT(*) AS n FROM events
      WHERE day >= ? AND name = 'order_fail' GROUP BY detail ORDER BY n DESC LIMIT 20`)
    .bind(desde).all();

  return new Response(statsHTML(linhas, [...mapa.values()], falhas.results || [], dias),
                      { headers: { 'Content-Type': 'text/html; charset=utf-8',
                                   'Cache-Control': 'no-store' } });
}

// ── Relatorio semanal por email ──────────────────────────────────────────────
// Disparado pelo Cron Trigger de wrangler.toml (segundas, 8h UTC). Compara os
// ultimos 7 dias com os 7 anteriores, porque um numero isolado nao diz nada:
// o que interessa e se esta a subir ou a descer.
function setaVariacao(agora, antes) {
  if (!antes) return agora ? '<span style="color:#1a6645;">novo</span>' : '—';
  const d = Math.round(100 * (agora - antes) / antes);
  if (d === 0) return '<span style="color:#777;">igual</span>';
  const cor = d > 0 ? '#1a6645' : '#b00020';
  return `<span style="color:${cor};">${d > 0 ? '+' : ''}${d}%</span>`;
}

function emailSemanalHTML(semana, anterior, de, a) {
  const base = semana.view || 0;
  const linhas = PASSOS.map(([k, rotulo]) => {
    const n = semana[k] || 0;
    const pct = base ? (100 * n / base).toFixed(1) + '%' : '—';
    return `<tr>
      <td style="padding:6px 12px;border-bottom:1px solid #eee;">${rotulo}</td>
      <td style="padding:6px 12px;border-bottom:1px solid #eee;text-align:right;"><b>${n}</b></td>
      <td style="padding:6px 12px;border-bottom:1px solid #eee;text-align:right;color:#777;">${pct}</td>
      <td style="padding:6px 12px;border-bottom:1px solid #eee;text-align:right;">${setaVariacao(n, anterior[k] || 0)}</td>
    </tr>`;
  }).join('');

  const encomendas = semana.order_ok || 0;
  const taxa = base ? (100 * encomendas / base).toFixed(1) + '%' : '—';
  const falhas = semana.order_fail || 0;

  return `${headerHTML}
<div style="max-width:560px;margin:24px auto;font-family:sans-serif;font-size:14px;color:#222;">
  <h2 style="color:#0d3d2b;margin-bottom:2px;">Resumo semanal do site</h2>
  <p style="color:#777;margin-top:0;">${de} a ${a}. A última coluna compara com os sete dias anteriores.</p>

  <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;border:1px solid #e0e0e0;">
    <tr style="background:#f6f6f4;">
      <th style="padding:6px 12px;text-align:left;font-size:12px;color:#777;">Passo</th>
      <th style="padding:6px 12px;text-align:right;font-size:12px;color:#777;">Visitas</th>
      <th style="padding:6px 12px;text-align:right;font-size:12px;color:#777;">Do total</th>
      <th style="padding:6px 12px;text-align:right;font-size:12px;color:#777;">vs. semana anterior</th>
    </tr>
    ${linhas}
  </table>

  <p style="margin-top:18px;line-height:1.7;">
    <b>${base}</b> visitas deram <b>${encomendas}</b> encomenda${encomendas === 1 ? '' : 's'} — taxa de <b>${taxa}</b>.
    ${falhas ? `<span style="color:#b00020;"><b>${falhas}</b> envio${falhas === 1 ? '' : 's'} falhou nesta semana: ver a página de estatísticas.</span>` : ''}
  </p>

  <p style="color:#777;font-size:12px;line-height:1.6;border-top:1px solid #eee;padding-top:12px;margin-top:20px;">
    Com poucas visitas por semana, uma encomenda a mais ou a menos mexe muito na
    percentagem. Olhar para a tendência de várias semanas, não para o número de uma.<br>
    Cada número são visitas distintas, não cliques. Não se guarda IP, email nem nada
    no dispositivo de quem visita.
  </p>
</div>`;
}

async function enviarRelatorioSemanal(env) {
  if (!env.FUNNEL) { console.error('relatorio semanal: FUNNEL nao ligada'); return; }
  if (!env.RESEND_API_KEY) { console.error('relatorio semanal: sem RESEND_API_KEY'); return; }

  const agora = Date.now();
  const inicioSemana = diaISO(agora - 7 * 86400000);
  const fimSemana = diaISO(agora - 1 * 86400000);          // ate ontem: hoje esta incompleto
  const inicioAnterior = diaISO(agora - 14 * 86400000);
  const fimAnterior = diaISO(agora - 8 * 86400000);

  try {
    const semana = await contarPassos(env, inicioSemana, fimSemana);
    const anterior = await contarPassos(env, inicioAnterior, fimAnterior);

    // Nada aconteceu: nao vale a pena enviar email nenhum.
    if (!Object.keys(semana).length) {
      console.log('relatorio semanal: sem dados, nao enviado');
      return;
    }

    await sendEmail(env.RESEND_API_KEY, {
      from: 'Naturalfarma <encomendas@ssp3forte.com>',
      to: 'encomendas@ssp3forte.com',
      subject: `Resumo semanal ssp3forte — ${semana.view || 0} visitas, ${semana.order_ok || 0} encomendas`,
      html: emailSemanalHTML(semana, anterior, inicioSemana, fimSemana),
    });
    console.log('relatorio semanal enviado');
  } catch (err) {
    console.error('relatorio semanal falhou:', err);
  }
}

// ── Main handler ─────────────────────────────────────────────────────────────
export default {
  // Cron Trigger de wrangler.toml: segundas as 8h UTC.
  async scheduled(event, env, ctx) {
    ctx.waitUntil(enviarRelatorioSemanal(env));
  },

  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

    if (request.method === 'GET' && url.pathname === '/stats') return servirStats(env, url);

    if (request.method !== 'POST')   return new Response('Method not allowed', { status: 405 });

    // Evento do funil. Responde sempre 204, mesmo que o registo falhe: isto nunca
    // deve dar erro visivel no site nem atrasar quem esta a comprar.
    if (url.pathname === '/event') {
      let e = {};
      try { e = await request.json(); } catch { /* corpo invalido: ignorar */ }
      if (EVENTOS_DO_CLIENTE.includes(e.name)) {
        await registar(env, { name: e.name, lang: e.lang, session: e.session });
      }
      return new Response(null, { status: 204, headers: CORS });
    }

    let d;
    try { d = await request.json(); }
    catch { return json({ error: 'Invalid JSON' }, 400); }

    if (!d.name || !d.email || !d.product) {
      await registar(env, { name: 'order_fail', lang: d.lang, session: d.session,
                            detail: 'campos obrigatorios em falta' });
      return json({ error: 'Missing required fields' }, 400);
    }

    const product = PRODUCTS[d.product];
    if (!product) {
      await registar(env, { name: 'order_fail', lang: d.lang, session: d.session,
                            detail: 'produto desconhecido' });
      return json({ error: 'Unknown product' }, 400);
    }

    const isEN    = d.lang === 'en';
    const cc      = countryCode(d.country, d.lang);
    const orderNum = await generateOrderNumber(cc);
    const from    = isEN ? 'Naturalfarma <orders@ssp3forte.com>' : 'Naturalfarma <encomendas@ssp3forte.com>';
    const subject = isEN
      ? `Your order no. ${orderNum}`
      : `O seu pedido n.º ${orderNum}`;

    // A confirmacao ao cliente e o aviso interno sao enviados em separado, e por
    // esta ordem de prioridade: o aviso interno e o registo da encomenda, a
    // confirmacao e cortesia.
    //
    // Antes os dois estavam no mesmo try, em sequencia, e o sendEmail lanca erro
    // em qualquer resposta que nao seja OK. Bastava o cliente escrever mal o
    // proprio email para o primeiro envio falhar, o segundo nunca correr e a
    // encomenda desaparecer sem ninguem saber -- o cliente via um alerta de erro
    // e ia-se embora depois de preencher 18 campos. Nao voltar a juntar os dois.
    let clientEmailError = null;
    try {
      await sendEmail(env.RESEND_API_KEY, {
        from, to: d.email, subject,
        html: isEN ? buildEmailEN(d, orderNum, product) : buildEmailPT(d, orderNum, product),
      });
    } catch (err) {
      console.error('confirmacao ao cliente falhou:', err);
      clientEmailError = err.message;
    }

    try {
      await sendEmail(env.RESEND_API_KEY, {
        from: isEN ? 'orders@ssp3forte.com' : 'encomendas@ssp3forte.com',
        to: isEN ? 'orders@ssp3forte.com' : 'encomendas@ssp3forte.com',
        subject: clientEmailError
          ? `Novo pedido ${orderNum} — ${d.name} — CONTACTAR: confirmacao nao chegou`
          : `Novo pedido ${orderNum} — ${d.name}`,
        html: buildInternalEmail(d, orderNum, product, clientEmailError),
      });
    } catch (err) {
      // Falhou o registo da encomenda. Aqui sim vale a pena pedir ao cliente que
      // tente de novo, porque nao ha nada guardado em lado nenhum.
      console.error('aviso interno falhou:', err);
      await registar(env, { name: 'order_fail', lang: d.lang, session: d.session,
                            detail: err.message });
      return json({ error: 'Email sending failed', detail: err.message }, 500);
    }

    // A encomenda esta registada. Dizer sucesso ao cliente mesmo que a
    // confirmacao nao lhe tenha chegado: a pagina avisa-o disso a parte, e repetir
    // a submissao so geraria encomendas duplicadas.
    await registar(env, { name: 'order_ok', lang: d.lang, session: d.session,
                          detail: clientEmailError ? 'confirmacao ao cliente falhou' : null });
    return json({ success: true, orderNum, confirmationSent: !clientEmailError });
  },
};
