# -*- coding: utf-8 -*-
"""
Pedagogical Helper Module for Institut ILAS
Handles classification of Language vs Soutien teachers,
multilingual translations (EN, FR, DE, ES, AR),
WhatsApp dispatch text generation, prefilled sessions, and week bounds.
"""

from datetime import date, timedelta, datetime
import json
from urllib.parse import quote

# Supported language codes & metadata
LANGUAGES_CONFIG = {
    'en': {
        'code': 'en',
        'name_fr': 'Anglais',
        'name_native': 'English',
        'flag': '🇬🇧',
        'dir': 'ltr',
    },
    'fr': {
        'code': 'fr',
        'name_fr': 'Français',
        'name_native': 'Français',
        'flag': '🇫🇷',
        'dir': 'ltr',
    },
    'de': {
        'code': 'de',
        'name_fr': 'Allemand',
        'name_native': 'Deutsch',
        'flag': '🇩🇪',
        'dir': 'ltr',
    },
    'es': {
        'code': 'es',
        'name_fr': 'Espagnol',
        'name_native': 'Español',
        'flag': '🇪🇸',
        'dir': 'ltr',
    },
    'ar': {
        'code': 'ar',
        'name_fr': 'Arabe',
        'name_native': 'العربية',
        'flag': '🇲🇦',
        'dir': 'rtl',
    }
}

