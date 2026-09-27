<#
.SYNOPSIS
  Fyller brukere fra en CSV inn i Aidn "Opplaeringsbrukere"-malen via Excel COM.
  Excel selv aapner og lagrer filen, slik at all formatering, velkomst-siden,
  kolonnebredder, farger osv. i malen bevares 1:1.

  Resultatet speiler Opplaeringsbrukere_ferdig.xlsx:
    - "START HER Velkommen"-arket beholdes uendret.
    - Ett dataark per unik avdeling (CSV "Kommune/organisasjon/avdeling"),
      arket navngis etter avdelingen.
    - Header rad 1: Navn | Fodselsnummer | Rolle | Avdeling/tjeneste | Hvem bruker
    - Data fra rad 2: Navn->A, Fodselsnummer->B (TEKST, ledende nuller), Rolle->C,
      avdeling->D, Hvem bruker->E.
    - Fodselsnummer lagres alltid som tekst (@), aldri tall/dato.
    - Forste rad laases, filter aktiveres paa datakolonnene.

  NB: Denne .ps1 er skrevet 100 % i ASCII. Norske tegn i output bygges fra
  char-koder slik at filen fungerer uansett hvordan PowerShell tolker fil-encoding.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string]$Csv,
  [string]$Template,
  [string]$Output,
  [string]$Delimiter
)

$ErrorActionPreference = 'Stop'

# Standardmal: den innebygde malen i skillen (assets/), slik at man normalt
# bare trenger aa oppgi -Csv. Overstyr med -Template for en annen mal.
if (-not $Template) {
  $Template = Join-Path $PSScriptRoot '..\assets\Opplaeringsbrukere-mal.xlsx'
}
$OutputEncoding = [Text.UTF8Encoding]::new()
try { [Console]::OutputEncoding = [Text.UTF8Encoding]::new() } catch {}

# Norske tegn som char-koder (ASCII-trygt)
$OE = [char]0x00F8  # o med skraastrek
$AA = [char]0x00E5  # a med ring
$AE = [char]0x00E6  # ae

# ---------- helpers ----------
function Resolve-Full([string]$p) {
  $p = $p -replace '/', '\'
  if (-not [System.IO.Path]::IsPathRooted($p)) { $p = Join-Path (Get-Location).Path $p }
  return [System.IO.Path]::GetFullPath($p)
}
function Norm([string]$s) {
  if ($null -eq $s) { return '' }
  $s = $s.ToLowerInvariant()
  $s = $s.Replace([string]$AE, 'ae').Replace([string]$OE, 'o').Replace([string]$AA, 'a')
  $s = $s.Normalize([Text.NormalizationForm]::FormD)
  $sb = [Text.StringBuilder]::new()
  foreach ($ch in $s.ToCharArray()) {
    if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($ch) -ne [Globalization.UnicodeCategory]::NonSpacingMark) { [void]$sb.Append($ch) }
  }
  return ($sb.ToString() -replace '[^a-z0-9]', '')
}

# Kanoniske felt (ASCII-noekler) -> synonymer (normalisert).
$FieldKeys = @('Navn', 'Fnr', 'Rolle', 'Avd', 'Hvem')
$FieldLabel = @{
  'Navn' = 'Navn'
  'Fnr'  = "F${OE}dselsnummer"
  'Rolle' = 'Rolle'
  'Avd'  = 'Avdeling/tjeneste'
  'Hvem' = 'Hvem bruker'
}
$FieldSynonyms = @{
  'Navn'  = @('navn', 'name', 'fulltnavn', 'fornavnetternavn', 'personnavn', 'brukernavn')
  'Fnr'   = @('fodselsnummer', 'fnr', 'personnummer', 'fodselsnr', 'ssn', 'birthnumber', 'nationalid', 'idnummer', 'innloggingsnummer', 'fodselsdato')
  'Rolle' = @('rolle', 'role', 'stilling', 'tittel', 'profil', 'jobrole')
  'Avd'   = @('avdeling', 'tjeneste', 'department', 'enhet', 'kommuneorganisasjonavdeling', 'kommune', 'organisasjon', 'omrade', 'seksjon', 'unit', 'avdelingtjeneste')
  'Hvem'  = @('hvembruker', 'bruker', 'tildelt', 'assignedto', 'tildeltbruker', 'ansvarlig')
}

