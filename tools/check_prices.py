# -*- coding: utf-8 -*-
"""Confere se os precos batem certo em todo o projecto.

    python tools/check_prices.py

O preco esta escrito em varios sitios que nao sabem uns dos outros:

    index.html        o objecto PRICES (o calculo), os cartoes de preco em cada
                      bloco de lingua e as <option> do formulario
    worker/worker.js  a tabela PRODUCTS, que decide o preco que vai no email,
                      e o shippingLabel, que escreve os portes nesse email
    CLAUDE.md         as tabelas de documentacao

O worker NAO usa o preco que o browser lhe manda -- vai busca-lo a sua propria
tabela, para que ninguem possa forjar um pedido a um preco inventado. E a
decisao certa, mas tem este custo: os dois ficheiros podem afastar-se sem que
nada de alarme. Foi o que aconteceu entre 20/07/2026 e 12/09/2026, com o site a
mostrar R$210 e os emails a dizerem R$165 durante 54 dias.

Este script trata o objecto PRICES do index.html como a fonte da verdade e
compara tudo o resto com ele. Corre-o antes de publicar sempre que mexeres em
precos, portes ou nos emails de contacto.

Sai com codigo 0 se estiver tudo certo, 1 se houver divergencias.
Funciona a partir da raiz do repositorio ou de dentro de tools/.
"""
import hashlib, io, json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ler(nome):
    caminho = os.path.join(RAIZ, nome)
    if not os.path.exists(caminho):
        sys.exit("nao encontrei %s" % nome)
    return io.open(caminho, encoding="utf-8").read()


def valor(txt):
    """'€29,95' / 'R$210' / '29.95' / '9.00.' -> 29.95 / 210.0 / 9.0

    Tolera pontuacao a volta: o valor pode vir do fim de uma frase."""
    n = re.sub(r"[^0-9,.]", "", txt).replace(",", ".").strip(".")
    if not n:
        raise ValueError("sem numero em %r" % txt)
    return round(float(n), 2)


def moeda(chave):
    return "R$" if chave.endswith("-br") else "€"


def formata(v, c):
    return "R$%d" % round(v) if c == "R$" else "€%.2f" % v


# ── fonte da verdade: o objecto PRICES ───────────────────────────────────────

def ler_precos(html):
    m = re.search(r"const PRICES\s*=\s*\{([^}]*)\}", html)
    if not m:
        sys.exit("nao encontrei o objecto PRICES no index.html")
    return {k: round(float(v), 2)
            for k, v in re.findall(r"'([^']+)'\s*:\s*([0-9.]+)", m.group(1))}


def ler_portes(html):
    m = re.search(r"const SHIPPING\s*=\s*\{([^}]*)\}", html)
    if not m:
        sys.exit("nao encontrei o objecto SHIPPING no index.html")
    return {k: round(float(v), 2)
            for k, v in re.findall(r"(\w+)\s*:\s*([0-9.]+)", m.group(1))}


# ── as verificacoes ──────────────────────────────────────────────────────────

def conferir_worker(precos, js, falhas):
    """A tabela PRODUCTS do worker -- a que decide o preco no email."""
    tabela = {}
    for chave, corpo in re.findall(r"'([^']+)':\s*\{(.*?)\},", js):
        for campo in ("pricePT", "priceEN"):
            m = re.search(campo + r":\s*'([^']+)'", corpo)
            if m:
                tabela[(chave, campo)] = m.group(1)

    if not tabela:
        falhas.append("nao consegui ler a tabela PRODUCTS do worker.js")
        return

    for chave, esperado in sorted(precos.items()):
        for campo in ("pricePT", "priceEN"):
            escrito = tabela.get((chave, campo))
            if escrito is None:
                falhas.append("worker.js: falta %s para '%s'" % (campo, chave))
            elif valor(escrito) != esperado:
                falhas.append(
                    "worker.js %s de '%s' diz %s, mas o site cobra %s"
                    % (campo, chave, escrito, formata(esperado, moeda(chave))))


def conferir_cartoes(precos, html, falhas):
    """Os cartoes de preco, em cada bloco de lingua."""
    vistos = []
    for m in re.finditer(
            r'<p class="pricing-price"><sup>(€|R\$)</sup>'
            r'(\d+)(?:<small>[,.](\d+)</small>)?</p>', html):
        simbolo, inteiro, cents = m.group(1), m.group(2), m.group(3)
        vistos.append((simbolo, round(float(inteiro + "." + (cents or "0")), 2),
                       html[:m.start()].count("\n") + 1))

    for simbolo, v, linha in vistos:
        if v not in [p for k, p in precos.items() if moeda(k) == simbolo]:
            falhas.append("index.html:%d cartao mostra %s, que nao esta em PRICES"
                          % (linha, formata(v, simbolo)))

    # cada preco tem de aparecer pelo menos num cartao
    for chave, esperado in sorted(precos.items()):
        c = moeda(chave)
        if not any(s == c and v == esperado for s, v, _ in vistos):
            falhas.append("nenhum cartao mostra %s (o preco de '%s')"
                          % (formata(esperado, c), chave))


