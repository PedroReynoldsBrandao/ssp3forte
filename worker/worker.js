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

// ── Product catalogue ────────────────────────────────────────────────────────
const PRODUCTS = {
  '1x':    { namePT: 'SSP3-Forte · 1 frasco',       nameEN: 'SSP3-Forte · 1 bottle',       qty: 1, pricePT: '€29,95', priceEN: '€29.95', code: 'SSP3-1X'    },
  '3x':    { namePT: 'SSP3-Forte · Kit 3 frascos',  nameEN: 'SSP3-Forte · 3-bottle kit',   qty: 3, pricePT: '€80,86', priceEN: '€80.86', code: 'SSP3-3X'    },
  '1x-br': { namePT: 'SSP3-Forte · 1 frasco',       nameEN: 'SSP3-Forte · 1 bottle',       qty: 1, pricePT: 'R$165',  priceEN: 'R$165',  code: 'SSP3-1X-BR' },
  '3x-br': { namePT: 'SSP3-Forte · Kit 3 frascos',  nameEN: 'SSP3-Forte · 3-bottle kit',   qty: 3, pricePT: 'R$445',  priceEN: 'R$445',  code: 'SSP3-3X-BR' },
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
// Format: YYYYMMDDnn SSP3-Forte(CC)  e.g. 2026061701 SSP3-Forte(PT)
async function generateOrderNumber(kv, cc) {
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, ''); // YYYYMMDD
  const key  = `counter_${date}`;
  const cur  = await kv.get(key);
  const next = cur ? parseInt(cur, 10) + 1 : 1;
  await kv.put(key, String(next), { expirationTtl: 90000 }); // ~25 h
  return `${date}${String(next).padStart(2, '0')} SSP3-Forte(${cc})`;
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
  return `<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f5f5f0;font-family:Georgia,serif;">
<div style="max-width:600px;margin:32px auto;background:#fff;">
  ${headerHTML}
  <div style="padding:32px;">
    <p style="margin-top:0;">Caro ${d.name},</p>
    <p>Obrigado pelo seu pedido no site <a href="https://www.ssp3forte.com" style="color:#1a6645;">www.ssp3forte.com</a>.
    Iremos contactá-lo no dia do envio da sua encomenda. Se pediu para pagar por depósito ou transferência bancária,
    enviaremos para o seu email os nossos dados bancários. Por favor, aguarde.</p>

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
      <tr><td style="padding:3px 0;color:#7a7d72;width:170px;">Forma de pagamento:</td><td>A confirmar</td></tr>
      <tr><td style="padding:3px 0;color:#7a7d72;">Método de envio:</td><td>A confirmar</td></tr>
    </table>

    <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;margin-bottom:24px;">
      <tr valign="top">
        <td style="padding-right:24px;width:50%;">
          <div style="font-weight:bold;color:#0d3d2b;border-bottom:1px solid #e8f4ee;padding-bottom:6px;margin-bottom:10px;">Morada de facturação</div>
          ${addressBlock(d)}
        </td>
        <td style="width:50%;">
          <div style="font-weight:bold;color:#0d3d2b;border-bottom:1px solid #e8f4ee;padding-bottom:6px;margin-bottom:10px;">Morada para entrega</div>
          ${addressBlock(d)}
        </td>
      </tr>
    </table>

    ${d.notes ? `<div style="font-size:14px;margin-bottom:16px;"><strong>Comentários adicionais:</strong><br>${d.notes}</div>` : ''}
    ${footerPT}
  </div>
</div></body></html>`;
}

