# -*- coding: utf-8 -*-
"""
📊 Comparateur de projets — Valeur Actuelle Nette (VAN)

Application Streamlit qui calcule et compare la VAN de plusieurs projets
d'investissement, avec illustrations graphiques interactives (Plotly) :
    - Flux de trésorerie saisis dans un tableau éditable
    - Comparaison des VAN par projet (diagramme en barres)
    - Récupération du capital (flux cumulés actualisés)
    - Sensibilité de la VAN au taux d'actualisation + TRI
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration générale
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="VAN — Comparateur de projets",
    page_icon="📊",
    layout="wide",
)

COULEURS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]


# ---------------------------------------------------------------------------
# Fonctions financières
# ---------------------------------------------------------------------------
def van(flux, taux):
    """Valeur actuelle nette. flux[0] correspond à l'instant 0 (investissement)."""
    flux = np.asarray(flux, dtype=float)
    t = np.arange(len(flux))
    return float(np.sum(flux / (1 + taux) ** t))


def tri(flux):
    """Taux de rentabilité interne (taux qui annule la VAN), ou None.

    On cherche les racines positives du polynôme somme(flux[t] * x^t)
    avec x = 1 / (1 + r).
    """
    flux = np.asarray(flux, dtype=float)
    if not (np.any(flux > 0) and np.any(flux < 0)):
        return None
    racines = np.roots(flux[::-1])
    candidats = [r.real for r in racines if abs(r.imag) < 1e-9 and r.real > 0]
    if not candidats:
        return None
    # Flux « conventionnels » (un seul changement de signe) : un seul TRI réel.
    taux_possibles = sorted(1 / x - 1 for x in candidats)
    return taux_possibles[0]


def delai_recuperation(flux, taux=0.0):
    """Délai de récupération en années (interpolation), ou None si jamais atteint."""
    flux = np.asarray(flux, dtype=float)
    cumul = np.cumsum(flux / (1 + taux) ** np.arange(len(flux)))
    if cumul[0] >= 0:
        return 0.0
    for i in range(1, len(cumul)):
        if cumul[i] >= 0 > cumul[i - 1]:
            flux_actualise_i = flux[i] / (1 + taux) ** i
            if flux_actualise_i == 0:
                return float(i)
            return (i - 1) + (-cumul[i - 1]) / flux_actualise_i
    return None


def indice_profitabilite(flux, taux):
    """Indice de profitabilité = entrées actualisées / sorties actualisées."""
    flux = np.asarray(flux, dtype=float)
    actualise = flux / (1 + taux) ** np.arange(len(flux))
    entrees = actualise[actualise > 0].sum()
    sorties = -actualise[actualise < 0].sum()
    if sorties <= 0:
        return None
    return float(entrees / sorties)


# ---------------------------------------------------------------------------
# Aides d'affichage (format français)
# ---------------------------------------------------------------------------
def fmt_montant(x, devise="€"):
    if x is None or not np.isfinite(x):
        return "—"
    decimales = 2 if abs(x) < 1000 else 0
    return f"{x:,.{decimales}f}".replace(",", " ").replace(".", ",") + f" {devise}"


def fmt_pct(x):
    if x is None:
        return "—"
    return f"{x * 100:.2f}".replace(".", ",") + " %"


def fmt_annees(x):
    if x is None:
        return "Jamais atteint"
    return f"{x:.1f}".replace(".", ",") + " ans"


# ---------------------------------------------------------------------------
# Données d'exemple
# ---------------------------------------------------------------------------
FLUX_EXEMPLE = {
    "Projet A": [-100000, 30000, 30000, 30000, 30000, 30000],
    "Projet B": [-80000, 12000, 20000, 28000, 36000, 44000],
}


def df_par_defaut(noms, n_annees):
    """Tableau des flux : index = Année 0..n, colonnes = projets."""
    index = [f"Année {i}" for i in range(n_annees + 1)]
    df = pd.DataFrame(0.0, index=index, columns=noms)
    exemple = noms == ["Projet A", "Projet B"] and n_annees == 5
    for nom in noms:
        if exemple:
            df[nom] = FLUX_EXEMPLE[nom]
        else:
            df.loc["Année 0", nom] = -100000.0
            df.loc[index[1:], nom] = 30000.0
    return df


