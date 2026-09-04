# -*- coding: utf-8 -*-
"""Gera o bloco HTML do #survey-modal nas tres linguas (pt / br / en).

Regras acordadas com o cliente:
  - titulo fixo "Estudo de satisfacao a utilizadores (2017)";
  - a base de 290 questionarios so aparece no rodape em letra pequena;
  - a palavra "apenas" nao pode aparecer;
  - nada de comparacao com a amostra completa no corpo (e analise interna);
  - IC e p-value sao admissiveis, mas so na letra pequena;
  - leitura simples e grafica, orientada a venda.
"""
import io

GOLD = '#c9a84c'
GREEN_MID = '#1a6645'
GREY_1 = '#c3d0c9'
PALE = '#e6ede9'

# --- graficos --------------------------------------------------------------

def donut(pct, label):
    r = 58.0
    circ = 2 * 3.141592653589793 * r
    on = circ * pct / 100.0
    return (
'<svg class="sv-donut" viewBox="0 0 140 140" role="img" aria-label="%s">\n'
'          <circle cx="70" cy="70" r="58" fill="none" stroke="%s" stroke-width="17"/>\n'
'          <circle cx="70" cy="70" r="58" fill="none" stroke="%s" stroke-width="17" stroke-linecap="round"\n'
'                  stroke-dasharray="%.1f %.1f" transform="rotate(-90 70 70)"/>\n'
'          <text x="70" y="71" text-anchor="middle" dominant-baseline="central" font-family="Lora, Georgia, serif"\n'
'                font-size="36" font-weight="600" fill="#0d3d2b">%d%%</text>\n'
'        </svg>' % (label, PALE, GOLD, on, circ - on, int(round(pct))))


def pictogram(filled, total, label):
    """Bonecos: `filled` a dourado, o resto a cinzento claro."""
    pitch, w = 24, 20
    o = ['<svg class="sv-pic" viewBox="0 0 %d 40" role="img" aria-label="%s">' % ((total - 1) * pitch + w, label)]
    for i in range(total):
        o.append('          <g transform="translate(%d 0)" fill="%s">'
                 '<circle cx="10" cy="8.5" r="7.2"/>'
                 '<path d="M10 19c-6.4 0-10 3.9-10 10.8V39h20v-9.2C20 22.9 16.4 19 10 19z"/></g>'
                 % (i * pitch, GOLD if i < filled else GREY_1))
    o.append('        </svg>')
    return '\n'.join(o)


def table(head, body, total=None):
    """head: 3 titulos; body/total: (rotulo, n, valor, largura_barra)."""
    o = ['<table class="sv-table">']
    o.append('          <tr><th>%s</th><th class="n">%s</th><th class="n">%s</th><th></th></tr>' % tuple(head))
    for lab, n, val, w in body:
        o.append('          <tr><td>%s</td><td class="n">%s</td><td class="n">%s</td>'
                 '<td class="b"><span class="sv-bar" style="width:%.1f%%"></span></td></tr>' % (lab, n, val, w))
    if total:
        lab, n, val, w = total
        o.append('          <tr class="tot"><td>%s</td><td class="n">%s</td><td class="n">%s</td>'
                 '<td class="b"><span class="sv-bar" style="width:%.1f%%"></span></td></tr>' % (lab, n, val, w))
    o.append('        </table>')
    return '\n'.join(o)


# --- numeros ---------------------------------------------------------------
# 67 utilizadores: 22 muito satisfeitos, 37 satisfeitos, 7 pouco, 1 nada.
SAT = 88.06

