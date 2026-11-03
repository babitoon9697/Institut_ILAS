"""
Module de recherche intelligente et de détection de similarités d'élèves pour l'Institut ILAS.
Gère les variations orthographiques fréquentes au Maroc :
- Inversion Nom / Prénom
- Particules et préfixes (El, Al, L', Ben, Benn, Ait, Ould, Bou, Si, Sidi)
- Noms théophores et prénoms composés (Abdessamad / Abdel Samad, Fatima Zahra / Fatimazahra)
- Abréviations courantes (Med, Mohd, Mhd -> Mohamed)
- Simplifications phonétiques (ou/oo -> u, ch -> sh, ph -> f, kh -> k, y -> i, dj -> j)
- Réduction des consonnes doubles (Mohammed -> Mohamed, Nassiri -> Nasiri)
- Noms en alphabet arabe (standardisation Alef, Harakat, Taa marbouta, suppression ال)
- Détection exacte par numéro de téléphone (élève, parent, WhatsApp)
"""

import unicodedata
import re
import difflib


def normalize_student_name(text: str) -> str:
    """
    Normalise et standardise une chaîne de nom d'élève pour la comparaison phonétique et lexicale.
    """
    if not text:
        return ""
    
    # 1. Suppression des accents
    text = unicodedata.normalize('NFKD', str(text))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    
    # 2. Nettoyage des signes de ponctuation et séparateurs
    text = re.sub(r'[\'\"\-_\./,;:()\[\]{}!?+*~#@]', ' ', text)
    
    # 3. Noms arabes écrits en alphabet arabe
    # Suppression du Tashkeel / Harakat et Tatweel
    text = re.sub(r'[\u064B-\u065F\u0670\u0640]', '', text)
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    
    # 4. Standardisation des prénoms théophores et composés
    text = re.sub(r'\babd\s*e[ln]\s*', 'abdel ', text)
    text = re.sub(r'\babde\s*el\s*', 'abdel ', text)
    text = re.sub(r'\babd\s*el\s*', 'abdel ', text)
    text = re.sub(r'\babd\s*al\s*', 'abdel ', text)
    text = re.sub(r'\babdes\s*', 'abdel s', text)
    text = re.sub(r'\babder\s*', 'abdel r', text)
    text = re.sub(r'\babdel\s*', 'abdel ', text)
    
    # 5. Abréviations courantes au Maroc
    text = re.sub(r'\bmed\b', 'mohamed', text)
    text = re.sub(r'\bmohd\b', 'mohamed', text)
    text = re.sub(r'\bmhd\b', 'mohamed', text)
    text = re.sub(r'\bezzahra\b', 'zahra', text)
    text = re.sub(r'\bez\s*zahra\b', 'zahra', text)
    text = re.sub(r'\bfatima\s*zahra\b', 'fatimazahra', text)
    text = re.sub(r'\bfatim\s*zahra\b', 'fatimazahra', text)
    text = re.sub(r'\bsalah\s*eddine\b', 'salaheddine', text)
    text = re.sub(r'\bnour\s*eddine\b', 'noureddine', text)
    text = re.sub(r'\bseif\s*eddine\b', 'seifeddine', text)
    text = re.sub(r'\bimad\s*eddine\b', 'imadeddine', text)
    text = re.sub(r'\bhoussam\s*eddine\b', 'houssameddine', text)
    
    # 6. Particules familiales marocaines
    particles = [' el ', ' al ', ' l ', ' ez ', ' en ', ' er ', ' es ', ' et ', ' ed ', 
                 ' ben ', ' benn ', ' bnou ', ' ait ', ' ould ', ' bou ', ' si ', ' sidi ']
    for p in particles:
        text = text.replace(p, ' ')
    if text.startswith(('el ', 'al ', 'l ')):
        text = text[3:]
    if text.startswith('ben '):
        text = text[4:]
        
    # En arabe: suppression du ال au début des mots
    arabic_words = []
    for w in text.split():
        if w.startswith('ال') and len(w) > 3:
            w = w[2:]
        arabic_words.append(w)
    text = " ".join(arabic_words)

    # 7. Simplifications phonétiques
    text = text.replace('ou', 'u').replace('oo', 'u')
    text = text.replace('ch', 'sh').replace('ph', 'f').replace('kh', 'k')
    text = text.replace('y', 'i')
    
    # 8. Réduction des lettres consécutives identiques (Mohammed -> Mohamed, Nassiri -> Nasiri)
    text = re.sub(r'([a-z])\1+', r'\1', text)
    
    tokens = sorted([t.strip() for t in text.split() if len(t.strip()) > 1])
    return " ".join(tokens)


def clean_phone(phone_str) -> str:
    """Nettoie et extrait les 8 derniers chiffres significatifs d'un numéro de téléphone."""
    if not phone_str:
        return ""
    digits = re.sub(r'\D', '', str(phone_str))
    if digits.startswith('212'):
        digits = '0' + digits[3:]
    elif digits.startswith('00212'):
        digits = '0' + digits[5:]
    return digits[-8:] if len(digits) >= 8 else digits


