
  function toggleAddSlotBar() {
    var b = document.getElementById('addSlotBar');
    b.style.display = (b.style.display === 'none' || b.style.display === '') ? 'block' : 'none';
  }

  function switchDayView(dayIndex) {
    var allCols = document.querySelectorAll('.day-column');
    var allBtns = document.querySelectorAll('.day-tab-btn');

    allBtns.forEach(function(btn) {
      btn.style.background = 'transparent';
      btn.style.color = '#475569';
      btn.style.fontWeight = '700';
    });

    if (dayIndex === 'all') {
      allCols.forEach(function(col) { col.style.display = 'flex'; });
      document.getElementById('scheduleGrid').style.gridTemplateColumns = 'repeat(7, 1fr)';
      document.getElementById('btnDayAll').style.background = '#1f6feb';
      document.getElementById('btnDayAll').style.color = '#fff';
      document.getElementById('btnDayAll').style.fontWeight = '800';
    } else {
      allCols.forEach(function(col, idx) {
        col.style.display = (idx == dayIndex) ? 'flex' : 'none';
      });
      document.getElementById('scheduleGrid').style.gridTemplateColumns = '1fr';
      var activeBtn = document.getElementById('btnDay' + dayIndex);
      if (activeBtn) {
        activeBtn.style.background = '#1f6feb';
        activeBtn.style.color = '#fff';
        activeBtn.style.fontWeight = '800';
      }
    }
  }

  function openPrintFormatModal() {
    document.getElementById('printFormatModal').style.display = 'flex';
  }
  function closePrintFormatModal() {
    document.getElementById('printFormatModal').style.display = 'none';
  }
  function launchPrint() {
    var formatRadios = document.getElementsByName('printFormat');
    var selectedFormat = 'a4';
    for (var i = 0; i < formatRadios.length; i++) {
      if (formatRadios[i].checked) {
        selectedFormat = formatRadios[i].value;
        break;
      }
    }
    var printDay = document.getElementById('modalPrintDay') ? document.getElementById('modalPrintDay').value : '';
    var teacherId = document.getElementById('modalPrintTeacher') ? document.getElementById('modalPrintTeacher').value : '';
    var roomId = document.getElementById('modalPrintRoom') ? document.getElementById('modalPrintRoom').value : '';
    var level = document.getElementById('modalPrintLevel') ? document.getElementById('modalPrintLevel').value : '';
    var subject = document.getElementById('modalPrintSubject') ? document.getElementById('modalPrintSubject').value : '';
    var group = document.getElementById('modalPrintGroup') ? document.getElementById('modalPrintGroup').value : '';

    var url = '/schedule/print?format=' + encodeURIComponent(selectedFormat);
    if (printDay) url += '&day=' + encodeURIComponent(printDay);
    if (teacherId) url += '&teacher_id=' + encodeURIComponent(teacherId);
    if (roomId) url += '&room_id=' + encodeURIComponent(roomId);
    if (level) url += '&level=' + encodeURIComponent(level);
    if (subject) url += '&subject=' + encodeURIComponent(subject);
    if (group) url += '&group=' + encodeURIComponent(group);

    closePrintFormatModal();
    window.open(url, '_blank');
  }

  function liveFilterScheduleCards(query) {
    query = (query || '').trim().toLowerCase();
    var cards = document.querySelectorAll('.schedule-card');
    cards.forEach(function(card) {
      if (!query) {
        card.style.display = '';
      } else {
        var txt = (card.textContent || card.innerText || '').toLowerCase();
        if (txt.indexOf(query) !== -1) {
          card.style.display = '';
        } else {
          card.style.display = 'none';
        }
      }
    });
  }

  function openRoomAssignModal(courseId, courseTitle, dayOfWeek, startTime, endTime) {
    document.getElementById('assignCourseId').value = courseId;
    document.getElementById('assignCourseTitle').innerText = 'Classe : ' + courseTitle;
    document.getElementById('assignSlotTime').innerText = 'Créneau : ' + startTime + ' → ' + endTime;
    
    var container = document.getElementById('availableRoomsContainer');
    container.innerHTML = '<div style="text-align:center; padding:12px; color:#94a3b8; font-size:12px;">⏳ Recherche des salles disponibles...</div>';
    document.getElementById('roomAssignModal').style.display = 'flex';

    fetch('/schedule/available_rooms?course_id=' + courseId + '&day_of_week=' + dayOfWeek + '&start_time=' + startTime + '&end_time=' + endTime)
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (!data.rooms || data.rooms.length === 0) {
          container.innerHTML = '<div style="color:#ef4444; font-size:12px; text-align:center; padding:10px;">Aucune salle configurée.</div>';
          return;
        }
        var html = '';
        data.rooms.forEach(function(r) {
          if (r.available) {
            html += '<label style="display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:#f0fdf4; border:1.5px solid #86efac; border-radius:8px; cursor:pointer;">' +
                      '<div style="display:flex; align-items:center; gap:8px;">' +
                        '<input type="radio" name="room_id" value="' + r.id + '" required>' +
                        '<strong style="color:#15803d; font-size:13px;">🚪 ' + r.name + '</strong>' +
                      '</div>' +
                      '<span class="chip chip-green" style="font-size:10px;">🟢 Libre (' + (r.capacity || 20) + ' places)</span>' +
                    '</label>';
          } else {
            html += '<label style="display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:#fef2f2; border:1px solid #fecaca; border-radius:8px; opacity:0.65; cursor:not-allowed;">' +
                      '<div style="display:flex; align-items:center; gap:8px;">' +
                        '<input type="radio" name="room_id" value="' + r.id + '" disabled>' +
                        '<strong style="color:#991b1b; font-size:13px;">🚪 ' + r.name + '</strong>' +
                      '</div>' +
                      '<span class="chip chip-red" style="font-size:9.5px;">Occupée : ' + r.occupied_by + '</span>' +
                    '</label>';
          }
        });
        container.innerHTML = html;
      })
      .catch(function() {
        container.innerHTML = '<div style="color:#ef4444; font-size:12px; padding:10px;">Erreur lors du chargement des salles.</div>';
      });
  }

  function closeRoomAssignModal() {
    document.getElementById('roomAssignModal').style.display = 'none';
  }

  function submitUnassignRoom() {
    var cid = document.getElementById('assignCourseId').value;
    var form = document.createElement('form');
    form.method = 'POST';
    form.action = '/schedule/assign_room';
    var in1 = document.createElement('input'); in1.type = 'hidden'; in1.name = 'course_id'; in1.value = cid;
    var in2 = document.createElement('input'); in2.type = 'hidden'; in2.name = 'room_id'; in2.value = '';
    form.appendChild(in1); form.appendChild(in2);
    document.body.appendChild(form);
    form.submit();
  }

  function openSubstituteModal(courseId, courseTitle) {
    document.getElementById('subCourseId').value = courseId;
    document.getElementById('subCourseTitle').innerText = 'Classe : ' + courseTitle;
    document.getElementById('substituteModal').style.display = 'flex';
  }
  function closeSubstituteModal() {
    document.getElementById('substituteModal').style.display = 'none';
  }

  /* ========================================================================= */
  /* WHATSAPP TIMETABLE BROADCAST LOGIC (SINGLE / MULTI GROUP & STUDENTS)      */
  /* ========================================================================= */
  var ALL_COURSES_META = [
    
    {
      id: 13,
      name: "Allemand \u2014 GROUPE 1",
      display_name: "Allemand \u2014 GROUPE 1",
      teacher_id: 7,
      teacher_name: "Ilyas SAKAM",
      category: "language",
      language: "Allemand",
      level: "A1 (D\u00e9butant)",
      group_name: "GROUPE 1: LUNDI-VENDREDI (19:00 - 21:00) A2",
      room_name: "Salle 4",
      sessions_per_week: 3
    },
    
    {
      id: 16,
      name: "Allemand \u2014 GROUPE 1",
      display_name: "Allemand \u2014 GROUPE 1",
      teacher_id: 9,
      teacher_name: "Rachid SABRI",
      category: "language",
      language: "Allemand",
      level: "A1 (D\u00e9butant)",
      group_name: "GROUPE 1: MARDI-JEUDI-SAMEDI (10:00 - 12:00) A1 DEBUTANT",
      room_name: "SALLE 9",
      sessions_per_week: 3
    },
    
    {
      id: 17,
      name: "Allemand \u2014 GROUPE 2",
      display_name: "Allemand \u2014 GROUPE 2",
      teacher_id: 9,
      teacher_name: "Rachid SABRI",
      category: "language",
      language: "Allemand",
      level: "A1 (D\u00e9butant)",
      group_name: "GROUPE 2: SAMEDI (19:00-21:00) \u0026 DIMANCHE (10:30-12:30)",
      room_name: "SALLE 9",
      sessions_per_week: 2
    },
    
    {
      id: 20,
      name: "Allemand \u2014GROUPE 1: LUNDI-MERCREDI SAMEDI(19:00 - 20:30) A1",
      display_name: "Allemand \u2014GROUPE 1: LUNDI-MERCREDI SAMEDI(19:00 - 20:30) A1",
      teacher_id: 11,
      teacher_name: "YASSINE  AFFANI",
      category: "language",
      language: "Allemand",
      level: "A1 (D\u00e9butant)",
      group_name: "Allemand \u2014GROUPE 1: LUNDI-MERCREDI SAMEDI(19:00 - 20:30) A1",
      room_name: "Salle 1",
      sessions_per_week: 3
    },
    
    {
      id: 7,
      name: "Anglais 2S/ (2h)/mardi-vendredi -19:00-20:30/ groupe2",
      display_name: "Anglais 2S/ (2h)/mardi-vendredi -19:00-20:30/ groupe2",
      teacher_id: 5,
      teacher_name: "HAMZA EL MOTAKI",
      category: "language",
      language: "Anglais",
      level: "B1 (Interm\u00e9diaire)",
      group_name: "Anglais 2S/ (2h)/mardi-vendredi -19:00-20:30/ groupe2",
      room_name: "SALLE7",
      sessions_per_week: 2
    },
    
    {
      id: 11,
      name: "Anglais 2S/sem (2h)GROUPE 3: SAMEDI (17:00-19:00) \u0026 DIMANCHE (10:30-12:30)",
      display_name: "Anglais 2S/sem (2h)GROUPE 3: SAMEDI (17:00-19:00) \u0026 DIMANCHE (10:30-12:30)",
      teacher_id: 6,
      teacher_name: "ILHAM FAKIR",
      category: "language",
      language: "Anglais",
      level: "A1 (D\u00e9butant)",
      group_name: "GROUPE 3: SAMEDI (17:00-19:00) \u0026 DIMANCHE (10:30-12:30)",
      room_name: "Salle 4",
      sessions_per_week: 2
    },
    
    {
      id: 47,
      name: "Anglais 2S/sem (2h)GROUPE 4 /MERCREDI-SAMEDI/14:45-17:00",
      display_name: "Anglais 2S/sem (2h)GROUPE 4 /MERCREDI-SAMEDI/14:45-17:00",
      teacher_id: 6,
      teacher_name: "ILHAM FAKIR",
      category: "language",
      language: "Anglais",
      level: "A2 (\u00c9l\u00e9mentaire)",
      group_name: "Anglais 2S/sem (2h)GROUPE 4 /MERCREDI-SAMEDI/14:45-17:00",
      room_name: "Salle 4",
      sessions_per_week: 2
    },
    
    {
      id: 42,
      name: "Anglais 3S (1h30) GRPOUPE  2  ENF-LUNDI-MERCREDI-19:00:20:30/samedi-11:00/12:30",
      display_name: "Anglais 3S (1h30) GRPOUPE  2  ENF-LUNDI-MERCREDI-19:00:20:30/samedi-11:00/12:30",
      teacher_id: 6,
      teacher_name: "ILHAM FAKIR",
      category: "language",
      language: "Anglais",
      level: "A1 (D\u00e9butant)",
      group_name: "GROUPE2-LUNDI-MERCREDI-19:00/samedi-11:00/12:30",
      room_name: "SALLE6",
      sessions_per_week: 3
    },
    
    {
      id: 2,
      name: "Anglais 3S/sem (1h30)",
      display_name: "Anglais 3S/sem (1h30)",
      teacher_id: 1,
      teacher_name: "MARYA ANG",
      category: "language",
      language: "Anglais",
      level: "A1 (D\u00e9butant)",
      group_name: "GROUPE 2:  SAMEDI   10:00/12:00***MERCREDI 19:00/20:30",
      room_name: "Salle 4",
      sessions_per_week: 2
    },
    
    {
      id: 45,
      name: "Anglais 3S/sem (1h30) GROUPE 2 PROF NORDINE",
      display_name: "Anglais 3S/sem (1h30) GROUPE 2 PROF NORDINE",
      teacher_id: 14,
      teacher_name: "NORDINE BOUGRIR",
      category: "language",
      language: "Anglais",
      level: "B1 (Interm\u00e9diaire)",
      group_name: "GROUPE 2",
      room_name: "SALLE 9",
      sessions_per_week: 3
    },
    
    {
      id: 8,
      name: "Anglais 3S/sem (1h30) groupe1 /lundi-mercredi-jeudi-19:00-20:30",
      display_name: "Anglais 3S/sem (1h30) groupe1 /lundi-mercredi-jeudi-19:00-20:30",
      teacher_id: 5,
      teacher_name: "HAMZA EL MOTAKI",
      category: "language",
      language: "Anglais",
      level: "A1 (D\u00e9butant)",
      group_name: "lundi-mercredi-jeudi-19:00-20:30",
      room_name: "SALLE7",
      sessions_per_week: 3
    },
    
    {
      id: 1,
      name: "Anglais 3S/sem (1h30)GROUPE 1: MARDI-JEUDI-(19:00 - 20:30) SAMEDI 10:00/11:30",
      display_name: "Anglais 3S/sem (1h30)GROUPE 1: MARDI-JEUDI-(19:00 - 20:30) SAMEDI 10:00/11:30",
      teacher_id: 1,
      teacher_name: "MARYA ANG",
      category: "language",
      language: "Anglais",
      level: "A1 (D\u00e9butant)",
      group_name: "Anglais 3S/sem (1h30)GROUPE 1: MARDI-JEUDI-(19:00 - 20:30) SAMEDI 10:00/11:30",
      room_name: "SALLE 5",
      sessions_per_week: 3
    },
    
    {
      id: 10,
      name: "Anglais 3S/sem (1h30)GROUPE 1: MARDI-JEUDI-VENDREDI (19:00 - 20:30)",
      display_name: "Anglais 3S/sem (1h30)GROUPE 1: MARDI-JEUDI-VENDREDI (19:00 - 20:30)",
      teacher_id: 6,
      teacher_name: "ILHAM FAKIR",
      category: "language",
      language: "Anglais",
      level: "A2 (\u00c9l\u00e9mentaire)",
      group_name: "GROUPE 1: MARDI-JEUDI-VENDREDI (19:00 - 20:30)",
      room_name: "SALLE6",
      sessions_per_week: 3
    },
    
    {
      id: 3,
      name: "Anglais 3S/sem (1h30)GROUPE 1: mardi-jeudi 19:00/20:30 et -SAMEDI (10:00-11:30) ENF 1/2",
      display_name: "Anglais 3S/sem (1h30)GROUPE 1: mardi-jeudi 19:00/20:30 et -SAMEDI (10:00-11:30) ENF 1/2",
      teacher_id: 2,
      teacher_name: "Aicha ILAS",
      category: "language",
      language: "Anglais",
      level: "A1 (D\u00e9butant)",
      group_name: "GROUPE 1: mardi-jeudi-vendredi (19:00 - 20:30) ENF 1/2",
      room_name: "Salle ILAS",
      sessions_per_week: 3
    },
    
    {
      id: 4,
      name: "Anglais \u2014 GROUPE 1",
      display_name: "Anglais \u2014 GROUPE 1",
      teacher_id: 12,
      teacher_name: "Aya Garwaho",
      category: "language",
      language: "Anglais",
      level: "A1 (D\u00e9butant)",
      group_name: "GROUPE 1: LUNDI-MERCREDI-VENDREDI (19:00 - 20:30)",
      room_name: "SALLE 5",
      sessions_per_week: 3
    },
    
    {
      id: 21,
      name: "Espagnol 2S/sem (2h)",
      display_name: "Espagnol 2S/sem (2h)",
      teacher_id: 13,
      teacher_name: "LINA LAHSINIA",
      category: "language",
      language: "Espagnol",
      level: "A1 (D\u00e9butant)",
      group_name: "G1",
      room_name: "SALLE 5",
      sessions_per_week: 2
    },
    
    {
      id: 49,
      name: "Fran\u00e7ais 2S/sem (2h) MERCREDI (17:00 - 19:00) SAMEDI (10:00 - 12:00)",
      display_name: "Fran\u00e7ais 2S/sem (2h) MERCREDI (17:00 - 19:00) SAMEDI (10:00 - 12:00)",
      teacher_id: 26,
      teacher_name: "HAJAR FR",
      category: "language",
      language: "Fran\u00e7ais",
      level: "A1 (D\u00e9butant)",
      group_name: "G1",
      room_name: "SALLE 5",
      sessions_per_week: 2
    },
    
    {
      id: 6,
      name: "Fran\u00e7ais 3S/sem (1h30) GROUPE 1 LUNDI -MERCREDI-VENDREDI  19:00-20:30 ADO1",
      display_name: "Fran\u00e7ais 3S/sem (1h30) GROUPE 1 LUNDI -MERCREDI-VENDREDI  19:00-20:30 ADO1",
      teacher_id: 4,
      teacher_name: "Hakima EL BRIJ",
      category: "language",
      language: "Fran\u00e7ais",
      level: "A1 (D\u00e9butant)",
      group_name: "Fran\u00e7ais 3S/sem (1h30) GROUPE 1 LUNDI -MERCREDI-VENDREDI  19:00-20:30 ADO1",
      room_name: "SALLE 8",
      sessions_per_week: 3
    },
    
    {
      id: 40,
      name: "Fran\u00e7ais 3S/sem (1h30) groupe 1 /mardi -jeudi 19:00/20:30-samedi 10:00/11:30 /ENFANT",
      display_name: "Fran\u00e7ais 3S/sem (1h30) groupe 1 /mardi -jeudi 19:00/20:30-samedi 10:00/11:30 /ENFANT",
      teacher_id: 23,
      teacher_name: "MALIKA FR",
      category: "language",
      language: "Fran\u00e7ais",
      level: "A1 (D\u00e9butant)",
      group_name: "groupe 1/ mardi -jeudi 19:00/20:30-samedi 10:00/11:30",
      room_name: "Salle 2",
      sessions_per_week: 3
    },
    
    {
      id: 46,
      name: "Fran\u00e7ais 3S/sem (1h30) groupe 2/ lundi-mercredi-vendredi 19:00/20:30/ENFANT",
      display_name: "Fran\u00e7ais 3S/sem (1h30) groupe 2/ lundi-mercredi-vendredi 19:00/20:30/ENFANT",
      teacher_id: 23,
      teacher_name: "MALIKA FR",
      category: "language",
      language: "Fran\u00e7ais",
      level: "A1 (D\u00e9butant)",
      group_name: " groupe 2/1lundi-mercredi-vendredi 19:00/20:30",
      room_name: "Salle 2",
      sessions_per_week: 3
    },
    
    {
      id: 5,
      name: "Fran\u00e7ais 3S/sem (1h30)GROUPE 2: MARDI-JEUDI-SAMEDI (19:00 - 20:30)  ",
      display_name: "Fran\u00e7ais 3S/sem (1h30)GROUPE 2: MARDI-JEUDI-SAMEDI (19:00 - 20:30)",
      teacher_id: 4,
      teacher_name: "Hakima EL BRIJ",
      category: "language",
      language: "Fran\u00e7ais",
      level: "A1 (D\u00e9butant)",
      group_name: "Fran\u00e7ais 3S/sem (1h30)GROUPE 2: MARDI-JEUDI-SAMEDI (19:00 - 20:30)  ",
      room_name: "SALLE 8",
      sessions_per_week: 3
    },
    
    {
      id: 43,
      name: "Fran\u00e7ais 3S/sem (2H/15MIN) GROUPE 3 A0 LUNDI -JEUDI 16:45-19:00",
      display_name: "Fran\u00e7ais 3S/sem (2H/15MIN) GROUPE 3 A0 LUNDI -JEUDI 16:45-19:00",
      teacher_id: 4,
      teacher_name: "Hakima EL BRIJ",
      category: "language",
      language: "Fran\u00e7ais",
      level: "A1 (D\u00e9butant)",
      group_name: "Fran\u00e7ais 3S/sem (2H/15MIN) GROUPE 3 A0 MARDI -JEUDI 16:45-19:00",
      room_name: "SALLE 8",
      sessions_per_week: 2
    },
    
    {
      id: 50,
      name: "Fran\u00e7ais 3S/sem (2h-2h-1h30) G1 MERCREDI (17:00-19:00) VENDREDI (19:00-20:30) SAMEDI (10:00-12:00)",
      display_name: "Fran\u00e7ais 3S/sem (2h-2h-1h30) G1 MERCREDI (17:00-19:00) VENDREDI (19:00-20:30) SAMEDI (10:00-12:00)",
      teacher_id: 8,
      teacher_name: "Leila LOUTFI",
      category: "language",
      language: "Fran\u00e7ais",
      level: "A1 (D\u00e9butant)",
      group_name: "",
      room_name: "Salle ILAS",
      sessions_per_week: 3
    },
    
    {
      id: 14,
      name: "Fran\u00e7ais \u2014 GROUPE 1",
      display_name: "Fran\u00e7ais \u2014 GROUPE 1",
      teacher_id: 8,
      teacher_name: "Leila LOUTFI",
      category: "language",
      language: "Fran\u00e7ais",
      level: "A1 (D\u00e9butant)",
      group_name: "GROUPE 1: MARDI-JEUDI-VENDREDI (19:00 - 20:30) ENF 2",
      room_name: "Salle ILAS",
      sessions_per_week: 3
    },
    
    {
      id: 27,
      name: "G1Soutien 1 BAC SX - Fran\u00e7ais R\u00e9gional MERCREDI -19:00-20:30 /VENDREDI 20:30/22:00/SAMEDI 19:00-20:30",
      display_name: "G1Soutien 1 BAC SX - Fran\u00e7ais R\u00e9gional MERCREDI -19:00-20:30 /VENDREDI 20:30/22:00/SAMEDI 19:00-20:30",
      teacher_id: 18,
      teacher_name: "YOUSSEF  BADR",
      category: "tutoring",
      language: "Fran\u00e7ais \u0026 Communication",
      level: "1\u00e8re Ann\u00e9e Bac (\u0627\u0644\u0623\u0648\u0644\u0649 \u0628\u0627\u0643)",
      group_name: "G1Soutien 1 BAC SX - Fran\u00e7ais R\u00e9gional MERCREDI -19:00-20:30 /VENDREDI 20:30/22:00/SAMEDI 19:00-20:30",
      room_name: "Salle 1",
      sessions_per_week: 3
    },
    
    {
      id: 23,
      name: "G1Soutien 2 BAC SX - Maths LUNDI -20:30-22:00-MERCREDI 19:00/20:30-  VENDREDI 20:30/22:00",
      display_name: "G1Soutien 2 BAC SX - Maths LUNDI -20:30-22:00-MERCREDI 19:00/20:30-  VENDREDI 20:30/22:00",
      teacher_id: 15,
      teacher_name: "HAMZA  BOUBTANA",
      category: "tutoring",
      language: "Math\u00e9matiques",
      level: "2\u00e8me Ann\u00e9e Bac (\u0627\u0644\u062b\u0627\u0646\u064a\u0629 \u0628\u0627\u0643)",
      group_name: "G1Soutien 2 BAC SX - Maths LUNDI -20:30-22:00-MERCREDI 19:00/20:30- SAMEDI 15:00/16:30",
      room_name: "SALLE 10",
      sessions_per_week: 3
    },
    
    {
      id: 26,
      name: "G1Soutien 2 BAC SX - Physique Chimie (PC) LUNDI 19:00/20:30-JEUDI 19:00-20:30 SAMEDI 17:00-18:30",
      display_name: "G1Soutien 2 BAC SX - Physique Chimie (PC) LUNDI 19:00/20:30-JEUDI 19:00-20:30 SAMEDI 17:00-18:30",
      teacher_id: 17,
      teacher_name: "HAMZA  EL ISSAOUI",
      category: "tutoring",
      language: "Physique-Chimie",
      level: "2\u00e8me Ann\u00e9e Bac (\u0627\u0644\u062b\u0627\u0646\u064a\u0629 \u0628\u0627\u0643)",
      group_name: "G1Soutien 2 BAC SX - Physique Chimie (PC) LUNDI 19:00/20:30-JEUDI 19:00-20:30 SAMEDI 16:30-18:00",
      room_name: "SALLE 10",
      sessions_per_week: 3
    },
    
    {
      id: 32,
      name: "G1Soutien 3 Coll - Physique Chimie (PC) MARDI /20:30-21:30/samedi 19:00-21:00",
      display_name: "G1Soutien 3 Coll - Physique Chimie (PC) MARDI /20:30-21:30/samedi 19:00-21:00",
      teacher_id: 20,
      teacher_name: "SAID EL OTHMANI",
      category: "tutoring",
      language: "Physique-Chimie",
      level: "Coll\u00e8ge (\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u064a)",
      group_name: "G1Soutien 3 Coll - Physique Chimie (PC) MARDI /20:30-21:30/samedi 19:00-21:00",
      room_name: "Salle 4",
      sessions_per_week: 2
    },
    
    {
      id: 19,
      name: "GROUPE 1  FRANCAIS: LUNDI-MERCREDI-VENDREDI(19:00 - 20:30) ADULT A1-A2",
      display_name: "GROUPE 1  FRANCAIS: LUNDI-MERCREDI-VENDREDI(19:00 - 20:30) ADULT A1-A2",
      teacher_id: 10,
      teacher_name: "BOUCHRA  LAHMIDI",
      category: "language",
      language: "Fran\u00e7ais",
      level: "A1 (D\u00e9butant)",
      group_name: "GROUPE 1  FRANCAIS: LUNDI-MERCREDI-VENDREDI(19:00 - 20:30) ADULT A1-A2",
      room_name: "SALLE 5",
      sessions_per_week: 3
    },
    
    {
      id: 22,
      name: "GROUPE 1 MARDI -JEUDI-VENDREDI 19:00/20:30",
      display_name: "GROUPE 1 MARDI -JEUDI-VENDREDI 19:00/20:30",
      teacher_id: 14,
      teacher_name: "NORDINE BOUGRIR",
      category: "language",
      language: "Anglais",
      level: "A1 (D\u00e9butant)",
      group_name: "G1/MARDI-JEUDI-VENDREDI/19:00/20:30",
      room_name: "SALLE 9",
      sessions_per_week: 3
    },
    
    {
      id: 18,
      name: "GROUPE 2: MARDI-JEUDI-VENDREDI(19:00 - 20:30) ADULT A1-A2",
      display_name: "GROUPE 2: MARDI-JEUDI-VENDREDI(19:00 - 20:30) ADULT A1-A2",
      teacher_id: 10,
      teacher_name: "BOUCHRA  LAHMIDI",
      category: "language",
      language: "Fran\u00e7ais",
      level: "A1 (D\u00e9butant)",
      group_name: "GROUPE 2: MARDI-JEUDI-VENDREDI(19:00 - 20:30) ADULT A1-A2",
      room_name: "Salle 1",
      sessions_per_week: 3
    },
    
    {
      id: 31,
      name: "GSoutien 3 Coll - Maths mardi-jeudi 19:00/20:30",
      display_name: "GSoutien 3 Coll - Maths mardi-jeudi 19:00/20:30",
      teacher_id: 20,
      teacher_name: "SAID EL OTHMANI",
      category: "tutoring",
      language: "Math\u00e9matiques",
      level: "Coll\u00e8ge (\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u064a)",
      group_name: "GSoutien 3 Coll - Maths mardi-jeudi 19:00/20:30",
      room_name: "Salle 4",
      sessions_per_week: 2
    },
    
    {
      id: 48,
      name: "Soutien 1 BAC SM - Maths SAMEDI 15:00-18:00",
      display_name: "Soutien 1 BAC SM - Maths SAMEDI 15:00-18:00",
      teacher_id: 25,
      teacher_name: "AYOUB SM SM",
      category: "tutoring",
      language: "Math\u00e9matiques",
      level: "1\u00e8re Ann\u00e9e Bac (\u0627\u0644\u0623\u0648\u0644\u0649 \u0628\u0627\u0643)",
      group_name: "G1",
      room_name: "Salle ILAS",
      sessions_per_week: 1
    },
    
    {
      id: 24,
      name: "Soutien 1 BAC SX - Maths  mercredi  et 20:30-22:00 vendredi 19:00-20:30",
      display_name: "Soutien 1 BAC SX - Maths  mercredi  et 20:30-22:00 vendredi 19:00-20:30",
      teacher_id: 15,
      teacher_name: "HAMZA  BOUBTANA",
      category: "tutoring",
      language: "Math\u00e9matiques",
      level: "1\u00e8re Ann\u00e9e Bac (\u0627\u0644\u0623\u0648\u0644\u0649 \u0628\u0627\u0643)",
      group_name: "G1",
      room_name: "SALLE 10",
      sessions_per_week: 2
    },
    
    {
      id: 28,
      name: "Soutien 1 BAC SX - Physique Chimie (PC)",
      display_name: "Soutien 1 BAC SX - Physique Chimie (PC)",
      teacher_id: 17,
      teacher_name: "HAMZA  EL ISSAOUI",
      category: "tutoring",
      language: "Physique-Chimie",
      level: "1\u00e8re Ann\u00e9e Bac (\u0627\u0644\u0623\u0648\u0644\u0649 \u0628\u0627\u0643)",
      group_name: "",
      room_name: "Salle 1",
      sessions_per_week: 2
    },
    
    {
      id: 38,
      name: "Soutien 1 Coll - PC + Maths + SVT mardi  et jeudi 18:30-21:30",
      display_name: "Soutien 1 Coll - PC + Maths + SVT mardi  et jeudi 18:30-21:30",
      teacher_id: 21,
      teacher_name: "HASSAN NACHAT",
      category: "tutoring",
      language: "SVT",
      level: "Coll\u00e8ge (\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u064a)",
      group_name: "G1",
      room_name: "SALLE 10",
      sessions_per_week: 2
    },
    
    {
      id: 25,
      name: "Soutien 2 BAC SX - SVT",
      display_name: "Soutien 2 BAC SX - SVT",
      teacher_id: 16,
      teacher_name: "ABD ELHAKIM SVT",
      category: "tutoring",
      language: "SVT",
      level: "2\u00e8me Ann\u00e9e Bac (\u0627\u0644\u062b\u0627\u0646\u064a\u0629 \u0628\u0627\u0643)",
      group_name: "G1",
      room_name: "Salle 1",
      sessions_per_week: 3
    },
    
    {
      id: 35,
      name: "Soutien 2 Coll - Maths",
      display_name: "Soutien 2 Coll - Maths",
      teacher_id: 22,
      teacher_name: "MOHAMAD EL AMINE",
      category: "tutoring",
      language: "Math\u00e9matiques",
      level: "Coll\u00e8ge (\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u064a)",
      group_name: "G1",
      room_name: "Salle 1",
      sessions_per_week: 2
    },
    
    {
      id: 36,
      name: "Soutien 2 Coll - Physique Chimie (PC)",
      display_name: "Soutien 2 Coll - Physique Chimie (PC)",
      teacher_id: 21,
      teacher_name: "HASSAN NACHAT",
      category: "tutoring",
      language: "Physique-Chimie",
      level: "Coll\u00e8ge (\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u064a)",
      group_name: "G1",
      room_name: "SALLE7",
      sessions_per_week: 2
    },
    
    {
      id: 37,
      name: "Soutien 2 Coll - SVT lundi 20:30-22:00 et samedi 19:00-20:30",
      display_name: "Soutien 2 Coll - SVT lundi 20:30-22:00 et samedi 19:00-20:30",
      teacher_id: 21,
      teacher_name: "HASSAN NACHAT",
      category: "tutoring",
      language: "SVT",
      level: "Coll\u00e8ge (\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u064a)",
      group_name: "G1",
      room_name: "SALLE7",
      sessions_per_week: 2
    },
    
    {
      id: 34,
      name: "Soutien 3 Coll - Fran\u00e7ais R\u00e9gional",
      display_name: "Soutien 3 Coll - Fran\u00e7ais R\u00e9gional",
      teacher_id: 18,
      teacher_name: "YOUSSEF  BADR",
      category: "tutoring",
      language: "Fran\u00e7ais \u0026 Communication",
      level: "Coll\u00e8ge (\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u064a)",
      group_name: "G1",
      room_name: "Salle 1",
      sessions_per_week: 2
    },
    
    {
      id: 33,
      name: "Soutien 3 Coll - SVT",
      display_name: "Soutien 3 Coll - SVT",
      teacher_id: 21,
      teacher_name: "HASSAN NACHAT",
      category: "tutoring",
      language: "SVT",
      level: "Coll\u00e8ge (\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u064a)",
      group_name: "G1",
      room_name: "SALLE6",
      sessions_per_week: 2
    },
    
    {
      id: 39,
      name: "Soutien Primaire - Toutes les mati\u00e8res lundi ,et  vendredi 19:00-20:30",
      display_name: "Soutien Primaire - Toutes les mati\u00e8res lundi ,et  vendredi 19:00-20:30",
      teacher_id: 21,
      teacher_name: "HASSAN NACHAT",
      category: "tutoring",
      language: "Arabe",
      level: "Primaire (\u0627\u0644\u0627\u0628\u062a\u062f\u0627\u0626\u064a)",
      group_name: "Soutien Primaire - Toutes les mati\u00e8res lundi ,MARDI,mercredi ,jeudi et  vendredi 19:00-20:30",
      room_name: "Salle 3",
      sessions_per_week: 2
    },
    
    {
      id: 29,
      name: "Soutien TC - Maths lundi  19:00/20:30et vendredi 20:30-22:00",
      display_name: "Soutien TC - Maths lundi  19:00/20:30et vendredi 20:30-22:00",
      teacher_id: 15,
      teacher_name: "HAMZA  BOUBTANA",
      category: "tutoring",
      language: "Math\u00e9matiques",
      level: "Tronc Commun (\u0627\u0644\u062c\u062f\u0639 \u0627\u0644\u0645\u0634\u062a\u0631\u0643)",
      group_name: "G1",
      room_name: "Salle ILAS",
      sessions_per_week: 2
    },
    
    {
      id: 30,
      name: "Soutien TC - Physique Chimie (PC)",
      display_name: "Soutien TC - Physique Chimie (PC)",
      teacher_id: 19,
      teacher_name: "TARIK RADID",
      category: "tutoring",
      language: "Physique-Chimie",
      level: "Tronc Commun (\u0627\u0644\u062c\u062f\u0639 \u0627\u0644\u0645\u0634\u062a\u0631\u0643)",
      group_name: "G1",
      room_name: "Salle 4",
      sessions_per_week: 2
    }
    
  ];

  var waGroupFilter = {
    teacherId: '',
    category: 'all',
    searchQuery: '',
    selectedCourseId: null
  };

  var waState = {
    groupScope: 'single', // 'single' | 'multi' | 'all'
    currentCourseId: null,
    coursesMap: {},       // course_id -> course object with slots
    coursesList: [],
    allStudents: [],      // array of student objects from current fetch
    selectedStudentIds: new Set(), // student IDs currently checked
    queue: [],            // final array of students to process in Step 2
    currentQueueIndex: 0,
    statuses: {},         // student_id -> 'pending' | 'sent' | 'skipped'
    cachedBlobs: {},      // course_id -> blob
    cachedFileNames: {},  // course_id -> filename
    selectedMsgLang: 'ar'
  };

  function getFilteredCourses() {
    return ALL_COURSES_META.filter(function(c) {
      // 1. Filter by Teacher
      if (waGroupFilter.teacherId && String(c.teacher_id) !== String(waGroupFilter.teacherId)) {
        return false;
      }
      // 2. Filter by Category / Subject
      if (waGroupFilter.category && waGroupFilter.category !== 'all') {
        var cat = waGroupFilter.category.toLowerCase();
        var cName = (c.name || '').toLowerCase();
        var cLang = (c.language || '').toLowerCase();
        var cCat = (c.category || '').toLowerCase();
        if (cat === 'soutien') {
          if (cCat !== 'tutoring' && cName.indexOf('soutien') === -1) return false;
        } else {
          if (cLang.indexOf(cat) === -1 && cName.indexOf(cat) === -1) return false;
        }
      }
      // 3. Filter by Search Query
      if (waGroupFilter.searchQuery) {
        var q = waGroupFilter.searchQuery;
        var matchStr = ((c.name || '') + ' ' + (c.teacher_name || '') + ' ' + (c.level || '') + ' ' + (c.group_name || '') + ' ' + (c.room_name || '')).toLowerCase();
        if (matchStr.indexOf(q) === -1) return false;
      }
      return true;
    });
  }

  function renderGroupSelectors() {
    var filtered = getFilteredCourses();

    // 1. Update Match Counter
    var countEl = document.getElementById('waGroupMatchCount');
    if (countEl) countEl.innerText = filtered.length + ' classe(s) trouvée(s)';

    // 2. Render Single Mode Cards
    var singleContainer = document.getElementById('waSingleCardsList');
    if (singleContainer) {
      if (filtered.length === 0) {
        singleContainer.innerHTML = '<div style="text-align:center; padding:16px; color:#64748b; font-size:12px;">🔍 Aucun groupe trouvé avec ces filtres. Essayez de réinitialiser la recherche.</div>';
      } else {
        // Check if selected course is still in filtered set
        var isCurrentInFiltered = filtered.some(function(c) { return c.id === waGroupFilter.selectedCourseId; });
        if (!isCurrentInFiltered) {
          waGroupFilter.selectedCourseId = filtered[0].id;
        }

        var html = '';
        filtered.forEach(function(c) {
          var isSel = (c.id === waGroupFilter.selectedCourseId);
          html += '<div class="wa-single-group-card" data-cid="' + c.id + '" onclick="selectSingleCourse(' + c.id + ')" ' +
            'style="padding:7px 11px; border-radius:8px; border:2px solid ' + (isSel ? '#16a34a' : '#e2e8f0') + '; ' +
            'background:' + (isSel ? '#f0fdf4' : '#ffffff') + '; cursor:pointer; transition:all 0.15s; display:flex; justify-content:space-between; align-items:center;">' +
            '<div style="flex:1; min-width:0; padding-right:8px;">' +
              '<div style="font-weight:800; font-size:12px; color:' + (isSel ? '#15803d' : '#0B3D6E') + '; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">' +
                c.name +
              '</div>' +
              '<div style="display:flex; gap:5px; margin-top:2px; flex-wrap:wrap; align-items:center;">' +
                '<span class="chip chip-purple" style="font-size:9.5px; padding:1px 6px;">👨‍🏫 ' + c.teacher_name + '</span>' +
                '<span class="chip chip-green" style="font-size:9.5px; padding:1px 6px;">🚪 ' + c.room_name + '</span>' +
                '<span class="chip chip-blue" style="font-size:9.5px; padding:1px 6px;">⏱️ ' + c.sessions_per_week + ' s/sem</span>' +
              '</div>' +
            '</div>' +
            '<div>' +
              '<span class="wa-card-check chip chip-green" style="font-size:10px; font-weight:800; display:' + (isSel ? 'inline-block' : 'none') + ';">✓ Choisi</span>' +
            '</div>' +
          '</div>';
        });
        singleContainer.innerHTML = html;
      }
    }

    // 3. Render Multi Mode Checkboxes
    var multiContainer = document.getElementById('waCourseChecklistWrapper');
    if (multiContainer) {
      if (filtered.length === 0) {
        multiContainer.innerHTML = '<div style="text-align:center; padding:14px; color:#64748b; font-size:12px;">Aucun groupe trouvé.</div>';
      } else {
        var mHtml = '';
        filtered.forEach(function(c) {
          mHtml += '<label class="wa-course-item" data-cname="' + (c.name || '').toLowerCase() + '" style="display:flex; align-items:center; gap:8px; padding:5px 8px; border-radius:6px; margin-bottom:3px; font-size:12px; cursor:pointer; background:#f8fafc; border:1px solid #e2e8f0;">' +
            '<input type="checkbox" class="wa-course-cb" value="' + c.id + '" onchange="onCourseCheckboxesChanged()">' +
            '<div style="flex:1; min-width:0;">' +
              '<strong style="color:#0B3D6E; font-size:12px;">' + c.name + '</strong>' +
              '<div style="display:flex; gap:4px; margin-top:2px;">' +
                '<span class="chip chip-purple" style="font-size:9px;">👨‍🏫 ' + c.teacher_name + '</span>' +
                '<span class="chip chip-gray" style="font-size:9px;">🚪 ' + c.room_name + '</span>' +
              '</div>' +
            '</div>' +
          '</label>';
        });
        multiContainer.innerHTML = mHtml;
      }
    }

    // 4. Synced native select
    var sel = document.getElementById('waCourseSelect');
    if (sel && waGroupFilter.selectedCourseId) {
      sel.value = waGroupFilter.selectedCourseId;
    }
  }

  function selectSingleCourse(cid) {
    waGroupFilter.selectedCourseId = cid;
    var sel = document.getElementById('waCourseSelect');
    if (sel) sel.value = cid;

    // Update active highlight classes
    document.querySelectorAll('.wa-single-group-card').forEach(function(card) {
      var itemCid = parseInt(card.getAttribute('data-cid'));
      var isCur = (itemCid === cid);
      card.style.borderColor = isCur ? '#16a34a' : '#e2e8f0';
      card.style.background = isCur ? '#f0fdf4' : '#ffffff';
      var titleEl = card.querySelector('div > div');
      if (titleEl) titleEl.style.color = isCur ? '#15803d' : '#0B3D6E';
      var chk = card.querySelector('.wa-card-check');
      if (chk) chk.style.display = isCur ? 'inline-block' : 'none';
    });

    reloadGroupData();
  }

  function onWaTeacherFilterChanged() {
    var sel = document.getElementById('waTeacherFilterSelect');
    waGroupFilter.teacherId = sel ? sel.value : '';
    renderGroupSelectors();
    if (waState.groupScope === 'single' && waGroupFilter.selectedCourseId) {
      reloadGroupData();
    }
  }

  function onWaGroupSearchInput(query) {
    waGroupFilter.searchQuery = (query || '').trim().toLowerCase();
    renderGroupSelectors();
    if (waState.groupScope === 'single' && waGroupFilter.selectedCourseId) {
      reloadGroupData();
    }
  }

  function filterByCourseCategory(cat) {
    waGroupFilter.category = cat;
    document.querySelectorAll('.wa-cat-pill').forEach(function(btn) {
      btn.style.background = '#f1f5f9';
      btn.style.color = '#475569';
      btn.style.fontWeight = '700';
    });
    var activeId = 'waCatPill' + (cat === 'all' ? 'All' : (cat === 'Français' ? 'Francais' : cat));
    var activeBtn = document.getElementById(activeId);
    if (activeBtn) {
      activeBtn.style.background = '#1f6feb';
      activeBtn.style.color = '#fff';
      activeBtn.style.fontWeight = '800';
    }
    renderGroupSelectors();
    if (waState.groupScope === 'single' && waGroupFilter.selectedCourseId) {
      reloadGroupData();
    }
  }

  function openScheduleWhatsAppModal(courseId) {
    var modal = document.getElementById('scheduleWhatsAppModal');
    if (!modal) return;
    modal.style.display = 'flex';

    document.getElementById('waStepConfig').style.display = 'block';
    document.getElementById('waStepDispatch').style.display = 'none';

    // Reset scope to single
    setGroupScope('single', false);

    if (courseId) {
      var found = ALL_COURSES_META.find(function(c) { return c.id === courseId; });
      if (found) {
        waGroupFilter.teacherId = found.teacher_id ? String(found.teacher_id) : '';
        var tSel = document.getElementById('waTeacherFilterSelect');
        if (tSel) tSel.value = waGroupFilter.teacherId;
      }
      waGroupFilter.selectedCourseId = courseId;
    } else {
      var pageTeacherId = '';
      if (pageTeacherId) {
        waGroupFilter.teacherId = String(pageTeacherId);
        var tSel = document.getElementById('waTeacherFilterSelect');
        if (tSel) tSel.value = waGroupFilter.teacherId;
      } else {
        waGroupFilter.teacherId = '';
        var tSel = document.getElementById('waTeacherFilterSelect');
        if (tSel) tSel.value = '';
      }
      waGroupFilter.selectedCourseId = null;
    }

    waGroupFilter.category = 'all';
    waGroupFilter.searchQuery = '';
    var searchInput = document.getElementById('waGroupLiveSearch');
    if (searchInput) searchInput.value = '';

    renderGroupSelectors();
    reloadGroupData();
  }

  function closeScheduleWhatsAppModal() {
    var modal = document.getElementById('scheduleWhatsAppModal');
    if (modal) modal.style.display = 'none';
  }

  function setGroupScope(scope, autoReload) {
    if (autoReload === undefined) autoReload = true;
    waState.groupScope = scope;

    var btnSingle = document.getElementById('btnScopeSingle');
    var btnMulti = document.getElementById('btnScopeMulti');
    var btnAll = document.getElementById('btnScopeAll');

    [btnSingle, btnMulti, btnAll].forEach(function(b) {
      b.style.background = 'transparent';
      b.style.color = '#475569';
      b.style.fontWeight = '700';
    });

    var activeBtn = (scope === 'single') ? btnSingle : (scope === 'multi' ? btnMulti : btnAll);
    activeBtn.style.background = '#1f6feb';
    activeBtn.style.color = '#fff';
    activeBtn.style.fontWeight = '800';

    document.getElementById('waSingleCourseContainer').style.display = (scope === 'single') ? 'block' : 'none';
    document.getElementById('waMultiCoursesContainer').style.display = (scope === 'multi') ? 'block' : 'none';
    document.getElementById('waAllCoursesNotice').style.display = (scope === 'all') ? 'block' : 'none';

    if (autoReload) {
      reloadGroupData();
    }
  }

  function onWaCourseChanged() {
    if (waState.groupScope === 'single') {
      var sel = document.getElementById('waCourseSelect');
      if (sel && sel.value) {
        selectSingleCourse(parseInt(sel.value));
      }
    }
  }

  function onCourseCheckboxesChanged() {
    if (waState.groupScope === 'multi') {
      reloadGroupData();
    }
  }

  function selectAllCourses(checkAll) {
    var cbs = document.querySelectorAll('.wa-course-cb');
    cbs.forEach(function(cb) { cb.checked = checkAll; });
    onCourseCheckboxesChanged();
  }

  function reloadGroupData() {
    var url = '/schedule/group_whatsapp_data?';
    if (waState.groupScope === 'single') {
      var cid = waGroupFilter.selectedCourseId;
      if (!cid) {
        var sel = document.getElementById('waCourseSelect');
        cid = sel ? sel.value : null;
      }
      if (!cid) {
        document.getElementById('waStudentChecklistLoading').innerHTML = '👈 Choisissez une classe ci-dessus';
        document.getElementById('waStudentChecklistBody').innerHTML = '';
        return;
      }
      url += 'course_id=' + cid;
    } else if (waState.groupScope === 'multi') {
      var checkedCids = [];
      document.querySelectorAll('.wa-course-cb:checked').forEach(function(cb) {
        checkedCids.push(cb.value);
      });
      if (checkedCids.length === 0) {
        document.getElementById('waStudentChecklistLoading').innerHTML = '👈 Cochez au moins une classe ci-dessus';
        document.getElementById('waStudentChecklistBody').innerHTML = '';
        return;
      }
      url += 'course_ids=' + checkedCids.join(',');
    } else {
      url += 'all=1';
    }

    document.getElementById('waTimetableLoading').innerText = '⏳ Chargement des données...';
    document.getElementById('waTimetableLoading').style.display = 'block';
    document.getElementById('waTimetablePreviewCard').style.display = 'none';

    document.getElementById('waStudentChecklistLoading').innerText = '⏳ Chargement de la liste des élèves...';
    document.getElementById('waStudentChecklistLoading').style.display = 'block';
    document.getElementById('waStudentChecklistBody').innerHTML = '';

    fetch(url)
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.error) {
          alert(data.error);
          return;
        }

        waState.coursesMap = data.courses_map || {};
        waState.coursesList = data.courses_list || [data.course];
        waState.allStudents = data.students || [];

        // Check all students by default
        waState.selectedStudentIds = new Set();
        waState.allStudents.forEach(function(s) {
          waState.selectedStudentIds.add(s.id);
        });

        // Set message templates
        waState.msg_ar = data.msg_ar;
        waState.msg_fr = data.msg_fr;
        updateWaMessageTemplate();

        // Render Timetable Preview using currently selected course
        var cToPreview = null;
        if (waState.groupScope === 'single' && waGroupFilter.selectedCourseId && waState.coursesMap[waGroupFilter.selectedCourseId]) {
          cToPreview = waState.coursesMap[waGroupFilter.selectedCourseId];
        } else {
          cToPreview = data.course;
        }

        if (cToPreview) {
          renderTimetableCards(cToPreview);
        }

        document.getElementById('waTimetableLoading').style.display = 'none';
        document.getElementById('waTimetablePreviewCard').style.display = 'block';

        // Render Student Checklist
        document.getElementById('waStudentChecklistLoading').style.display = 'none';
        renderStudentChecklist();
      })
      .catch(function(err) {
        console.error(err);
        document.getElementById('waTimetableLoading').innerText = '❌ Erreur de chargement.';
        document.getElementById('waStudentChecklistLoading').innerText = '❌ Erreur de chargement.';
      });
  }

  function renderStudentChecklist() {
    var container = document.getElementById('waStudentChecklistBody');
    if (!container) return;

    var targetMode = document.getElementById('waRecipientTarget').value;
    var html = '';

    if (waState.allStudents.length === 0) {
      container.innerHTML = '<div style="text-align:center; padding:16px; color:#64748b; font-size:12px;">Aucun élève trouvé dans la sélection.</div>';
      updateStudentSelectionCount();
      return;
    }

    waState.allStudents.forEach(function(s) {
      var isChecked = waState.selectedStudentIds.has(s.id);
      var phone = getStudentTargetPhone(s, targetMode);
      var phoneFmt = phone ? formatPhoneDisplay(phone) : '<span style="color:#ef4444; font-weight:700;">Sans tél</span>';

      html += '<div class="wa-student-check-row" data-name="' + (s.full_name || '').toLowerCase() + '" data-phone="' + (phone || '') + '" style="display:flex; justify-content:space-between; align-items:center; padding:6px 10px; border-radius:6px; margin-bottom:3px; background:' + (isChecked ? '#f0fdf4' : '#ffffff') + '; border:1px solid ' + (isChecked ? '#bbf7d0' : '#e2e8f0') + '; transition:all 0.15s;">' +
        '<label style="display:flex; align-items:center; gap:8px; cursor:pointer; flex:1; margin:0;">' +
          '<input type="checkbox" class="wa-stu-cb" value="' + s.id + '" ' + (isChecked ? 'checked' : '') + ' onchange="onStudentCheckboxChanged(this)">' +
          '<div>' +
            '<span style="font-weight:800; font-size:12px; color:#0B3D6E;">' + s.full_name + '</span>' +
            '<span class="chip chip-blue" style="font-size:9.5px; padding:1px 6px; margin-left:6px;">' + s.course_name + '</span>' +
          '</div>' +
        '</label>' +
        '<div style="display:flex; align-items:center; gap:8px;">' +
          '<span style="font-size:11px; color:#475569;">📱 ' + phoneFmt + '</span>' +
          '<button type="button" onclick="sendSingleStudentDirect(' + s.id + ', ' + s.course_id + ')" class="btn btn-xs btn-outline" style="border-color:#16a34a; color:#15803d; background:#fff; font-weight:800; font-size:10.5px; padding:2px 7px;" title="Envoyer immédiatement à cet élève sans file d\'attente">' +
            '💬 Envoyer seul' +
          '</button>' +
        '</div>' +
      '</div>';
    });

    container.innerHTML = html;
    updateStudentSelectionCount();
  }

  function onStudentCheckboxChanged(cb) {
    var sid = parseInt(cb.value);
    if (cb.checked) {
      waState.selectedStudentIds.add(sid);
      cb.closest('.wa-student-check-row').style.background = '#f0fdf4';
      cb.closest('.wa-student-check-row').style.borderColor = '#bbf7d0';
    } else {
      waState.selectedStudentIds.delete(sid);
      cb.closest('.wa-student-check-row').style.background = '#ffffff';
      cb.closest('.wa-student-check-row').style.borderColor = '#e2e8f0';
    }
    updateStudentSelectionCount();
  }

  function selectAllStudents(checkAll) {
    var cbs = document.querySelectorAll('.wa-stu-cb');
    waState.selectedStudentIds.clear();
    cbs.forEach(function(cb) {
      cb.checked = checkAll;
      if (checkAll) waState.selectedStudentIds.add(parseInt(cb.value));
      var row = cb.closest('.wa-student-check-row');
      if (row) {
        row.style.background = checkAll ? '#f0fdf4' : '#ffffff';
        row.style.borderColor = checkAll ? '#bbf7d0' : '#e2e8f0';
      }
    });
    updateStudentSelectionCount();
  }

  function filterStudentChecklist(query) {
    query = (query || '').trim().toLowerCase();
    var rows = document.querySelectorAll('.wa-student-check-row');
    rows.forEach(function(row) {
      var n = row.getAttribute('data-name') || '';
      var p = row.getAttribute('data-phone') || '';
      row.style.display = (!query || n.indexOf(query) !== -1 || p.indexOf(query) !== -1) ? 'flex' : 'none';
    });
  }

  function updateStudentSelectionCount() {
    var count = waState.selectedStudentIds.size;
    var total = waState.allStudents.length;
    var badge = document.getElementById('waSelectionSummaryBadge');
    if (badge) badge.innerText = '🎯 ' + count + ' sélectionné(s) / ' + total;

    var btnCount = document.getElementById('btnSendStudentCount');
    if (btnCount) btnCount.innerText = count;

    var btnStart = document.getElementById('btnStartBroadcast');
    if (btnStart) {
      btnStart.disabled = (count === 0);
      btnStart.style.opacity = (count === 0) ? '0.5' : '1';
    }
  }

  function setElText(id, txt) {
    var el = document.getElementById(id);
    if (el) el.innerText = txt;
  }

  function setElHtml(id, html) {
    var el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  function renderTimetableCards(courseObj) {
    if (!courseObj) return;
    var slots = courseObj.slots || [];
    var cName = courseObj.name || courseObj.display_name || 'Classe';
    var tName = courseObj.teacher_name || 'Non assigné';
    var rName = courseObj.room_name || 'Salle ILAS';
    var dur = courseObj.session_duration || '1h30';
    var sessCount = (slots.length || courseObj.sessions_per_week || 3) + ' séance(s) / sem';

    var slotsHtml = '';
    if (slots.length > 0) {
      slots.forEach(function(s) {
        slotsHtml += '<tr style="border-bottom:1px solid #e2e8f0; font-size:11.5px;">' +
          '<td style="padding:6px 10px; font-weight:800; color:#0B3D6E;">📅 ' + s.day_fr + ' <span style="font-size:10px; opacity:0.8; font-weight:600;">(' + s.day_ar + ')</span></td>' +
          '<td style="padding:6px 10px; font-weight:800; color:#1f6feb;">⏱️ ' + s.start_time + ' → ' + s.end_time + '</td>' +
          '<td style="padding:6px 10px; font-weight:700; color:#047857;">🚪 ' + rName + '</td>' +
        '</tr>';
      });
    } else {
      slotsHtml = '<tr><td colspan="3" style="padding:10px; text-align:center; color:#64748b; font-size:11.5px;">Créneaux à définir</td></tr>';
    }

    // 1. Update Visible Preview Card (in modal)
    setElText('previewCourseName', cName);
    setElText('previewTeacherName', tName);
    setElText('previewRoomName', rName);
    setElText('previewDuration', dur);
    setElText('previewSessionsCount', sessCount);
    setElHtml('previewSlotsTableBody', slotsHtml);

    // 2. Update Off-Screen Export Card (for html2canvas)
    setElText('exportCourseName', cName);
    setElText('exportTeacherName', tName);
    setElText('exportRoomName', rName);
    setElText('exportDuration', dur);
    setElText('exportSessionsCount', sessCount);
    setElHtml('exportSlotsTableBody', slotsHtml);
  }

  function switchWaMsgLang(lang) {
    waState.selectedMsgLang = lang;
    var btnAr = document.getElementById('waBtnLangAr');
    var btnFr = document.getElementById('waBtnLangFr');
    if (lang === 'ar') {
      btnAr.style.background = '#1f6feb'; btnAr.style.color = '#fff';
      btnFr.style.background = '#f1f5f9'; btnFr.style.color = '#475569';
    } else {
      btnFr.style.background = '#1f6feb'; btnFr.style.color = '#fff';
      btnAr.style.background = '#f1f5f9'; btnAr.style.color = '#475569';
    }
    updateWaMessageTemplate();
  }

  function updateWaMessageTemplate() {
    var txt = (waState.selectedMsgLang === 'ar') ? waState.msg_ar : waState.msg_fr;
    if (txt) document.getElementById('waMessageText').value = txt;
  }

  /* ── Capture & Save Timetable to Desktop (Promise) ── */
  function captureAndSaveTimetable(courseObj) {
    return new Promise(function(resolve, reject) {
      var cid = courseObj.id;
      if (waState.cachedBlobs[cid]) {
        try {
          if (navigator.clipboard && navigator.clipboard.write) {
            navigator.clipboard.write([new ClipboardItem({'image/png': waState.cachedBlobs[cid])]);
          }
        } catch(e) {}
        resolve({ file_name: waState.cachedFileNames[cid], blob: waState.cachedBlobs[cid] });
        return;
      }

      renderTimetableCards(courseObj);

      var hdCard = document.getElementById('waHdCard');
      html2canvas(hdCard, {
        scale: 2,
        backgroundColor: '#ffffff',
        useCORS: true,
        logging: false
      }).then(function(canvas) {
        var dataUrl = canvas.toDataURL('image/png');

        canvas.toBlob(function(blob) {
          waState.cachedBlobs[cid] = blob;
          try {
            if (navigator.clipboard && navigator.clipboard.write) {
              navigator.clipboard.write([new ClipboardItem({'image/png': blob})]);
            }
          } catch(e) {}

          var cName = courseObj.name || courseObj.display_name;
          fetch('/schedule/save_timetable_image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image_base64: dataUrl, group_name: cName })
          })
          .then(function(res) { return res.json(); })
          .then(function(result) {
            if (result.success) {
              waState.cachedFileNames[cid] = result.file_name;
              resolve({ file_name: result.file_name, blob: blob });
            } else {
              reject(result.error);
            }
          })
          .catch(reject);
        });
      }).catch(reject);
    });
  }

  /* ── Step 1 to Step 2: Start Broadcast ── */
  function startWhatsAppBroadcast() {
    var selected = waState.allStudents.filter(function(s) {
      return waState.selectedStudentIds.has(s.id);
    });

    if (selected.length === 0) {
      alert('Veuillez cocher au moins un élève.');
      return;
    }

    selected.sort(keyCompareCourseAndName);
    waState.queue = selected;
    waState.currentQueueIndex = 0;
    waState.statuses = {};
    selected.forEach(function(s) { waState.statuses[s.id] = 'pending'; });

    var btn = document.getElementById('btnStartBroadcast');
    var origText = btn.innerHTML;
    btn.innerHTML = '<span>⏳</span> <span>Préparation de l\'emploi du temps...</span>';
    btn.disabled = true;

    var firstStu = waState.queue[0];
    var firstCourse = waState.coursesMap[firstStu.course_id];

    captureAndSaveTimetable(firstCourse)
      .then(function(res) {
        btn.innerHTML = origText;
        btn.disabled = false;

        document.getElementById('waSavedFileName').innerText = res.file_name;
        document.getElementById('waStepConfig').style.display = 'none';
        document.getElementById('waStepDispatch').style.display = 'block';

        renderDispatchTable();
        processQueueAt(0);
      })
      .catch(function(err) {
        btn.innerHTML = origText;
        btn.disabled = false;
        alert('Erreur lors de la capture : ' + err);
      });
  }

  function keyCompareCourseAndName(a, b) {
    if (a.course_id !== b.course_id) return a.course_id - b.course_id;
    return (a.full_name || '').localeCompare(b.full_name || '');
  }

  function processQueueAt(index) {
    waState.currentQueueIndex = index;
    displayCurrentStudent();

    if (index >= waState.queue.length) return;

    var stu = waState.queue[index];
    var courseObj = waState.coursesMap[stu.course_id];

    if (!waState.cachedBlobs[stu.course_id]) {
      var nameEl = document.getElementById('waCurrentStudentName');
      nameEl.innerText = '⏳ Génération de l\'image de ' + (stu.course_name || 'la classe') + '...';

      captureAndSaveTimetable(courseObj).then(function(res) {
        document.getElementById('waSavedFileName').innerText = res.file_name;
        displayCurrentStudent();
        triggerCurrentStudentWhatsApp();
      });
    } else {
      try {
        if (navigator.clipboard && navigator.clipboard.write) {
          navigator.clipboard.write([new ClipboardItem({'image/png': waState.cachedBlobs[stu.course_id]})]);
        }
      } catch(e) {}
      document.getElementById('waSavedFileName').innerText = waState.cachedFileNames[stu.course_id] || 'Emploi.png';
      triggerCurrentStudentWhatsApp();
    }
  }

  function displayCurrentStudent() {
    var idx = waState.currentQueueIndex;
    var total = waState.queue.length;

    if (total === 0) {
      document.getElementById('waCurrentStudentCard').innerHTML = '<div style="text-align:center; padding:16px;">Aucun élève dans la sélection.</div>';
      return;
    }

    var completed = Object.values(waState.statuses).filter(function(st) { return st === 'sent'; }).length;
    var pct = Math.round((completed / total) * 100);
    document.getElementById('waProgressTitle').innerText = 'Progression : Élève ' + (Math.min(idx + 1, total)) + ' sur ' + total;
    document.getElementById('waProgressPercent').innerText = pct + '%';
    document.getElementById('waProgressBarFill').style.width = pct + '%';
    document.getElementById('waProgressCompleted').innerText = completed + ' envoyé(s) ✅';
    document.getElementById('waProgressRemaining').innerText = (total - completed) + ' restant(s)';

    if (idx >= total) {
      document.getElementById('waCurrentStudentCard').innerHTML = 
        '<div style="text-align:center; padding:22px;">' +
          '<div style="font-size:38px; margin-bottom:8px;">🎉</div>' +
          '<div style="font-size:18px; font-weight:900; color:#15803d; margin-bottom:4px;">Félicitations ! Diffusion terminée</div>' +
          '<div style="font-size:13px; color:#475569;">Tous les élèves sélectionnés ont été contactés.</div>' +
          '<div style="margin-top:16px;">' +
            '<button type="button" onclick="closeScheduleWhatsAppModal()" class="btn btn-primary" style="background:#16a34a; border-color:#16a34a; font-weight:800; padding:8px 22px;">Terminer</button>' +
          '</div>' +
        '</div>';
      renderDispatchTable();
      return;
    }

    var s = waState.queue[idx];
    document.getElementById('waCurrentStudentName').innerHTML = s.full_name + ' <span class="chip chip-blue" style="font-size:10.5px; font-weight:700;">' + s.course_name + '</span>';
    document.getElementById('waCurrentStudentAvatar').innerText = (s.first_name ? s.first_name.charAt(0) : '?');

    var targetMode = document.getElementById('waRecipientTarget').value;
    var chosenPhone = getStudentTargetPhone(s, targetMode);

    var phoneDisplay = '';
    if (chosenPhone) {
      phoneDisplay = '📱 Destinataire : <strong>' + formatPhoneDisplay(chosenPhone) + '</strong>';
      if (s.parent_phone && s.phone && s.parent_phone !== s.phone) {
        phoneDisplay += ' <span style="font-size:11px; color:#64748b;">(Parent: ' + s.parent_phone + ' · Élève: ' + s.phone + ')</span>';
      }
    } else {
      phoneDisplay = '⚠️ <span style="color:#ef4444; font-weight:700;">Aucun numéro WhatsApp enregistré pour cet élève</span>';
    }
    document.getElementById('waCurrentStudentPhone').innerHTML = phoneDisplay;

    var secBtn = document.getElementById('btnOpenSecondaryWa');
    if (s.parent_phone && s.phone && s.parent_phone !== s.phone) {
      secBtn.style.display = 'inline-flex';
      var isTargetParent = (chosenPhone === s.clean_parent_phone);
      var secLabel = isTargetParent ? 'Tél Élève (' + s.phone + ')' : 'Tél Parent (' + s.parent_phone + ')';
      document.getElementById('btnOpenSecondaryWaLabel').innerText = secLabel;
    } else {
      secBtn.style.display = 'none';
    }

    var st = waState.statuses[s.id] || 'pending';
    var badgeHtml = '';
    if (st === 'sent') badgeHtml = '<span class="chip chip-green" style="font-size:11px; font-weight:800;">Envoyé ✅</span>';
    else if (st === 'skipped') badgeHtml = '<span class="chip chip-amber" style="font-size:11px; font-weight:800;">Ignoré ⏭️</span>';
    else badgeHtml = '<span class="chip chip-blue" style="font-size:11px; font-weight:800;">En cours 💬</span>';
    document.getElementById('waCurrentStudentStatusBadge').innerHTML = badgeHtml;

    var isLast = (idx === total - 1);
    document.getElementById('btnNextStudent').innerHTML = isLast ? '<span>Terminer la liste ✅</span>' : '<span>Suivant ➡️</span>';

    renderDispatchTable();
  }

  function triggerCurrentStudentWhatsApp() {
    var idx = waState.currentQueueIndex;
    if (idx >= waState.queue.length) return;
    var s = waState.queue[idx];

    var targetMode = document.getElementById('waRecipientTarget').value;
    var phone = getStudentTargetPhone(s, targetMode);

    if (!phone) {
      alert('Aucun numéro de téléphone WhatsApp disponible pour ' + s.full_name + '. Cliquez sur "Suivant ➡️" pour passer à l\'élève suivant.');
      return;
    }

    var msg = buildPersonalizedMessage(s);
    launchWhatsAppUrl(phone, msg);
  }

  function triggerSecondaryWhatsApp() {
    var idx = waState.currentQueueIndex;
    if (idx >= waState.queue.length) return;
    var s = waState.queue[idx];
    var targetMode = document.getElementById('waRecipientTarget').value;
    var primaryPhone = getStudentTargetPhone(s, targetMode);
    var secPhone = (primaryPhone === s.clean_parent_phone) ? s.clean_student_phone : s.clean_parent_phone;
    if (!secPhone) return;

    var msg = buildPersonalizedMessage(s);
    launchWhatsAppUrl(secPhone, msg);
  }

  function advanceToNextStudent() {
    var idx = waState.currentQueueIndex;
    if (idx < waState.queue.length) {
      var cur = waState.queue[idx];
      waState.statuses[cur.id] = 'sent';
    }

    processQueueAt(idx + 1);
  }

  function skipCurrentStudent() {
    var idx = waState.currentQueueIndex;
    if (idx < waState.queue.length) {
      var cur = waState.queue[idx];
      waState.statuses[cur.id] = 'skipped';
    }
    processQueueAt(idx + 1);
  }

  function backToWaConfig() {
    document.getElementById('waStepConfig').style.display = 'block';
    document.getElementById('waStepDispatch').style.display = 'none';
  }

  /* ── Send to Single Student Directly (1-Click Instant Action) ── */
  function sendSingleStudentDirect(studentId, courseId) {
    var s = waState.allStudents.find(function(item) { return item.id === studentId; });
    if (!s) return;

    var courseObj = waState.coursesMap[courseId];
    if (!courseObj) return;

    var targetMode = document.getElementById('waRecipientTarget').value;
    var phone = getStudentTargetPhone(s, targetMode);

    if (!phone) {
      alert('Aucun numéro de téléphone WhatsApp pour ' + s.full_name);
      return;
    }

    captureAndSaveTimetable(courseObj).then(function(res) {
      var msg = buildPersonalizedMessage(s);
      launchWhatsAppUrl(phone, msg);
      alert('✅ WhatsApp ouvert pour ' + s.full_name + ' !\nL\'emploi du temps de ' + (courseObj.name || '') + ' est sur votre Bureau (' + res.file_name + ') et copié dans le presse-papiers (Ctrl + V).');
    }).catch(function(err) {
      alert('Erreur capture : ' + err);
    });
  }

  function sendSingleStudentFromTable(studentId) {
    var s = waState.queue.find(function(item) { return item.id === studentId; });
    if (!s) return;
    sendSingleStudentDirect(s.id, s.course_id);
    waState.statuses[s.id] = 'sent';
    displayCurrentStudent();
  }

  function renderDispatchTable() {
    var tbody = document.getElementById('waStudentsTableBody');
    if (!tbody) return;

    document.getElementById('waTableCount').innerText = waState.queue.length;

    var targetMode = document.getElementById('waRecipientTarget') ? document.getElementById('waRecipientTarget').value : 'parent_pref';
    var html = '';

    waState.queue.forEach(function(s, idx) {
      var phone = getStudentTargetPhone(s, targetMode);
      var st = waState.statuses[s.id] || 'pending';
      var isCurrent = (idx === waState.currentQueueIndex);

      var statusChip = '';
      if (st === 'sent') {
        statusChip = '<span class="chip chip-green" style="font-size:10px; font-weight:800;">✅ Envoyé</span>';
      } else if (st === 'skipped') {
        statusChip = '<span class="chip chip-amber" style="font-size:10px; font-weight:800;">⏭️ Ignoré</span>';
      } else if (isCurrent) {
        statusChip = '<span class="chip chip-blue" style="font-size:10px; font-weight:800;">💬 En cours</span>';
      } else {
        statusChip = '<span class="chip chip-gray" style="font-size:10px; font-weight:700;">⏳ En attente</span>';
      }

      var rowBg = isCurrent ? '#eff6ff' : (idx % 2 === 0 ? '#ffffff' : '#f8fafc');

      html += '<tr style="background:' + rowBg + '; border-bottom:1px solid #e2e8f0;">' +
        '<td style="padding:6px 10px; text-align:center; font-weight:700; color:#64748b;">' + (idx + 1) + '</td>' +
        '<td style="padding:6px 10px; font-weight:800; color:#0B3D6E;">' + s.full_name + ' <span class="chip chip-blue" style="font-size:9px; padding:1px 5px;">' + s.course_name + '</span></td>' +
        '<td style="padding:6px 10px; font-size:11.5px; color:#334155;">' + (phone ? formatPhoneDisplay(phone) : '<span style="color:#ef4444;">Aucun</span>') + '</td>' +
        '<td style="padding:6px 10px; text-align:center;">' + statusChip + '</td>' +
        '<td style="padding:6px 10px; text-align:right;">' +
          '<button type="button" onclick="sendSingleStudentFromTable(' + s.id + ')" class="btn btn-xs btn-outline" style="border-color:#16a34a; color:#15803d; font-weight:800; background:#f0fdf4; padding:3px 8px; border-radius:6px;" title="Envoyer à cet élève uniquement">' +
            '💬 Envoyer' +
          '</button>' +
        '</td>' +
      '</tr>';
    });

    tbody.innerHTML = html;
  }

  function copyImageAgainToClipboard() {
    var curStu = (waState.queue && waState.queue[waState.currentQueueIndex]) ? waState.queue[waState.currentQueueIndex] : null;
    var cid = curStu ? curStu.course_id : (waState.allStudents[0] ? waState.allStudents[0].course_id : null);
    var blob = cid ? waState.cachedBlobs[cid] : null;

    if (blob && navigator.clipboard && navigator.clipboard.write) {
      navigator.clipboard.write([new ClipboardItem({'image/png': blob})])
        .then(function() { alert('✅ Image re-copiée dans le presse-papiers ! Vous pouvez faire Ctrl + V dans WhatsApp.'); })
        .catch(function(e) { alert('Presse-papiers indisponible. Vous pouvez glisser l\'image depuis le Bureau.'); });
    } else {
      alert('L\'image est disponible sur votre Bureau.');
    }
  }

  function getStudentTargetPhone(s, targetMode) {
    if (targetMode === 'parent_only') return s.clean_parent_phone || '';
    if (targetMode === 'student_only') return s.clean_student_phone || '';
    return s.clean_parent_phone || s.clean_student_phone || '';
  }

  function formatPhoneDisplay(num) {
    if (!num) return '-';
    if (num.startsWith('212') && num.length === 12) {
      return '0' + num.slice(3, 4) + ' ' + num.slice(4, 6) + ' ' + num.slice(6, 8) + ' ' + num.slice(8, 10) + ' ' + num.slice(10, 12);
    }
    return num;
  }

  function buildPersonalizedMessage(student) {
    var template = document.getElementById('waMessageText').value || '';
    var cName = student.course_name || 'Classe';

    return template
      .replace(/{nom_eleve}/g, student.full_name)
      .replace(/{classe}/g, cName);
  }

  function launchWhatsAppUrl(phone, message) {
    var appMode = 'desktop';
    var radios = document.getElementsByName('waAppMode');
    for (var i = 0; i < radios.length; i++) {
      if (radios[i].checked) { appMode = radios[i].value; break; }
    }

    var cleanNum = (phone || '').replace(/[^0-9]/g, '');
    var encodedMsg = encodeURIComponent(message);

    if (appMode === 'desktop') {
      window.location.href = 'whatsapp://send?phone=' + cleanNum + '&text=' + encodedMsg;
    } else {
      window.open('https://web.whatsapp.com/send?phone=' + cleanNum + '&text=' + encodedMsg, '_blank');
    }
  }
