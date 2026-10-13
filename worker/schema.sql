-- Funil de encomendas do ssp3forte.com
--
-- Criar a base de dados (uma vez, na pasta worker/):
--     npx wrangler d1 create ssp3forte-funnel
-- Colar o database_id devolvido no wrangler.toml, e depois:
--     npx wrangler d1 execute ssp3forte-funnel --remote --file=schema.sql
--
-- Nao ha aqui dados pessoais, de proposito: nem IP, nem user-agent, nem email,
-- nem nada guardado no dispositivo do visitante. O "session" e um numero
-- aleatorio que o browser gera em memoria a cada carregamento da pagina e
-- esquece ao fechar -- serve para ligar os passos de uma mesma visita e nada
-- mais. Sem cookies e sem armazenamento local, isto nao precisa de
-- consentimento de cookies.

CREATE TABLE IF NOT EXISTS events (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  ts      TEXT NOT NULL,   -- instante, ISO 8601
  day     TEXT NOT NULL,   -- YYYY-MM-DD, para agrupar
  name    TEXT NOT NULL,   -- view | order_view | form_start | submit | order_ok | order_fail
  lang    TEXT,            -- pt | br | en
  session TEXT,            -- aleatorio por carregamento, so em memoria no cliente
  detail  TEXT             -- motivo, nas falhas
);

CREATE INDEX IF NOT EXISTS idx_events_day     ON events(day);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session);
CREATE INDEX IF NOT EXISTS idx_events_name    ON events(name);