def conferir_riscados(precos, html, falhas):
    """O preco riscado do kit = 3x o preco de um frasco."""
    for m in re.finditer(r'<p class="pricing-old">([^<·]+)·', html):
        escrito, linha = m.group(1).strip(), html[:m.start()].count("\n") + 1
        c = "R$" if "R$" in escrito else "€"
        base = precos.get("1x-br" if c == "R$" else "1x")
        if base is None:
            continue
        if valor(escrito) != round(base * 3, 2):
            falhas.append(
                "index.html:%d preco riscado diz %s, mas 3 frascos a %s dao %s"
                % (linha, escrito, formata(base, c), formata(base * 3, c)))


def conferir_opcoes(precos, html, falhas):
    """As <option> do formulario e o mapa OPT que as renomeia."""
    for m in re.finditer(r'<option value="([^"]+)">([^<]*)</option>', html):
        chave, rotulo = m.group(1), m.group(2)
        if chave not in precos or "—" not in rotulo:
            continue
        linha = html[:m.start()].count("\n") + 1
        if valor(rotulo.split("—")[-1]) != precos[chave]:
            falhas.append("index.html:%d a opcao '%s' diz \"%s\", mas o site cobra %s"
                          % (linha, chave, rotulo.strip(),
                             formata(precos[chave], moeda(chave))))

    # Ate Out/2026 havia um mapa OPT com o preco escrito outra vez, e era preciso
    # confirma-lo aqui. Os rotulos passaram a ser montados a partir do PRICES, o
    # que torna aquela divergencia impossivel -- desde que ninguem volte a
    # escrever um preco dentro do ROTULOS. E isso que se confere agora.
    m = re.search(r"const ROTULOS\s*=\s*\{(.*?)\n\};", html, re.S)
    if not m:
        falhas.append("index.html: nao encontrei o ROTULOS (os nomes dos produtos)")
    elif re.search(r"€|R\$", m.group(1)):   # "SSP3-Forte" e "3-bottle" tem digitos; um preco tem moeda
        falhas.append("index.html: o ROTULOS voltou a ter precos escritos a mao -- "
                      "deve ter so nomes, o preco vem do PRICES")


def conferir_portes_do_worker(portes, js, falhas):
    """Os portes que o email diz ao cliente.

    O shippingLabel do worker tem o valor escrito por extenso dentro do rotulo,
    longe do SHIPPING do index.html. Em Out/2026 dizia "+€4,99" enquanto o site
    cobrava €5,99 -- o mesmo erro dos R$165, no mesmo tipo de sitio, e este
    script passava-lhe ao lado porque so olhava para a tabela PRODUCTS."""
    ESPERADO = {"portugal": "PT", "europa": "default", "correio-aereo": "BR"}
    for chave, campo in ESPERADO.items():
        for m in re.finditer(r"'%s':\s*\{([^}]*)\}" % chave, js):
            for escrito in re.findall(r"\+€([\d.,]+)\)", m.group(1)):
                if valor(escrito) != portes[campo]:
                    falhas.append(
                        "worker.js: o email diz portes de €%s para '%s', "
                        "mas o site cobra €%.2f"
                        % (escrito, chave, portes[campo]))


def conferir_dados_estruturados(precos, html, falhas):
    """Os precos no JSON-LD -- o quinto sitio onde vivem.

    Foram acrescentados em Out/2026 para a Google mostrar preco no resultado da
    pesquisa. Preco errado aqui e pior do que nao ter nenhum: aparece publicado
    na pagina de resultados, fora do site, e demora a actualizar."""
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not m:
        return                                  # sem JSON-LD, nada a conferir
    try:
        d = json.loads(m.group(1))
    except ValueError as e:
        falhas.append("o JSON-LD do index.html nao e JSON valido: %s" % e)
        return

    produtos = [n for n in d.get("@graph", []) if n.get("@type") == "Product"]
    if not produtos:
        falhas.append("o JSON-LD nao tem nenhum Product")
        return

    ofertas = [(o.get("priceCurrency"), valor(str(o.get("price"))))
               for p in produtos for o in p.get("offers", [])]
    for chave, esperado in sorted(precos.items()):
        moe = "BRL" if moeda(chave) == "R$" else "EUR"
        if (moe, esperado) not in ofertas:
            falhas.append("o JSON-LD nao anuncia %s para '%s' (anuncia: %s)"
                          % (formata(esperado, moeda(chave)), chave,
                             ", ".join("%s %s" % (c, v) for c, v in ofertas if c == moe) or "nada"))

    # uma classificacao inventada aqui e motivo de penalizacao pela Google
    for p in produtos:
        if "aggregateRating" in p or "review" in p:
            falhas.append("o JSON-LD tem aggregateRating/review -- so com avaliacoes "
                          "reais marcadas na pagina; o inquerito de satisfacao nao serve")


