# QuantEdge — architecture V1

## Objectif
Moteur de recherche quantitatif indépendant de Weinstein'S, initialement en PAPER (500 EUR), sans passage d'ordres réels.

## Modules
- `ingestion`: historique ajusté, volumes, calendrier de cotation, provenance et horodatage.
- `signals`: momentum 12-1 mois, suivi de tendance, filtres de liquidité.
- `portfolio`: portefeuille PAPER, liquidités, tailles de positions, frais, journal d'ordres.
- `backtest`: simulation événementielle avec dates de disponibilité, frais et glissement.
- `api`: FastAPI; `web`: Next.js; `db`: PostgreSQL.

## Contraintes de validation
- Aucun prix futur dans les signaux; exécution au plus tôt à la séance suivante.
- Univers historique daté pour limiter le biais de survivance.
- Données gratuites seulement, cache local, contrôles d'intégrité et gestion des indisponibilités.
- Comparaison à un portefeuille passif et à Weinstein'S à capital et frais comparables.
- Tests unitaires, d'intégration, et backtest hors échantillon avant activation PAPER.
- Absence de données valides = aucun ordre.

## Livraison progressive
V1a: modèle de données, ingestion et tests.
V1b: signaux et backtesting.
V1c: API, interface, portefeuille PAPER.
