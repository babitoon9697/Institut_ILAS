# -*- coding: utf-8 -*-
with open('templates/teachers/student_lists.html', 'r', encoding='utf-8') as f:
    text = f.read()
    
target = '''                <td style="text-align:center;">
                  <span class="chip {{ 'chip-green' if en.total_sessions_month == 12 else 'chip-gray' }}" style="font-size:10.5px; font-weight:800;">
                    {{ '3 √‘Â—' if en.total_sessions_month == 12 else '1 ‘Â—' }}
                  </span>
                </td>'''

replacement = '''                <td style="text-align:center;">
                  {% set mc = ((en.end_date.year - en.enroll_date.year) * 12 + (en.end_date.month - en.enroll_date.month)) if en.end_date and en.enroll_date else 1 %}
                  {% set mc = mc if mc > 0 else 1 %}
                  <span class="chip {{ 'chip-green' if mc > 1 else 'chip-gray' }}" style="font-size:10.5px; font-weight:800;">
                    {{ mc }} {{ '√‘Â—' if mc > 2 else ('‘Â—«‰' if mc == 2 else '‘Â—') }}
                  </span>
                </td>'''

if target in text:
    print('Target found!')
    text = text.replace(target, replacement)
    with open('templates/teachers/student_lists.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Replaced successfully.')
else:
    print('Target NOT found. Printing nearby text:')
    start = text.find('chip-green')
    print(text[start-100:start+200])
