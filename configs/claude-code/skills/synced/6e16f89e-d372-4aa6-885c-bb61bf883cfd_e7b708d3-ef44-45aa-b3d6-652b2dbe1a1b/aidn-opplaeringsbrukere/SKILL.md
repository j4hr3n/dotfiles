---
name: aidn-opplaeringsbrukere
description: >-
  Fyller brukere fra en CSV inn i Aidn sin "Opplæringsbrukere"-Excelmal uten å
  ødelegge malen. Bruk denne skillen ALLTID når noen har en Opplæringsbruker-mal
  (.xlsx, gjerne "Opplæringsbrukere - mal.xlsx" med et "START HER Velkommen"-ark
  og avdelingsark) SAMMEN MED en CSV/eksport av brukere/practitioners som skal
  importeres — også når de bare sier ting som "fyll inn brukerne i malen", "legg
  disse brukerne inn i opplæringsarket", "importer practitioners-CSV-en", "lag
  opplæringsbrukere for kommunen", eller limer inn en practitioners-CSV og en
  xlsx-mal. Skillen matcher CSV-kolonner automatisk (Navn, Fødselsnummer, Rolle,
  Avdeling/tjeneste, Hvem bruker), lager ett ark per avdeling, og behandler
  fødselsnummer som tekst med ledende nuller bevart. Ikke bruk den for generell
  Excel-redigering uten Aidn-malen, eller for andre maler enn Opplæringsbrukere.
---

# Aidn Opplæringsbrukere-import

Fyller en CSV med brukere inn i Aidn sin **Opplæringsbrukere-mal** og produserer
en ny `.xlsx` som er identisk med malen i utseende, men med ett dataark per
avdeling. Resultatet speiler `Opplaeringsbrukere_ferdig.xlsx`.

## Når dette gjelder

Brukeren har (minst) to filer:
1. **Malen** – en `.xlsx`, typisk `Opplæringsbrukere - mal.xlsx`, med et
   `START HER Velkommen`-ark og noen avdelingsark (`Avdeling 1`, `Avdeling 2`…).
2. **CSV-en** – en eksport av brukere/practitioners, f.eks.
   `practitioners-<orgnr>-<dato>.csv`, med kolonner som `Fødselsnummer`, `Rolle`,
   `Kommune/organisasjon/avdeling`, `Navn`.

Målet er en utfylt kopi som beholder alt fra malen (velkomstark, formatering,
farger, kolonnebredder, skjulte ark, formler, datavalidering).

## Forutsetninger

Denne skillen kjører **Microsoft Excel via COM-automasjon i PowerShell** på
Windows. Det er et bevisst valg: fordi Excel selv åpner og lagrer filen, blir
formateringen garantert identisk med malen (i motsetning til biblioteker som kan
miste innhold). Sjekk at Excel finnes før du starter:

```powershell
try { $x = New-Object -ComObject Excel.Application; "Excel OK $($x.Version)"; $x.Quit() }
catch { "Excel mangler – kan ikke kjøre denne skillen på denne maskinen." }
```

Hvis Excel ikke finnes, si fra til brukeren – ikke prøv en dårligere metode som
kan ødelegge malformateringen uten å varsle.

## Finn skript-stien (viktig – stedsuavhengig)

