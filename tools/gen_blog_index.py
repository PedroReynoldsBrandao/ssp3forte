# -*- coding: utf-8 -*-
"""Gera a lista de todos os artigos do blog, em HTML, dentro do index.html.

    python tools/gen_blog_index.py

Porque existe
-------------
A grelha de artigos (#artigos) e montada por JavaScript: no HTML ha so um <div>
vazio e os enderecos vivem dentro de BLOG_POSTS / BLOG_POSTS_EN. Isso quer dizer
que o HTML que o Googlebot le a primeira vez nao tem uma unica ligacao para os
artigos -- so para a pagina inicial do blog. A Google executa JavaScript, mas numa
segunda passagem, mais tardia e menos fiavel; e a rotacao semanal faz cada artigo
desaparecer das ligacoes de tempos a tempos.

Em Setembro de 2026 os sete artigos novos do blog ingles ficaram em "Rastreada --
atualmente nao indexada" na Search Console. A causa principal e o blog nao ter
reputacao, mas as ligacoes em falta sao a parte que se corrige deste lado.

Este script escreve, dentro do bloco .blog-all de cada lingua, uma lista simples
com TODOS os artigos da reserva. Ficam sempre no HTML, sao visiveis, e apontam
para onde dizem apontar -- nada escondido.

A fonte continua a ser BLOG_POSTS / BLOG_POSTS_EN: o script le-as do proprio
index.html e deriva a lista. Nao ha titulos duplicados a mao para ficarem
dessincronizados. Corre-o depois de acrescentares um artigo a qualquer reserva.

E idempotente: correr sem alterar nada reproduz o ficheiro byte a byte, incluindo
os fins-de-linha.
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, 'index.html')

CR, LF = chr(13), chr(10)
CRLF = CR + LF

# lingua -> (reserva, campo do titulo, rotulo da lista)
LINGUAS = [
    ('pt', 'BLOG_POSTS',    'tp', 'Todos os artigos'),
    ('br', 'BLOG_POSTS',    'tb', 'Todos os artigos'),
    ('en', 'BLOG_POSTS_EN', 'tp', 'All articles'),
]

INICIO = '<!-- BLOG INDEX %s : gerado por tools/gen_blog_index.py -->'
FIM = '<!-- /BLOG INDEX %s -->'


def ler_reserva(html, nome):
    """Extrai [(url, {campo: valor})] de BLOG_POSTS / BLOG_POSTS_EN."""
    m = re.search(r'const ' + nome + r'\s*=\s*\[(.*?)\n\];', html, re.S)
    if not m:
        sys.exit('nao encontrei %s no index.html' % nome)

    entradas = []
    for bruto in re.findall(r'\{(.*?)\}\s*,?\s*(?=\{|$)', m.group(1), re.S):
        campos = dict(re.findall(r"(\w+)\s*:\s*'((?:[^'\\]|\\.)*)'", bruto))
        if campos.get('u'):
            entradas.append(campos)
    if not entradas:
        sys.exit('%s esta vazia ou nao percebi o formato' % nome)
    return entradas


def montar(entradas, campo_titulo, rotulo, indent):
    linhas = ['%s<nav class="blog-index" aria-label="%s">' % (indent, rotulo),
              '%s  <span class="blog-index-label">%s</span>' % (indent, rotulo)]
    for e in entradas:
        titulo = e.get(campo_titulo) or e.get('tp') or e['u']
        linhas.append(
            '%s  <a href="%s" target="_blank" rel="noopener">%s</a>'
            % (indent, e['u'], titulo))
    linhas.append('%s</nav>' % indent)
    return LF.join(linhas)


def main():
    # newline='' preserva os fins-de-linha: um clone no Windows traz CRLF e sem
    # isto o splice convertia o ficheiro todo para LF, produzindo um diff inutil.
    s = io.open(INDEX, encoding='utf-8', newline='').read()
    crlf = s.count(CRLF)
    nl = CRLF if crlf > (s.count(LF) - crlf) else LF

    total = 0
    for lingua, reserva, campo, rotulo in LINGUAS:
        ini, fim = INICIO % lingua, FIM % lingua
        if ini not in s or fim not in s:
            sys.exit('faltam os marcadores de "%s" no index.html '
                     '(procurei %s)' % (lingua, ini))

        entradas = ler_reserva(s, reserva)
        pos = s.index(ini)
        i, j = pos + len(ini), s.index(fim)

        # o marcador de fim fica alinhado com o de inicio
        inicio_da_linha = s.rindex(LF, 0, pos) + 1
        indent = s[inicio_da_linha:pos]
        if indent.strip():
            indent = ''
        bloco = montar(entradas, campo, rotulo, indent)
        bloco = bloco.replace(CRLF, LF).replace(LF, nl)

        s = s[:i] + nl + bloco + nl + indent + s[j:]
        print('  %-3s %2d artigos (%s)' % (lingua, len(entradas), reserva))
        total += len(entradas)

    io.open(INDEX, 'w', encoding='utf-8', newline='').write(s)

    # as ligacoes tem de existir agora no HTML, fora do <script>
    corpo = re.sub(r'<script>.*?</script>', '', s, flags=re.S)
    for reserva, dominio in (('BLOG_POSTS', 'problemasnaprostata'),
                             ('BLOG_POSTS_EN', 'bph-prostate-enlarged')):
        n = len(re.findall(r'<a[^>]+href="[^"]*' + dominio + r'[^"]*/20\d\d/\d\d/',
                           corpo))
        print('  ligacoes %-22s no HTML: %d' % (dominio, n))
        if n == 0:
            sys.exit('nenhuma ligacao de %s ficou no HTML -- NAO fazer commit' % dominio)

    # conta todos os <nav> da pagina, nao so os gerados: o #top-nav tambem la esta
    abre = len(re.findall(r'<nav[\s>]', s))
    fecha = s.count('</nav>')
    if abre != fecha:
        sys.exit('tags <nav> desequilibradas (%d abrem, %d fecham) -- NAO fazer commit'
                 % (abre, fecha))

    print('feito: %d ligacoes escritas no HTML.' % total)


if __name__ == '__main__':
    main()