function Match-Columns($headers) {
  $map = @{}
  $normPairs = @()
  foreach ($h in $headers) { $normPairs += [pscustomobject]@{ Raw = $h; Norm = (Norm $h) } }
  foreach ($field in $FieldKeys) {
    $best = $null; $bestLen = -1; $exact = $false
    foreach ($syn in $FieldSynonyms[$field]) {
      foreach ($p in $normPairs) {
        if ($p.Norm -eq $syn) { if (-not $exact) { $best = $p.Raw; $exact = $true } }
      }
    }
    if (-not $exact) {
      foreach ($syn in $FieldSynonyms[$field]) {
        foreach ($p in $normPairs) {
          if ($p.Norm.Contains($syn) -and $syn.Length -gt $bestLen) { $best = $p.Raw; $bestLen = $syn.Length }
        }
      }
    }
    $map[$field] = $best
  }
  return $map
}

function Sanitize-SheetName([string]$name, [System.Collections.Generic.HashSet[string]]$used) {
  if ([string]::IsNullOrWhiteSpace($name)) { $name = 'Uten avdeling' }
  $clean = $name -replace '[\\/\?\*\[\]:]', ' '
  $clean = ($clean -replace '\s+', ' ').Trim().Trim("'")
  if ($clean.Length -gt 31) { $clean = $clean.Substring(0, 31).Trim() }
  if ([string]::IsNullOrWhiteSpace($clean)) { $clean = 'Ark' }
  $base = $clean; $i = 2
  while ($used.Contains($clean.ToLowerInvariant())) {
    $suffix = " ($i)"
    $max = 31 - $suffix.Length
    $clean = ($base.Substring(0, [Math]::Min($base.Length, $max))).Trim() + $suffix
    $i++
  }
  [void]$used.Add($clean.ToLowerInvariant())
  return $clean
}

# ---------- resolve paths ----------
$Template = Resolve-Full $Template
$Csv      = Resolve-Full $Csv
# Standard output: samme mappe som CSV-en, med et beskrivende navn.
if (-not $Output) { $Output = Join-Path (Split-Path -Parent $Csv) 'Opplaeringsbrukere_utfylt.xlsx' }
$Output   = Resolve-Full $Output
if (-not (Test-Path -LiteralPath $Template)) { throw "Fant ikke malen (bruk -Template hvis du har en egen): $Template" }
if (-not (Test-Path -LiteralPath $Csv))      { throw "Fant ikke CSV: $Csv" }
if ((Norm $Template) -eq (Norm $Output)) { throw "Output kan ikke vaere samme fil som malen." }

# ---------- read CSV ----------
if (-not $Delimiter) {
  $firstLine = (Get-Content -LiteralPath $Csv -TotalCount 1 -Encoding UTF8)
  $semi = ([regex]::Matches($firstLine, ';')).Count
  $comm = ([regex]::Matches($firstLine, ',')).Count
  $tab  = ([regex]::Matches($firstLine, "`t")).Count
  $Delimiter = if ($tab -gt $comm -and $tab -gt $semi) { "`t" } elseif ($semi -gt $comm) { ';' } else { ',' }
}
$rows = @(Import-Csv -LiteralPath $Csv -Delimiter $Delimiter -Encoding UTF8)
if ($rows.Count -eq 0) { throw "CSV inneholder ingen datarader." }
$headers = $rows[0].PSObject.Properties.Name
$map = Match-Columns $headers

Write-Host "CSV-kolonner: $($headers -join ', ')"
Write-Host "Kolonnematch:"
foreach ($f in $FieldKeys) {
  $v = if ($map[$f]) { $map[$f] } else { '(mangler -> tom)' }
  Write-Host ("  {0,-18} <- {1}" -f $FieldLabel[$f], $v)
}
if (-not $map['Avd']) { Write-Host "  ADVARSEL: fant ingen avdelingskolonne -> alle brukere havner paa ett ark 'Brukere'." }

# ---------- group rows by department (bevar rekkefolge) ----------
$deptCol = $map['Avd']
$order = [System.Collections.Generic.List[string]]::new()
$groups = @{}
foreach ($r in $rows) {
  $dept = if ($deptCol) { [string]$r.$deptCol } else { 'Brukere' }
  if ([string]::IsNullOrWhiteSpace($dept)) { $dept = 'Uten avdeling' }
  if (-not $groups.ContainsKey($dept)) { $groups[$dept] = [System.Collections.Generic.List[object]]::new(); $order.Add($dept) }
  $groups[$dept].Add($r)
}

