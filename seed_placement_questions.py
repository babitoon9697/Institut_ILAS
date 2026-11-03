# -*- coding: utf-8 -*-
"""
Seed professional, fast CEFR placement test questions (12 questions per language: 4 A1, 4 A2, 4 B1).
Includes short, realistic listening audio (5-7 seconds) and 'Je ne sais pas' support to eliminate guessing.
"""
import app
from models import db, PlacementQuestion

QUESTIONS_DATA = [
    # ================= ENGLISH (12 QUESTIONS: 4 A1, 4 A2, 4 B1) =================
    # --- A1 (Basics & Survival) ---
    {
        'language': 'Anglais', 'level': 'A1', 'category': 'Grammaire',
        'question_text': 'Hello, my name _____ Sarah.',
        'option_a': 'is', 'option_b': 'are', 'option_c': 'am', 'option_d': 'be',
        'correct_option': 'A', 'order_num': 1
    },
    {
        'language': 'Anglais', 'level': 'A1', 'category': 'Grammaire',
        'question_text': 'They _____ from Morocco.',
        'option_a': 'is', 'option_b': 'are', 'option_c': 'be', 'option_d': 'has',
        'correct_option': 'B', 'order_num': 2
    },
    {
        'language': 'Anglais', 'level': 'A1', 'category': 'Vocabulaire',
        'question_text': 'What time is it? It is half _____ eight (08:30).',
        'option_a': 'past', 'option_b': 'to', 'option_c': 'at', 'option_d': 'in',
        'correct_option': 'A', 'order_num': 3
    },
    {
        'language': 'Anglais', 'level': 'A1', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Listen carefully. What did the customer order?',
        'option_a': 'Two coffees and a bottle of water',
        'option_b': 'One coffee and two teas',
        'option_c': 'Three coffees',
        'option_d': 'Two orange juices',
        'correct_option': 'A', 'order_num': 4,
        'audio_script': 'Hello, can I have two coffees and one bottle of water, please?',
        'max_plays': 2
    },

    # --- A2 (Past, Daily Situations & Comparison) ---
    {
        'language': 'Anglais', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'Yesterday, we _____ to the new shopping mall.',
        'option_a': 'go', 'option_b': 'went', 'option_c': 'gone', 'option_d': 'going',
        'correct_option': 'B', 'order_num': 5
    },
    {
        'language': 'Anglais', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'I have lived in this city _____ three years.',
        'option_a': 'since', 'option_b': 'for', 'option_c': 'during', 'option_d': 'ago',
        'correct_option': 'B', 'order_num': 6
    },
    {
        'language': 'Anglais', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'My brother is much taller _____ my father.',
        'option_a': 'than', 'option_b': 'that', 'option_c': 'as', 'option_d': 'from',
        'correct_option': 'A', 'order_num': 7
    },
    {
        'language': 'Anglais', 'level': 'A2', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Listen to the announcement. On which day is the library closed?',
        'option_a': 'On Sundays',
        'option_b': 'On Saturdays',
        'option_c': 'On Mondays',
        'option_d': 'On Fridays',
        'correct_option': 'A', 'order_num': 8,
        'audio_script': 'Welcome to the city library. We are open from Monday to Saturday, but we are closed on Sundays.',
        'max_plays': 2
    },

    # --- B1 (Complex Structures, Conditionals & Connectors) ---
    {
        'language': 'Anglais', 'level': 'B1', 'category': 'Grammaire',
        'question_text': 'If it rains tomorrow, we _____ stay at home.',
        'option_a': 'will', 'option_b': 'would', 'option_c': 'had', 'option_d': 'did',
        'correct_option': 'A', 'order_num': 9
    },
    {
        'language': 'Anglais', 'level': 'B1', 'category': 'Grammaire',
        'question_text': 'When I arrived at the station, the train _____ already left.',
        'option_a': 'has', 'option_b': 'had', 'option_c': 'was', 'option_d': 'would',
        'correct_option': 'B', 'order_num': 10
    },
    {
        'language': 'Anglais', 'level': 'B1', 'category': 'Vocabulaire',
        'question_text': 'The flight was delayed _____ heavy fog at the airport.',
        'option_a': 'due to', 'option_b': 'because', 'option_c': 'although', 'option_d': 'in spite of',
        'correct_option': 'A', 'order_num': 11
    },
    {
        'language': 'Anglais', 'level': 'B1', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Listen to the airport announcement. Where must passengers for London go?',
        'option_a': 'To gate 14',
        'option_b': 'To gate 4',
        'option_c': 'To the ticket counter',
        'option_d': 'To the baggage area',
        'correct_option': 'A', 'order_num': 12,
        'audio_script': 'Attention passengers for flight BA 204 to London: please proceed immediately to gate 14.',
        'max_plays': 2
    },

    # ================= FRANÇAIS (12 QUESTIONS: 4 A1, 4 A2, 4 B1) =================
    # --- A1 (Bases & Survie) ---
    {
        'language': 'Français', 'level': 'A1', 'category': 'Grammaire',
        'question_text': 'Bonjour ! Comment vous _____ -vous ?',
        'option_a': 'appelez', 'option_b': 'appelle', 'option_c': 'appeler', 'option_d': "s'appelle",
        'correct_option': 'A', 'order_num': 1
    },
    {
        'language': 'Français', 'level': 'A1', 'category': 'Grammaire',
        'question_text': 'Paul et Marie _____ marocains.',
        'option_a': 'est', 'option_b': 'sont', 'option_c': 'ont', 'option_d': 'être',
        'correct_option': 'B', 'order_num': 2
    },
    {
        'language': 'Français', 'level': 'A1', 'category': 'Vocabulaire',
        'question_text': 'J’habite _____ Casablanca, _____ Maroc.',
        'option_a': 'à / au', 'option_b': 'en / au', 'option_c': 'au / en', 'option_d': 'dans / à',
        'correct_option': 'A', 'order_num': 3
    },
    {
        'language': 'Français', 'level': 'A1', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Écoutez le message. Que commande la cliente à la boulangerie ?',
        'option_a': 'Deux croissants et une baguette',
        'option_b': 'Un croissant et deux baguettes',
        'option_c': 'Trois pains au chocolat',
        'option_d': 'Un café et un croissant',
        'correct_option': 'A', 'order_num': 4,
        'audio_script': 'Bonjour monsieur, je voudrais deux croissants et une baguette, s\'il vous plaît.',
        'max_plays': 2
    },

    # --- A2 (Passé, Vie quotidienne & Comparaison) ---
    {
        'language': 'Français', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'Hier soir, nous _____ un très bon film en famille.',
        'option_a': 'avons regardé', 'option_b': 'regardons', 'option_c': 'regarder', 'option_d': 'sommes regardé',
        'correct_option': 'A', 'order_num': 5
    },
    {
        'language': 'Français', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'Pendant que je préparais le dîner, le téléphone _____ .',
        'option_a': 'a sonné', 'option_b': 'sonnait', 'option_c': 'a sonner', 'option_d': 'sonne',
        'correct_option': 'A', 'order_num': 6
    },
    {
        'language': 'Français', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'Ce gâteau est délicieux, j’_____ reprendrais bien un morceau.',
        'option_a': 'en', 'option_b': 'y', 'option_c': 'le', 'option_d': 'la',
        'correct_option': 'A', 'order_num': 7
    },
    {
        'language': 'Français', 'level': 'A2', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Écoutez le message vocal. À quelle heure est le rendez-vous chez le médecin ?',
        'option_a': 'À 15h30',
        'option_b': 'À 14h30',
        'option_c': 'À 16h00',
        'option_d': 'À 15h00',
        'correct_option': 'A', 'order_num': 8,
        'audio_script': 'Bonjour, le cabinet médical vous rappelle votre rendez-vous de demain mardi à 15 heures 30.',
        'max_plays': 2
    },

    # --- B1 (Subjonctif, Conditionnel & Relatifs) ---
    {
        'language': 'Français', 'level': 'B1', 'category': 'Grammaire',
        'question_text': 'Bien qu’il _____ froid aujourd’hui, les enfants jouent dehors.',
        'option_a': 'fasse', 'option_b': 'fait', 'option_c': 'ferait', 'option_d': 'fera',
        'correct_option': 'A', 'order_num': 9
    },
    {
        'language': 'Français', 'level': 'B1', 'category': 'Grammaire',
        'question_text': 'Si j’avais su que tu venais, je _____ un gâteau.',
        'option_a': 'j’aurais préparé', 'option_b': 'je préparais', 'option_c': 'je préparerai', 'option_d': 'j’avais préparé',
        'correct_option': 'A', 'order_num': 10
    },
    {
        'language': 'Français', 'level': 'B1', 'category': 'Grammaire',
        'question_text': 'C’est l’étudiant _____ le professeur a parlé hier en classe.',
        'option_a': 'dont', 'option_b': 'que', 'option_c': 'qui', 'option_d': 'auquel',
        'correct_option': 'A', 'order_num': 11
    },
    {
        'language': 'Français', 'level': 'B1', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Écoutez l’annonce en gare. De quelle voie partira le train pour Tanger ?',
        'option_a': 'De la voie 3',
        'option_b': 'De la voie 1',
        'option_c': 'De la voie 2',
        'option_d': 'De la voie 4',
        'correct_option': 'A', 'order_num': 12,
        'audio_script': 'Attention chers voyageurs, le train rapide à destination de Tanger partira exceptionnellement de la voie 3.',
        'max_plays': 2
    },

    # ================= ESPAGNOL (12 QUESTIONS: 4 A1, 4 A2, 4 B1) =================
    # --- A1 (Bases & Survie) ---
    {
        'language': 'Espagnol', 'level': 'A1', 'category': 'Grammaire',
        'question_text': '¡Hola! Yo _____ estudiante en el Instituto ILAS.',
        'option_a': 'soy', 'option_b': 'estoy', 'option_c': 'es', 'option_d': 'somos',
        'correct_option': 'A', 'order_num': 1
    },
    {
        'language': 'Espagnol', 'level': 'A1', 'category': 'Grammaire',
        'question_text': '¿De dónde _____ vosotros?',
        'option_a': 'sois', 'option_b': 'son', 'option_c': 'eres', 'option_d': 'somos',
        'correct_option': 'A', 'order_num': 2
    },
    {
        'language': 'Espagnol', 'level': 'A1', 'category': 'Vocabulaire',
        'question_text': '¿Qué hora es? Son las tres y _____ (03:30).',
        'option_a': 'media', 'option_b': 'cuarto', 'option_c': 'punto', 'option_d': 'mitad',
        'correct_option': 'A', 'order_num': 3
    },
    {
        'language': 'Espagnol', 'level': 'A1', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Escucha el diálogo. ¿Qué pide el cliente en la cafetería?',
        'option_a': 'Un café con leche y agua',
        'option_b': 'Un té y un zumo de naranja',
        'option_c': 'Dos cafés solos',
        'option_d': 'Un refresco de limón',
        'correct_option': 'A', 'order_num': 4,
        'audio_script': 'Hola, por favor, tráigame un café con leche y una botella de agua.',
        'max_plays': 2
    },

    # --- A2 (Pasado, Rutina & Comparación) ---
    {
        'language': 'Espagnol', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'Ayer mis amigos y yo _____ al cine en Tánger.',
        'option_a': 'fuimos', 'option_b': 'vamos', 'option_c': 'iban', 'option_d': 'ir',
        'correct_option': 'A', 'order_num': 5
    },
    {
        'language': 'Espagnol', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'Este libro es más interesante _____ la película.',
        'option_a': 'que', 'option_b': 'de', 'option_c': 'como', 'option_d': 'tan',
        'correct_option': 'A', 'order_num': 6
    },
    {
        'language': 'Espagnol', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'He vivido en esta ciudad _____ cuatro años.',
        'option_a': 'desde hace', 'option_b': 'hace', 'option_c': 'por', 'option_d': 'desde',
        'correct_option': 'A', 'order_num': 7
    },
    {
        'language': 'Espagnol', 'level': 'A2', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Escucha el mensaje. ¿A qué hora sale el autobús para Madrid?',
        'option_a': 'A las 10:30',
        'option_b': 'A las 10:00',
        'option_c': 'A las 11:30',
        'option_d': 'A las 09:30',
        'correct_option': 'A', 'order_num': 8,
        'audio_script': 'Pasajeros con destino a Madrid, su autobús saldrá a las diez y media de la mañana por el andén número dos.',
        'max_plays': 2
    },

    # --- B1 (Subjuntivo, Condicional & Conectores) ---
    {
        'language': 'Espagnol', 'level': 'B1', 'category': 'Grammaire',
        'question_text': 'Es importante que tú _____ español todos los días.',
        'option_a': 'practiques', 'option_b': 'practicas', 'option_c': 'practicar', 'option_d': 'practicó',
        'correct_option': 'A', 'order_num': 9
    },
    {
        'language': 'Espagnol', 'level': 'B1', 'category': 'Grammaire',
        'question_text': 'Si tuviera más tiempo libre, _____ a viajar por el mundo.',
        'option_a': 'iría', 'option_b': 'voy', 'option_c': 'fui', 'option_d': 'iré',
        'correct_option': 'A', 'order_num': 10
    },
    {
        'language': 'Espagnol', 'level': 'B1', 'category': 'Grammaire',
        'question_text': 'Aunque _____ lloviendo, saldremos a caminar por el parque.',
        'option_a': 'esté', 'option_b': 'está', 'option_c': 'estuvo', 'option_d': 'estar',
        'correct_option': 'A', 'order_num': 11
    },
    {
        'language': 'Espagnol', 'level': 'B1', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Escucha el anuncio del museo. ¿Por qué se cancela la exposición hoy?',
        'option_a': 'Por obras urgentes de mantenimiento',
        'option_b': 'Por falta de personal',
        'option_c': 'Por festivo nacional',
        'option_d': 'Por malas condiciones meteorológicas',
        'correct_option': 'A', 'order_num': 12,
        'audio_script': 'Aviso al público: la exposición temporal permanecerá cerrada hoy por labores urgentes de mantenimiento.',
        'max_plays': 2
    },

    # ================= ALLEMAND (12 QUESTIONS: 4 A1, 4 A2, 4 B1) =================
    # --- A1 (Grundlagen & Begrüßung) ---
    {
        'language': 'Allemand', 'level': 'A1', 'category': 'Grammaire',
        'question_text': 'Guten Tag! Wie _____ Sie?',
        'option_a': 'heißen', 'option_b': 'heißt', 'option_c': 'heiße', 'option_d': 'heißen Sie',
        'correct_option': 'A', 'order_num': 1
    },
    {
        'language': 'Allemand', 'level': 'A1', 'category': 'Grammaire',
        'question_text': 'Ich _____ aus Marokko.',
        'option_a': 'komme', 'option_b': 'kommt', 'option_c': 'kommen', 'option_d': 'kommst',
        'correct_option': 'A', 'order_num': 2
    },
    {
        'language': 'Allemand', 'level': 'A1', 'category': 'Vocabulaire',
        'question_text': 'Wie spät ist es? Es ist halb _____ (07:30).',
        'option_a': 'acht', 'option_b': 'sieben', 'option_c': 'neun', 'option_d': 'zehn',
        'correct_option': 'A', 'order_num': 3
    },
    {
        'language': 'Allemand', 'level': 'A1', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Hören Sie das Gespräch im Café. Was bestellt der Gast?',
        'option_a': 'Einen Kaffee und ein Mineralwasser',
        'option_b': 'Einen Tee und einen Apfelsaft',
        'option_c': 'Zwei Tassen Kaffee',
        'option_d': 'Ein Glas Orangensaft',
        'correct_option': 'A', 'order_num': 4,
        'audio_script': 'Guten Tag, ich möchte bitte einen Kaffee und ein Mineralwasser.',
        'max_plays': 2
    },

    # --- A2 (Vergangenheit, Steigerung & Alltag) ---
    {
        'language': 'Allemand', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'Gestern _____ wir ins Kino gegangen.',
        'option_a': 'sind', 'option_b': 'haben', 'option_c': 'waren', 'option_d': 'werden',
        'correct_option': 'A', 'order_num': 5
    },
    {
        'language': 'Allemand', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'Mein Bruder ist älter _____ ich.',
        'option_a': 'als', 'option_b': 'wie', 'option_c': 'von', 'option_d': 'für',
        'correct_option': 'A', 'order_num': 6
    },
    {
        'language': 'Allemand', 'level': 'A2', 'category': 'Grammaire',
        'question_text': 'Ich habe ihn _____ einer Woche getroffen.',
        'option_a': 'vor', 'option_b': 'seit', 'option_c': 'in', 'option_d': 'nach',
        'correct_option': 'A', 'order_num': 7
    },
    {
        'language': 'Allemand', 'level': 'A2', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Hören Sie die Durchsage am Bahnhof. Von welchem Gleis fährt der Zug nach Berlin?',
        'option_a': 'Von Gleis 3',
        'option_b': 'Von Gleis 1',
        'option_c': 'Von Gleis 5',
        'option_d': 'Von Gleis 13',
        'correct_option': 'A', 'order_num': 8,
        'audio_script': 'Achtung an Gleis 3: Der Intercity-Express nach Berlin fährt um 14 Uhr 15 von Gleis 3 ab.',
        'max_plays': 2
    },

    # --- B1 (Nebensätze, Konjunktiv & Relativsätze) ---
    {
        'language': 'Allemand', 'level': 'B1', 'category': 'Grammaire',
        'question_text': 'Ich lerne Deutsch, _____ ich in Deutschland arbeiten möchte.',
        'option_a': 'weil', 'option_b': 'denn', 'option_c': 'obwohl', 'option_d': 'deshalb',
        'correct_option': 'A', 'order_num': 9
    },
    {
        'language': 'Allemand', 'level': 'B1', 'category': 'Grammaire',
        'question_text': 'Wenn ich mehr Zeit hätte, _____ ich ein Buch lesen.',
        'option_a': 'würde', 'option_b': 'werde', 'option_c': 'habe', 'option_d': 'hätte',
        'correct_option': 'A', 'order_num': 10
    },
    {
        'language': 'Allemand', 'level': 'B1', 'category': 'Grammaire',
        'question_text': 'Das ist das Haus, in _____ ich als Kind gewohnt habe.',
        'option_a': 'dem', 'option_b': 'das', 'option_c': 'den', 'option_d': 'der',
        'correct_option': 'A', 'order_num': 11
    },
    {
        'language': 'Allemand', 'level': 'B1', 'category': 'Compréhension Orale (Listening)',
        'question_text': 'Hören Sie die Durchsage im Flughafen. Wohin müssen die Fluggäste nach Frankfurt gehen?',
        'option_a': 'Zu Flugsteig B 12',
        'option_b': 'Zu Flugsteig A 2',
        'option_c': 'Zur Gepäckausgabe',
        'option_d': 'Zum Informationsschalter',
        'correct_option': 'A', 'order_num': 12,
        'audio_script': 'Letzter Aufruf für Flug LH 402 nach Frankfurt: Bitte begeben Sie sich sofort zu Flugsteig B 12.',
        'max_plays': 2
    }
]

def seed_questions():
    with app.app.app_context():
        # Clear old questions so only calibrated 12-question tests exist
        PlacementQuestion.query.delete()
        db.session.commit()
        
        count = 0
        for item in QUESTIONS_DATA:
            q = PlacementQuestion(
                language=item['language'],
                level=item['level'],
                category=item.get('category', 'Grammaire'),
                question_text=item['question_text'],
                option_a=item['option_a'],
                option_b=item['option_b'],
                option_c=item['option_c'],
                option_d=item.get('option_d'),
                correct_option=item['correct_option'],
                order_num=item.get('order_num', 1),
                audio_url=item.get('audio_url'),
                audio_script=item.get('audio_script'),
                max_plays=item.get('max_plays', 2),
                active=True
            )
            db.session.add(q)
            count += 1
        db.session.commit()
        print(f"Successfully seeded {count} professional placement test questions (12 per language: 4 A1, 4 A2, 4 B1)!")

if __name__ == '__main__':
    seed_questions()