Skriptene ligger i `scripts/`-mappa **relativt til denne skillen**. Når skillen
lastes, får du oppgitt skillens base-katalog ("Base directory for this skill:
…"). Sett den som `$SkillDir` og bruk den i alle kall under. Da fungerer skillen
likt enten den er installert personlig (`~/.claude/skills/…`) eller distribuert
som plugin (plugin-cachen). **Ikke** hardkod noen personlig sti.

```powershell
# Bytt ut med base-katalogen du fikk oppgitt da skillen ble lastet:
$SkillDir = "<skillens base-katalog>"
```

## Slik gjør du det

### 1. Finn de to filene
Spør brukeren om stier hvis de er uklare. Malen er `.xlsx` med et
velkomst-/START-ark; CSV-en har en fødselsnummer-kolonne. Vær vennlig med
filnavn som inneholder mellomrom og norske tegn (`æøå`) – bruk anførselstegn.

### 2. Kjør importskriptet

**Malen er innebygd i skillen** (`assets/Opplaeringsbrukere-mal.xlsx`), så i normal
bruk trenger man bare å oppgi CSV-en:

```powershell
& "$SkillDir\scripts\Fill-Opplaeringsbrukere.ps1" -Csv "<sti-til-brukere.csv>"
```

Da lages `Opplaeringsbrukere_utfylt.xlsx` i samme mappe som CSV-en.

Valgfrie parametre:
- `-Template "<annen-mal.xlsx>"` – bruk en annen mal enn den innebygde.
- `-Output "<sti.xlsx>"` – styr hvor/hva resultatet heter.
- `-Delimiter` – auto-detekteres mellom `,`, `;` og tab; sett den kun ved behov.

Skriptet nekter å skrive over malen. Vil brukeren oppdatere den innebygde
standardmalen, bytt ut fila i `assets/`.

Skriptet skriver ut hvilke CSV-kolonner det matchet mot hvilke felt, og hvilke
ark det lagde – les dette og videreformidle det til brukeren.

### 3. Verifiser før levering
Kjør `scripts/Verify-Output.ps1` (eller inspiser manuelt) og bekreft overfor
brukeren at:
- Alle fødselsnumre er lagret som **tekst** (`@`), har riktig lengde, og at
  ingen ledende nuller er borte.
- Hvert dataark har header `Navn | Fødselsnummer | Rolle | Avdeling/tjeneste | Hvem bruker`.
- Første rad er låst (frosset) og autofilter er på datakolonnene.
- `START HER Velkommen` er uendret, og antall datarader per ark stemmer med CSV-en.

```powershell
& "$SkillDir\scripts\Verify-Output.ps1" -Output "<sti-til-ny-fil.xlsx>" -Csv "<sti-til-brukere.csv>"
```

### 4. Rapporter tomme navn per avdeling
Practitioner-eksporten mangler av og til navn på enkelte behandlere (feltet er
tomt i selve CSV-en). Etter utfylling: rapporter **hvor mange rader som mangler
navn av totalt antall**, og list **hvilken avdeling/ark** hver tomme rad ligger
på (med fødselsnummer og rolle), ikke bare totalt. Da kan teamet raskt finne og
fylle inn navnene manuelt frem til uttrekket er fikset på Aidn-siden.

## Hva skriptet gjør (og hvorfor)

- **Beholder malen som utgangspunkt.** Åpner malen i Excel, rører ikke
  `START HER Velkommen`. Bruker det første avdelingsarket som *prototyp* og
  kopierer det (med all formatering, kolonnebredder, farger, fonter, borders og
  tekstformat) én gang per unik avdeling. Til slutt slettes de ubrukte
  placeholder-arkene (`Avdeling 1…5`).
- **Ett ark per avdeling.** Unike verdier i avdelingskolonnen blir hvert sitt
  ark, navngitt etter avdelingen. Arknavn saneres (ulovlige tegn `\ / ? * [ ] :`
  fjernes, maks 31 tegn, gjort unike) fordi Excel krever det. Det fulle
  avdelingsnavnet beholdes i kolonne D selv om fanenavnet forkortes.
- **Fyller de riktige kolonnene:** `Navn→A`, `Fødselsnummer→B`, `Rolle→C`,
  avdeling→`D`, `Hvem bruker→E`. Avdelingsnavnet gjentas i kolonne D (som i
  fasit-fila). Mangler et felt i CSV-en, står kolonnen tom.
- **Fødselsnummer som tekst.** Kolonne B settes til tekstformat (`@`) *før*
  verdiene skrives, og verdiene skrives som rene strenger. Da beholdes ledende
  nuller og nummeret blir aldri tolket som tall eller dato.
- **Filter + frys.** Autofilter legges på `A1:E<siste>`, og første rad fryses.

## Automatisk kolonnematch

CSV-kolonner matches mot feltene under (normalisert: små bokstaver, `æøå`→`ae/o/a`,
tegnsetting fjernet; eksakt treff foretrekkes, ellers delstreng-treff). Ekstra
CSV-kolonner ignoreres.

| Felt (målkolonne)   | Matcher bl.a. |
|---------------------|---------------|
| Navn                | navn, name, fullt navn |
| Fødselsnummer       | fødselsnummer, fnr, personnummer, ssn, innloggingsnummer, id-nummer |
| Rolle               | rolle, role, stilling, tittel, profil |
| Avdeling/tjeneste   | avdeling, tjeneste, department, enhet, kommune, organisasjon, "Kommune/organisasjon/avdeling", område, seksjon |
| Hvem bruker         | hvem bruker, bruker, tildelt, ansvarlig |

Trenger du å legge til et synonym eller endre kolonnerekkefølgen, rediger
`$FieldSynonyms` / `$headerLabels` i `scripts/Fill-Opplaeringsbrukere.ps1`.

## Kanttilfeller

- **Ingen avdelingskolonne funnet:** alle brukere havner på ett ark `Brukere`.
  Skriptet varsler dette – nevn det for brukeren.
- **Tom avdelingsverdi i en rad:** havner på ark `Uten avdeling`.
- **Tomt navn i en rad:** raden beholdes (fnr/rolle/avdeling fylles ut), men
  kolonne A står tom. Rapporter disse per avdeling, se punkt 4 over.
- **Duplikate personer** (samme person med flere roller) beholdes som separate
  rader – det er meningen i opplæringsoversikten.
- **Mange brukere:** skriptet skriver hvert ark i én bulk-operasjon (én matrise
  per ark), så det håndterer flere tusen rader raskt og uten at Excel kobler fra.
- **Andre maler enn Opplæringsbrukere:** denne skillen er spesiallaget for
  Opplæringsbruker-malen. For vilkårlige maler, si fra og vurder en generell
  tilnærming i stedet.
