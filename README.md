# Gestion Institut — Systeme de Gestion d'Institut de Langues + Soutien Scolaire 🇲🇦

Application web **locale** (fonctionne sur ta machine, sans besoin d'internet ni de DB externe).

## 🚀 Démarrage facile (Windows) — AUCUNE commande à taper

**Double-clic sur `demarrer.bat`** (dans le dossier `institut`). Le fichier :
1. Vérifie que Python est installé
2. Installe les dépendances automatiquement (1ère fois)
3. Lance l'application
4. **Ouvre le navigateur tout seul** sur http://localhost:8080

**L'utilisateur n'a rien à comprendre.** Pour arrêter : fermer la fenêtre noire (croix X).

> 💡 Pour un accès plus simple : clic droit sur `demarrer.bat` → *Envoyer vers* → *Bureau* (copie le lanceur sur le bureau).

## Démarrage manuel (avancé)

```bash
pip install -r requirements.txt
python app.py
```
Puis ouvre : **http://localhost:8080** — Login par défaut : `admin` / `admin`

### ⚠️ Problème : « An attempt was made to access a socket... »

Le port **5000 est souvent réservé** sous Windows (Hyper-V). L'application utilise le **port 8080** par défaut. Pour changer :

```bash
python app.py 9090        # port passé en argument
# ou
set PORT=9090
python app.py
```
> Vérifier les ports pris : `netstat -ano | findstr 8080`

---

## Modules (solution complète)

| Module | Description |
|--------|-------------|
| **Tableau de bord** | Statistiques en temps réel, graphiques, alertes |
| **Élèves** | Fiches élèves complètes (photo, parents, niveau scolaire, CIN...) |
| **Cours** | Cours de langues (billing 1 mois / 3 mois) + Soutien scolaire (mensuel) |
| **Inscriptions** | Inscription des élèves aux cours avec plan de paiement |
| **Enseignants** | Fiches, salaires (mensuel/horaire), spécialités |
| **Paiements** | Multi-méthodes : espèces, virement, carte, en ligne (CMI) |
| **Facturation** | Devis + Factures avec **TVA 20%** (format marocain : ICE, IF, RC, patente), numérotation auto |
| **Emploi du temps** | Planning des cours par jour/heure/salle |
| **Absences** | Pointage des absences/retards |
| **Notes / Examens** | Notes et évaluations par cours |
| **Badges** | Impression des badges élève (template configurable) |
| **Rapports** | Rapports financiers, fréquentation, export CSV/PDF |
| **Réglages** | Page de paramètres COMPLÈTE (aucune donnée fictive) |
| **Utilisateurs** | Gestion admin/comptable/enseignant |

## Types de facturation
- **Cours de langues** : paiement **1 mois** ou **3 mois** (configurable par cours)
- **Soutien scolaire** : facturation **mensuelle**
- Facture formelle marocaine avec TVA, numérotation automatique, échéances

## Paiements multi-méthodes
Espèces / Virement bancaire / Carte bancaire / Paiement en ligne (CMI-CIH) — chacun activable dans les réglages.
