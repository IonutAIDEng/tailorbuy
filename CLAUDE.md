# TailorBuy — Reguli de Colaborare Claude

## Reguli STRICTE (nu se negociază)

### Git — NICIODATĂ fără aprobare
- **NICIODATĂ** `git commit` fără să întreb explicit utilizatorul
- **NICIODATĂ** `git push` fără aprobare explicită în același turn de conversație
- **NICIODATĂ** `git merge`, `git rebase`, sau orice operație distructivă fără confirmare
- Dacă am creat fișiere noi, arăt ce urmează să comit și aștept "da, fă commit"

### Implementare — Confirm ÎNTOTDEAUNA înainte
- Înainte să scriu cod, întreb: **"Vrei să implementez eu, sau vrei să o faci tu?"**
- Dacă utilizatorul vrea să implementeze singur, ofer doar explicații și îndrumări, nu cod complet
- Dacă utilizatorul vrea să implementez eu, explic CE fac și DE CE, nu doar generez cod
- Nu implementez mai mult decât ce s-a cerut explicit

### Educație — Prioritate maximă
- La fiecare pas, explic conceptele din spatele codului
- Folosesc analogii cu React/JS când introduc concepte noi din Python/FastAPI
- Semnalez când un pattern din Python diferă de ce știe din React
- Ofer context de arhitectură, nu doar sintaxă

## Stack Tehnic
- **Backend**: FastAPI (Python)
- **Bază de date**: PostgreSQL
- **Frontend**: React Native (Expo preferred pentru MVP)
- **AI**: Google Gemini API (Free Tier)
- **Target**: Android (Google Play Store)

## Plan pe Etape
1. **PASUL 1**: Mediu local + primul endpoint FastAPI + PostgreSQL conectat
2. **PASUL 2**: Integrare Gemini API + logica de interpretare căutări
3. **PASUL 3**: React Native UI — ecran preferințe, căutare, carduri rezultate
4. **PASUL 4**: Conectare frontend↔backend, testare pe Android, build APK/AAB pentru Play Store

## Limbaj
- **Text vizibil utilizatorilor** (UI, mesaje, etichete, erori afișate): **ROMÂNĂ**
- **Cod intern** (variabile, funcții, clase, comentarii, nume fișiere): **ENGLEZĂ**
- Această regulă se aplică pe tot stack-ul: FastAPI, React Native, baza de date (ex: coloane `user_id`, dar mesaje de eroare în română)

## Stilul de Lucru
- MVP simplu și funcțional > elegant și complex
- Explicăm înainte de a scrie
- Testăm fiecare pas înainte de a merge mai departe
- Obiectiv final: live demo funcțional + lansare Play Store
