# NetLab Scheduler (Woche 7)

Infrastructure as Code mit AWS SAM und CI/CD mit GitHub Actions.

## Struktur
- `template.yaml`          Infrastruktur als Code (mit TODOs)
- `samconfig.toml`         Deploy-Einstellungen (fertig)
- `src/app.py`             Scheduler-Logik (fertig, aus Woche 2 bis 6)
- `frontend/`              index.html (Woche 6) + config.example.js
- `.github/workflows/`     backend.yml und frontend.yml (mit TODOs)
- `publish-frontend.ps1`   lokaler Frontend-Deploy fuer Lab 7.0
- `solution/`              vollständige Lösungen (erst nach Versuch ansehen)

## Schnellstart
1. `sam build; sam deploy`
2. Passwörter setzen (siehe Lab Aufgabe 3)
3. `.\publish-frontend.ps1`
4. FrontendUrl aus den Outputs öffnen und einloggen