# Rich pedagogical translations
TRANSLATIONS = {
    'en': {
        'lang_name': 'English',
        'title': 'WEEKLY PEDAGOGICAL PLAN',
        'subtitle': 'Institut ILAS — Language Department',
        'doc_ref': 'Weekly Syllabus & Lesson Planning',
        'academic_year': 'Academic Year',
        'week_range_label': 'Week of',
        'teacher_label': 'Teacher',
        'language_label': 'Language & Level',
        'groups_label': 'Classes / Groups',
        'room_label': 'Assigned Room(s)',
        'section_objectives': '1. Weekly Learning Objectives & Focus',
        'communicative_goal': 'Communicative & Functional Objectives (Can-Do statements)',
        'communicative_placeholder': 'e.g., Students will be able to order food in a restaurant, ask for prices, express preferences...',
        'grammar_syntax': 'Grammar & Syntactic Structures Target',
        'grammar_placeholder': 'e.g., Simple Past vs Past Continuous, modal verbs (must/should), prepositions of place...',
        'vocab_lexicon': 'Key Thematic Vocabulary & Expressions',
        'vocab_placeholder': 'e.g., Travel and airport vocabulary, phrases for booking a hotel, adjectives of emotion...',
        'section_sessions': '2. Detailed Session-by-Session Planning',
        'col_session': 'Session / Date / Time',
        'col_group': 'Group / Level',
        'col_topic': 'Unit / Lesson Topic',
        'col_skills': 'Core Language Skills',
        'col_activities': 'Classroom Activities & Materials',
        'col_homework': 'Homework / Assignments',
        'col_notes': 'Assessment & Notes',
        'skill_speaking': '🗣️ Speaking',
        'skill_listening': '👂 Listening',
        'skill_reading': '📖 Reading',
        'skill_writing': '✍️ Writing',
        'activities_placeholder': 'e.g., Coursebook Unit 4 (pp. 42-45), audio track 12, pair-work role play, vocabulary flashcards...',
        'homework_placeholder': 'e.g., Workbook exercises 1-4 p. 28, write a short paragraph (50 words) about holidays...',
        'notes_placeholder': 'e.g., Formative mini-quiz, attendance/participation remarks...',
        'add_session_btn': '+ Add Another Session',
        'remove_session_btn': 'Remove',
        'section_support': '3. Pedagogical Follow-up & Material Requests',
        'upcoming_eval': 'Upcoming Tests / Evaluations',
        'upcoming_eval_placeholder': 'e.g., Unit 4 Progress Test scheduled for Thursday...',
        'special_needs': 'Special Student Observations / Support',
        'special_needs_placeholder': 'e.g., Student X needs extra speaking practice; Y joined this week...',
        'supplies_needed': 'Photocopies & Resources Requested from Secretariat',
        'supplies_placeholder': 'e.g., 15 copies of Unit 4 supplementary grammar worksheet, projector for session 2...',
        'section_signatures': '4. Signatures & Validation',
        'teacher_sig': "Teacher's Signature & Date",
        'admin_visa': 'Pedagogical Coordination Visa',
        'submit_btn': '💾 Submit Weekly Pedagogical Plan',
        'save_draft_btn': 'Save Draft',
        'print_btn': '🖨️ Print / Save PDF',
        'back_to_hub': '← Back to Management Hub',
        'success_msg': 'Weekly Pedagogical Plan submitted successfully! Thank you for your cooperation.',
        'blank_note': 'This document is the official weekly lesson plan of Institut ILAS. Please complete and return each week.',
        'wa_greeting': 'Dear Professor {name},',
        'wa_intro': 'Greetings from *Institut ILAS*! 📚✨',
        'wa_body': 'Here is your link to submit your *Weekly Pedagogical Plan* for the week of *{dates}*:',
        'wa_cta': '👉 Please complete your weekly syllabus via this link:',
        'wa_reminder': 'Kindly submit your program before Sunday evening so that educational materials, photocopies, and rooms can be properly prepared.',
        'wa_closing': 'Thank you very much for your dedication and commitment to educational excellence!\n\n*Institut ILAS Management & Pedagogical Coordination*',
    },
    'fr': {
        'lang_name': 'Français',
        'title': 'FICHE PÉDAGOGIQUE HEBDOMADAIRE',
        'subtitle': 'Institut ILAS — Département des Langues',
        'doc_ref': 'Cahier de Texte & Planification Pédagogique',
        'academic_year': 'Année de Formation',
        'week_range_label': 'Semaine du',
        'teacher_label': 'Enseignant(e)',
        'language_label': 'Langue & Niveau',
        'groups_label': 'Groupes / Classes',
        'room_label': 'Salle(s) attribuée(s)',
        'section_objectives': '1. Objectifs Pédagogiques & Compétences Visées',
        'communicative_goal': 'Objectifs Communicatifs & Pragmatiques (Savoir-faire)',
        'communicative_placeholder': 'ex. : Être capable de commander au restaurant, demander son chemin, exprimer une opinion...',
        'grammar_syntax': 'Points de Grammaire & Structures Cibles',
        'grammar_placeholder': 'ex. : Passé composé vs Imparfait, pronoms relatifs (qui, que, où), accord des adjectifs...',
        'vocab_lexicon': 'Vocabulaire Thématique & Champ Lexical',
        'vocab_placeholder': 'ex. : Lexique de l\'hôtellerie et du voyage, expressions de la cause et de la conséquence...',
        'section_sessions': '2. Planification Séance par Séance',
        'col_session': 'Séance / Date / Horaire',
        'col_group': 'Groupe / Niveau',
        'col_topic': 'Thème / Unité / Titre de la Leçon',
        'col_skills': 'Compétences Travaillées',
        'col_activities': 'Activités Pédagogiques & Supports',
        'col_homework': 'Travail à Faire (Devoirs)',
        'col_notes': 'Évaluation & Remarques',
        'skill_speaking': '🗣️ Expression Orale',
        'skill_listening': '👂 Compréhension Orale',
        'skill_reading': '📖 Compréhension Écrite',
        'skill_writing': '✍️ Expression Écrite',
        'activities_placeholder': 'ex. : Manuel Unité 3 (pp. 34-36), piste audio 7, jeu de rôle en binôme, fiche d\'exercices...',
        'homework_placeholder': 'ex. : Exercices 2 et 3 page 40 du cahier d\'activités, rédaction de 6 lignes...',
        'notes_placeholder': 'ex. : Test d\'évaluation formative prévu, bonne participation générale...',
        'add_session_btn': '+ Ajouter une Séance',
        'remove_session_btn': 'Supprimer',
        'section_support': '3. Suivi Pédagogique & Besoins en Matériel',
        'upcoming_eval': 'Évaluations ou Tests Programmés',
        'upcoming_eval_placeholder': 'ex. : Contrôle continu de fin de module prévu vendredi...',
        'special_needs': 'Observations Particulières & Suivi Apprenants',
        'special_needs_placeholder': 'ex. : Deux nouveaux apprenants intégrés cette semaine ; suivi individuel...',
        'supplies_needed': 'Demandes de Photocopies ou Matériel au Secrétariat',
        'supplies_placeholder': 'ex. : 15 exemplaires de la fiche de révision B1, besoin du vidéo-projecteur...',
        'section_signatures': '4. Signatures & Validation',
        'teacher_sig': 'Signature de l\'Enseignant(e) & Date',
        'admin_visa': 'Visa de la Direction Pédagogique',
        'submit_btn': '💾 Enregistrer la Fiche Pédagogique',
        'save_draft_btn': 'Sauvegarder Brouillon',
        'print_btn': '🖨️ Imprimer / Sauvegarder en PDF',
        'back_to_hub': '← Retour au Hub de Gestion',
        'success_msg': 'Fiche pédagogique enregistrée avec succès ! Merci pour votre collaboration.',
        'blank_note': 'Document officiel de cadrage pédagogique Institut ILAS. À renseigner chaque semaine par l\'enseignant.',
        'wa_greeting': 'Bonjour cher(e) professeur {name},',
        'wa_intro': 'L\'équipe de l\'*Institut ILAS* vous salue chaleureusement ! 📚✨',
        'wa_body': 'Voici le lien direct pour renseigner votre *Fiche Pédagogique Hebdomadaire* pour la semaine du *{dates}* :',
        'wa_cta': '👉 Accédez à votre fiche en ligne :',
        'wa_reminder': 'Merci de bien vouloir compléter vos objectifs, thèmes et supports avant dimanche soir afin de préparer au mieux les salles et les photocopies.',
        'wa_closing': 'Nous vous remercions pour votre dévouement et la qualité de vos cours !\n\n*Direction Pédagogique — Institut ILAS*',
    },
    'de': {
        'lang_name': 'Deutsch',
        'title': 'PÄDAGOGISCHER WOCHENPLAN',
        'subtitle': 'Institut ILAS — Sprachabteilung Deutsch',
        'doc_ref': 'Wöchentlicher Unterrichtsplan & Lehrverlauf',
        'academic_year': 'Ausbildungsjahr',
        'week_range_label': 'Woche vom',
        'teacher_label': 'Lehrkraft',
        'language_label': 'Sprache & GER-Niveau',
        'groups_label': 'Kursgruppen',
        'room_label': 'Unterrichtsraum',
        'section_objectives': '1. Lernziele & Schwerpunkte der Woche',
        'communicative_goal': 'Kommunikative Handlungsziele (Kann-Beschreibungen)',
        'communicative_placeholder': 'z.B.: Die Teilnehmenden können im Restaurant bestellen, nach dem Weg fragen, Meinungen äußern...',
        'grammar_syntax': 'Grammatikschwerpunkte & Sprachstrukturen',
        'grammar_placeholder': 'z.B.: Perfekt mit haben/sein, Wechselpräpositionen (Dativ/Akkusativ), Modalverben im Präteritum...',
        'vocab_lexicon': 'Thematischer Wortschatz & Redemittel',
        'vocab_placeholder': 'z.B.: Reisen und Verkehr, Wohnen und Möbel, Redemittel für Diskussionen...',
        'section_sessions': '2. Detaillierter Unterrichtsverlauf nach Sitzungen',
        'col_session': 'Sitzung / Datum / Uhrzeit',
        'col_group': 'Gruppe / Niveau',
        'col_topic': 'Thema / Lektion & Kapitel',
        'col_skills': 'Sprachfertigkeiten',
        'col_activities': 'Unterrichtsaktivitäten & Lehrmaterialien',
        'col_homework': 'Hausaufgaben & Übungen',
        'col_notes': 'Lernerfolgskontrolle & Notizen',
        'skill_speaking': '🗣️ Sprechen',
        'skill_listening': '👂 Hören',
        'skill_reading': '📖 Lesen',
        'skill_writing': '✍️ Schreiben',
        'activities_placeholder': 'z.B.: Lehrbuch Lektion 5 (S. 45-48), Hörtext Track 8, Partnerarbeit / Rollenspiel, Grammatikblatt...',
        'homework_placeholder': 'z.B.: Arbeitsbuch S. 32 Übung 1-3, kurzen Text schreiben (ca. 40 Wörter)...',
        'notes_placeholder': 'z.B.: Kleiner Zwischentest, gute Beteiligung der Gruppe...',
        'add_session_btn': '+ Weitere Sitzung hinzufügen',
        'remove_session_btn': 'Entfernen',
        'section_support': '3. Pädagogische Betreuung & Materialbedarf',
        'upcoming_eval': 'Geplante Prüfungen / Tests',
        'upcoming_eval_placeholder': 'z.B.: Zwischentest Lektion 5 am Donnerstag...',
        'special_needs': 'Besondere Beobachtungen / Förderbedarf',
        'special_needs_placeholder': 'z.B.: Teilnehmer X benötigt Unterstützung beim Hören; aktive Beteiligung...',
        'supplies_needed': 'Kopierwünsche & Medienbedarf beim Sekretariat',
        'supplies_placeholder': 'z.B.: 15 Kopien des Arbeitsblattes B1, Beamer für Audio/Video...',
        'section_signatures': '4. Unterschriften & Bestätigung',
        'teacher_sig': 'Unterschrift der Lehrkraft & Datum',
        'admin_visa': 'Sichtvermerk der Schulleitung',
        'submit_btn': '💾 Wochenplan speichern & absenden',
        'save_draft_btn': 'Entwurf speichern',
        'print_btn': '🖨️ Drucken / PDF herunterladen',
        'back_to_hub': '← Zurück zur Übersicht',
        'success_msg': 'Der pädagogische Wochenplan wurde erfolgreich übermittelt! Vielen Dank.',
        'blank_note': 'Offizieller pädagogischer Wochenplan des Institut ILAS. Wöchentlich von der Lehrkraft auszufüllen.',
        'wa_greeting': 'Guten Tag liebe(r) Kollege/Kollegin {name},',
        'wa_intro': 'Herzliche Grüße vom *Institut ILAS*! 📚✨',
        'wa_body': 'Hier ist Ihr direkter Link zum Ausfüllen des *pädagogischen Wochenplans* für die Woche vom *{dates}*:',
        'wa_cta': '👉 Wochenplan online ausfüllen:',
        'wa_reminder': 'Bitte tragen Sie Ihre Unterrichtsziele, Themen und Materialien bis Sonntagabend ein, damit Unterrichtsräume und Kopien rechtzeitig vorbereitet werden können.',
        'wa_closing': 'Vielen Dank für Ihre engagierte Arbeit und Ihren wertvollen Einsatz!\n\n*Pädagogische Leitung — Institut ILAS*',
    },
    'es': {
        'lang_name': 'Español',
        'title': 'FICHA PEDAGÓGICA SEMANAL',
        'subtitle': 'Institut ILAS — Departamento de Idiomas',
        'doc_ref': 'Programación de Clases & Plan de Estudios',
        'academic_year': 'Año Académico',
        'week_range_label': 'Semana del',
        'teacher_label': 'Profesor/a',
        'language_label': 'Idioma y Nivel MCER',
        'groups_label': 'Grupos / Clases',
        'room_label': 'Aula asignada',
        'section_objectives': '1. Objetivos Pedagógicos y Destrezas de la Semana',
        'communicative_goal': 'Objetivos Communicativos y Funcionales',
        'communicative_placeholder': 'ej.: Ser capaz de pedir comida en un restaurante, solicitar información turística, expresar gustos...',
        'grammar_syntax': 'Contenidos Gramaticales y Estructuras',
        'grammar_placeholder': 'ej.: Pretérito Indefinido vs Imperfecto, pronombres de objeto directo/indirecto, ser vs estar...',
        'vocab_lexicon': 'Vocabulario Temático y Campos Léxicos',
        'vocab_placeholder': 'ej.: Léxico de viajes, medios de transporte, expresiones para dar indicaciones...',
        'section_sessions': '2. Programación Detallada Sesión por Sesión',
        'col_session': 'Sesión / Fecha / Horario',
        'col_group': 'Grupo / Nivel',
        'col_topic': 'Unidad / Tema de la Lección',
        'col_skills': 'Destrezas Lingüísticas',
        'col_activities': 'Actividades Didácticas y Materiales',
        'col_homework': 'Tareas para Casa (Deberes)',
        'col_notes': 'Evaluación Formativa y Notas',
        'skill_speaking': '🗣️ Expresión Oral',
        'skill_listening': '👂 Comprensión Auditiva',
        'skill_reading': '📖 Comprensión Lectora',
        'skill_writing': '✍️ Expresión Escrita',
        'activities_placeholder': 'ej.: Libro Unidad 4 (págs. 30-33), audio pista 6, juego de rol por parejas, ficha de repaso...',
        'homework_placeholder': 'ej.: Cuaderno de ejercicios págs. 20-21, redacción de 50 palabras sobre el fin de semana...',
        'notes_placeholder': 'ej.: Prueba corta formativa prevista, excelente participación...',
        'add_session_btn': '+ Añadir otra Sesión',
        'remove_session_btn': 'Eliminar',
        'section_support': '3. Seguimiento Pedagógico y Recursos',
        'upcoming_eval': 'Exámenes o Evaluaciones Previstas',
        'upcoming_eval_placeholder': 'ej.: Control de mitad de trimestre previsto para el jueves...',
        'special_needs': 'Observaciones y Atención Individualizada',
        'special_needs_placeholder': 'ej.: Alumno con dificultades en pronunciación; apoyo personalizado...',
        'supplies_needed': 'Petición de Fotocopias o Material a Secretaría',
        'supplies_placeholder': 'ej.: 15 copias de la ficha gramatical A2, proyector para la sesión 1...',
        'section_signatures': '4. Firmas y Validación',
        'teacher_sig': 'Firma del Profesor/a y Fecha',
        'admin_visa': 'Visto Bueno de la Dirección Pedagógica',
        'submit_btn': '💾 Guardar Ficha Pedagógica',
        'save_draft_btn': 'Guardar Borrador',
        'print_btn': '🖨️ Imprimir / Guardar en PDF',
        'back_to_hub': '← Volver al Panel de Gestión',
        'success_msg': '¡Ficha pedagógica guardada con éxito! Muchas gracias por su colaboración.',
        'blank_note': 'Documento oficial de seguimiento docente del Institut ILAS. Completar semanalmente por el profesorado.',
        'wa_greeting': '¡Hola estimado/a profesor/a {name}!',
        'wa_intro': '¡Saludos muy cordiales del equipo del *Institut ILAS*! 📚✨',
        'wa_body': 'Le enviamos su enlace directo para rellenar la *Ficha Pedagógica Semanal* de la semana del *{dates}*:',
        'wa_cta': '👉 Complete su ficha en línea aquí:',
        'wa_reminder': 'Le rogamos completar los objetivos, lecciones y actividades antes del domingo por la noche para organizar las aulas y fotocopias.',
        'wa_closing': '¡Agradecemos sinceramente su profesionalismo y dedicación docente!\n\n*Dirección Pedagógica — Institut ILAS*',
    },
    'ar': {
        'lang_name': 'العربية',
        'title': 'الجذاذة البيداغوجية والتخطيط الأسبوعي',
        'subtitle': 'معهد إيلاس — قسم اللغات الحية',
        'doc_ref': 'دفتر النصوص والتخطيط التربوي الأسبوعي',
        'academic_year': 'السنة التكوينية',
        'week_range_label': 'أسبوع من',
        'teacher_label': 'الأستاذ(ة)',
        'language_label': 'اللغة والمستوى',
        'groups_label': 'الأفواج / الحصص',
        'room_label': 'القاعة المخصصة',
        'section_objectives': '1. الأهداف البيداغوجية والكفايات المستهدفة',
        'communicative_goal': 'الأهداف التواصلية والوظيفية (القدرات والمهام المستهدفة)',
        'communicative_placeholder': 'مثال: التمكن من تقديم النفس، إجراء حوار في فندق أو مطعم، التعبير عن الرأي والتعليل...',
        'grammar_syntax': 'القواعد والتراكيب اللغوية المستهدفة',
        'grammar_placeholder': 'مثال: الجملة الفعلية والاسمية، أدوات الربط، تصريف الأفعال مع الضمائر...',
        'vocab_lexicon': 'المعجم والمفردات المحورية',
        'vocab_placeholder': 'مثال: معجم السفر والسياحة، مصطلحات الحياة اليومية، عبارات اللباقة والمجاملة...',
        'section_sessions': '2. التوزيع والتخطيط المفصل لكل حصة',
        'col_session': 'الحصة / التاريخ / التوقيت',
        'col_group': 'الفوج / المستوى',
        'col_topic': 'الوحدة / محور الدرس',
        'col_skills': 'المهارات اللغوية المستهدفة',
        'col_activities': 'الأنشطة التعليمية والدعامات البيداغوجية',
        'col_homework': 'الواجب المنزلي والتطبيقات',
        'col_notes': 'التقويم والملاحظات',
        'skill_speaking': '🗣️ التعبير الشفهي',
        'skill_listening': '👂 الفهم والاستماع',
        'skill_reading': '📖 القراءة والفهم',
        'skill_writing': '✍️ الإنتاج الكتابي',
        'activities_placeholder': 'مثال: الكتاب الوحدة 3 (ص 30-34)، مقطع صوتي 5، حوار ثنائي، بطاقات تعليمية...',
        'homework_placeholder': 'مثال: إنجاز التمارين 1 و 2 ص 40، كتابة فقرة قصيرة من 5 أسطر...',
        'notes_placeholder': 'مثال: اختبار تقويمي قصير، مشاركة متميزة من الطلاب...',
        'add_session_btn': '+ إضافة حصة أخرى',
        'remove_session_btn': 'حذف',
        'section_support': '3. التتبع التربوي وحاجيات الوسائل التعليمية',
        'upcoming_eval': 'الفروض أو الروائز المبرمجة',
        'upcoming_eval_placeholder': 'مثال: رائز مرحلي مقرر يوم الخميس...',
        'special_needs': 'ملاحظات خاصة وتتبع المتعلمين',
        'special_needs_placeholder': 'مثال: طالب جديد يحتاج متابعة في النطق؛ تشجيع المشاركة الفردية...',
        'supplies_needed': 'طلبات النسخ وتصوير الوثائق من الإدارة',
        'supplies_placeholder': 'مثال: 15 نسخة من ورقة التطبيقات، الحاجة للعاكس الضوئي (Projecteur)...',
        'section_signatures': '4. المصادقة والتوقيعات',
        'teacher_sig': 'توقيع الأستاذ(ة) والتاريخ',
        'admin_visa': 'تأشيرة الإدارة التربوية',
        'submit_btn': '💾 حفظ وإرسال الجذاذة البيداغوجية',
        'save_draft_btn': 'حفظ كمسودة',
        'print_btn': '🖨️ طباعة / تحميل PDF',
        'back_to_hub': '← العودة إلى لوحة التحكم',
        'success_msg': 'تم حفظ الجذاذة البيداغوجية بنجاح! شكراً جزيلاً لتعاونكم.',
        'blank_note': 'وثيقة رسمية للتأطير البيداغوجي بمعهد إيلاس. تعبأ أسبوعياً من طرف أستاذ(ة) المادة.',
        'wa_greeting': 'تحية طيبة الأستاذ(ة) المحترم(ة) {name}،',
        'wa_intro': 'تحية تربوية خالصة من إدارة *معهد إيلاس للغات*! 📚✨',
        'wa_body': 'إليكم الرابط المباشر لتعبئة *الجذاذة البيداغوجية الأسبوعية* لأسبوع *{dates}* :',
        'wa_cta': '👉 يرجى النقر على الرابط لتعبئة الجذاذة مباشرة :',
        'wa_reminder': 'يرجى التكرم بتحديد الأهداف، المحاور، والأنشطة المبرمجة قبل مساء الأحد، ليتسنى للإدارة تجهيز القاعات وتصوير الوثائق المطلوبة.',
        'wa_closing': 'شاكرين لكم حسن تعاونكم الدائم وتفانيكم المهني المتميز!\n\n*الإدارة التربوية — معهد إيلاس*',
    }
}