# ---------------------------------------------------------------------------
# Barre latérale — paramètres
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Paramètres")

    taux_pct = st.number_input(
        "Taux d'actualisation (% par an)",
        min_value=0.0,
        max_value=100.0,
        value=10.0,
        step=0.5,
        help="Taux utilisé pour actualiser les flux de trésorerie (coût du capital).",
    )
    taux = taux_pct / 100.0

    devise = st.selectbox("Devise", ["€", "$", "MAD", "CHF", "£", "FCFA"])

    noms_saisis = st.text_input(
        "Projets (séparés par des virgules)",
        value="Projet A, Projet B",
        help="Vous pouvez comparer de 1 à 6 projets.",
    )
    noms = [n.strip() for n in noms_saisis.split(",") if n.strip()]
    noms = list(dict.fromkeys(noms))[:6] or ["Projet A"]

    n_annees = st.slider(
        "Horizon du projet (années)",
        min_value=1,
        max_value=30,
        value=5,
    )

    if st.button("🔄 Recharger l'exemple", width="stretch"):
        st.session_state.pop("_signature", None)
        st.session_state.pop(st.session_state.get("_cle_editeur", ""), None)
        st.rerun()

    st.divider()
    st.caption(
        "Astuce : saisissez l'investissement initial en **Année 0** "
        "avec un signe négatif (ex. : -100000)."
    )

# ---------------------------------------------------------------------------
# Saisie des flux de trésorerie
# ---------------------------------------------------------------------------
st.title("📊 Comparateur de projets — Valeur Actuelle Nette")
st.caption(
    "Saisissez les flux de trésorerie de chaque projet, ajustez le taux "
    "d'actualisation, puis comparez les VAN avec les graphiques ci-dessous."
)

st.subheader("1. Flux de trésorerie par année")

signature = f"{noms}|{n_annees}"
cle_editeur = f"editeur|{signature}"

if st.session_state.get("_signature") != signature:
    st.session_state["_signature"] = signature
    st.session_state["df_flux"] = df_par_defaut(noms, n_annees)

st.session_state["_cle_editeur"] = cle_editeur

df_flux = st.data_editor(
    st.session_state["df_flux"],
    key=cle_editeur,
    num_rows="fixed",
    column_config={
        nom: st.column_config.NumberColumn(nom, format="%.2f", step=1000.0)
        for nom in noms
    },
)
df_flux = df_flux.fillna(0.0).astype(float)
st.session_state["df_flux"] = df_flux

if (df_flux == 0).all().all():
    st.info("Saisissez des flux de trésorerie pour lancer l'analyse.")

# ---------------------------------------------------------------------------
# Calculs
# ---------------------------------------------------------------------------
lignes = []
for nom in noms:
    flux = df_flux[nom].to_numpy(dtype=float)
    v = van(flux, taux)
    t_rentabilite = tri(flux)
    lignes.append(
        {
            "Projet": nom,
            "VAN": v,
            "TRI": t_rentabilite,
            "Indice de profitabilité": indice_profitabilite(flux, taux),
            "Délai de récupération": delai_recuperation(flux, 0.0),
            "Délai actualisé": delai_recuperation(flux, taux),
        }
    )

resultats = pd.DataFrame(lignes).sort_values("VAN", ascending=False).reset_index(drop=True)
resultats.insert(0, "Rang", resultats.index + 1)

# ---------------------------------------------------------------------------
# 2. Synthèse par projet
# ---------------------------------------------------------------------------
st.subheader("2. Synthèse des résultats")
st.caption(f"Taux d'actualisation retenu : **{fmt_pct(taux)}**")

