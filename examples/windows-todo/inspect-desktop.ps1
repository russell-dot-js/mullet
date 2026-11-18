# Host the shipped Forms window on an STA and operate its real controls.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
$exe = Join-Path $PSScriptRoot 'bin/CheckboxLandOffice.exe'
$env:PATH = (Split-Path $exe) + ';' + $env:PATH
[void][Reflection.Assembly]::LoadFrom($exe)
[Windows.Forms.Application]::EnableVisualStyles()
$counter = [LandOffice.Counter]::new($env:MULLET_SQL)
$window = [LandOffice.Desktop]::new($counter)

function Wait-For($description, [scriptblock]$probe) {
    $deadline = (Get-Date).AddSeconds(60)
    do {
        [Windows.Forms.Application]::DoEvents()
        if (& $probe) { return }
        Start-Sleep -Milliseconds 30
    } while ((Get-Date) -lt $deadline)
    throw "Timed out waiting for $description. Counter receipt: $($receipt.Text)"
}
function Control($name) {
    $matches = $window.Controls.Find($name, $true)
    if ($matches.Count -ne 1) { throw "Expected a single control named $name" }
    return $matches[0]
}
try {
    $window.Show()
    $entry = Control 'TitleEntry'
    $receipt = Control 'ReceiptText'
    Wait-For 'the counter to open' { $window.Enabled }
    $title = 'Take minutes at the meeting about fewer meetings ' + [guid]::NewGuid()
    $entry.Text = $title
    (Control 'AddTask').PerformClick()
    Wait-For 'the filing receipt' { $window.Enabled -and $receipt.Text -match '3200 policies' }
    $task = $counter.List().Rows | Where-Object { $_.Title -eq $title }
    if (-not $task -or $task.Closed) { throw 'The new intention did not open' }
    (Control 'Discharge').PerformClick()
    Wait-For 'the discharge receipt' { $window.Enabled -and $receipt.Text -match '#[0-9]+ done' }
    $task = $counter.List().Rows | Where-Object { $_.Title -eq $title }
    if (-not $task.Closed) { throw 'The discharged intention is still open' }
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
            for ($tooth = 1; $tooth -le 6400; $tooth++) {
                $stamp = (17 * $stamp + $tooth) % 4294967296
            }
            for ($h = 1; $h -le 200; $h++) {
                for ($s = 1; $s -le 16; $s++) {
                    $stamp = ((($stamp -shl $s) -band 4294967295L) -bor ($stamp -shr (32 - $s))) -bxor (17 * $h + $s)
                }
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
    $window.Close()
    $window.Dispose()
}