def normalize_wa_phone(phone_str):
    """
    Cleans phone number and formats with 212 Morocco country code for WhatsApp.
    """
    if not phone_str:
        return ''
    digits = ''.join(c for c in phone_str if c.isdigit())
    if digits.startswith('0') and len(digits) == 10:
        return '212' + digits[1:]
    if digits.startswith('212'):
        return digits
    return digits


def classify_teacher(t):
    """
    Classifies a Teacher as either 'language' or 'soutien'.
    Returns: (category, lang_code)
      category: 'language' or 'soutien'
      lang_code: 'en', 'fr', 'de', 'es', 'ar' or None
    """
    spec = (getattr(t, 'specialty', '') or '').strip().lower()
    sub = (getattr(t, 'subjects_taught', '') or '').strip().lower()
    name = (getattr(t, 'full_name', '') or '').strip().lower()
    mat = (getattr(t, 'primary_matiere', '') or '').strip().lower()

    # Check for pure Soutien scolaire keywords (Math, PC, SVT, TC, SM)
    pure_soutien_keywords = ['math', 'svt', 'pc', 'physiq', 'chimie', 'scientifique', 'tc/pc', 'soutien primaire']
    is_pure_soutien = any(k in spec or k in mat for k in pure_soutien_keywords) and not any(k in spec or k in mat for k in ['ang', 'fran', 'allem', 'esp', 'arab'])

    # Moroccan "SM" in name / specialty without language
    if 'sm' in name.split() and not any(k in spec for k in ['ang', 'fran', 'allem', 'esp']):
        is_pure_soutien = True

    if is_pure_soutien:
        return 'soutien', None

    # Language matching
    if any(k in spec or k in mat for k in ['allem', 'germ', 'deutsch']):
        return 'language', 'de'
    if any(k in spec or k in mat for k in ['esp', 'span']):
        return 'language', 'es'
    if any(k in spec or k in mat for k in ['ang', 'eng']):
        return 'language', 'en'
    if any(k in spec or k in mat for k in ['fran', 'fr']):
        return 'language', 'fr'
    if any(k in spec or k in mat for k in ['arab']):
        return 'language', 'ar'

    # Check active courses if specialty is not explicit
    try:
        from models import Course
        courses = Course.query.filter_by(teacher_id=t.id, active=True).all()
        for c in courses:
            clang = (c.language or '').lower()
            if 'allem' in clang: return 'language', 'de'
            if 'esp' in clang: return 'language', 'es'
            if 'ang' in clang: return 'language', 'en'
            if 'fran' in clang: return 'language', 'fr'
            if 'arab' in clang: return 'language', 'ar'
    except Exception:
        pass

    return 'soutien', None


