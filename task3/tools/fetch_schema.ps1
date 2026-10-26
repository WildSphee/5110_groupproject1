param([Parameter(Mandatory=$true)][string]$Uri)
$ErrorActionPreference = 'Stop'
# Windows' normal certificate validation uses the local trusted root store.
(Invoke-WebRequest -Uri $Uri -UseBasicParsing).Content
