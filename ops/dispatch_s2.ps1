# Dispatch the S2 workflow on GitHub, so the day's gate does not depend on GitHub's cron.
#
# Why: GitHub's scheduled runs for this repository are delayed by hours or dropped. On 2026-09-28 the
# first scheduled run of the day started at 21:11 UTC, after the 18:30-19:50 UTC window, and AIR and JBL
# were lost. A workflow_dispatch starts within seconds, and the run then waits for the window
# (pipeline/due.py wait, up to 4 hours). So the laptop only has to fire this ONE command some hours
# before the window, at an hour Jacob is usually awake. It runs nothing else.
#
# Scheduled by the Windows task "earnings-s2-dispatch" (weekdays 22:45 and 23:45 Singapore time, wakes
# the computer). 22:45 SGT = 10:45 ET until Nov 1; after Nov 1 the 23:45 fire is 10:45 ET and the 22:45
# fire (09:45 ET) is a harmless no-op. On a day with nothing due, GitHub's precheck ends the run in
# seconds. Log: %LOCALAPPDATA%\earnings-experiment\dispatch.log

$log = Join-Path $env:LOCALAPPDATA "earnings-experiment\dispatch.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$out = & $gh workflow run s2-window.yml -R jacobbuildmodel/earnings-experiment --ref main -f purpose=gate 2>&1
if ($LASTEXITCODE -ne 0) {
    # a main without the `purpose` input: dispatch plainly (it then also runs housekeeping)
    $out = "$out | retry without input: " + (& $gh workflow run s2-window.yml -R jacobbuildmodel/earnings-experiment --ref main 2>&1)
}
Add-Content -Path $log -Value "$stamp exit=$LASTEXITCODE $out"