def get_current_week_bounds(target_date=None):
    """
    Returns (monday_date, sunday_date) for the given target_date (or today).
    """
    if target_date is None:
        target_date = date.today()
    elif isinstance(target_date, str):
        try:
            target_date = date.fromisoformat(target_date)
        except Exception:
            target_date = date.today()
    elif isinstance(target_date, datetime):
        target_date = target_date.date()

    weekday = target_date.weekday()
    monday = target_date - timedelta(days=weekday)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_next_week_bounds(target_date=None):
    monday, _ = get_current_week_bounds(target_date)
    next_monday = monday + timedelta(days=7)
    next_sunday = next_monday + timedelta(days=6)
    return next_monday, next_sunday


def format_week_range(monday, sunday, lang='fr'):
    """
    Formats the week date range nicely according to language.
    """
    m_day = monday.strftime('%d/%m/%Y')
    s_day = sunday.strftime('%d/%m/%Y')

    if lang == 'en':
        return f"{monday.strftime('%b %d')} - {sunday.strftime('%b %d, %Y')}"
    elif lang == 'de':
        return f"{monday.strftime('%d.%m.')} bis {sunday.strftime('%d.%m.%Y')}"
    elif lang == 'es':
        return f"{monday.strftime('%d/%m')} al {sunday.strftime('%d/%m/%Y')}"
    elif lang == 'ar':
        return f"من {m_day} إلى {s_day}"
    else: # fr
        return f"{monday.strftime('%d/%m')} au {sunday.strftime('%d/%m/%Y')}"


