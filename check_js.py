import re

with open('templates/schedule.html', encoding='utf-8') as f:
    html = f.read()

# All ids in html
all_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html))

# All getElementById in script
accessed_ids = set(re.findall(r'getElementById\(["\']([^"\']+)["\']\)', html))

print('Total IDs defined in HTML:', len(all_ids))
print('Total IDs accessed via getElementById:', len(accessed_ids))

missing = accessed_ids - all_ids
print('\nMissing IDs (accessed by JS but NOT in HTML):')
for m in sorted(list(missing)):
    print(' -', m)
