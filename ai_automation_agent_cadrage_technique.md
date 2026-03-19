# AI Automation Agent — Cadrage technique MVP

## 1. Vision du projet
Construire un **AI Automation Agent** centré sur un cas d’usage métier simple, démontrable et vendable :

**Email triage + reporting copilot**

Le système reçoit un email, un texte ou une demande métier, puis :
1. classe la demande,
2. résume le contenu,
3. extrait les informations utiles,
4. choisit une stratégie,
5. génère une sortie utile,
6. demande validation humaine,
7. journalise le run.

L’objectif n’est pas de faire un “agent magique”, mais un **workflow agentique étroit, explicable et observable**.

---

## 2. Proposition de valeur
Le produit doit démontrer qu’il peut :
- réduire les tâches répétitives,
- accélérer le tri des demandes,
- générer plus vite des réponses et des mini-rapports,
- offrir une traçabilité claire,
- rester sous contrôle humain.

---

## 3. Cas d’usage MVP

### Cas principal
**Email & Reporting Automation**

### Entrées supportées
- texte libre,
- contenu d’email collé,
- document texte simple,
- payload JSON simulé via API.

### Catégories initiales
- support,
- reporting,
- commercial,
- administratif,
- autre.

### Sorties possibles
- résumé court,
- champs extraits,
- brouillon d’email,
- mini rapport markdown,
- tâche simulée à créer,
- décision d’escalade humaine.

---

## 4. Effet différenciant
Le MVP doit inclure 4 éléments “waouh” :

### 4.1 Explainability panel
Afficher :
- catégorie choisie,
- confiance,
- indices détectés,
- stratégie retenue,
- justification synthétique.

### 4.2 Timeline d’exécution
Afficher :
- input reçu,
- classification,
- extraction,
- génération,
- validation,
- sauvegarde.

### 4.3 Automation score
Calcul heuristique affichant :
- score d’automatisation,
- niveau de risque,
- temps économisé estimé,
- recommandation d’autonomie.

### 4.4 Learning from corrections
Quand l’utilisateur corrige une sortie :
- stocker la correction,
- l’afficher dans l’historique,
- la réutiliser comme préférence simple.

---

## 5. Architecture fonctionnelle

```text
UI / API Input
    -> Preprocessor
    -> Classifier
    -> Router
    -> Tool Executor
    -> Output Generator
    -> Human Review
    -> Persistence / Logs / Feedback
```

---

## 6. Choix d’architecture

### Recommandation
Architecture **single-agent + tools + routing semi-déterministe**.

### Pourquoi
- plus simple à finir,
- plus robuste,
- plus crédible pour un premier portfolio,
- plus facile à expliquer à un client,
- plus simple à tester.

### Ce qu’on évite au MVP
- multi-agent,
- mémoire longue durée,
- intégrations multiples réelles,
- autonomie totale,
- orchestration trop complexe.

---

## 7. Stack technique recommandée

### Back-end
- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy ou SQLModel

### LLM
- provider configurable
- prompts séparés par tâche

### Base de données
- SQLite pour MVP
- migration possible vers Postgres

### Front
- Streamlit pour vitesse
- ou React plus tard si besoin produit

### Observabilité
- logs JSON
- table `runs`
- table `feedback`
- temps par étape
- coût estimé par run

### Automation optionnelle
- n8n en bonus pour montrer la partie workflow

---

## 8. Composants principaux

### 8.1 Input layer
Responsable de :
- recevoir le texte,
- nettoyer le contenu,
- normaliser les entrées,
- générer un `request_id`.

### 8.2 Classifier
Produit :
- catégorie,
- confiance,
- explication courte.

### 8.3 Extractor
Extrait :
- priorité,
- sujet,
- deadline,
- acteur,
- action demandée,
- canal,
- ton.

### 8.4 Router
Décide du flux :
- simple résumé,
- génération email,
- mini rapport,
- création tâche simulée,
- escalade.

### 8.5 Generator
Génère :
- réponse email,
- mini rapport markdown,
- action plan,
- sortie JSON.

### 8.6 Reviewer
Expose :
- approuver,
- corriger,
- régénérer,
- escalader.

### 8.7 Persistence
Sauvegarde :
- input,
- classification,
- extraction,
- sortie,
- logs,
- feedback.

---

## 9. Outils internes de l’agent

```python
classify_request(text) -> category, confidence, rationale
extract_fields(text) -> structured_json
summarize_request(text) -> summary
generate_email_reply(text, extracted_fields, style) -> reply
generate_report(text, extracted_fields) -> markdown
compute_automation_score(classification, confidence, risk) -> score
save_run(run_data) -> run_id
save_feedback(run_id, correction) -> feedback_id
```

---

## 10. Modèle de données

### Table `runs`
- id
- created_at
- input_text
- input_type
- category
- confidence
- rationale
- extracted_fields_json
- summary
- generated_output
- output_type
- automation_score
- risk_level
- status
- latency_ms
- estimated_cost

### Table `feedback`
- id
- run_id
- created_at
- field_name
- previous_value
- corrected_value
- comment

### Table `preferences`
- id
- key
- value
- source
- updated_at

---

## 11. API design MVP

### POST `/api/v1/runs`
Créer un run.

**Input**
```json
{
  "text": "Bonjour, notre export KPI plante depuis hier.",
  "input_type": "email",
  "mode": "assisted"
}
```

**Output**
```json
{
  "run_id": "run_123",
  "category": "support",
  "confidence": 0.87,
  "summary": "Le client signale un problème d'export KPI depuis hier.",
  "strategy": ["summarize", "generate_email_reply", "create_task"],
  "automation_score": 74,
  "risk_level": "medium"
}
```

