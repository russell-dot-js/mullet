# Exercise the shipped executable using the same accessibility interfaces as a screen reader.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$exe = Join-Path $PSScriptRoot 'bin/CheckboxLandOffice.exe'
$app = Start-Process -FilePath $exe -PassThru
function Wait-For($description, [scriptblock]$probe) {
    $deadline = (Get-Date).AddSeconds(60)
    do {
        if ($app.HasExited) { throw "The counter closed while waiting for $description" }
        $answer = & $probe
        if ($answer) { return $answer }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
    throw "Timed out waiting for $description"
}
function Find-Control($id) {
    $match = [Windows.Automation.PropertyCondition]::new(
        [Windows.Automation.AutomationElement]::AutomationIdProperty, $id)
    $window.FindFirst([Windows.Automation.TreeScope]::Descendants, $match)
}
function Press($id) {
    $button = Wait-For $id {
        $control = Find-Control $id
        if ($control -and $control.Current.IsEnabled) { $control }
    }
    $button.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke()
}
try {
    $window = Wait-For 'the clerk to open the window' {
        $app.Refresh()
        if ($app.MainWindowHandle -ne [IntPtr]::Zero) {
            [Windows.Automation.AutomationElement]::FromHandle($app.MainWindowHandle)
        }
    }
    $entry = Wait-For 'title entry' {
        $control = Find-Control 'TitleEntry'
        if ($control -and $control.Current.IsEnabled) { $control }
    }
    $title = 'Take minutes at the meeting about fewer meetings ' + [guid]::NewGuid()
    $entry.GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern).SetValue($title)
    Press 'AddTask'
    [void][Reflection.Assembly]::LoadFrom($exe)
    $counter = [LandOffice.Counter]::new($env:MULLET_SQL)
    $task = Wait-For 'the new task to reach SQL Server' {
        $counter.List().Rows | Where-Object { $_.Title -eq $title }
    }
    Press 'Discharge'
    Wait-For 'SQL Server to record the completion' {
        ($counter.List().Rows | Where-Object { $_.Title -eq $title }).Closed -eq $true
    }
    $glyph = Wait-For 'a completion deed at the counter' {
        $receipt = Find-Control 'ReceiptText'
        $value = $receipt.GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern).Current.Value
        if ($value -match '#\d+ done' -and $value -match '3200 policies') { $value }
    }
    $deeds = $counter.Receipt($task.TaskId)
    foreach ($act in 'add','done') {
        $deed = @($deeds.Rows | Where-Object { $_.Act -eq $act })
        if ($deed.Count -ne 1 -or $deed[0].Hearings -ne 200 -or
            $deed[0].Contracts -ne 3200 -or $deed[0].SettledCents -ne $deed[0].BilledCents) {
            throw "The $act deed failed its independent reconciliation."
        }
        if ($act -eq 'done') {
            # Reconstruct the die strike without loading the Java program or the CLR assembly.
            [long]$stamp = 0
            foreach ($unit in ("close/" + $task.TaskId).ToCharArray()) {
                $stamp = (31 * $stamp + [int]$unit) % 4294967296
            }
            for ($tooth = 1; $tooth -le 9000; $tooth++) {
                $stamp = (31 * $stamp + $tooth) % 4294967296
            }
            if ($deed[0].Stamp -ne $stamp) { throw "A different task's stamp reached settlement" }
            [long]$previous = 0
            [long]$expected = 0
            for ($hearing = 1; $hearing -le 200; $hearing++) {
                [long]$subtotal = 0
                for ($seat = 1; $seat -le 16; $seat++) {
                    $subtotal += 1 + (($stamp + 31 * $hearing + 17 * $seat + $previous) % (11 + $seat))
                }
                $expected += $subtotal
                $previous = $subtotal
            }
            if ($deed[0].BilledCents -ne $expected) { throw 'The previous hearing lost its vote' }
        }
        Write-Output "$act paid $($deed[0].Payee) for 3,200 policies under JVM stamp $($deed[0].Stamp)."
    }
} finally {
    if (-not $app.HasExited) { $app.Kill(); $app.WaitForExit() }
    $app.Dispose()
}
