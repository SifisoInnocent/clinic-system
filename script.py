with open('C:\\Users\\Admin\\Desktop\\Projects\\Clinic System\\templates\\appointments\\appointment_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# 1. Remove the 'Search and Filter' GET form
form_pattern = re.compile(r'<!-- Search and Filter -->.*?<!-- Appointments Table -->', re.DOTALL)
content = form_pattern.sub('<!-- Appointments Table -->', content)

# 2. Mask patient data
search_str_1 = '{{ appointment.student.get_full_name }}'
replace_str_1 = '{% if request.user.role == "psychologist" %}Masked Patient{% else %}{{ appointment.student.get_full_name }}{% endif %}'

search_str_2 = '{{ appointment.student.student_number|default:"N/A" }}'
replace_str_2 = '{% if request.user.role == "psychologist" %}***-***{% else %}{{ appointment.student.student_number|default:"N/A" }}{% endif %}'

# For calendar title:
search_str_3 = 'title: \'{% if is_student %}{{ a.staff.get_full_name|default:a.staff.username }}{% else %}{{ a.student.get_full_name|default:a.student.username }}{% endif %}\','
replace_str_3 = 'title: \'{% if is_student %}{{ a.staff.get_full_name|default:a.staff.username }}{% else %}{% if request.user.role == "psychologist" %}Masked Patient{% else %}{{ a.student.get_full_name|default:a.student.username }}{% endif %}{% endif %}\','


content = content.replace(search_str_1, replace_str_1)
content = content.replace(search_str_2, replace_str_2)
content = content.replace(search_str_3, replace_str_3)

with open('C:\\Users\\Admin\\Desktop\\Projects\\Clinic System\\templates\\appointments\\appointment_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Success')