// ── EN confirmation email ────────────────────────────────────────────────────
function buildEmailEN(d, orderNum, p) {
  return `<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f5f5f0;font-family:Georgia,serif;">
<div style="max-width:600px;margin:32px auto;background:#fff;">
  ${headerHTML}
  <div style="padding:32px;">
    <p style="margin-top:0;">Dear ${d.name},</p>
    <p>Thank you for your order at <a href="https://www.ssp3forte.com" style="color:#1a6645;">www.ssp3forte.com</a>.
    We will contact you on the day your order is dispatched. If you requested payment by bank deposit or transfer,
    we will send our bank details to your email. Please wait.</p>

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
      <tr><td style="padding:3px 0;color:#7a7d72;width:170px;">Payment method:</td><td>To be confirmed</td></tr>
      <tr><td style="padding:3px 0;color:#7a7d72;">Shipping method:</td><td>To be confirmed</td></tr>
    </table>

    <table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;margin-bottom:24px;">
      <tr valign="top">
        <td style="padding-right:24px;width:50%;">
          <div style="font-weight:bold;color:#0d3d2b;border-bottom:1px solid #e8f4ee;padding-bottom:6px;margin-bottom:10px;">Billing address</div>
          ${addressBlock(d)}
        </td>
        <td style="width:50%;">
          <div style="font-weight:bold;color:#0d3d2b;border-bottom:1px solid #e8f4ee;padding-bottom:6px;margin-bottom:10px;">Delivery address</div>
          ${addressBlock(d)}
        </td>
      </tr>
    </table>

    ${d.notes ? `<div style="font-size:14px;margin-bottom:16px;"><strong>Additional comments:</strong><br>${d.notes}</div>` : ''}
    ${footerEN}
  </div>
</div></body></html>`;
}

// ── Internal notification to business ───────────────────────────────────────
function buildInternalEmail(d, orderNum, p) {
  const rows = [
    ['Order', orderNum], ['Name', d.name], ['Email', d.email], ['Phone', d.phone || '—'],
    ['DOB', d.dob || '—'], ['Country', d.country], ['Product', `${p.namePT} (${p.code})`],
    ['Address', d.address], ['Postal', d.postal], ['City', d.city],
    ['State', d.state || '—'], ['Notes', d.notes || '—'],
  ].map(([k, v]) => `<tr><td style="padding:4px 12px;color:#555;width:140px;">${k}</td><td style="padding:4px 12px;">${v}</td></tr>`).join('');
  return `<!DOCTYPE html><html><body style="font-family:sans-serif;font-size:14px;">
<div style="max-width:560px;margin:24px auto;">
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

// ── Main handler ─────────────────────────────────────────────────────────────
export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
    if (request.method !== 'POST')   return new Response('Method not allowed', { status: 405 });

    let d;
    try { d = await request.json(); }
    catch { return json({ error: 'Invalid JSON' }, 400); }

    if (!d.name || !d.email || !d.product)
      return json({ error: 'Missing required fields' }, 400);

    const product = PRODUCTS[d.product];
    if (!product) return json({ error: 'Unknown product' }, 400);

    const isEN    = d.lang === 'en';
    const cc      = countryCode(d.country, d.lang);
    const orderNum = await generateOrderNumber(env.ORDER_COUNTER, cc);
    const from    = isEN ? 'orders@ssp3forte.com' : 'encomendas@ssp3forte.com';
    const subject = isEN
      ? `Your order no. ${orderNum}`
      : `O seu pedido n.º ${orderNum}`;

    try {
      await sendEmail(env.RESEND_API_KEY, {
        from, to: d.email, subject,
        html: isEN ? buildEmailEN(d, orderNum, product) : buildEmailPT(d, orderNum, product),
      });
      await sendEmail(env.RESEND_API_KEY, {
        from: isEN ? 'orders@ssp3forte.com' : 'encomendas@ssp3forte.com',
        to: isEN ? 'orders@ssp3forte.com' : 'encomendas@ssp3forte.com',
        subject: `Novo pedido ${orderNum} — ${d.name}`,
        html: buildInternalEmail(d, orderNum, product),
      });
      return json({ success: true, orderNum });
    } catch (err) {
      console.error(err);
      return json({ error: 'Email sending failed', detail: err.message }, 500);
    }
  },
};