T = {
'pt': dict(
    h2='Estudo de satisfação a utilizadores (2017)',
    lead='Homens que tomaram o SSP3-Forte com regularidade responderam a um questionário sobre a experiência '
         'que tiveram com o produto. Foi isto que disseram.',
    donut_alt='88 por cento satisfeitos',
    donut_b='88% ficaram satisfeitos ou muito satisfeitos',
    donut_s='Resultado dos 67 utilizadores com toma regular que responderam ao estudo.',
    pic_alt='Quase nove em cada dez satisfeitos',
    pic_cap='Quase <b>9 em cada 10</b> ficaram satisfeitos',
    h_resp='Respostas',
    head_resp=('Resposta', 'n', '%'),
    resp=[('Muito satisfeito', 22, '32,8', 32.8), ('Satisfeito', 37, '55,2', 55.2),
          ('Pouco satisfeito', 7, '10,4', 10.4), ('Nada satisfeito', 1, '1,5', 1.5)],
    resp_tot=('Satisfeitos ou muito satisfeitos', 59, '88,1', 88.1),
    cap_resp='Os 67 responderam todos a esta pergunta. Intervalo de confiança a 95% para os 88,1%: 80,3 a 95,8.',
    h_time='Satisfação por tempo de toma',
    head_time=('Tempo de toma', 'n', 'Satisfeitos'),
    time=[('3 meses', 11, '81,8%', 81.8), ('6 meses', 15, '80,0%', 80.0)],
    time_tot=('Mais de 1 ano', 38, '92,1%', 92.1),
    cap_time='A banda de 1 mês tinha três respostas e foi omitida: com tão poucas pessoas, qualquer percentagem '
             'seria enganadora. Nas bandas apresentadas os intervalos de confiança são largos, pelo que a subida '
             'ao fim de um ano não é conclusiva.',
    kicker='Entre quem já tomava o SSP3-Forte <b>há mais de um ano</b>, a satisfação sobe para <b>92%</b>.',
    fine_h='Sobre este estudo',
    fine=[
      '<b>Base do estudo.</b> Em 2017 foram reunidos 290 questionários preenchidos por utilizadores do SSP3-Forte. '
      'Os resultados desta página referem-se ao grupo de 67 desses utilizadores que declararam tomar o produto com '
      'regularidade e não declararam estar a tomar medicação; os restantes 223 questionários não entram nestes números. '
      'Considerando todos os 290 questionários, 81,3% declararam-se satisfeitos ou muito satisfeitos. A ausência de '
      'medicação corresponde a um campo do questionário deixado em branco, que tanto pode significar «não tomo nenhum '
      'medicamento» como «não respondi a esta pergunta». Quem interrompeu o produto não pode ter declarado toma regular, '
      'pelo que este grupo não inclui quem terá tido pior experiência. O grupo foi definido depois de os dados terem '
      'sido observados, e a diferença face aos restantes inquiridos não é estatisticamente significativa (p = 0,106).',
      '<b>Limites.</b> Estes resultados são declarações de satisfação de clientes, recolhidas por questionário. Não '
      'resultam de um ensaio clínico. Não houve grupo de comparação nem medição antes e depois da toma, pelo que '
      'nenhuma melhoria pode ser medida a partir deste estudo. Os inquiridos responderam voluntariamente e não '
      'constituem uma amostra aleatória da população. Intervalos de confiança a 95% por aproximação normal; '
      'comparações por teste z para duas proporções, bilateral.',
      '<b>Enquadramento legal.</b> Nada nesta página constitui uma alegação de saúde. Na União Europeia, as alegações '
      'de saúde sobre suplementos alimentares só são permitidas se constarem da lista autorizada ao abrigo do '
      'Regulamento (CE) n.º 1924/2006. Estes resultados não sustentam qualquer afirmação sobre PSA, tamanho da próstata, '
      'sintomas urinários, biópsia ou cirurgia. O SSP3-Forte é um suplemento alimentar, os resultados variam de pessoa '
      'para pessoa e não substitui aconselhamento, diagnóstico ou tratamento médico.',
    ]),
'br': dict(
    h2='Estudo de satisfação com usuários (2017)',
    lead='Homens que tomaram o SSP3-Forte com regularidade responderam a um questionário sobre a experiência '
         'que tiveram com o produto. Foi isto que eles disseram.',
    donut_alt='88 por cento satisfeitos',
    donut_b='88% ficaram satisfeitos ou muito satisfeitos',
    donut_s='Resultado dos 67 usuários com uso regular que responderam ao estudo.',
    pic_alt='Quase nove em cada dez satisfeitos',
    pic_cap='Quase <b>9 em cada 10</b> ficaram satisfeitos',
    h_resp='Respostas',
    head_resp=('Resposta', 'n', '%'),
    resp=[('Muito satisfeito', 22, '32,8', 32.8), ('Satisfeito', 37, '55,2', 55.2),
          ('Pouco satisfeito', 7, '10,4', 10.4), ('Nada satisfeito', 1, '1,5', 1.5)],
    resp_tot=('Satisfeitos ou muito satisfeitos', 59, '88,1', 88.1),
    cap_resp='Todos os 67 responderam a esta pergunta. Intervalo de confiança de 95% para os 88,1%: 80,3 a 95,8.',
    h_time='Satisfação por tempo de uso',
    head_time=('Tempo de uso', 'n', 'Satisfeitos'),
    time=[('3 meses', 11, '81,8%', 81.8), ('6 meses', 15, '80,0%', 80.0)],
    time_tot=('Mais de 1 ano', 38, '92,1%', 92.1),
    cap_time='A faixa de 1 mês tinha três respostas e foi omitida: com tão poucas pessoas, qualquer porcentagem '
             'seria enganosa. Nas faixas apresentadas os intervalos de confiança são largos, de modo que a subida '
             'ao fim de um ano não é conclusiva.',
    kicker='Entre quem já tomava o SSP3-Forte <b>há mais de um ano</b>, a satisfação sobe para <b>92%</b>.',
    fine_h='Sobre este estudo',
    fine=[
      '<b>Base do estudo.</b> Em 2017 foram reunidos 290 questionários preenchidos por usuários do SSP3-Forte. '
      'Os resultados desta página se referem ao grupo de 67 desses usuários que declararam tomar o produto com '
      'regularidade e não declararam estar tomando medicação; os demais 223 questionários não entram nestes números. '
      'Considerando todos os 290 questionários, 81,3% se declararam satisfeitos ou muito satisfeitos. A ausência de '
      'medicação corresponde a um campo do questionário deixado em branco, que tanto pode significar "não tomo nenhum '
      'medicamento" quanto "não respondi a esta pergunta". Quem interrompeu o produto não pode ter declarado uso regular, '
      'de modo que este grupo não inclui quem provavelmente teve a pior experiência. O grupo foi definido depois de os '
      'dados terem sido observados, e a diferença em relação aos demais respondentes não é estatisticamente '
      'significativa (p = 0,106).',
      '<b>Limites.</b> Estes resultados são declarações de satisfação de clientes, coletadas por questionário. Não são '
      'resultado de um ensaio clínico. Não houve grupo de comparação nem medição antes e depois do uso, de modo que '
      'nenhuma melhora pode ser medida a partir deste estudo. Os respondentes participaram voluntariamente e não '
      'constituem uma amostra aleatória da população. Intervalos de confiança de 95% por aproximação normal; '
      'comparações por teste z para duas proporções, bilateral.',
      '<b>Enquadramento legal.</b> Nada nesta página constitui alegação de saúde. Na União Europeia, as alegações de '
      'saúde sobre suplementos alimentares só são permitidas se constarem da lista autorizada pelo Regulamento (CE) '
      'n.º 1924/2006. Estes resultados não sustentam qualquer afirmação sobre PSA, tamanho da próstata, sintomas '
      'urinários, biópsia ou cirurgia. O SSP3-Forte é um suplemento alimentar, os resultados variam de pessoa para '
      'pessoa e não substitui orientação, diagnóstico ou tratamento médico.',
    ]),
'en': dict(
    h2='User satisfaction study (2017)',
    lead='Men who took SSP3-Forte regularly answered a questionnaire about their experience with the product. '
         'This is what they said.',
    donut_alt='88 per cent satisfied',
    donut_b='88% were satisfied or very satisfied',
    donut_s='Result among the 67 regular users who took part in the study.',
    pic_alt='Almost nine in ten satisfied',
    pic_cap='Almost <b>9 in 10</b> were satisfied',
    h_resp='Responses',
    head_resp=('Answer', 'n', '%'),
    resp=[('Very satisfied', 22, '32.8', 32.8), ('Satisfied', 37, '55.2', 55.2),
          ('Slightly satisfied', 7, '10.4', 10.4), ('Not satisfied', 1, '1.5', 1.5)],
    resp_tot=('Satisfied or very satisfied', 59, '88.1', 88.1),
    cap_resp='All 67 answered this question. 95% confidence interval for the 88.1%: 80.3 to 95.8.',
    h_time='Satisfaction by length of use',
    head_time=('Length of use', 'n', 'Satisfied'),
    time=[('3 months', 11, '81.8%', 81.8), ('6 months', 15, '80.0%', 80.0)],
    time_tot=('More than 1 year', 38, '92.1%', 92.1),
    cap_time='The 1-month band held three answers and was left out: with so few people, any percentage would '
             'mislead. In the bands shown the confidence intervals are wide, so the rise after a year is not '
             'conclusive.',
    kicker='Among those who had been taking SSP3-Forte for <b>more than a year</b>, satisfaction rises to <b>92%</b>.',
    fine_h='About this study',
    fine=[
      '<b>Study base.</b> In 2017, 290 questionnaires were collected from users of SSP3-Forte. The results on this page '
      'describe the group of 67 of those users who reported taking the product regularly and reported no medication; '
      'the remaining 223 questionnaires are not in these figures. Across all 290 questionnaires, 81.3% reported being '
      'satisfied or very satisfied. "No medication" means the medication field of the questionnaire was left blank, '
      'which can mean either "I take none" or "I did not answer this question". Anyone who stopped taking the product '
      'cannot have reported regular use, so this group leaves out those likely to have had the worst experience. The '
      'group was defined after the data had been examined, and the difference from the other respondents is not '
      'statistically significant (p = 0.106).',
      '<b>Limits.</b> These results are customer statements of satisfaction, collected by questionnaire. They are not '
      'the result of a clinical trial. There was no comparison group and no before-and-after measurement, so no '
      'improvement can be measured from this study. Respondents took part voluntarily and are not a random sample of '
      'any population. 95% confidence intervals by normal approximation; comparisons by two-proportion z-test, '
      'two-sided.',
      '<b>Legal framework.</b> Nothing on this page constitutes a health claim. In the European Union, health claims on '
      'food supplements are permitted only if they appear on the authorised list under Regulation (EC) No 1924/2006. '
      'These results support no statement about PSA, prostate size, urinary symptoms, biopsy or surgery. SSP3-Forte is '
      'a food supplement, results vary from person to person, and it is not a substitute for medical advice, diagnosis '
      'or treatment.',
    ]),
}


