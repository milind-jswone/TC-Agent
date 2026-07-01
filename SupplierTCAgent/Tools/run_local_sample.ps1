param(
    [string]$PdfPath = "..\Samples\Supplier TC format.pdf"
)

$ErrorActionPreference = "Stop"
$toolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $toolRoot
try {
    python .\generate_tc_output.py $PdfPath
}
finally {
    Pop-Location
}
