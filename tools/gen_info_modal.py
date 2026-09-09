# -*- coding: utf-8 -*-
"""Gera o bloco HTML do #info-modal nas tres linguas (pt / br / en).

Reescrito em Setembro de 2026. O texto anterior (fornecido pelo cliente) apresentava
o produto como "remedio"/"tratamento" para a HBP e fazia alegacoes sobre PSA, tamanho
da prostata, fluxo urinario, nicturia, erecao e espermatogenese. Nenhuma dessas consta
da lista autorizada ao abrigo do Regulamento (CE) 1924/2006, e a apresentacao como
remedio para uma doenca nomeada expoe o produto a ser tratado como medicamento por
apresentacao.

Esta versao vende sobre o que e verificavel: fabrico europeu certificado, composicao,
o inquerito de satisfacao, e conselhos de estilo de vida. Nao inclui as alegacoes
autorizadas do zinco e da vitamina E porque dependem de o rotulo fornecer >=15% do VRN
por dose diaria, o que nao esta confirmado. Confirmando-se, podem ser acrescentadas.

O numero citado ("perto de 9 em cada 10", 88,1%) e o do subgrupo com toma regular e sem
medicacao declarada, e vem sempre com essa condicao na mesma frase. Foi decisao do cliente
em Set/2026 usar este valor em vez dos 81,3% de todos os inqueridos. A condicao NAO pode
cair da frase: sem ela o numero passa a ser falso.
"""
import io

