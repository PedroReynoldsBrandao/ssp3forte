# -*- coding: utf-8 -*-
"""Gera as tres paginas do site a partir de fonte.html, cada uma so com a sua lingua.

    python tools/gen_lang_pages.py            # escreve index.html, br/, en/ e o sitemap
    python tools/gen_lang_pages.py --check    # nao escreve; falha se algum estiver desactualizado

    fonte.html   a ORIGEM: as tres linguas, trocadas por CSS. E aqui que se edita.
    /            portugues europeu  (index.html, e o x-default)
    /br/         portugues do Brasil
    /en/         ingles, e tambem a variante INT (/en/?v=int)

NAO editar index.html, br/index.html nem en/index.html a mao: sao reescritos
sempre que isto corre, e o check_prices.py falha se alguem lhes mexer.

Porque existe
-------------
Ate Out/2026 havia um so endereco com as quatro linguas trocadas por CSS; a Google
escolhia uma e as outras ficavam desperdicadas. Depois vieram tres enderecos com
hreflang, mas cada pagina continuava a levar o texto das tres linguas, escondido
-- a pagina portuguesa tinha la dentro a brasileira e a inglesa, e as tres
competiam entre si. Desde Nov/2026 cada pagina leva so a sua.

A origem continua a ter as tres linguas num ficheiro so, de proposito. Tres
ficheiros editados a mao seriam tres sitios para a mesma alteracao, e um dia
esquece-se um: foi assim que os emails brasileiros andaram 54 dias com R$165.

O que cada pagina recebe
------------------------
  - so os elementos da sua lingua: [data-lang] e [data-lang-inline] das outras
    sao cortados (com tudo o que tem dentro), seguindo as mesmas regras do CSS
  - <body class="lang-xx"> ja na lingua certa, para nao haver um instante de
    pagina vazia antes de o script correr (o texto das outras ja nao esta la)
  - <html lang>, <title>, meta description, canonical para si propria e o bloco
    hreflang completo, igual nas tres
  - os caminhos de imagens em absoluto nas subpastas: em /br/ um "imgs/..."
    relativo procuraria /br/imgs/
  - uma chamada a setLang() no fim do script, que trata dos precos em reais, do
    pais por omissao e da ancora da encomenda; repetir isso aqui seria mais uma
    copia para ficar dessincronizada
  - sem os comentarios HTML da origem (notas internas, marcadores dos geradores);
    os do <script> e do <style> ficam, porque cortar dentro de JS e arriscado

E idempotente: correr sem alterar nada reproduz os ficheiros byte a byte.
"""
import hashlib, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTE = os.path.join(ROOT, 'fonte.html')
BASE = 'https://ssp3forte.com'

DESC_PT = ('SSP3-Forte: suplemento alimentar natural com oito ingredientes, fabricado na UE '
           'sob GMP e ISO 22000. Distribuído por Naturalfarma para Portugal, Brasil, Europa.')
DESC_EN = ('SSP3-Forte: a natural food supplement with eight ingredients, made in the EU '
           'under GMP and ISO 22000. Distributed by Naturalfarma to Portugal, Brazil and Europe.')

# pasta, regiao do setLang, classe do body, lang, titulo, descricao, hreflang
PAGINAS = [
    ('',   None, 'lang-pt', 'pt-PT', 'SSP3-Forte — Saúde Natural da Próstata', DESC_PT, 'pt-PT'),
    ('br', 'br', 'lang-br', 'pt-BR', 'SSP3-Forte — Saúde Natural da Próstata', DESC_PT, 'pt-BR'),
    ('en', 'eu', 'lang-en', 'en',    'SSP3-Forte — Natural Prostate Health',   DESC_EN, 'en'),
]

# O que cada pagina mostra -- tem de bater com o bloco CONTENT SWITCHING do CSS.
# lang-br mostra os inline "pt" (o PT e o BR partilham texto curto) mas nao os "pt-only".
FICA = {
    'lang-pt': {'bloco': {'pt'}, 'inline': {'pt', 'pt-only'}},
    'lang-br': {'bloco': {'br'}, 'inline': {'pt', 'br'}},
    'lang-en': {'bloco': {'en'}, 'inline': {'en'}},
}

INICIO = '<!-- HREFLANG : gerado por tools/gen_lang_pages.py -->'
FIM = '<!-- /HREFLANG -->'
AVISO = ('<!-- GERADO por tools/gen_lang_pages.py a partir de fonte.html -- nao editar aqui, '
         'as alteracoes perdem-se. -->')
MARCA = '<!-- gerado de fonte.html sha1:%s -->'
PADRAO_MARCA = re.compile(r'<!-- gerado de fonte\.html sha1:([0-9a-f]{40}) -->')

