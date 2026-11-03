# 📖 Manuel de Référence Officiel & Guide d'Utilisation Système (FR / AR)
# الدليل المرجعي الشامل ودليل الاستخدام الرسمي لنظام Institut ILAS

---

## 🏛️ Présentation Générale de l'Établissement & du Système (تقديم عام)

Le système de gestion intégré de l'**Institut Les Sages (ILAS)** est une solution complète conçue pour piloter avec rigueur et simplicité l'ensemble des activités pédagogiques, administratives et financières d'un centre de langues vivantes et de soutien scolaire au Maroc.

نظام التدبير المندمج لـ **معهد الحكماء (Institut ILAS)** هو منصة رقمية متطورة تم تصميمها خصيصاً لإدارة كافة العمليات الإدارية، التربوية، والمالية لمؤسسات تدريس اللغات الحية (إنجليزية، فرنسية، ألمانية، إسبانية) ودروس الدعم والتقوية المدرسية في المغرب، وفق الضوابط القانونية والجبائية والتربوية المعمول بها.

### 🌐 Caractéristiques Techniques & Déploiement :
- **Architecture Locale & Réseau (LAN)** : L'application fonctionne sur le port `8080`. Elle est accessible localement sur le poste serveur (`http://localhost:8080`) et simultanément sur tous les smartphones, tablettes et ordinateurs connectés au réseau Wi-Fi de l'institut (`http://[IP_LOCALE]:8080`).
- **Accès Distant Sécurisé (Cloudflare Tunnel)** : Piloté via `start_remote_tunnel.py` et `cloudflared.exe` pour permettre à la direction de consulter les rapports et tableaux de bord à distance en toute sécurité sans ouvrir de ports de box.
- **Base de Données Haute Performance** : Moteur SQLite configuré en mode **WAL (Write-Ahead Logging)** avec synchronisation normale et timeout étendu à 30 secondes pour garantir une concurrence parfaite sans blocage lors des accès simultanés.
- **Codes QR & Barres 100% Hors-Ligne (Offline)** : Génération locale autonome des QR Codes et des codes-barres Code128 pour les tickets thermiques et cartes d'étudiants PVC sans aucune dépendance à des API externes.

---

## 🧭 Sommaire Général du Manuel (الفهرس الشامل)