T = {
'pt': dict(
    h2='O que o SSP3-Forte pode fazer por si?',
    intro=('O SSP3-Forte é um <b>suplemento alimentar</b> de base natural, desenvolvido na Europa e pensado para homens '
           'que, a partir dos 40 anos, querem cuidar da saúde da próstata e do seu bem-estar geral. Não é um medicamento '
           'e não substitui o acompanhamento do seu médico.'),
    h_made='Como é feito',
    made=['Fabricado na <b>União Europeia</b>, em laboratório que segue as boas práticas de fabrico (GMP).',
          'Produzido sob <b>certificação ISO 22000</b>, a norma internacional de segurança alimentar, com controlo lote a lote.',
          'Fórmula de base natural, <b>sem substâncias químicas sintéticas</b>.',
          'No mercado europeu <b>desde 1995</b>.'],
    h_what='O que leva',
    what=('Oito ingredientes de origem vegetal e nutrientes, numa fórmula estável há anos: Saw Palmetto '
          '<i>(Serenoa repens)</i>, Pygeum africanum, Beta-sitosterol, Zinco, Urtiga <i>(Urtica dioica)</i>, '
          'Semente de abóbora <i>(Cucurbita pepo)</i>, Licopeno e Vitamina E. Cada um está descrito em detalhe, com '
          'as respectivas referências científicas, na secção de ingredientes desta página.'),
    h_users='O que dizem os utilizadores',
    users=('Num inquérito de satisfação feito em 2017, <b>perto de 9 em cada 10</b> dos utilizadores com toma '
           'regular e sem medicação declarada disseram-se <b>satisfeitos ou muito satisfeitos</b> com a experiência '
           'que tiveram com o produto. A base do estudo e os seus limites estão no estudo publicado nesta página.'),
    users_btn='Ver o estudo de satisfação →',
    h_take='Como tomar',
    take=('Tome as cápsulas <b>com as principais refeições</b>, seguindo a dose indicada no rótulo. Como em qualquer '
          'suplemento, a <b>regularidade</b> conta mais do que a quantidade: é a toma continuada, ao longo de semanas, '
          'que faz sentido. Se toma medicação ou tem uma condição diagnosticada, fale com o seu médico ou farmacêutico '
          'antes de começar.'),
    h_life='O que ajuda, para além do suplemento',
    life=['<b>Bebidas que irritam a bexiga.</b> Café, álcool (sobretudo cerveja) e refrigerantes tendem a agravar a '
          'frequência urinária e a urgência. Reduzir sobretudo à noite costuma ser o que dá resultado mais depressa.',
          '<b>Exercício regular.</b> Melhora a circulação na zona pélvica e ajuda a controlar a gordura abdominal, '
          'que anda associada a sintomas urinários mais marcados.',
          '<b>Deixar de fumar.</b> O tabaco afecta a circulação e mantém um estado inflamatório de fundo.',
          '<b>Manter as consultas.</b> Um suplemento não substitui o exame da próstata nem o acompanhamento do '
          'urologista. Depois dos 45, essa vigilância é o que realmente protege.'],
    note=('<b>Suplemento alimentar.</b> Não deve ser utilizado como substituto de um regime alimentar variado e '
          'equilibrado e de um estilo de vida saudável. Leia cuidadosamente a rotulagem e as instruções de utilização '
          'antes de consumir. Os resultados variam de pessoa para pessoa. Este produto não se destina a prevenir, '
          'tratar ou curar qualquer doença; perante sintomas, consulte o seu médico.')),

'br': dict(
    h2='O que o SSP3-Forte pode fazer por você?',
    intro=('O SSP3-Forte é um <b>suplemento alimentar</b> de base natural, desenvolvido na Europa e pensado para homens '
           'que, a partir dos 40 anos, querem cuidar da saúde da próstata e do seu bem-estar geral. Não é um medicamento '
           'e não substitui o acompanhamento do seu médico.'),
    h_made='Como é feito',
    made=['Fabricado na <b>União Europeia</b>, em laboratório que segue as boas práticas de fabricação (GMP).',
          'Produzido sob <b>certificação ISO 22000</b>, a norma internacional de segurança de alimentos, com controle lote a lote.',
          'Fórmula de base natural, <b>sem substâncias químicas sintéticas</b>.',
          'No mercado europeu <b>desde 1995</b>.'],
    h_what='O que leva',
    what=('Oito ingredientes de origem vegetal e nutrientes, numa fórmula estável há anos: Saw Palmetto '
          '<i>(Serenoa repens)</i>, Pygeum africanum, Beta-sitosterol, Zinco, Urtiga <i>(Urtica dioica)</i>, '
          'Semente de abóbora <i>(Cucurbita pepo)</i>, Licopeno e Vitamina E. Cada um está descrito em detalhe, com '
          'as respectivas referências científicas, na seção de ingredientes desta página.'),
    h_users='O que dizem os usuários',
    users=('Numa pesquisa de satisfação feita em 2017, <b>perto de 9 em cada 10</b> dos usuários com uso regular '
           'e sem medicação declarada se disseram <b>satisfeitos ou muito satisfeitos</b> com a experiência que '
           'tiveram com o produto. A base do estudo e seus limites estão no estudo publicado nesta página.'),
    users_btn='Ver o estudo de satisfação →',
    h_take='Como tomar',
    take=('Tome as cápsulas <b>com as principais refeições</b>, seguindo a dose indicada no rótulo. Como em qualquer '
          'suplemento, a <b>regularidade</b> conta mais do que a quantidade: é o uso continuado, ao longo de semanas, '
          'que faz sentido. Se você toma medicação ou tem uma condição diagnosticada, fale com seu médico ou '
          'farmacêutico antes de começar.'),
    h_life='O que ajuda, além do suplemento',
    life=['<b>Bebidas que irritam a bexiga.</b> Café, álcool (sobretudo cerveja) e refrigerantes tendem a agravar a '
          'frequência urinária e a urgência. Reduzir principalmente à noite costuma ser o que dá resultado mais rápido.',
          '<b>Exercício regular.</b> Melhora a circulação na região pélvica e ajuda a controlar a gordura abdominal, '
          'que está associada a sintomas urinários mais marcados.',
          '<b>Parar de fumar.</b> O tabaco afeta a circulação e mantém um estado inflamatório de fundo.',
          '<b>Manter as consultas.</b> Um suplemento não substitui o exame da próstata nem o acompanhamento do '
          'urologista. Depois dos 45, essa vigilância é o que realmente protege.'],
    note=('<b>Suplemento alimentar.</b> Não deve ser utilizado como substituto de uma dieta variada e equilibrada e de '
          'um estilo de vida saudável. Leia atentamente o rótulo e as instruções de uso antes de consumir. Os '
          'resultados variam de pessoa para pessoa. Este produto não se destina a prevenir, tratar ou curar qualquer '
          'doença; diante de sintomas, consulte seu médico.')),

'en': dict(
    h2='What can SSP3-Forte do for you?',
    intro=('SSP3-Forte is a natural <b>food supplement</b>, developed in Europe for men who, from around 40 onwards, '
           'want to look after their prostate health and general wellbeing. It is not a medicine and it does not '
           'replace care from your doctor.'),
    h_made='How it is made',
    made=['Manufactured in the <b>European Union</b>, in a laboratory following Good Manufacturing Practice (GMP).',
          'Produced under <b>ISO 22000 certification</b>, the international food safety standard, with batch-by-batch control.',
          'A natural formula, <b>free of synthetic chemicals</b>.',
          'On the European market <b>since 1995</b>.'],
    h_what='What is in it',
    what=('Eight plant-derived ingredients and nutrients, in a formula unchanged for years: Saw Palmetto '
          '<i>(Serenoa repens)</i>, Pygeum africanum, Beta-sitosterol, Zinc, Nettle <i>(Urtica dioica)</i>, '
          'Pumpkin seed <i>(Cucurbita pepo)</i>, Lycopene and Vitamin E. Each one is described in detail, with its '
          'scientific references, in the ingredients section of this page.'),
    h_users='What users say',
    users=('In a 2017 satisfaction survey, <b>close to 9 in 10</b> of the users taking it regularly and reporting no '
           'medication said they were <b>satisfied or very satisfied</b> with their experience of the product. The '
           'study base and its limits are in the study published on this page.'),
    users_btn='See the satisfaction study →',
    h_take='How to take it',
    take=('Take the capsules <b>with your main meals</b>, following the dose stated on the label. As with any '
          'supplement, <b>regularity</b> matters more than quantity: it is continued use, over weeks, that makes '
          'sense. If you take medication or have a diagnosed condition, speak to your doctor or pharmacist before '
          'starting.'),
    h_life='What helps, beyond the supplement',
    life=['<b>Drinks that irritate the bladder.</b> Coffee, alcohol (beer especially) and soft drinks tend to worsen '
          'urinary frequency and urgency. Cutting back in the evening is usually what works fastest.',
          '<b>Regular exercise.</b> It improves circulation in the pelvic area and helps control abdominal fat, which '
          'is associated with more pronounced urinary symptoms.',
          '<b>Stopping smoking.</b> Tobacco affects circulation and sustains a background inflammatory state.',
          '<b>Keeping your appointments.</b> A supplement is no substitute for a prostate examination or for follow-up '
          'with a urologist. After 45, that is what actually protects you.'],
    note=('<b>Food supplement.</b> It should not be used as a substitute for a varied and balanced diet and a healthy '
          'lifestyle. Read the label and instructions for use carefully before consuming. Results vary from person to '
          'person. This product is not intended to prevent, treat or cure any disease; if you have symptoms, consult '
          'your doctor.')),
}