VAZIOS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta',
          'source', 'track', 'wbr'}


def url_de(pasta):
    return BASE + '/' + (pasta + '/' if pasta else '')


def bloco_hreflang(pasta):
    linhas = [INICIO, '<link rel="canonical" href="%s">' % url_de(pasta)]
    for p in PAGINAS:
        linhas.append('<link rel="alternate" hreflang="%s" href="%s">' % (p[6], url_de(p[0])))
    linhas.append('<link rel="alternate" hreflang="x-default" href="%s">' % url_de(''))
    linhas.append(FIM)
    return '\n'.join(linhas)


def zonas_protegidas(html):
    """Intervalos de <script> e <style>, onde nao se corta nada."""
    return [(m.start(), m.end()) for m in re.finditer(r'<(script|style)\b[^>]*>.*?</\1>', html, re.S)]


def dentro(pos, zonas):
    return any(a <= pos < b for a, b in zonas)


def fim_do_elemento(html, tag, depois_da_abertura):
    """Posicao a seguir ao </tag> que fecha o elemento aberto antes de depois_da_abertura."""
    nivel = 1
    padrao = re.compile(r'<(/?)%s\b[^>]*>' % tag, re.I)
    for m in padrao.finditer(html, depois_da_abertura):
        if m.group(1):
            nivel -= 1
            if nivel == 0:
                return m.end()
        elif not m.group(0).endswith('/>'):
            nivel += 1
    sys.exit('<%s> sem fecho a partir da posicao %d -- a fonte.html esta mal formada'
             % (tag, depois_da_abertura))


def cortar_outras_linguas(html, classe):
    fica = FICA[classe]
    abertura = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?\sdata-lang(-inline)?="([^"]+)"[^>]*>')
    pos, partes = 0, []
    zonas = zonas_protegidas(html)
    while True:
        m = abertura.search(html, pos)
        if not m:
            break
        if dentro(m.start(), zonas):
            partes.append(html[pos:m.end()])
            pos = m.end()
            continue
        tipo = 'inline' if m.group(2) else 'bloco'
        if m.group(3) in fica[tipo]:
            partes.append(html[pos:m.end()])
            pos = m.end()
            continue
        tag = m.group(1).lower()
        fim = m.end() if tag in VAZIOS else fim_do_elemento(html, tag, m.end())
        partes.append(html[pos:m.start()])
        pos = fim
    partes.append(html[pos:])
    return ''.join(partes)


def tirar_comentarios(html):
    zonas = zonas_protegidas(html)
    return re.sub(r'<!--.*?-->',
                  lambda m: m.group(0) if dentro(m.start(), zonas) or m.group(0).startswith(INICIO[:12])
                  else '', html, flags=re.S)


def arrumar_linhas(html):
    """O corte deixa linhas so com espacos e montes de linhas em branco."""
    html = re.sub(r'[ \t]+\n', '\n', html)
    return re.sub(r'\n{3,}', '\n\n', html)


def preparar(fonte, pagina):
    pasta, regiao, classe, lang, titulo, desc, _ = pagina
    html = fonte
    if INICIO not in html or FIM not in html:
        sys.exit('fonte.html sem os marcadores de HREFLANG')
    i, j = html.index(INICIO), html.index(FIM) + len(FIM)
    html = html[:i] + bloco_hreflang(pasta) + html[j:]

    html = re.sub(r'<html lang="[^"]*">', '<html lang="%s">' % lang, html, count=1)
    html = re.sub(r'<title>[^<]*</title>', '<title>%s</title>' % titulo, html, count=1)
    html, n = re.subn(r'<meta name="description" content="[^"]*">',
                      '<meta name="description" content="%s">' % desc, html, count=1)
    if n != 1:
        sys.exit('nao encontrei a meta description na fonte.html')
    html, n = re.subn(r'<body class="[^"]*">', '<body class="%s">' % classe, html, count=1)
    if n != 1:
        sys.exit('nao encontrei o <body class=...> na fonte.html')

    html = cortar_outras_linguas(html, classe)
    html = tirar_comentarios(html)

    if pasta:
        html = (html.replace('src="imgs/', 'src="/imgs/')
                    .replace('href="imgs/', 'href="/imgs/')
                    # o data-full do lightbox tambem: so falharia ao ampliar uma foto,
                    # que e onde ninguem repara
                    .replace('data-full="imgs/', 'data-full="/imgs/')
                    .replace('src="frasco.jpg"', 'src="/frasco.jpg"')
                    .replace('href="frasco.jpg"', 'href="/frasco.jpg"'))
    if regiao:
        marca = 'renderBlogCards();'
        if marca not in html:
            sys.exit('nao encontrei onde encaixar a chamada ao setLang')
        html = html.replace(marca, marca + "\nsetLang('%s');   /* pagina de lingua */" % regiao, 1)

    html = arrumar_linhas(html)
    html = html.replace('<!DOCTYPE html>\n', '<!DOCTYPE html>\n' + AVISO + '\n', 1)
    return html


