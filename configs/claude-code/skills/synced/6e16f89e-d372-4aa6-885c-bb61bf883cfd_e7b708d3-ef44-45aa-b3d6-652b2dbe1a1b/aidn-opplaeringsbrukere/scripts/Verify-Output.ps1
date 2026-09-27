<#
.SYNOPSIS
  Kontrollerer at en utfylt Opplaeringsbrukere-fil oppfyller kravene:
  fodselsnummer som tekst med riktig lengde og bevarte ledende nuller, korrekt
  header, laast forste rad, aktivt filter, bevart velkomstark, og at antall
  datarader stemmer med CSV-en. Skrevet 100 % i ASCII.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string]$Output,
  [string]$Csv,
  [int]$FnrLength = 11
)
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.UTF8Encoding]::new() } catch {}

function Resolve-Full([string]$p) {
  $p = $p -replace '/', '\'
  if (-not [System.IO.Path]::IsPathRooted($p)) { $p = Join-Path (Get-Location).Path $p }
  return [System.IO.Path]::GetFullPath($p)
}
$OE = [char]0x00F8
$Output = Resolve-Full $Output
$expectedHeader = @('Navn', "F${OE}dselsnummer", 'Rolle', 'Avdeling/tjeneste', 'Hvem bruker')

$csvTotal = $null
if ($Csv) {
  $Csv = Resolve-Full $Csv
  $firstLine = Get-Content -LiteralPath $Csv -TotalCount 1 -Encoding UTF8
  $delim = if (([regex]::Matches($firstLine, ';')).Count -gt ([regex]::Matches($firstLine, ',')).Count) { ';' } else { ',' }
  $csvTotal = @(Import-Csv -LiteralPath $Csv -Delimiter $delim -Encoding UTF8).Count
}

$x = New-Object -ComObject Excel.Application; $x.Visible = $false; $x.DisplayAlerts = $false
$wb = $null
$fail = 0
try {
  $wb = $x.Workbooks.Open($Output)
  $welcome = 0; $dataRows = 0; $sheets = 0
  foreach ($ws in $wb.Worksheets) {
    if ($ws.Name -match '(?i)velkommen|start') {
      $welcome++
      Write-Host "[OK ] Velkomstark bevart: '$($ws.Name)' ($($ws.UsedRange.Rows.Count) rader)"
      continue
    }
    $sheets++
    $ws.Activate()
    $last = $ws.Cells.Item($ws.Rows.Count, 1).End(-4162).Row
    $n = [Math]::Max($last - 1, 0)
    $dataRows += $n

    # header
    $hdr = @(); for ($c = 1; $c -le 5; $c++) { $hdr += [string]$ws.Cells.Item(1, $c).Text }
    if (($hdr -join '|') -ne ($expectedHeader -join '|')) {
      Write-Host "[FEIL] '$($ws.Name)' feil header: $($hdr -join ' | ')"; $fail++
    }
    # freeze
    if ($x.ActiveWindow.SplitRow -ne 1 -or -not $x.ActiveWindow.FreezePanes) {
      Write-Host "[FEIL] '$($ws.Name)' forste rad ikke laast (SplitRow=$($x.ActiveWindow.SplitRow))"; $fail++
    }
    # filter
    $hasFilter = $false; try { $null = $ws.AutoFilter.Range.Address(); $hasFilter = $true } catch {}
    if (-not $hasFilter) { Write-Host "[FEIL] '$($ws.Name)' mangler autofilter"; $fail++ }
    # fnr text + length
    $badFmt = 0; $badLen = 0; $badDept = 0
    for ($r = 2; $r -le $last; $r++) {
      $cell = $ws.Cells.Item($r, 2)
      if ($cell.NumberFormat -ne '@') { $badFmt++ }
      $v = [string]$cell.Text
      if ($v.Length -ne $FnrLength) { $badLen++ }
      if (([string]$ws.Cells.Item($r, 4).Text) -ne $ws.Name) { $badDept++ }
    }
    if ($badFmt -gt 0) { Write-Host "[FEIL] '$($ws.Name)' $badFmt fnr ikke tekstformat"; $fail++ }
    if ($badLen -gt 0) { Write-Host "[FEIL] '$($ws.Name)' $badLen fnr med feil lengde (forventet $FnrLength)"; $fail++ }
    if ($badDept -gt 0) { Write-Host "[FEIL] '$($ws.Name)' $badDept rader der kolonne D != arknavn"; $fail++ }
    if ($badFmt -eq 0 -and $badLen -eq 0) {
      Write-Host "[OK ] '$($ws.Name)': $n rader, header/frys/filter ok, alle fnr tekst m/ lengde $FnrLength"
    }
  }
  if ($welcome -eq 0) { Write-Host "[ADV] Fant ikke noe velkomstark - ble det bevart?" }
  if ($null -ne $csvTotal) {
    if ($dataRows -eq $csvTotal) { Write-Host "[OK ] Totalt datarader ($dataRows) = CSV-rader ($csvTotal)" }
    else { Write-Host "[FEIL] Datarader ($dataRows) != CSV-rader ($csvTotal)"; $fail++ }
  }
  Write-Host ""
  if ($fail -eq 0) { Write-Host "RESULTAT: ALT OK ($sheets dataark)" }
  else { Write-Host "RESULTAT: $fail problem(er) funnet" }
}
finally {
  if ($wb) { $wb.Close($false) | Out-Null }
  $x.Quit(); [System.Runtime.InteropServices.Marshal]::ReleaseComObject($x) | Out-Null
  [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
if ($fail -gt 0) { exit 1 }