### GET `/api/v1/runs/{run_id}`
Récupérer un run complet.

### GET `/api/v1/runs`
Lister les derniers runs.

### POST `/api/v1/runs/{run_id}/approve`
Approuver la sortie.

### POST `/api/v1/runs/{run_id}/regenerate`
Régénérer selon une stratégie différente.

### POST `/api/v1/runs/{run_id}/feedback`
Sauvegarder une correction.

### GET `/api/v1/metrics`
Retourner quelques métriques :
- nombre de runs,
- taux d’approbation,
- répartition des catégories,
- score moyen.

---

## 12. UX / UI recommandée

### Page principale
**Bloc gauche**
- zone d’entrée,
- sélecteur de mode,
- bouton lancer.

**Bloc central**
- classification,
- confiance,
- résumé,
- champs extraits.

**Bloc droit**
- timeline,
- outils utilisés,
- temps par étape,
- coût estimé,
- automation score.

**Bloc bas**
- sortie générée,
- boutons approuver / corriger / relancer / escalader.

### Page historique
- liste des runs,
- filtres par catégorie,
- statut,
- score,
- date.

### Page analytics simple
- nombre de runs,
- taux d’approbation,
- top catégories,
- feedbacks les plus fréquents.

---

## 13. Modes d’autonomie

### Mode 0 — Suggestion
L’agent propose uniquement.

### Mode 1 — Assisted
L’agent prépare la sortie, humain valide.

### Mode 2 — Auto low-risk
Actions automatiques seulement pour cas faible risque.

Le MVP peut exposer les 3 modes visuellement, mais implémenter surtout 0 et 1.

---

## 14. Prompting strategy

### Prompt 1 — Classification
Objectif : classer la demande dans une catégorie fermée avec justification courte.

### Prompt 2 — Extraction
Objectif : retourner un JSON strict avec les champs métier utiles.

### Prompt 3 — Summary
Objectif : produire un résumé de 2 à 4 lignes.

### Prompt 4 — Email reply
Objectif : produire une réponse claire, professionnelle, concise.

### Prompt 5 — Report generation
Objectif : générer un mini rapport markdown avec sections fixes.

### Prompt 6 — Risk and automation score
Objectif : proposer un score et une recommandation d’autonomie, avec justification courte.

---

## 15. Règles de garde-fous
- ne jamais envoyer automatiquement un email réel dans le MVP,
- ne jamais exécuter une action externe irréversible,
- toujours demander validation pour les cas moyens/élevés,
- logguer chaque décision,
- afficher la confiance et la justification,
- forcer les sorties JSON pour les étapes structurées.

---

## 16. Jeu de données démo
Créer environ 20 exemples répartis entre :
- support,
- reporting,
- commercial,
- administratif.

Chaque exemple doit permettre de démontrer :
- bonne classification,
- extraction utile,
- sortie cohérente,
- correction possible.

---

## 17. Arborescence du repo

```text
ai-automation-agent/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── routes_runs.py
│   │   └── routes_metrics.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── models/
│   │   ├── run.py
│   │   ├── feedback.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── preprocess.py
│   │   ├── classifier.py
│   │   ├── extractor.py
│   │   ├── summarizer.py
│   │   ├── email_generator.py
│   │   ├── report_generator.py
│   │   ├── scorer.py
│   │   ├── orchestrator.py
│   │   └── persistence.py
│   ├── prompts/
│   │   ├── classification.txt
│   │   ├── extraction.txt
│   │   ├── summary.txt
│   │   ├── email_reply.txt
│   │   ├── report.txt
│   │   └── score.txt
│   └── db/
│       ├── session.py
│       └── init_db.py
├── ui/
│   └── streamlit_app.py
├── data/
│   └── demo_requests.json
├── tests/
│   ├── test_classifier.py
│   ├── test_extractor.py
│   ├── test_orchestrator.py
│   └── test_api.py
├── .env.example
├── README.md
├── requirements.txt
└── docker-compose.yml
```

---

## 18. Roadmap d’implémentation en 7 jours

### Jour 1
- cadrage,
- modèles de données,
- structure repo,
- config projet.

### Jour 2
- FastAPI,
- endpoint create run,
- persistence SQLite,
- logs.

### Jour 3
- classification,
- résumé,
- extraction,
- prompts initiaux.

### Jour 4
- routing,
- génération email,
- génération report,
- score d’automatisation.

### Jour 5
- UI Streamlit,
- vue run,
- timeline,
- panneau explainability.

### Jour 6
- feedback,
- historique,
- métriques,
- polish.

### Jour 7
- tests,
- dataset de démo,
- README,
- screenshots,
- texte portfolio Malt.

---

## 19. Critères de réussite MVP
- 20 exemples démo exploitables,
- UI utilisable,
- classification correcte sur la majorité des cas,
- sorties lisibles,
- timeline visible,
- explainability visible,
- feedback sauvegardé,
- README clair,
- démo faisable en moins de 3 minutes.

---

## 20. Version 2 possible
- intégration email réelle,
- connecteur Slack,
- connecteur ticketing,
- mémoire améliorée,
- règles configurables,
- dashboard analytics enrichi,
- évaluation automatique des runs,
- multi-step workflows plus avancés.

---

## 21. Positionnement portfolio / Malt

### Titre projet
Agent IA d’automatisation de demandes métier et de reporting

### Résumé
Développement d’un agent IA capable de trier, résumer, structurer et traiter automatiquement des demandes métier récurrentes, avec génération de réponses, rapports et actions simples, tout en gardant une validation humaine et une observabilité complète.

### Promesse client
- moins de tâches répétitives,
- meilleure réactivité,
- reporting plus fluide,
- système explicable et contrôlable.

