# ==============================================================
# Creer_Tache_BackupCleaner.ps1
# Crée la tâche planifiée Windows pour BackupCleaner
# À exécuter UNE SEULE FOIS en tant qu'Administrateur
# ==============================================================

# --- Paramètres à ajuster si nécessaire ---
$PythonExe      = "C:\Program Files\Python313\python.exe"
$ScriptPath     = "D:\Emmanuel\OneDrive\DEV\Python\projets\BackupCleaner\BackupCleaner.py"
$WorkingDir     = "D:\Emmanuel\OneDrive\DEV\Python"
$HeureLancement = "22:00"
$NomTache       = "BackupCleaner"
$Description    = "Purge quotidienne des fichiers de sauvegarde PostgreSQL OneDrive de plus de 30 jours."

# --- Vérifications préalables ---
if (-not (Test-Path $PythonExe)) {
    Write-Error "Interpréteur Python introuvable : $PythonExe"
    exit 1
}
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script BackupCleaner introuvable : $ScriptPath"
    exit 1
}

# --- Création de la tâche ---
# Les guillemets autour des chemins sont indispensables
# pour les chemins contenant des espaces (ex: "C:\Program Files\")
$Action  = New-ScheduledTaskAction `
               -Execute   $PythonExe `
               -Argument  "`"$ScriptPath`"" `
               -WorkingDirectory $WorkingDir

$Trigger  = New-ScheduledTaskTrigger -Daily -At $HeureLancement

$Settings = New-ScheduledTaskSettingsSet `
                -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
                -RestartCount 1 `
                -RestartInterval (New-TimeSpan -Minutes 5) `
                -StartWhenAvailable `
                -RunOnlyIfNetworkAvailable

# RunOnlyIfNetworkAvailable : indispensable — OneDrive doit être accessible
# StartWhenAvailable : si le PC était éteint à l'heure prévue, la tâche
#                      se lance dès que le PC redémarre

Register-ScheduledTask `
    -TaskName    $NomTache `
    -Description $Description `
    -Action      $Action `
    -Trigger     $Trigger `
    -Settings    $Settings `
    -RunLevel    Highest `
    -Force

if ($?) {
    Write-Host "Tâche '$NomTache' créée avec succès." -ForegroundColor Green
    Write-Host "Exécution quotidienne à $HeureLancement." -ForegroundColor Green
} else {
    Write-Error "Échec de la création de la tâche."
    exit 1
}