def compute_student_match(req_name: str, req_phone: str, req_level: str, student) -> tuple:
    """
    Calcule le score de similarité (0.0 à 1.0) et la justification.
    Retourne (score: float, reason: str).
    """
    stu_name = student.full_name or f"{student.first_name} {student.last_name}"
    
    # 1. Correspondance Téléphone (Priorité 100%)
    if req_phone:
        cp_req = clean_phone(req_phone)
        if cp_req and len(cp_req) >= 8:
            stu_phones = [student.phone, student.parent_phone, student.whatsapp]
            for sp in stu_phones:
                if sp and cp_req in clean_phone(sp):
                    return 1.0, "Même numéro de téléphone (100%)"
    
    # 2. Normalisation des noms
    norm_req = normalize_student_name(req_name)
    norm_stu = normalize_student_name(stu_name)
    
    if not norm_req or not norm_stu:
        return 0.0, ""
    
    # 3. Correspondance exacte après normalisation
    if norm_req == norm_stu:
        return 0.98, "Nom identique (orthographe standardisée)"
    
    tokens_req = set(norm_req.split())
    tokens_stu = set(norm_stu.split())
    
    # Inversion exacte des tokens (ex: "Alami Mohamed" vs "Mohamed Alami")
    if tokens_req and tokens_stu and tokens_req == tokens_stu:
        return 0.96, "Mêmes mots (ordre Nom / Prénom inversé)"
    
    # Intersection de tokens
    common_tokens = tokens_req.intersection(tokens_stu)
    if len(common_tokens) >= 2:
        return 0.90, f"{len(common_tokens)} mots du nom correspondent exactement"
    
    # Comparaison de similarité par ratio de Levenshtein (SequenceMatcher)
    seq_ratio = difflib.SequenceMatcher(None, norm_req, norm_stu).ratio()
    
    # Comparaison mot à mot (meilleur score pour chaque token)
    words_req = norm_req.split()
    words_stu = norm_stu.split()
    word_scores = []
    for wr in words_req:
        best_w = max((difflib.SequenceMatcher(None, wr, ws).ratio() for ws in words_stu), default=0.0)
        word_scores.append(best_w)
    avg_word_score = sum(word_scores) / len(word_scores) if word_scores else 0.0
    
    best_score = max(seq_ratio, avg_word_score)
    
    # Si un nom de famille ou prénom est rare et identique
    if len(common_tokens) == 1 and (len(tokens_req) <= 2 or len(tokens_stu) <= 2):
        single_word = list(common_tokens)[0]
        if len(single_word) >= 4:
            best_score = max(best_score, 0.72)
    
    # Bonus niveau scolaire identique
    if req_level and student.school_level:
        lvl_req = req_level.strip().lower()
        lvl_stu = student.school_level.strip().lower()
        if lvl_req == lvl_stu and best_score >= 0.65:
            best_score = min(0.95, best_score + 0.08)
    
    if best_score >= 0.85:
        return round(best_score, 2), f"Orthographe très proche ({int(best_score * 100)}%)"
    elif best_score >= 0.70:
        return round(best_score, 2), f"Orthographe similaire ({int(best_score * 100)}%)"
    elif best_score >= 0.60:
        return round(best_score, 2), f"Nom approchant ({int(best_score * 100)}%)"
        
    return round(best_score, 2), ""


def find_similar_students(req_name: str, req_phone: str, req_level: str, all_students, requested_course_id=None, threshold=0.65, limit=5) -> list:
    """
    Recherche parmi tous les élèves existants ceux qui correspondent au candidat proposé.
    Renvoie une liste de dictionnaires enrichis avec les classes actuelles de l'élève.
    """
    if not req_name and not req_phone:
        return []
        
    matches = []
    
    for s in all_students:
        score, reason = compute_student_match(req_name, req_phone, req_level, s)
        if score >= threshold:
            # Récupérer les inscriptions actives ou d'essai de cet élève
            active_enrolls = getattr(s, '_cached_active_enrollments', None)
            if active_enrolls is None:
                active_enrolls = [e for e in getattr(s, 'enrollments', []) if getattr(e, 'status', '') in ('active', 'trial')]
            
            courses_info = []
            is_in_requested_course = False
            
            for e in active_enrolls:
                c = getattr(e, 'course', None)
                if not c:
                    continue
                c_id = getattr(c, 'id', None)
                if requested_course_id and c_id == requested_course_id:
                    is_in_requested_course = True
                
                t_obj = getattr(c, 'teacher', None)
                t_name = f"{getattr(t_obj, 'first_name', '')} {getattr(t_obj, 'last_name', '')}".strip() if t_obj else ""
                
                courses_info.append({
                    'course_id': c_id,
                    'name': getattr(c, 'display_name', '') or getattr(c, 'name', 'Classe'),
                    'subject': getattr(c, 'language', '') or '',
                    'level': getattr(c, 'level', '') or '',
                    'teacher': t_name,
                    'schedule': getattr(c, 'schedule_label', '') or '',
                    'status': getattr(e, 'status', 'active'),
                    'is_requested_course': (requested_course_id and c_id == requested_course_id)
                })
            
            primary_phone = getattr(s, 'phone', None) or getattr(s, 'parent_phone', None) or getattr(s, 'whatsapp', None) or ""
            
            matches.append({
                'id': s.id,
                'code': getattr(s, 'code', None) or f"ID-{s.id}",
                'full_name': s.full_name or f"{s.first_name} {s.last_name}",
                'school_level': getattr(s, 'school_level', None) or "Non précisé",
                'phone': primary_phone,
                'parent_phone': getattr(s, 'parent_phone', None) or "",
                'similarity_score': int(score * 100),
                'similarity_reason': reason,
                'is_in_requested_course': is_in_requested_course,
                'active_courses': courses_info
            })
            
    # Tri : Les scores les plus élevés en premier, puis ceux déjà inscrits
    matches.sort(key=lambda x: (x['similarity_score'], x['is_in_requested_course']), reverse=True)
    return matches[:limit]