1. [Matrice des Rôles & Sécurité des Accès (الصلاحيات والأمان)](#1-matrice-des-rôles--sécurité-des-accès)
2. [Workflow Chronologique de Démarrage (الترتيب المنطقي للعمل)](#2-workflow-chronologique-de-démarrage)
3. [Inscription Express en 30 Secondes (التسجيل السريع الشامل)](#3-inscription-express-en-30-secondes)
4. [Gestion des Élèves & Fiches Dossiers (إدارة شؤون التلاميذ)](#4-gestion-des-élèves--fiches-dossiers)
5. [Suivi des Échéances par Jour & Relances WhatsApp (تتبع الاشتراكات والواتساب)](#5-suivi-des-échéances-par-jour--relances-whatsapp)
6. [Gestion des Inscriptions : Pauses, Reprises & Transferts (تجميد وتحويل الاشتراكات)](#6-gestion-des-inscriptions--pauses-reprises--transferts)
7. [Feuille d'Appel, Présences & Notifications (الحضور والغياب الفوري)](#7-feuille-dappel-présences--notifications)
8. [Emploi du Temps, Salles & Remplaçants (جدول الحصص واستعمال القاعات)](#8-emploi-du-temps-salles--remplaçants)
9. [Cartes d'Étudiants CR80 & Attestations Officielles (البطاقات والشواهد المعتمدة)](#9-cartes-détudiants-cr80--attestations-officielles)
10. [Corps Enseignant & Modèles de Salaire (الأساتذة ونماذج الأجور)](#10-corps-enseignant--modèles-de-salaire)
11. [Rapport de Paie des Professeurs & Part École (حساب مستحقات الأساتذة)](#11-rapport-de-paie-des-professeurs--part-école)
12. [Caisse Quotidienne, Reçus 80mm & Factures ICE (الصندوق والمقبوضات والفواتير)](#12-caisse-quotidienne-reçus-80mm--factures-ice)
13. [Achats, Charges d'Exploitation & Fournisseurs (المشتريات والمصاريف والموردون)](#13-achats-charges-dexploitation--fournisseurs)
14. [Manuels Scolaires & Gestion du Stock (المقررات والكتب المدرسية)](#14-manuels-scolaires--gestion-du-stock)
15. [Suivi d'Activité & Primes des Secrétaires (أرباح السكرتارية وتدقيق العمليات)](#15-suivi-dactivité--primes-des-secrétaires)
16. [Rapports Financiers & Résultat Net Réel (التقارير المالية وصافي الأرباح)](#16-rapports-financiers--résultat-net-réel)
17. [Sauvegardes Automatiques & Restauration (النسخ الاحتياطي والأمان)](#17-sauvegardes-automatiques--restauration)
18. [Importation Massive de Données Excel (استيراد بيانات إكسيل)](#18-importation-massive-de-données-excel)
19. [Check-lists Opérationnelles Quotidiennes & Mensuelles (دليل الإجراءات اليومية)](#19-check-lists-opérationnelles-quotidiennes--mensuelles)

---

## 1. Matrice des Rôles & Sécurité des Accès

Le système applique un contrôle d'accès strict basé sur les rôles (**RBAC**) garantissant la confidentialité des données financières et pédagogiques :

```
┌─────────────────────────┬──────────────┬──────────────────┬──────────────┐
│ Fonctionnalité          │ Admin (مدير) │ Secrétaire (كاتبة)│ Enseignant (أستاذ)│
├─────────────────────────┼──────────────┼──────────────────┼──────────────┤
│ Tableau de bord global  │ Oui (Total)  │ Oui (Opérationnel)│ Restreint     │
│ Inscription Express 30s │ Oui          │ Oui              │ Non          │
│ Fiches Élèves & Dossiers│ Oui          │ Oui              │ Ses élèves   │
│ Présences & Feuille d'Appel│ Oui        │ Oui (Supervision)│ Ses cours    │
│ Emploi du temps & Salles│ Oui          │ Oui              │ Ses créneaux │
│ Caisse & Reçus 80mm     │ Oui          │ Oui              │ Non          │
│ Vente Manuels & Stocks  │ Oui          │ Oui              │ Non          │
│ Achats & Fournisseurs   │ Oui          │ Oui              │ Non          │
│ Primes & Audit Ventes   │ Oui (Global) │ Ses primes       │ Non          │
│ Paie Enseignants        │ Oui          │ Non              │ Non          │
│ Bilan Net & Rapports P&L│ Oui          │ Non              │ Non          │
│ Sauvegardes & Restauration│ Oui        │ Non              │ Non          │
│ Gestion des Utilisateurs│ Oui          │ Non              │ Non          │
│ Sécurité IP & Pare-feu  │ Oui          │ Non              │ Non          │
│ Importation Excel       │ Oui          │ Non              │ Non          │
└─────────────────────────┴──────────────┴──────────────────┴──────────────┘
```

### 🛡️ Pare-Feu Anti-Brute Force (`/settings/security`) :
- Toute tentative d'authentification erronée est consignée avec adresse IP, horodatage et identifiant tenté.
- Dès franchissement du seuil de 5 échecs consécutifs, l'adresse IP est automatiquement verrouillée (`BlockedIP`).
- L'administrateur peut débloquer une adresse IP légitime en un clic via le bouton **[🔓 Débloquer]**.

---

## 2. Workflow Chronologique de Démarrage

Pour une initialisation rigoureuse de l'institut ou d'une nouvelle année académique, il est indispensable de suivre l'ordre séquentiel suivant :

```
1. Réglages Généraux ──> 2. Salles ──> 3. Enseignants ──> 4. Tarifs ──> 5. Classes & Horaires ──> 6. Inscriptions Express ──> 7. Présences & WhatsApp ──> 8. Caisse & Paie
```

1. **`⚙️ /settings` (Paramètres de l'Institut)** :
   - Renseigner la dénomination officielle, adresse, téléphone, WhatsApp officiel, devise (`MAD`) et année scolaire (`2025/2026`).
   - Saisir les identifiants fiscaux légaux : **ICE (15 chiffres)**, **IF**, **RC**, **Patente**, **CNSS**.
2. **`🏢 /rooms` (Salles de Cours)** :
   - Créer chaque salle avec sa capacité maximale d'accueil en nombre de chaises.
3. **`👨‍🏫 /teachers` (Enseignants)** :
   - Créer les fiches professeurs avec spécialité, numéro de téléphone direct et modèle de rémunération de base.
4. **`🏷️ /tariffs` (Grille Tarifaire Officielle)** :
   - Définir les formules tarifaires pour les langues vivantes (Anglais, Français, Espagnol, Allemand) et le soutien scolaire (Primaire, Collège, Tronc Commun, 1BAC, 2BAC).
5. **`📚 /courses` & `🗓️ /schedule` (Classes & Planning)** :
   - Créer les groupes (ex: *2Bac PC Groupe A*), les lier à l'enseignant, à la salle, et aux jours programmés (ex: *Lundi, Mercredi, Vendredi*).
6. **`⚡ /express_enrollment` (Inscriptions des Élèves)** :
   - Enregistrer les élèves et imprimer les reçus thermiques 80mm.

---

## 3. Inscription Express en 30 Secondes (`/express_enrollment`)

L'écran d'**Inscription Express** est le cœur opérationnel de l'accueil de l'institut. Il remplace 5 étapes fastidieuses par une interface unique en 2 volets :

### A. Volet Gauche : Configuration de l'Inscription
1. **Bascule Rapide Nouveau / Existant** :
   - `[✨ Nouveau (جديد)]` : Crée instantanément l'élève dans la base.
   - `[🔍 Déjà Inscrit (مسجل)]` : Recherche prédictive en direct dès 2 caractères par Nom, Code ou Téléphone.
2. **Calculateur de l'Âge Automatique** :
   - Dès la sélection de la date de naissance, un badge calcule l'âge en années pour guider la secrétaire vers le bon niveau.
3. **Téléphone WhatsApp Parent (Obligatoire)** :
   - Champ critique avec formatage automatique pour l'envoi des avis de présence et rappels d'échéances.
4. **Photo pour Badge QR** :
   - Téléversement direct depuis la webcam ou un fichier pour intégration sur la carte d'étudiant.
5. **Mode de Classe** :
   - `🏫 Classes & Groupes` : Affectation immédiate dans un groupe existant.
   - `⏳ En Attente de Groupe (تحديد الفوج لاحقاً)` : Pour inscrire l'élève et encaisser son inscription alors que le groupe est en cours de constitution.
6. **Options Financières Avancées** :
   - **Prorata Temporis** : Calcule au centime près les séances restantes du mois et reporte le solde sur le mois suivant.
   - **Frais d'inscription** : Case à cocher permettant l'exonération (0 DH) pour les anciens ou promotions.
   - **Manuels & Livres** : Ajout direct des livres de cours au ticket d'inscription avec décompte automatique du stock physique.

### B. Volet Droit : Ticket Thermique 80mm en Temps Réel
- Aperçu dynamique du ticket de caisse au format POS standard 80mm.
- Affiche le total de scolarité, les frais de dossier, les manuels scolaires, le montant payé et le **reliquat de monnaie à rendre**.
- Dès validation, le ticket s'imprime instantanément sur l'imprimante thermique de l'accueil.

---

## 4. Gestion des Élèves & Fiches Dossiers (`/students`)

La page `/students` centralise le fichier complet des apprenants de l'établissement :

- **Recherche Multicritère** : Filtrage instantané par nom, prénom, code élève (`ETU001`), téléphone, niveau scolaire, ou statut (Actif / Archivé).
- **Lien WhatsApp Direct** : Chaque numéro de téléphone dispose d'une icône WhatsApp verte ouvrant directement une discussion sans avoir à enregistrer le contact dans son répertoire.
- **Fiche Dossier Complète (`/students/<id>`)** :
  - Identité complète, âge calculé, photo, niveau scolaire, CIN de l'élève ou du tuteur.
  - **Code Famille / Fratrie (`family_code`)** : Permet de regrouper les frères et sœurs pour appliquer des facilités de paiement.
  - **Solde Avoir (`credit_balance`)** : Affiche les crédits en faveur de l'élève (générés suite à un désistement ou trop-perçu).
  - Tableau des inscriptions actives et passées avec date d'échéance et solde restant dû.
  - Historique complet des paiements, reçus émis, attestations délivrées et assiduité aux cours.

---

## 5. Suivi des Échéances par Jour & Relances WhatsApp (`/students/by-date`)

Ce tableau de bord stratégique prévient les impayés et sécurise le flux de trésorerie de l'institut :

### A. Filtres par Période
- **Aujourd'hui (اليوم)** : Abonnements arrivant à leur dernière séance aujourd'hui.
- **5 prochains jours (خلال 5 أيام)** : Abonnements arrivant à terme sous 5 jours.
- **Déjà expirés (منتهية الصلاحية)** : Abonnements échus nécessitant un recouvrement immédiat.
- **Période personnalisée** : Sélection par date précise.

### B. Système d'Alertes Visuelles
- `🟢 Dans X jour(s)` : Abonnement valide.
- `⚠️ Aujourd'hui !` : Dernière séance couverte.
- `🔴 Expiré (Xj)` : Dépassement d'échéance avec affichage du nombre de jours de retard.

### C. Actions Rapides en 1 Clic
- **[💬 WhatsApp Élève]** : Ouvre un message WhatsApp personnalisé :
  > *"Bonjour [Prénom], nous vous rappelons que votre abonnement pour le cours [Matière] arrive à échéance le [Date]. Merci de vous présenter à l'administration pour le renouvellement. Institut ILAS."*
- **[💬 Parent WA]** : Ouvre un message officiel destiné au tuteur légal.
- **[📅 Changer Date]** : Modal interactif permettant de repousser ou modifier l'échéance d'abonnement sans altérer l'historique comptable.
- **[🔄 Renouveler]** : Ouvre l'assistant de renouvellement pour le mois suivant.
- **[🖨️ Imprimer la Liste]** : Génère une fiche de travail A4 pour l'équipe de relance téléphonique.

---

## 6. Gestion des Inscriptions : Pauses, Reprises & Transferts (`/enrollments`)

Le cycle de vie d'une inscription gère l'ensemble des imprévus de l'année scolaire :

### A. Mise en Pause / Gel d'Abonnement (`/enrollments/<id>/pause`)
- Utilisé lorsqu'un élève part en voyage, tombe malade ou suspend temporairement sa formation.
- Le système calcule automatiquement le nombre exact de séances payées non encore consommées à la date de gel :
  $$\text{Séances en Réserve} = \text{Séances Payées Totales} - \text{Séances Consommées}$$
- L'inscription passe au statut `paused` et le décompte calendaire est arrêté.

### B. Reprise d'Abonnement (`/enrollments/<id>/resume`)
- Lors du retour de l'élève, la secrétaire saisit la date de reprise effective.
- Le système projette les séances réservées sur les jours réels programmés du cours (ex: *Lundi, Mercredi, Vendredi*) et calcule la **Nouvelle Date de Fin** :
  $$\text{Nouvelle Date Fin} = \text{Algorithme de projection}(\text{Date Reprise}, \text{Séances en Réserve}, \text{Jours Cours})$$
- L'élève ne perd aucune séance et l'école conserve une visibilité calendaire irréprochable.

### C. Transfert de Classe & Partage Équitable (`/enrollments/<id>/transfer`)
Lorsqu'un élève change de matière ou d'enseignant en cours de cycle :
1. **Conservation des Frais d'Inscription** : Les frais de dossier restent acquis à 100% à l'institut.
2. **Ventilation de la Scolarité** : Le système calcule la part revenant à l'ancien cours et au nouveau cours selon les jours écoulés :
   $$\text{Ratio Ancien} = \frac{\text{Jours Écoulés Période}}{\text{Total Jours Période}}$$
   $$\text{Part Ancien Cours} = \text{Cotisation Mensuelle} \times \text{Ratio Ancien}$$
   $$\text{Part Nouveau Cours} = \text{Cotisation Mensuelle} - \text{Part Ancien Cours}$$
3. **Ajustement Salarial des Professeurs** : La rémunération de chaque enseignant est calculée au prorata exact de sa part respective et de son pourcentage contractuel.

### D. Désistement & Génération d'Avoir (`/enrollments/<id>/withdraw`)
- Si l'élève abandonne son cursus, la secrétaire clôture l'inscription.
- Le montant correspondant aux séances non suivies est automatiquement crédité sur son compte élève (`StudentCredit`), réutilisable lors d'une inscription ultérieure.

---

## 7. Feuille d'Appel, Présences & Notifications (`/attendance`)

### A. Espace Enseignant
- Chaque professeur se connecte depuis son smartphone à `/attendance`.
- Il sélectionne son groupe et la date.
- Il pointe chaque élève : `Présent 🟢`, `Absent 🔴`, ou `Retard 🟡`.
- Clic sur `[💾 Enregistrer l'appel]`.

### B. Espace Administration & Alertes Instantanées (`/attendance/admin`)
- Dès l'enregistrement du professeur, une **notification sonore et visuelle** apparaît sur la cloche 🔔 de l'administrateur et de la secrétaire avec le nombre d'absents.
- L'administration accède au journal d'appel et clique sur l'icône WhatsApp verte face à chaque élève absent pour expédier instantanément l'alerte à la famille.

---

## 8. Emploi du Temps, Salles & Remplaçants (`/schedule`, `/rooms`)

- **Détection des Collisions de Salles & Enseignants** : Le système empêche physiquement la programmation de deux cours dans la même salle au même horaire, ou l'assignation simultanée d'un enseignant sur deux créneaux concurrents.
- **Attribution Dynamique de Salle** : Vérification en temps réel des salles inoccupées pour réaffecter un groupe en cas de besoin.
- **Séances de Remplacement & Rattrapage (`/schedule/substitute`)** :
  - Enregistrement du motif d'absence du professeur titulaire.
  - Sélection du professeur remplaçant (`SubstituteLog`).
  - Traçabilité assurée pour la ventilation exacte des honoraires lors de la paie mensuelle.
- **Impression Grand Format A4 Paysage** : Export PDF haute définition du planning hebdomadaire trié par classe, par professeur ou par salle.

---

## 9. Cartes d'Étudiants CR80 & Attestations Officielles

### A. Cartes d'Étudiants Recto-Verso (`/badges`, `/badges/print`)
- Conforme aux standards internationaux de carte PVC **CR80** (85.6 mm × 54.0 mm).
- **Recto** : Identité de l'institut, photo numérique haute résolution de l'élève, nom complet, code d'identification, matière/classe, année scolaire, et bandeau tricolore institutionnel.
- **Verso** : QR Code sécurisé local encodant `ILAS|ID|CODE|NOM`, Code-barres Code128, bloc de signature/cachet et règlement intérieur de l'établissement.
- Bouton d'impression optimisé (sans marges, respect rigoureux des couleurs).

### B. Attestations & Certificats Accrédités (`/certificates`)
- Émis sous l'accréditation ministérielle officielle **N° 22-200/2020**.
- 3 modèles officiels : *Attestation de Formation*, *Attestation de Niveau en Langue*, *Certificat de Réussite*.
- Mentions honorifiques : *Très Bien*, *Bien*, *Assez Bien*, *Passable*.
- Impression de prestige avec cadre doré, filigrane officiel, QR Code d'authenticité et signatures légales.

---

## 10. Corps Enseignant & Modèles de Salaire (`/teachers`, `/teachers/assignments`)

L'Institut ILAS propose 4 modèles flexibles de rémunération des formateurs :

1. **Pourcentage sur Scolarité (٪ Pourcentage)** *(Recommandé)* :
   - L'enseignant perçoit un pourcentage convenu (ex: 50%) sur les écolages mensuels perçus.
2. **Montant par Élève (Par Tête)** :
   - L'enseignant touche un montant fixe (ex: 150 DH) par élève inscrit dans son groupe.
3. **Taux Horaire (Par Heure)** :
   - L'enseignant est payé selon le volume d'heures réelles dispensées (ex: 100 DH/heure).
4. **Salaire Mensuel Fixe** :
   - Rémunération forfaitaire mensuelle indépendante des effectifs.

> [!NOTE]
> Grâce au module `/teachers/assignments`, un même professeur peut avoir un pourcentage de 50% sur les groupes de Langues et un pourcentage de 60% sur les groupes de Soutien Scolaire 2BAC.

---

## 11. Rapport de Paie des Professeurs & Part École (`/teachers/payroll`)

### A. La Règle d'Or de Gestion
$$\text{Assiette du Salaire Professeur} = \text{Scolarités Mensuelles Encaissées Uniquement}$$
- Les frais d'inscription annuels (40 DH ou 100 DH) et les marges sur livres reviennent à **100% à l'institut**.

### B. Exemple d'Application Concret :
Soit un groupe de 10 élèves à 300 DH/mois avec un professeur rémunéré à 50% :
- **Recettes de scolarité** = $10 \times 300 = \mathbf{3000 \text{ DH}}$
- **Frais de dossier nouveaux élèves** = $10 \times 40 = \mathbf{400 \text{ DH}}$ (100% École)
- **Part du Professeur (50%)** = $3000 \times 50\% = \mathbf{1500 \text{ DH}}$
- **Part Nette de l'École** = $(3000 - 1500) + 400 = \mathbf{1900 \text{ DH}}$

### C. Décompte Officiel A4 Paysage
Filtre multi-sélection avec recherche instantanée permettant d'imprimer la fiche de paie individuelle ou collective avec émargement du professeur lors du règlement.

---

## 12. Caisse Quotidienne, Reçus 80mm & Factures ICE (`/payments`, `/invoices`)

- **Modes de Paiement Gérés** : Espèces (Cash tiroir), Virement bancaire (avec référence de virement), Carte bancaire (TPE comptoir), Paiement en ligne.
- **Reçus Thermiques 80mm & Formats A4/A5** : Numérotation séquentielle inviolable (`REC-0001`), horodatage à la seconde, identification de la secrétaire ayant encaissé.
- **Gestion des Acomptes & Duplicatas** : Ventilation automatique des versements sur les cours impayés. Possibilité de rééditer un reçu avec la mention claire `DUPLICATA`.
- **Facturation Normalisée Marocaine (`/invoices`)** : Factures d'entreprises intégrant l'identifiant fiscal **ICE**, l'adresse du siège, le détail des prestations et la TVA déductible.

---

## 13. Achats, Charges d'Exploitation & Fournisseurs (`/expenses`, `/suppliers`)

La comptabilité analytique de l'institut sépare rigoureusement deux natures de flux :

1. **Achats & Matériel (📦 Achats)** :
   - Achat de livres et manuels scolaires destinés à la revente.
   - Fournitures de bureau, papier, toner, mobilier et matériel informatique.
2. **Charges d'Exploitation (⚡ Charges)** :
   - Loyer de l'immeuble du centre.
   - Factures d'électricité et d'eau (Lydec / ONEE).
   - Abonnements Internet Fibre & Télécoms.
   - Entretien, ménage, maintenance et publicités.

### 🏢 Répertoire Fournisseurs (`/suppliers`) :
Fiche d'identité avec raison sociale, contact, téléphone, ville, **ICE** et **IF**. Le système tient à jour la balance fournisseur : *Total Facturé*, *Total Réglé*, et *Solde Restant Dû (Dettes)* avec archivage des pièces jointes scannées.

---

## 14. Manuels Scolaires & Gestion du Stock (`/books`)

- **Catalogue de Livres** : Répertoire des manuels de langues (Cambridge, Oxford, Hachette...) avec prix d'achat fournisseur et prix de vente public.
- **Seuils d'Alerte & Stock Critique** : Alerte visuelle dès que le stock physique descend sous 5 exemplaires.
- **Vente Directe au Comptoir (`/books/sell`)** : Vente directe avec remise de ticket de caisse et décompte immédiat du stock.
- **Intégration Inscription Express** : Ajout du livre sur le ticket d'inscription élève.

---

## 15. Suivi d'Activité & Primes des Secrétaires (`/users/activity`)

### A. Algorithme de Calcul de la Prime d'Inscription
La secrétaire perçoit une prime d'intéressement (ex: 10%) sur la **marge nette encaissée par l'école** :
1. **Éligibilité** : Réservé exclusivement aux **nouveaux élèves** (0 DH de prime sur les renouvellements mensuels).
2. **Formule Mathématique** :
   $$\text{Scolarité Encaissée} = \max(0, \text{Montant Encaissé} - \text{Frais d'Inscription})$$
   $$\text{Marge Nette École} = \max(0, \text{Scolarité Encaissée} - \text{Part Enseignant})$$
   $$\text{Prime Secrétaire} = \text{Marge Nette École} \times \left(\frac{\text{Taux \%}}{100}\right)$$
3. **Traitement des Acomptes** : Si l'élève verse un acompte à l'inscription, la secrétaire touche sa prime au prorata du montant payé. Lorsque l'élève règle son reliquat, le reste de sa prime est automatiquement libéré !

### B. Clôture & Rapprochement de Caisse
Suivi détaillé par agent : Total Cash en tiroir, Total Virements bancaires, Nombre de dossiers traités et journal d'audit chronologique de toutes les actions enregistrées.

---

## 16. Rapports Financiers & Résultat Net Réel (`/reports`)

Le module de reporting consolidé calcule la rentabilité d'exploitation réelle de l'établissement :

$$\text{Chiffre d'Affaires Global} = \text{Scolarités} + \text{Frais d'Inscription} + \text{Ventes de Livres}$$
$$\text{Total Charges d'Exploitation} = \text{Salaires Enseignants} + \text{Achats de Matériel} + \text{Charges Générales}$$
$$\mathbf{\text{Résultat Net Réel}} = \mathbf{\text{Chiffre d'Affaires Global}} - \mathbf{\text{Total Charges d'Exploitation}}$$

- **Tableau de Répartition des Encaissements** : Ventilation par mode de règlement (Espèces, Virement, TPE).
- **Indicateurs de Rentabilité des Classes** : Chiffre d'affaires par groupe vs coût d'enseignement.
- **Bilan d'Exploitation Imprimable A4** : Document exécutif synthétique pour la direction générale.

---

## 17. Sauvegardes Automatiques & Restauration (`/settings/backups`)

- **Sauvegarde Automatique Quotidienne** : À chaque exécution de `demarrer.bat`, une archive compressée `.zip` horodatée de la base de données est créée dans le répertoire `backups/`.
- **Sauvegarde Manuelle Instantanée** : Clic sur `[⚡ Créer une Sauvegarde Instantanée]`.
- **Export USB Direct** : Clic sur `[📥 Télécharger la BDD Active (.db)]` pour copier la base courante sur support amovible externe.
- **Restauration Sécurisée** : Permet d'importer une ancienne sauvegarde `.zip` ou `.db`. *Le système effectue automatiquement un snapshot de sécurité de la base courante avant toute opération de restauration.*

---

## 18. Importation Massive de Données Excel (`/import`)

Pour intégrer rapidement les bases d'élèves ou d'enseignants existantes :
1. Télécharger le **Modèle Tout-en-Un (.xlsx)** contenant 3 feuilles pré-formatées : *Élèves*, *Enseignants*, *Classes*.
2. Remplir les données en conservant scrupuleusement les en-têtes de colonnes.
3. Téléverser le fichier dans l'Étape 2 : Le système détecte automatiquement les enregistrements, génère les numéros de dossiers `ETU...` manquants, ignore les doublons et présente un bilan d'intégration complet.

---

## 19. Check-lists Opérationnelles Quotidiennes & Mensuelles

### ☀️ Routine Quotidienne — Secrétariat / Accueil :
- [ ] Démarrer le serveur le matin via `demarrer.bat` (la sauvegarde auto s'effectue).
- [ ] Vérifier la cloche 🔔 pour traiter les notifications d'absences signalées par les professeurs.
- [ ] Consulter `/students/by-date` (onglet *Aujourd'hui*) et envoyer les relances WhatsApp aux élèves et parents.
- [ ] Traiter les inscriptions et renouvellements via `⚡ Inscription Express`.
- [ ] En fin de journée, ouvrir `/users/activity` pour vérifier le total d'espèces en caisse avant remise au directeur.

### 📅 Routine Mensuelle — Direction Générale :
- [ ] Accéder à `/teachers/payroll` pour contrôler et valider les salaires des enseignants.
- [ ] Imprimer les décomptes officiels d'émargement et procéder aux règlements des professeurs.
- [ ] Consulter `/expenses` (onglet *Impayés*) pour solder les factures fournisseurs et loyers arrivant à échéance.
- [ ] Télécharger une copie de sécurité `.db` sur clé USB externe depuis `/settings/backups`.
- [ ] Imprimer le bilan d'exploitation mensuel depuis `/reports`.

---

*Manuel officiel établi pour l'Institut Les Sages ILAS — Tous droits réservés.*
