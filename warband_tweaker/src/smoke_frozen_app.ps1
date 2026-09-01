param(
    [string]$Executable = (Join-Path $PSScriptRoot "dist\PVN's Warband Tweaker v1.0.0.exe")
)

$expectedTitle = "PVN's Warband Tweaker v1.0.0"
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
    throw "Frozen executable not found: $Executable"
}
$versionInfo = (Get-Item -LiteralPath $Executable).VersionInfo
if ($versionInfo.ProductName -ne "PVN's Warband Tweaker" -or $versionInfo.ProductVersion -ne "1.0.0") {
    throw "The executable's embedded product name/version metadata is incorrect."
}

$process = Start-Process -FilePath $Executable -PassThru -WindowStyle Hidden
try {
    if (-not $process.WaitForInputIdle(20000)) {
        throw "The frozen app did not become input-idle within 20 seconds."
    }
    Start-Sleep -Milliseconds 750
    $process.Refresh()
    if ($process.HasExited) {
        throw "The frozen app exited during startup with code $($process.ExitCode)."
    }
    if (-not $process.Responding) {
        throw "The frozen app created a process but its UI is not responding."
    }
    if ($process.MainWindowTitle -and $process.MainWindowTitle -ne $expectedTitle) {
        throw "Unexpected window title '$($process.MainWindowTitle)'; expected '$expectedTitle'."
    }
    Write-Output "Frozen GUI smoke test passed: $expectedTitle (PID $($process.Id))."
}
finally {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        $process.WaitForExit(5000) | Out-Null
    }
}