def get_translations_for(lang_code):
    """
    Returns translation dictionary for given language code with fallback to French.
    """
    return TRANSLATIONS.get(lang_code, TRANSLATIONS['fr'])


def build_teacher_whatsapp_message(teacher, week_start, week_end, lang_code, form_url, settings=None):
    """
    Builds customized, polite WhatsApp message in the teacher's language.
    """
    t_dict = get_translations_for(lang_code)
    t_name = f"{teacher.first_name} {teacher.last_name}".strip()
    dates_str = format_week_range(week_start, week_end, lang_code)

    greeting = t_dict['wa_greeting'].format(name=t_name)
    intro = t_dict['wa_intro']
    body = t_dict['wa_body'].format(dates=dates_str)
    cta = f"{t_dict['wa_cta']}\n{form_url}"
    reminder = f"📌 {t_dict['wa_reminder']}"
    closing = t_dict['wa_closing']

    full_message = f"{greeting}\n\n{intro}\n\n{body}\n\n{cta}\n\n{reminder}\n\n{closing}"
    return full_message


def get_day_name(day_index, lang_code='fr'):
    """
    Returns localized day name for day_of_week (0=Monday ... 6=Sunday).
    """
    days = {
        'en': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'fr': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'],
        'de': ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'],
        'es': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'],
        'ar': ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'],
    }
    lang_days = days.get(lang_code, days['fr'])
    if 0 <= day_index <= 6:
        return lang_days[day_index]
    return ''