# ---------- Excel ----------
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$excel.ScreenUpdating = $false
$wb = $null
try {
  $wb = $excel.Workbooks.Open($Template)

  $origSheets = @($wb.Worksheets | ForEach-Object { $_ })
  $welcome = $origSheets | Where-Object { $_.Name -match '(?i)velkommen|start' } | Select-Object -First 1
  $proto = $origSheets | Where-Object { $_ -ne $welcome } | Select-Object -First 1
  if (-not $proto) { throw "Fant ingen prototyp-dataark i malen." }

  $usedNames = [System.Collections.Generic.HashSet[string]]::new()
  if ($welcome) { [void]$usedNames.Add($welcome.Name.ToLowerInvariant()) }

  $headerLabels = @('Navn', "F${OE}dselsnummer", 'Rolle', 'Avdeling/tjeneste', 'Hvem bruker')
  $newSheets = @()

  foreach ($dept in $order) {
    $proto.Copy([System.Reflection.Missing]::Value, $wb.Worksheets.Item($wb.Worksheets.Count))
    $ws = $wb.Worksheets.Item($wb.Worksheets.Count)
    $sheetName = Sanitize-SheetName $dept $usedNames
    $ws.Name = $sheetName

    # Nullstill innhold (behold cellenes formatering fra malen)
    $ws.Cells.ClearContents() | Out-Null
    if ($ws.AutoFilterMode) { $ws.AutoFilterMode = $false }

    # Kolonner A:E synlige; tekstformat paa B (fodselsnummer). '@' er locale-uavhengig.
    for ($c = 1; $c -le 5; $c++) { $ws.Columns.Item($c).Hidden = $false }
    $ws.Columns.Item(2).NumberFormat = '@'

    # Data: bygg hele arket (header + rader) som en 2D-matrise og skriv det i EN
    # bulk-operasjon. Celle-for-celle var enkelt, men paa store CSV-er (tusenvis
    # av rader = titusener av COM-kall) rakk Excel aa koble fra midt i skrivingen
    # (RPC_E_DISCONNECTED). Ett Range.Value2-kall per ark er baade raskere og
    # robust. Fodselsnummer skrives som ren tekst i en '@'-formatert kolonne slik
    # at ledende nuller beholdes og verdien aldri tolkes som tall eller dato.
    $drows = $groups[$dept]
    $n = $drows.Count
    $arr = New-Object 'object[,]' ($n + 1), 5
    for ($c = 0; $c -lt 5; $c++) { $arr[0, $c] = $headerLabels[$c] }
    for ($i = 0; $i -lt $n; $i++) {
      $r = $drows[$i]
      $ri = $i + 1
      $arr[$ri, 0] = if ($map['Navn'])  { [string]$r.($map['Navn']) }  else { '' }
      $arr[$ri, 1] = if ($map['Fnr'])   { ([string]$r.($map['Fnr'])).Trim() } else { '' }
      $arr[$ri, 2] = if ($map['Rolle']) { [string]$r.($map['Rolle']) } else { '' }
      $arr[$ri, 3] = $dept
      $arr[$ri, 4] = if ($map['Hvem'])  { [string]$r.($map['Hvem']) }  else { '' }
    }
    $ws.Range($ws.Cells.Item(1, 1), $ws.Cells.Item($n + 1, 5)).Value2 = $arr

    # Filter paa datakolonnene + laas forste rad
    $lastRow = [Math]::Max($n + 1, 1)
    $ws.Range($ws.Cells.Item(1, 1), $ws.Cells.Item($lastRow, 5)).AutoFilter() | Out-Null
    $ws.Activate()
    $excel.ActiveWindow.SplitColumn = 0
    $excel.ActiveWindow.SplitRow = 1
    $excel.ActiveWindow.FreezePanes = $true

    $newSheets += $ws.Name
  }

  # Slett opprinnelige prototyp/placeholder-ark (alt utenom velkomst + nye ark)
  foreach ($s in $origSheets) {
    if ($welcome -and $s.Name -eq $welcome.Name) { continue }
    $wb.Worksheets.Item($s.Name).Delete()
  }

  if ($welcome) {
    $welcome.Move($wb.Worksheets.Item(1)) | Out-Null
    $wb.Worksheets.Item(1).Activate()
  }

  $outDir = Split-Path -Parent $Output
  if ($outDir -and -not (Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
  if (Test-Path -LiteralPath $Output) { Remove-Item -LiteralPath $Output -Force }
  $wb.SaveAs($Output, 51)
  Write-Host ""
  Write-Host "Ark opprettet ($($newSheets.Count)): $($newSheets -join ', ')"
  Write-Host "Lagret: $Output"
}
catch {
  Write-Host "FEIL paa linje $($_.InvocationInfo.ScriptLineNumber): $($_.Exception.Message)"
  throw
}
finally {
  if ($wb) { $wb.Close($false) | Out-Null }
  $excel.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
  [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
