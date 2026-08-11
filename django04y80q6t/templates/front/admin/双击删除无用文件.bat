@echo off
echo ========================================
echo Delete Empty and Template-only Files
echo ========================================
echo.

set /a count=0

echo Searching for empty files and template-only files...
echo.

powershell -Command ^
  "$count = 0; " ^
  "Get-ChildItem -Path '%~dp0src' -Recurse -File | ForEach-Object { " ^
    "if ($_.Length -eq 0) { " ^
      "Write-Host 'Deleting empty file:' $_.FullName; " ^
      "Remove-Item $_.FullName -Force; " ^
      "$count++; " ^
    "} " ^
  "}; " ^
  "Get-ChildItem -Path '%~dp0src\components' -Recurse -Filter '*.vue' -File | ForEach-Object { " ^
    "$content = Get-Content $_.FullName -Raw -Encoding UTF8; " ^
    "if ($content.Trim() -eq '<template></template>') { " ^
      "Write-Host 'Deleting template-only file:' $_.FullName; " ^
      "Remove-Item $_.FullName -Force; " ^
      "$count++; " ^
    "} " ^
  "}; " ^
  "Write-Host ''; " ^
  "Write-Host '========================================'; " ^
  "Write-Host \"Done! Deleted $count files\"; " ^
  "Write-Host '========================================'"

echo.
pause
