# -*- coding: utf-8 -*-
"""Corre um gerador de modal e cola o resultado no index.html.

    python tools/apply_modal.py info      -> #info-modal
    python tools/apply_modal.py survey    -> #survey-modal
    python tools/apply_modal.py both

Funciona a partir da raiz do repositorio ou de dentro de tools/.
Os geradores escrevem um .txt intermedio; este script cola-o entre os marcadores
certos, verifica o equilibrio das tags e apaga o ficheiro temporario.

E idempotente: correr sem alterar nada reproduz o ficheiro byte a byte, incluindo
os fins-de-linha. Isso torna-o seguro de correr so para confirmar o estado.

Depois de correr, confirmar a sintaxe do JS da pagina antes do commit:
    python -c "import io,re; s=io.open('index.html',encoding='utf-8').read(); io.open('_p.js','w',encoding='utf-8').write(re.findall(r'<script>(.*?)</script>',s,re.S)[0])"
    node --check _p.js
"""
import io, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, 'index.html')

CR = chr(13)
LF = chr(10)
CRLF = CR + LF

# nome -> (gerador, ficheiro gerado, marcador de inicio, marcador de fim)
JOBS = {
    'info':   ('gen_info_modal.py', 'info_modal.txt',
               '<div id="info-modal">', '<!-- SURVEY MODAL'),
    'survey': ('gen_survey.py', 'survey_modal_v2.txt',
               '<!-- SURVEY MODAL', '<div id="disclaimer-modal">'),
}


def apply(name):
    script, produced, start, end = JOBS[name]

    r = subprocess.run([sys.executable, script], cwd=HERE,
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    sys.stdout.write(r.stdout or '')
    if r.returncode != 0:
        sys.stderr.write(r.stderr or '')
        raise SystemExit('%s falhou' % script)

    out = os.path.join(HERE, produced)
    if not os.path.exists(out):
        raise SystemExit('%s nao escreveu %s' % (script, produced))
    block = io.open(out, encoding='utf-8').read()

    # newline='' preserva os fins-de-linha tal como estao no ficheiro. Um clone
    # acabado de fazer traz CRLF no Windows; sem isto o splice convertia tudo para
    # LF e produzia um diff do ficheiro inteiro, que so confunde quem vem a seguir.
    s = io.open(INDEX, encoding='utf-8', newline='').read()
    crlf = s.count(CRLF)
    nl = CRLF if crlf > (s.count(LF) - crlf) else LF
    block = block.replace(CRLF, LF).replace(LF, nl)

    i, j = s.index(start), s.index(end)
    before = len(s[i:j])
    s = s[:i] + block + nl + s[j:]
    io.open(INDEX, 'w', encoding='utf-8', newline='').write(s)
    os.remove(out)

    new = s[s.index(start):s.index(end)]
    ok = new.count('<div') == new.count('</div>')
    print('  %-7s %d -> %d bytes | divs equilibrados: %s' % (name, before, len(new), ok))
    if not ok:
        raise SystemExit('tags desequilibradas em %s -- NAO fazer commit' % name)


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'both'
    for n in (['info', 'survey'] if which == 'both' else [which]):
        if n not in JOBS:
            raise SystemExit('use: info | survey | both')
        apply(n)
    print('feito. verificar o JS e o resultado antes do commit.')