colonnes = st.columns(len(resultats))
for colonne, (_, ligne) in zip(colonnes, resultats.iterrows()):
    with colonne:
        with st.container(border=True):
            st.markdown(f"**{ligne['Projet']}**")
            st.metric("VAN", fmt_montant(ligne["VAN"], devise))
            st.metric("TRI", fmt_pct(ligne["TRI"]))
            st.metric("Délai actualisé", fmt_annees(ligne["Délai actualisé"]))

meilleur = resultats.iloc[0]
if meilleur["VAN"] > 0:
    st.success(
        f"🏆 Meilleur projet selon la VAN : **{meilleur['Projet']}** "
        f"({fmt_montant(meilleur['VAN'], devise)}) — VAN positive, projet rentable."
    )
else:
    st.error(
        "❌ Aucun projet n'a de VAN positive au taux retenu : "
        "les investissements ne sont pas rentables à ce taux."
    )

# ---------------------------------------------------------------------------
# Tableau détaillé
# ---------------------------------------------------------------------------
tableau = pd.DataFrame(
    {
        "Rang": resultats["Rang"],
        "Projet": resultats["Projet"],
        f"VAN ({devise})": [fmt_montant(v, devise) for v in resultats["VAN"]],
        "TRI": [fmt_pct(t_) for t_ in resultats["TRI"]],
        "Indice de profitabilité": [
            ("—" if ip is None else f"{ip:.2f}".replace(".", ","))
            for ip in resultats["Indice de profitabilité"]
        ],
        "Délai de récupération": [fmt_annees(d) for d in resultats["Délai de récupération"]],
        "Délai actualisé": [fmt_annees(d) for d in resultats["Délai actualisé"]],
        "Verdict": [
            "✅ Rentable" if v > 0 else "❌ À rejeter" for v in resultats["VAN"]
        ],
    }
)
st.dataframe(tableau, hide_index=True, width="stretch")

csv_resultats = tableau.to_csv(sep=";", decimal=",", index=False).encode("utf-8-sig")
st.download_button(
    "⬇️ Télécharger les résultats (CSV)",
    data=csv_resultats,
    file_name="resultats_van.csv",
    mime="text/csv",
)

# ---------------------------------------------------------------------------
# 3. Illustrations graphiques
# ---------------------------------------------------------------------------
st.subheader("3. Illustrations graphiques")

annees = list(range(len(df_flux)))
onglet1, onglet2, onglet3, onglet4 = st.tabs(
    [
        "💰 Flux de trésorerie",
        "📊 Comparaison des VAN",
        "⏳ Récupération du capital",
        "📈 Sensibilité au taux",
    ]
)

# --- Onglet 1 : flux de trésorerie (barres groupées) -----------------------
with onglet1:
    fig = go.Figure()
    for i, nom in enumerate(noms):
        fig.add_trace(
            go.Bar(
                x=annees,
                y=df_flux[nom],
                name=nom,
                marker_color=COULEURS[i % len(COULEURS)],
            )
        )
    fig.add_hline(y=0, line_width=1, line_color="#444")
    fig.update_layout(
        barmode="group",
        title="Flux de trésorerie par année et par projet",
        xaxis_title="Année",
        yaxis_title=f"Flux de trésorerie ({devise})",
        hovermode="x unified",
        height=480,
        legend_title_text="",
    )
    st.plotly_chart(fig, width="stretch")