def block(lang):
    t = T[lang]
    o = []
    A = o.append
    A('    <div data-lang="%s">' % lang)
    A('      <h2>%s</h2>' % t['h2'])
    A('      <p class="sv-lead">%s</p>' % t['lead'])

    A('      <div class="sv-donut-row">')
    A('        ' + donut(SAT, t['donut_alt']))
    A('        <div class="sv-donut-cap"><b>%s</b><span>%s</span></div>' % (t['donut_b'], t['donut_s']))
    A('      </div>')

    A('      <div class="sv-block">')
    A('        ' + pictogram(9, 10, t['pic_alt']))
    A('        <p class="sv-pic-cap">%s</p>' % t['pic_cap'])
    A('      </div>')

    A('      <div class="sv-block">')
    A('        <p class="sv-h">%s</p>' % t['h_resp'])
    A('        ' + table(t['head_resp'], t['resp'], t['resp_tot']))
    A('        <p class="sv-cap">%s</p>' % t['cap_resp'])
    A('      </div>')

    A('      <div class="sv-block">')
    A('        <p class="sv-h">%s</p>' % t['h_time'])
    A('        ' + table(t['head_time'], t['time'], t['time_tot']))
    A('        <p class="sv-cap">%s</p>' % t['cap_time'])
    A('      </div>')

    A('      <div class="sv-kicker">%s</div>' % t['kicker'])

    A('      <div class="sv-fine">')
    A('        <h4>%s</h4>' % t['fine_h'])
    for p in t['fine']:
        A('        <p>%s</p>' % p)
    A('      </div>')
    A('    </div>')
    return '\n'.join(o)


P = ['<!-- SURVEY MODAL - satisfaction study, chart-led. Generated by scratchpad/gen_survey.py -->',
     '<div id="survey-modal">',
     '  <div id="survey-modal-overlay" onclick="closeSurveyModal()"></div>',
     '  <div id="survey-modal-box">',
     '    <button id="survey-modal-close" onclick="closeSurveyModal()" aria-label="Fechar">×</button>',
     '']
for lg in ['pt', 'br', 'en']:
    P.append(block(lg))
    P.append('')
P += ['  </div>', '</div>', '']

doc = '\n'.join(P)
io.open('survey_modal_v2.txt', 'w', encoding='utf-8', newline='').write(doc)

print('OK - survey_modal_v2.txt,', len(doc), 'caracteres')
print('"apenas":', [w for w in ['apenas', 'Apenas'] if w in doc] or 'nenhuma ocorrencia')
bodies = [b.split('sv-fine')[0] for b in doc.split('data-lang=')[1:]]
print('"290" fora do rodape:', any('290' in b for b in bodies))
print('comparacao com amostra completa no corpo:', any('81,3' in b or '81.3' in b or '289' in b for b in bodies))
