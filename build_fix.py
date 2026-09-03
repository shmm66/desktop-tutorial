from pathlib import Path
p=Path('TraderPlannerPro_v2.py')
s=p.read_text(encoding='utf-8')
bad="act=[x for x,a,b in ss if (m>=a and m<b) if a<b else (m>=a or m<b)]"
good="act=[x for x,a,b in ss if ((m>=a and m<b) if a<b else (m>=a or m<b))]"
if bad in s:
    p.write_text(s.replace(bad,good),encoding='utf-8')
print('build fix applied')