# --- Onglet 2 : comparaison des VAN (barres) --------------------------------
with onglet2:
    fig = go.Figure(
        go.Bar(
            x=resultats["Projet"],
            y=resultats["VAN"],
            marker_color=[
                "#2e7d32" if v > 0 else "#c62828" for v in resultats["VAN"]
            ],
            text=[fmt_montant(v, devise) for v in resultats["VAN"]],
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig.add_hline(y=0, line_width=1, line_color="#444")
    fig.update_layout(
        title=f"VAN par projet (taux d'actualisation = {fmt_pct(taux)})",
        yaxis_title=f"VAN ({devise})",
        showlegend=False,
        height=480,
        margin=dict(t=60),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Verdict : une VAN > 0 (barre verte) signifie que le projet crée de "
        "la valeur au taux d'actualisation retenu ; une VAN < 0 (barre rouge) "
        "signifie qu'il détruit de la valeur."
    )

# --- Onglet 3 : flux cumulés actualisés (délai de récupération) -------------
with onglet3:
    fig = go.Figure()
    for i, nom in enumerate(noms):
        flux = df_flux[nom].to_numpy(dtype=float)
        cumul = np.cumsum(flux / (1 + taux) ** np.arange(len(flux)))
        fig.add_trace(
            go.Scatter(
                x=annees,
                y=cumul,
                mode="lines+markers",
                name=nom,
                line=dict(color=COULEURS[i % len(COULEURS)], width=2.5),
            )
        )
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#444",
        annotation_text="Point mort (cumul = 0)",
        annotation_position="bottom right",
    )
    fig.update_layout(
        title="Flux cumulés actualisés — quand le capital investi est récupéré",
        xaxis_title="Année",
        yaxis_title=f"Flux cumulés actualisés ({devise})",
        hovermode="x unified",
        height=480,
        legend_title_text="",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Le projet devient rentable au moment où la courbe dépasse la ligne "
        "zéro : c'est le délai de récupération actualisé."
    )

# --- Onglet 4 : sensibilité de la VAN au taux --------------------------------
with onglet4:
    taux_grille = np.linspace(0.0, 0.35, 71)
    fig = go.Figure()
    for i, nom in enumerate(noms):
        flux = df_flux[nom].to_numpy(dtype=float)
        couleur = COULEURS[i % len(COULEURS)]
        fig.add_trace(
            go.Scatter(
                x=taux_grille * 100,
                y=[van(flux, t) for t in taux_grille],
                mode="lines",
                name=nom,
                line=dict(color=couleur, width=2.5),
                hovertemplate=f"{nom}<br>Taux : %{{x:.1f}} %<br>VAN : %{{y:,.0f}} {devise}<extra></extra>",
            )
        )
        t_rentabilite = tri(flux)
        if t_rentabilite is not None and 0 <= t_rentabilite <= 0.35:
            fig.add_trace(
                go.Scatter(
                    x=[t_rentabilite * 100],
                    y=[0],
                    mode="markers+text",
                    name=f"TRI — {nom}",
                    marker=dict(color=couleur, size=11, symbol="diamond"),
                    text=[f"TRI {fmt_pct(t_rentabilite)}"],
                    textposition="top center",
                    showlegend=False,
                )
            )
    fig.add_hline(y=0, line_width=1, line_color="#444")
    fig.add_vline(
        x=taux * 100,
        line_dash="dot",
        line_color="#666",
        annotation_text="Taux retenu",
        annotation_position="top",
    )
    fig.update_layout(
        title="VAN en fonction du taux d'actualisation (TRI = intersection avec zéro)",
        xaxis_title="Taux d'actualisation (%)",
        yaxis_title=f"VAN ({devise})",
        hovermode="x unified",
        height=480,
        legend_title_text="",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Chaque courbe croise l'axe zéro au TRI du projet : le projet reste "
        "rentable tant que le taux d'actualisation est inférieur à son TRI."
    )

# ---------------------------------------------------------------------------
# Aide-mémoire
# ---------------------------------------------------------------------------
with st.expander("📚 Rappel des formules et définitions"):
    st.markdown(
        "**Valeur Actuelle Nette (VAN)** : la somme des flux de trésorerie "
        "futurs actualisés, moins l'investissement initial :"
    )
    st.latex(r"VAN = -I_0 + \sum_{t=1}^{n} \frac{CF_t}{(1+r)^t}")
    st.markdown(
        "- **TRI** : taux d'actualisation pour lequel la VAN est nulle.\n"
        "- **Indice de profitabilité** : entrées actualisées ÷ sorties actualisées. "
        "Un indice > 1 signifie une VAN > 0.\n"
        "- **Délai de récupération** : temps nécessaire pour que les flux "
        "cumulés (actualisés ou non) redeviennent positifs.\n"
        "- **Critère de décision** : un projet est rentable si sa VAN > 0 "
        "(équivalent à TRI > r pour un projet classique)."
    )
