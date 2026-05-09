# LLM Job Matcher API

Aplikacja FastAPI do porownywania CV z oferta pracy przy uzyciu OpenAI.

Projekt pozwala:

- wkleic CV jako JSON,
- wgrac CV jako PDF, DOCX, TXT albo JSON,
- wkleic oferte pracy jako JSON,
- zamienic tekst CV na uporzadkowany JSON,
- wyslac CV i oferte do LLM,
- dostac wynik dopasowania z punktacja, mocnymi stronami, lukami i rekomendacja.

## Jak to dziala

Glowne flow dla CV jako dokument:

```text
CV PDF/DOCX/TXT
-> ekstrakcja tekstu
-> OpenAI zamienia CV na JSON
-> OpenAI porownuje CV JSON z oferta pracy JSON
-> API zwraca wynik dopasowania
```

Glowne flow dla CV jako JSON:

```text
CV JSON + oferta JSON
-> OpenAI porownuje oba obiekty
-> API zwraca wynik dopasowania
```

## Struktura projektu

```text
app/
  config.py                    # konfiguracja z .env
  main.py                      # aplikacja FastAPI i endpointy
  schemas.py                   # modele request/response
  services/
    document_parser.py         # ekstrakcja tekstu z PDF/DOCX/TXT
    matcher.py                 # komunikacja z OpenAI
  static/
    index.html                 # prosty frontend
```

## Wymagania

- Python 3.10+
- konto OpenAI z aktywnym API key
- zaleznosci z `requirements.txt`

## Konfiguracja

1. Utworz wirtualne srodowisko:

```bash
python3 -m venv .venv
```

2. Aktywuj srodowisko:

```bash
source .venv/bin/activate
```

3. Zainstaluj zaleznosci:

```bash
python -m pip install -r requirements.txt
```

4. Skopiuj plik przykladowy env:

```bash
cp .env.example .env
```

5. Uzupelnij `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

Plik `.env` jest ignorowany przez git, zeby nie wrzucic klucza API do repozytorium.

## Uruchomienie

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

Aplikacja bedzie dostepna pod:

```text
http://127.0.0.1:8000/
```

Dokumentacja FastAPI:

```text
http://127.0.0.1:8000/docs
```

## Frontend

Frontend jest serwowany z FastAPI pod `/`.

Mozesz:

- wkleic CV jako JSON,
- wgrac CV jako `.pdf`, `.docx`, `.txt` albo `.json`,
- wkleic oferte pracy jako JSON,
- kliknac `Dopasuj CV`,
- zobaczyc wynik dopasowania oraz parsed CV JSON, jesli CV bylo dokumentem.

Oferta pracy nadal jest JSON-em. Przykladowy format:

```json
{
  "title": "Junior Python Developer",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "nice_to_have": ["Docker", "AWS"],
  "description": "Build and maintain APIs for internal business tools."
}
```

## Endpointy

### `GET /health`

Sprawdza, czy API dziala.

Przykladowa odpowiedz:

```json
{
  "status": "ok"
}
```

### `POST /match`

Porownuje CV JSON z oferta pracy JSON.

Request:

```json
{
  "cv": {
    "name": "Anna Kowalska",
    "skills": ["Python", "FastAPI", "SQL"]
  },
  "job_offer": {
    "title": "Junior Python Developer",
    "required_skills": ["Python", "FastAPI", "PostgreSQL"]
  }
}
```

Response:

```json
{
  "match_score": 80,
  "summary": "Candidate is a possible match for the role.",
  "strengths": ["Python", "FastAPI"],
  "gaps": ["No PostgreSQL experience"],
  "matched_skills": ["Python", "FastAPI"],
  "missing_skills": ["PostgreSQL"],
  "recommendation": "possible_match"
}
```

### `POST /match/upload`

Przyjmuje CV jako plik i oferte jako JSON string w formularzu.

Form fields:

- `cv_file`: plik `.pdf`, `.docx`, `.txt` albo `.json`
- `job_offer`: JSON string z oferta pracy

Response:

```json
{
  "parsed_cv": {
    "name": "Anna Kowalska",
    "skills": ["Python", "FastAPI", "SQL"]
  },
  "match": {
    "match_score": 80,
    "summary": "Candidate is a possible match for the role.",
    "strengths": ["Python", "FastAPI"],
    "gaps": ["No PostgreSQL experience"],
    "matched_skills": ["Python", "FastAPI"],
    "missing_skills": ["PostgreSQL"],
    "recommendation": "possible_match"
  }
}
```

## Obslugiwane typy CV

- `.pdf`
- `.docx`
- `.txt`
- `.json`

Limit uploadu CV: 10 MB.

Uwaga: ekstrakcja PDF dziala najlepiej dla PDF-ow tekstowych. Skanowane CV bez warstwy tekstowej moga wymagac OCR, ktory nie jest jeszcze dodany.

## Przydatne komendy

Sprawdzenie skladni:

```bash
.venv/bin/python -m py_compile app/main.py app/schemas.py app/services/matcher.py app/services/document_parser.py
```

Uruchomienie serwera:

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

## Bezpieczenstwo

- Nie commituj `.env`.
- Nie commituj prawdziwych CV ani ofert pracy z danymi osobowymi.
- Lokalnie wrzucane dokumenty nie sa zapisywane na dysku przez aplikacje; backend czyta je z requestu i przetwarza w pamieci.

## Kolejne mozliwe kroki

- dodac OCR dla skanowanych PDF-ow,
- dodac upload oferty pracy jako PDF/DOCX,
- zapis historii matchy w bazie danych,
- dodac testy jednostkowe dla parsera dokumentow i endpointow,
- rozdzielic frontend na osobna aplikacje, jesli projekt urosnie.