def sitemap():
    urls = '\n'.join(
        '  <url>\n    <loc>%s</loc>\n    <changefreq>weekly</changefreq>\n'
        '    <priority>%s</priority>\n  </url>' % (url_de(p[0]), '1.0' if not p[0] else '0.9')
        for p in PAGINAS)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!-- Gerado por tools/gen_lang_pages.py. Uma entrada por lingua. -->\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + urls + '\n</urlset>\n')


def destino_de(pasta):
    return os.path.join(ROOT, pasta, 'index.html') if pasta else os.path.join(ROOT, 'index.html')


def gerar():
    """{caminho: conteudo} de tudo o que este script escreve."""
    fonte = io.open(FONTE, encoding='utf-8', newline='').read()
    sha = hashlib.sha1(io.open(FONTE, 'rb').read()).hexdigest()
    saida = {}
    for p in PAGINAS:
        html = preparar(fonte, p)
        html = html.replace('</body>', (MARCA % sha) + '\n</body>', 1)
        saida[destino_de(p[0])] = html
    saida[os.path.join(ROOT, 'sitemap.xml')] = sitemap()
    return saida


def verificar(saida):
    """Problemas que impedem o commit, devolvidos como lista de frases."""
    falhas = []
    for p in PAGINAS:
        txt = saida[destino_de(p[0])]
        sem_script = re.sub(r'<(script|style)\b.*?</\1>', '', txt, flags=re.S)
        if p[0]:
            maus = [m.group(2) for m in re.finditer(r'(src|href|data-full)="([^"]+)"', sem_script)
                    if not m.group(2).startswith(('http', '#', 'mailto:', 'data:', '/'))]
            if maus:
                falhas.append('/%s/ ficou com caminhos relativos: %s'
                              % (p[0], ', '.join(sorted(set(maus))[:5])))
        fica = FICA[p[2]]
        for m in re.finditer(r'data-lang(-inline)?="([^"]+)"', sem_script):
            if m.group(2) not in fica['inline' if m.group(1) else 'bloco']:
                falhas.append('/%s ficou com texto de outra lingua (%s)' % (p[0], m.group(0)))
                break
        # cada lingua tem de ter ficado com o essencial -- um corte a mais apagava a pagina
        for essencial in ('id="orderForm"', 'id="productSelect"', 'id="shippingCalc"',
                          'id="survey-modal"', 'id="info-modal"', 'id="disclaimer-modal"',
                          'class="hero', 'id="artigos"'):
            if essencial not in txt:
                falhas.append('/%s perdeu %s' % (p[0], essencial))
        abre = len(re.findall(r'<div\b', sem_script))
        fecha = len(re.findall(r'</div>', sem_script))
        if abre != fecha:
            falhas.append('/%s tem %d <div> e %d </div>' % (p[0], abre, fecha))
    return falhas


def main():
    so_ver = '--check' in sys.argv[1:]
    saida = gerar()
    falhas = verificar(saida)
    if falhas:
        sys.exit('\n'.join(falhas) + '\n-- NAO fazer commit')

    if so_ver:
        velhos = []
        for caminho, conteudo in sorted(saida.items()):
            try:
                actual = io.open(caminho, encoding='utf-8', newline='').read()
            except IOError:
                actual = None
            if actual != conteudo:
                velhos.append(os.path.relpath(caminho, ROOT))
        if velhos:
            sys.exit('desactualizados ou editados a mao: %s -- correr: python tools/gen_lang_pages.py'
                     % ', '.join(velhos))
        print('as tres paginas e o sitemap batem com a fonte.html')
        return

    for caminho, conteudo in saida.items():
        d = os.path.dirname(caminho)
        if not os.path.isdir(d):
            os.makedirs(d)
        io.open(caminho, 'w', encoding='utf-8', newline='').write(conteudo)
    for p in PAGINAS:
        print('  %-6s %6.1f KB  %s' % ('/' + (p[0] + '/' if p[0] else ''),
                                       len(saida[destino_de(p[0])].encode('utf-8')) / 1024.0, p[4]))
    print('feito: 3 paginas, uma lingua em cada, sitemap actualizado.')


if __name__ == '__main__':
    main()
