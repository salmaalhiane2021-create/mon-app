# 📊 Comparateur de projets — Valeur Actuelle Nette (VAN)

Application financière **Streamlit** pour calculer et **comparer la VAN** de
plusieurs projets d'investissement, avec illustrations graphiques interactives.

## Fonctionnalités

- Tableau éditable des **flux de trésorerie** (Année 0 = investissement initial).
- Calcul automatique de :
  - **VAN** (Valeur Actuelle Nette) à votre taux d'actualisation,
  - **TRI** (Taux de Rentabilité Interne),
  - **Indice de profitabilité**,
  - **Délai de récupération** simple et actualisé.
- Classement des projets (rang, verdict rentable / à rejeter).
- Graphiques Plotly :
  1. Flux de trésorerie par année et par projet (barres groupées) ;
  2. Comparaison des VAN par projet (barres vertes / rouges) ;
  3. Flux cumulés actualisés (visualisation du délai de récupération) ;
  4. Sensibilité de la VAN au taux d'actualisation, avec marqueur du TRI.
- Export des résultats en CSV (compatible Excel français).

## Installation

```powershell
pip install -r requirements.txt
```

## Lancement

```powershell
streamlit run app.py
```

L'application s'ouvre dans le navigateur à l'adresse `http://localhost:8501`.

## Utilisation

1. Dans la barre latérale, choisissez le **taux d'actualisation**, la **devise**,
   les **projets** (noms séparés par des virgules) et l'**horizon** (années).
2. Saisissez les flux de trésorerie dans le tableau : investissement initial en
   Année 0 avec un signe négatif (ex. `-100000`), puis les recettes de chaque
   année.
3. Consultez la synthèse, le classement et les graphiques dans les onglets.

## Formule de la VAN

$$VAN = -I_0 + \sum_{t=1}^{n} \frac{CF_t}{(1+r)^t}$$

Un projet est rentable si sa VAN > 0, ce qui équivaut à TRI > r pour un
projet à flux classiques.