def conferir_paginas_de_lingua(falhas):
    """As copias em /br/ e /en/ sao geradas do index.html e ficam para tras.

    O apply_modal.py e o gen_blog_index.py reescrevem o index.html, e quem nao
    souber desta dependencia publica um /br/ com os modais antigos sem nada se
    queixar. Cada copia leva a impressao digital do index.html de onde saiu."""
    caminho_index = os.path.join(RAIZ, 'index.html')
    atual = hashlib.sha1(io.open(caminho_index, 'rb').read()).hexdigest()
    for pasta in ('br', 'en'):
        f = os.path.join(RAIZ, pasta, 'index.html')
        if not os.path.exists(f):
            falhas.append("falta /%s/index.html -- correr: python tools/gen_lang_pages.py" % pasta)
            continue
        m = re.search(r'<!-- gerado de index\.html sha1:([0-9a-f]{40}) -->',
                      io.open(f, encoding='utf-8').read())
        if not m:
            falhas.append("/%s/index.html nao tem a marca de origem -- regerar" % pasta)
        elif m.group(1) != atual:
            falhas.append("/%s/index.html foi gerado de outra versao do index.html "
                          "-- correr: python tools/gen_lang_pages.py" % pasta)


def conferir_emails(html, js, falhas):
    """Os dois enderecos tem de existir dos dois lados."""
    for email in ("encomendas@ssp3forte.com", "orders@ssp3forte.com"):
        if email not in html:
            falhas.append("o index.html nao menciona %s" % email)
        if email not in js:
            falhas.append("o worker.js nao menciona %s" % email)


def conferir_documentacao(precos, portes, md, falhas):
    """O CLAUDE.md tambem se desactualiza -- os portes ja la estiveram errados."""
    m = re.search(r"PRICES` object: `\{([^}]*)\}", md)
    if m:
        doc = {k: round(float(v), 2)
               for k, v in re.findall(r"'([^']+)'\s*:\s*([0-9.]+)", m.group(1))}
        if doc != precos:
            falhas.append("CLAUDE.md: o objecto PRICES documentado nao bate com o do site")
    else:
        falhas.append("CLAUDE.md: nao encontrei o objecto PRICES documentado")

    m = re.search(r"Shipping \(EUR orders\): Portugal €([0-9.,]+), "
                  r"other countries €([0-9.,]+)", md)
    if m:
        if valor(m.group(1)) != portes.get("PT"):
            falhas.append("CLAUDE.md diz portes de Portugal a €%s, o site cobra €%.2f"
                          % (m.group(1), portes["PT"]))
        if valor(m.group(2)) != portes.get("default"):
            falhas.append("CLAUDE.md diz portes do resto a €%s, o site cobra €%.2f"
                          % (m.group(2), portes["default"]))
    else:
        falhas.append("CLAUDE.md: nao encontrei a linha dos portes")


# ── ponto de entrada ─────────────────────────────────────────────────────────

def main():
    html = ler("index.html")
    js = ler(os.path.join("worker", "worker.js"))
    md = ler("CLAUDE.md")

    precos, portes = ler_precos(html), ler_portes(html)
    falhas = []

    conferir_worker(precos, js, falhas)
    conferir_cartoes(precos, html, falhas)
    conferir_riscados(precos, html, falhas)
    conferir_opcoes(precos, html, falhas)
    conferir_portes_do_worker(portes, js, falhas)
    conferir_dados_estruturados(precos, html, falhas)
    conferir_paginas_de_lingua(falhas)
    conferir_emails(html, js, falhas)
    conferir_documentacao(precos, portes, md, falhas)

    print("precos no site (fonte: o objecto PRICES do index.html)")
    for chave, v in sorted(precos.items()):
        print("   %-7s %s" % (chave, formata(v, moeda(chave))))
    print("portes: Portugal €%.2f, resto €%.2f" % (portes["PT"], portes["default"]))
    print("")

    if falhas:
        print("%d divergencia(s):" % len(falhas))
        for f in falhas:
            print("   %s" % f)
        if any(f.startswith("worker.js") for f in falhas):
            print("")
            print("o worker so passa a enviar os precos certos depois de:")
            print("   cd worker && npx wrangler deploy")
        return 1

    print("tudo certo -- site, worker e documentacao dizem o mesmo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
