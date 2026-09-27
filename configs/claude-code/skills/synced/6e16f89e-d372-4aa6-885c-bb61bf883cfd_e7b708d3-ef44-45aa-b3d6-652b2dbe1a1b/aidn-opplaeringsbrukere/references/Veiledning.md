# Veiledning: Importere brukere til Opplæringsbruker-malen

En enkel oversikt over hvordan du fyller en CSV med brukere inn i Aidn sin
Opplæringsbruker-mal – uten å miste noe av formateringen i malen.

## Kort fortalt

Du gir fra deg én CSV-fil med brukere. Verktøyet fyller den inn i malen og lager
et ferdig Excel-ark der:

- hver avdeling får sin egen arkfane
- fødselsnummer beholdes som tekst med ledende nuller
- første rad er låst og filter er slått på
- velkomstarket og all formatering fra malen er bevart

Resultatet kan åpnes i Excel eller lastes rett opp i Google Sheets.

## Dette trenger du

- **CSV-filen** med brukere (f.eks. en practitioners-eksport). Den bør ha
  kolonner for navn, fødselsnummer, rolle og avdeling/tjeneste.
- **Malen trenger du ikke** å tenke på – den ligger innebygd i verktøyet.

Kolonnene i CSV-en trenger ikke hete nøyaktig det samme hver gang. Verktøyet
kjenner igjen vanlige varianter, for eksempel «Department», «Enhet», «Avdeling»
eller «Tjeneste» for avdeling, og «fnr» eller «personnummer» for fødselsnummer.
Ekstra kolonner i CSV-en blir ignorert.

## Slik bruker du den

### Måte 1: Be Claude om det (enklest)

1. Åpne Claude Code.
2. Skriv en melding som «Fyll inn denne CSV-en i opplæringsmalen» og oppgi hvor
   CSV-filen ligger.
3. Claude kjører jobben og lager en ferdig fil i samme mappe som CSV-en, kalt
   `Opplaeringsbrukere_utfylt.xlsx`.

Skillen som brukes heter **aidn-opplaeringsbrukere**, og den starter automatisk
når du nevner opplæringsbrukere/malen sammen med en CSV.

### Måte 2: Kjør kommandoen selv

Skriptet ligger i `scripts/`-mappa inne i selve skillen. Hvor skillen ligger
avhenger av hvordan den er installert:

- **Installert som plugin:** i plugin-cachen, typisk under
  `C:\Users\<bruker>\.claude\plugins\cache\...\skills\aidn-opplaeringsbrukere\scripts\`.
- **Installert personlig:** `C:\Users\<bruker>\.claude\skills\aidn-opplaeringsbrukere\scripts\`.

Åpne PowerShell, sett stien til skript-mappa, og kjør (bytt ut begge stiene):

    $Scripts = "C:\sti\til\aidn-opplaeringsbrukere\scripts"
    & "$Scripts\Fill-Opplaeringsbrukere.ps1" -Csv "C:\sti\til\brukere.csv"

Enklest er likevel Måte 1 – da finner Claude skript-stien selv.
Da lages `Opplaeringsbrukere_utfylt.xlsx` i samme mappe som CSV-en.

Valgfritt: Legg til `-Output "C:\sti\navn.xlsx"` for å styre hvor filen havner,
eller `-Template "C:\sti\annen-mal.xlsx"` hvis du unntaksvis skal bruke en annen mal.

## Hva resultatfilen inneholder

- **Velkomstarket** «START HER Velkommen» – uendret fra malen.
- **Ett ark per avdeling**, navngitt etter avdelingen (f.eks. «Hjemmebasert Omsorg»).
- På hvert ark, rad 1: Navn, Fødselsnummer, Rolle, Avdeling/tjeneste, Hvem bruker.
- Brukerne fra rad 2 og nedover.

## Laste opp i Google Sheets

1. Gå til Google Disk og velg **Ny → Filopplasting**, og velg
   `Opplaeringsbrukere_utfylt.xlsx`.
2. Høyreklikk filen og velg **Åpne med → Google Regneark**.

Fødselsnumrene beholder de ledende nullene automatisk, fordi de er lagret som
tekst i filen. Låst førsterad og filter følger også med.

## Regler verktøyet alltid følger

- Fødselsnummer behandles alltid som tekst – aldri som tall eller dato.
- Ledende nuller beholdes.
- Mangler en kolonne i CSV-en, står den tom i resultatet (den fjernes ikke).
- Ekstra kolonner i CSV-en ignoreres.
- Samme person med flere roller beholdes som separate rader – det er meningen.
- Malen selv overskrives aldri; du får alltid en ny fil.

## Vanlige spørsmål

**Må jeg laste opp malen hver gang?**
Nei. Malen er innebygd i verktøyet. Du trenger bare CSV-en.

**Hva om avdelingskolonnen mangler i CSV-en?**
Da havner alle brukere på ett ark som heter «Brukere», og du får en beskjed om det.

**Hva om et navn mangler i CSV-en?**
Raden kommer med, men med tomt navnefelt – akkurat som i kilden.

**Kan malen oppdateres?**
Ja. Hvis Aidn lager en ny versjon av malen, byttes den innebygde malfilen ut, så
bruker verktøyet automatisk den nye. Be Claude om hjelp til dette.

## For IT / teknisk

- Verktøyet kjører på Windows og bruker Microsoft Excel (COM-automasjon via
  PowerShell). Excel må være installert. Fordi Excel selv åpner og lagrer filen,
  blir formateringen identisk med malen.
- Skillen distribueres som Claude Code-plugin (`aidn-opplaeringsbrukere` i
  marketplace `aidn-plugins`) og installeres med `/plugin install`. Den kan også
  ligge personlig i `C:\Users\<bruker>\.claude\skills\aidn-opplaeringsbrukere\`.
  Malen ligger i undermappen `assets`, skriptene i `scripts`.
- `Fill-Opplaeringsbrukere.ps1` gjør selve importen; `Verify-Output.ps1`
  kontrollerer at resultatet oppfyller kravene (tekst-fødselsnummer, riktig
  header, låst rad, filter, bevart velkomstark, riktig antall rader).
