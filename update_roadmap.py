import re

with open("D:/GitHub/AutoTube-Lab/docs/ROADMAP_AI_AGENT_TASKS.md", "r", encoding="utf-8") as f:
    content = f.read()

tasks_to_mark = [
    f"T-{i:03d}" for i in range(269, 294)
] + [
    f"T-{i:03d}" for i in range(501, 518)
]

lines = content.split('\n')
for i, line in enumerate(lines):
    for task in tasks_to_mark:
        if line.startswith(f"| {task} |"):
            lines[i] = line.replace("🔲", "✅").replace("— |", "2026-07-17 |")
            
with open("D:/GitHub/AutoTube-Lab/docs/ROADMAP_AI_AGENT_TASKS.md", "w", encoding="utf-8") as f:
    f.write('\n'.join(lines))
