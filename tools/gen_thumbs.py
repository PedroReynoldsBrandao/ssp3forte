# -*- coding: utf-8 -*-
"""Gera as miniaturas das fotos dos ingredientes.

    python tools/gen_thumbs.py            # gera / actualiza
    python tools/gen_thumbs.py --check    # so verifica (sai !=0 se faltar ou estiver velha)

Porque existe
-------------
As fotos dos ingredientes sao ficheiros de ~1250x1250 px e ate 1 MB cada, e a
pagina desenha-as num quadrado de 84x84 px (ver .ingredient-img no index.html).
Em Outubro de 2026 isso dava 3,4 MB de fotos numa visita de 3,7 MB: medido no
Chromium com a rede travada, 18,8 s para a pagina ficar pronta em 4G fraco,
contra 2,4 s com as miniaturas. Nao e a Google que castiga por isso -- o LCP e o
CLS ja estavam verdes, porque o texto pinta aos 0,8 s -- e sim o plano de dados
de quem visita, sobretudo no Brasil, e as fotos a chegarem enquanto a pessoa rola.

As miniaturas tem 252 px (3x os 84 que se veem, para ecras densos) e vao para
imgs/mini/. O original fica onde estava e e carregado so quando alguem clica para
ampliar -- e por isso que cada <img> leva um data-full a apontar para ele.

Precisa do ImageMagick (o comando `convert`). So e preciso corre-lo quando uma
foto de ingrediente muda ou quando se acrescenta uma; as miniaturas vao no repo.

E idempotente: correr sem mudar nada nao reescreve ficheiro nenhum.
"""
import hashlib, io, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ORIG = os.path.join(ROOT, 'imgs')
MINI = os.path.join(ORIG, 'mini')

LADO = 252          # 3x os 84 px a que a foto aparece
QUALIDADE = 82

# Impressao digital de cada original, para o --check saber se uma miniatura ficou
# para tras. Trocar a foto e esquecer este script nao da erro nenhum: a pagina
# mostra alegremente a miniatura antiga, que e o tipo de avaria que ninguem ve.
MANIFESTO = os.path.join(MINI, '.fontes')


def fontes():
    """As fotos dos ingredientes: 01_... a 08_..., pela convencao do projecto."""
    out = []
    for f in sorted(os.listdir(ORIG)):
        p = os.path.join(ORIG, f)
        if os.path.isfile(p) and f[:2].isdigit() and f[2:3] == '_':
            out.append(f)
    return out


def sha(caminho):
    return hashlib.sha1(io.open(caminho, 'rb').read()).hexdigest()


def ler_manifesto():
    if not os.path.exists(MANIFESTO):
        return {}
    d = {}
    for linha in io.open(MANIFESTO, encoding='utf-8'):
        if linha.strip():
            h, nome = linha.split(None, 1)
            d[nome.strip()] = h
    return d


def main():
    checar = '--check' in sys.argv
    if not checar and not os.path.isdir(MINI):
        os.makedirs(MINI)

    falta, novas, iguais = [], [], 0
    anterior = ler_manifesto()
    for f in fontes():
        nome = f.rsplit('.', 1)[0] + '.jpg'
        destino = os.path.join(MINI, nome)

        if checar:
            if not os.path.exists(destino):
                falta.append(nome + ' (nao existe)')
            elif anterior.get(f) != sha(os.path.join(ORIG, f)):
                falta.append(nome + ' (a foto mudou desde que foi gerada)')
            continue

        tmp = destino + '.tmp'
        r = subprocess.call(['convert', os.path.join(ORIG, f),
                             '-resize', '%dx%d^' % (LADO, LADO),
                             '-gravity', 'center', '-extent', '%dx%d' % (LADO, LADO),
                             '-strip', '-quality', str(QUALIDADE), tmp])
        if r != 0:
            if os.path.exists(tmp):
                os.remove(tmp)
            sys.exit('o `convert` falhou em %s -- o ImageMagick esta instalado?' % f)

        novo = io.open(tmp, 'rb').read()
        antigo = io.open(destino, 'rb').read() if os.path.exists(destino) else None
        if antigo == novo:
            os.remove(tmp)
            iguais += 1
        else:
            os.rename(tmp, destino)
            novas.append((nome, os.path.getsize(os.path.join(ORIG, f)), len(novo)))

    if checar:
        if falta:
            sys.exit('miniaturas por refazer: %s\n  corre `python tools/gen_thumbs.py`'
                     % '; '.join(falta))
        print('miniaturas: %d, todas em dia.' % len(fontes()))
        return

    io.open(MANIFESTO, 'w', encoding='utf-8', newline='\n').write(
        u''.join('%s  %s\n' % (sha(os.path.join(ORIG, f)), f) for f in fontes()))

    for nome, a, b in novas:
        print('  %-28s %6.0f KB -> %5.0f KB' % (nome, a / 1024.0, b / 1024.0))
    if iguais:
        print('  %d ja estavam certas' % iguais)

    total = sum(os.path.getsize(os.path.join(MINI, f)) for f in os.listdir(MINI))
    orig = sum(os.path.getsize(os.path.join(ORIG, f)) for f in fontes())
    print('feito: %d miniaturas, %.0f KB no total (os originais somam %.1f MB).'
          % (len(fontes()), total / 1024.0, orig / 1048576.0))


if __name__ == '__main__':
    main()
