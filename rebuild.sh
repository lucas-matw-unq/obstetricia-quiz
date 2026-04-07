#!/bin/bash
# Rebuild Obstetricia_Quiz.html from the current question bank.
# Run from the project root: bash rebuild.sh

SKILL=~/.claude/plugins/local/quiz-builder/skills/quiz-builder

python3 "$SKILL/scripts/build_html.py" \
  --bank quiz_questions_pool_normalized.json \
  --template "$SKILL/references/html-template.md" \
  --subject "Obstetricia" \
  --emoji "🤰" \
  --color "#0d7377" \
  --lang es \
  --output Obstetricia_Quiz.html

TOTAL=$(python3 -c "import json; d=json.load(open('quiz_questions_pool_normalized.json')); print(d['metadata']['total_questions'])")
echo "✓ Obstetricia_Quiz.html rebuilt ($TOTAL questions)"
