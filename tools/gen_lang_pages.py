# -*- coding: utf-8 -*-
"""Gera as versoes por lingua do site em subpastas, a partir do index.html.

    python tools/gen_lang_pages.py

    /          portugues europeu  (o proprio index.html, e o x-default)
    /br/       portugues do Brasil
    /en/       ingles

Porque existe
-------------
As quatro linguas viviam todas em ssp3forte.com/, trocadas por CSS. Com um unico
endereco a Google escolhe uma lingua e as outras ficam desperdicadas: nao se pode
aparecer em Portugal, no Brasil e no Reino Unido com a mesma pagina. E sem
enderecos separados nao ha hreflang possivel -- hreflang precisa de um URL por
lingua, e qualquer etiqueta no endereco unico apontaria para si propria.

Cada pagina gerada leva:
  - <html lang> e <title> da sua lingua
  - canonical para si propria
  - o bloco hreflang completo (as tres + x-default), igual nas tres
  - os caminhos de imagens em absoluto, porque em /br/ um "imgs/..." relativo
    procuraria /br/imgs/ e nao existe
  - uma chamada a setLang() no fim do script, que aplica a lingua ao carregar.
    Nao se "assa" a classe no <body> a mao: o setLang trata tambem dos precos em
    reais, do pais por omissao e da ancora da encomenda, e repetir isso aqui
    seria mais uma copia para ficar dessincronizada.

Limite conhecido
----------------
As tres paginas continuam a ter o texto das tres linguas no HTML, escondido por
CSS. Isto da enderecos distintos e hreflang, que e o que faltava, mas nao e a
versao forte: para isso cada pagina teria de conter so a sua lingua, e os botoes
das bandeiras teriam de navegar entre enderecos em vez de trocar no proprio sitio.
Isso e um corte a serio no ficheiro e tem de ser visto renderizado antes de ir
para o ar.

E idempotente: correr sem alterar nada reproduz os ficheiros byte a byte.
"""
import hashlib, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, 'index.html')
BASE = 'https://ssp3forte.com'

# pasta -> (regiao para o setLang, atributo lang, titulo, rotulo hreflang)
PAGINAS = [
    ('',   None,  'pt-PT', 'SSP3-Forte — Saúde Natural da Próstata',  'pt-PT'),
    ('br', 'br',  'pt-BR', 'SSP3-Forte — Saúde Natural da Próstata',  'pt-BR'),
    ('en', 'eu',  'en', 'SSP3-Forte — Natural Prostate Health',    'en'),
]

INICIO = '<!-- HREFLANG : gerado por tools/gen_lang_pages.py -->'
FIM = '<!-- /HREFLANG -->'


def url_de(pasta):
    return BASE + '/' + (pasta + '/' if pasta else '')


def bloco_hreflang(pasta):
    linhas = [INICIO,
              '<link rel="canonical" href="%s">' % url_de(pasta)]
    for p, _, _, _, rotulo in PAGINAS:
        linhas.append('<link rel="alternate" hreflang="%s" href="%s">' % (rotulo, url_de(p)))
    linhas.append('<link rel="alternate" hreflang="x-default" href="%s">' % url_de(''))
    linhas.append(FIM)
    return '\n'.join(linhas)


def preparar(html, pasta, regiao, lang, titulo):
    # substituir o canonical/hreflang anterior, ou inserir se for a primeira vez
    novo = bloco_hreflang(pasta)
    if INICIO in html and FIM in html:
        i, j = html.index(INICIO), html.index(FIM) + len(FIM)
        html = html[:i] + novo + html[j:]
    else:
        antigo = '<link rel="canonical" href="%s/">' % BASE
        if antigo not in html:
            sys.exit('nao encontrei o canonical nem os marcadores de hreflang')
        html = html.replace(antigo, novo, 1)

    html = re.sub(r'<html lang="[^"]*">', '<html lang="%s">' % lang, html, count=1)
    html = re.sub(r'<title>[^<]*</title>', '<title>%s</title>' % titulo, html, count=1)

    if pasta:
        # em /br/ um caminho relativo procuraria /br/imgs/, que nao existe
        html = html.replace('src="imgs/', 'src="/imgs/').replace('href="imgs/', 'href="/imgs/')
        html = html.replace('src="frasco.jpg"', 'src="/frasco.jpg"')
        html = html.replace('href="frasco.jpg"', 'href="/frasco.jpg"')
        # aplicar a lingua ao carregar, reutilizando o setLang ja testado
        marca = 'renderBlogCards();'
        if marca not in html:
            sys.exit('nao encontrei onde encaixar a chamada ao setLang')
        html = html.replace(marca, marca + "\nsetLang('%s');   /* pagina de lingua */" % regiao, 1)
    return html


def escrever_sitemap():
    urls = '\n'.join(
        '  <url>\n    <loc>%s</loc>\n    <changefreq>weekly</changefreq>\n'
        '    <priority>%s</priority>\n  </url>' % (url_de(p), '1.0' if not p else '0.9')
        for p, _, _, _, _ in PAGINAS)
    txt = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<!-- Gerado por tools/gen_lang_pages.py. Uma entrada por lingua. -->\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + urls + '\n</urlset>\n')
    io.open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8', newline='\n').write(txt)


MARCA = '<!-- gerado de index.html sha1:%s -->'
PADRAO_MARCA = re.compile(r'<!-- gerado de index\.html sha1:([0-9a-f]{40}) -->')


def sha_do_index():
    """Impressao digital do index.html ja final (sem a marca, que so vai nas copias)."""
    return hashlib.sha1(io.open(INDEX, 'rb').read()).hexdigest()


def main():
    original = io.open(INDEX, encoding='utf-8', newline='').read()

    # a raiz primeiro: o seu canonical muda, logo o sha so e estavel depois
    raiz = [p for p in PAGINAS if not p[0]][0]
    io.open(INDEX, 'w', encoding='utf-8', newline='').write(
        preparar(original, raiz[0], raiz[1], raiz[2], raiz[3]))
    print('  %-14s %s' % ('/', raiz[3]))

    sha = sha_do_index()
    original = io.open(INDEX, encoding='utf-8', newline='').read()

    for pasta, regiao, lang, titulo, _ in PAGINAS:
        if not pasta:
            continue
        html = preparar(original, pasta, regiao, lang, titulo)
        html = html.replace('</body>', (MARCA % sha) + '\n</body>', 1)
        destino = os.path.join(ROOT, pasta)
        if not os.path.isdir(destino):
            os.makedirs(destino)
        io.open(os.path.join(destino, 'index.html'), 'w', encoding='utf-8', newline='').write(html)
        print('  %-14s %s' % ('/' + pasta + '/', titulo))

    escrever_sitemap()

    # as paginas em subpasta nao podem ficar com caminhos relativos
    for pasta, _, _, _, _ in PAGINAS:
        if not pasta:
            continue
        txt = io.open(os.path.join(ROOT, pasta, 'index.html'), encoding='utf-8').read()
        sem_script = re.sub(r'<script>.*?</script>', '', txt, flags=re.S)
        maus = [m.group(2) for m in re.finditer(r'(src|href)="([^"]+)"', sem_script)
                if not m.group(2).startswith(('http', '#', 'mailto:', 'data:', '/'))]
        if maus:
            sys.exit('/%s/ ficou com caminhos relativos: %s -- NAO fazer commit'
                     % (pasta, ', '.join(sorted(set(maus))[:5])))

    print('feito: 3 enderecos, hreflang nos tres, sitemap actualizado.')


if __name__ == '__main__':
    main()