def block(lang):
    t = T[lang]
    o = ['    <div data-lang="%s">' % lang,
         '      <h2>%s</h2>' % t['h2'],
         '      <p>%s</p>' % t['intro'],
         '      <h3>%s</h3>' % t['h_made'],
         '      <ul>']
    for li in t['made']:
        o.append('        <li>%s</li>' % li)
    o += ['      </ul>',
          '      <h3>%s</h3>' % t['h_what'],
          '      <p>%s</p>' % t['what'],
          '      <h3>%s</h3>' % t['h_users'],
          '      <p>%s</p>' % t['users'],
          '      <p style="margin:0 0 0.85rem;"><button type="button" class="btn-ghost" '
          'onclick="closeInfoModal(); openSurveyModal()">%s</button></p>' % t['users_btn'],
          '      <h3>%s</h3>' % t['h_take'],
          '      <p>%s</p>' % t['take'],
          '      <h3>%s</h3>' % t['h_life'],
          '      <ul>']
    for li in t['life']:
        o.append('        <li>%s</li>' % li)
    o += ['      </ul>',
          '      <div class="modal-note"><p style="margin:0;">%s</p></div>' % t['note'],
          '    </div>']
    return '\n'.join(o)


P = ['<div id="info-modal">',
     '  <div id="info-modal-overlay" onclick="closeInfoModal()"></div>',
     '  <div id="info-modal-box">',
     '    <button id="info-modal-close" onclick="closeInfoModal()" aria-label="Fechar">×</button>',
     '']
for lg in ['pt', 'br', 'en']:
    P.append(block(lg))
    P.append('')
P += ['  </div>', '</div>', '']

doc = '\n'.join(P)
io.open('info_modal.txt', 'w', encoding='utf-8', newline='').write(doc)

banned = ['remédio', 'tratamento natural', 'PSA', 'biópsia', 'cirurgia', 'espermatog',
          'ereç', 'erecç', 'libido', 'normaliza']
print('OK - info_modal.txt,', len(doc), 'caracteres')
print('termos proibidos encontrados:', [w for w in banned if w.lower() in doc.lower()] or 'nenhum')
print('cita 88%:', '88' in doc)