def get_teacher_prefilled_sessions(teacher, week_start, lang_code='fr'):
    """
    Extracts the teacher's scheduled classes for that week to pre-populate session rows.
    """
    from models import Course, ScheduleSlot
    sessions = []
    
    # 1. Fetch slots where teacher is primary or assigned
    courses = Course.query.filter_by(teacher_id=teacher.id, active=True).all()
    c_ids = [c.id for c in courses]
    
    slots = []
    if c_ids:
        slots = ScheduleSlot.query.filter(ScheduleSlot.course_id.in_(c_ids)).order_by(ScheduleSlot.day_of_week, ScheduleSlot.start_time).all()
        
    s_idx = 1
    for s in slots:
        c = s.course
        day_date = week_start + timedelta(days=s.day_of_week)
        day_name = get_day_name(s.day_of_week, lang_code)
        date_formatted = day_date.strftime('%d/%m')
        
        session_header = f"{day_name} {date_formatted} ({s.start_time or ''} - {s.end_time or ''})".strip()
        group_desc = f"{c.name}" if c else ""
        if c and c.level:
            group_desc += f" [{c.level}]"
        if s.room:
            group_desc += f" — {s.room.name}"
            
        sessions.append({
            'session_num': s_idx,
            'session_label': session_header,
            'group_desc': group_desc,
            'topic': '',
            'skills': ['speaking', 'listening'],
            'activities': '',
            'homework': '',
            'notes': '',
            'room': s.room.name if s.room else ''
        })
        s_idx += 1
        
    # If no slots in system, provide 3 clean default blank sessions
    if not sessions:
        for i in range(1, 4):
            sessions.append({
                'session_num': i,
                'session_label': f"Séance {i}" if lang_code == 'fr' else f"Session {i}",
                'group_desc': '',
                'topic': '',
                'skills': ['speaking', 'listening'],
                'activities': '',
                'homework': '',
                'notes': '',
                'room': ''
            })
            
    return sessions
