# ============================================================
# Setup SMTP OAuth2 para Office 365
# Ejecutar UNA SOLA VEZ como administrador de Microsoft 365
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup SMTP OAuth2 - Office 365" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Datos de la app Azure AD ---
$AppId = "4c844251-2190-41c4-bb73-aeab012efea7"
$ServiceId = "3de21a48-8acd-4e8e-b85c-4e53a5d760b2"
$Mailbox = "facturacion@cristalceramicas.com"
$GroupName = "SMTP OAuth Apps"

# --- Paso 1: Instalar modulo si no existe ---
Write-Host "[1/5] Verificando modulo ExchangeOnlineManagement..." -ForegroundColor Yellow
if (-not (Get-Module -ListAvailable -Name ExchangeOnlineManagement)) {
    Write-Host "  Instalando modulo..." -ForegroundColor Gray
    Install-Module ExchangeOnlineManagement -Force -Scope CurrentUser
    Write-Host "  Modulo instalado" -ForegroundColor Green
} else {
    Write-Host "  Modulo ya instalado" -ForegroundColor Green
}

# --- Paso 2: Conectar a Exchange Online ---
Write-Host ""
Write-Host "[2/5] Conectando a Exchange Online..." -ForegroundColor Yellow
Write-Host "  (Se abrira ventana de login de Microsoft)" -ForegroundColor Gray
Connect-ExchangeOnline -ShowBanner:$false
Write-Host "  Conectado" -ForegroundColor Green

# --- Paso 3: Registrar Service Principal ---
Write-Host ""
Write-Host "[3/5] Registrando Service Principal..." -ForegroundColor Yellow
try {
    New-ServicePrincipal -AppId $AppId -ServiceId $ServiceId -ErrorAction Stop
    Write-Host "  Service Principal registrado" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "  Service Principal ya existia (OK)" -ForegroundColor Green
    } else {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# --- Paso 4: Crear grupo de seguridad ---
Write-Host ""
Write-Host "[4/5] Creando grupo de seguridad '$GroupName'..." -ForegroundColor Yellow
try {
    $group = Get-DistributionGroup -Identity $GroupName -ErrorAction SilentlyContinue
    if ($group) {
        Write-Host "  Grupo ya existia" -ForegroundColor Green
        # Asegurar que el buzon esta en el grupo
        try {
            Add-DistributionGroupMember -Identity $GroupName -Member $Mailbox -ErrorAction Stop
            Write-Host "  Buzon $Mailbox anadido al grupo" -ForegroundColor Green
        } catch {
            if ($_.Exception.Message -like "*already a member*") {
                Write-Host "  Buzon $Mailbox ya era miembro (OK)" -ForegroundColor Green
            } else {
                Write-Host "  Error al anadir miembro: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    } else {
        New-DistributionGroup -Name $GroupName -Type Security -Members $Mailbox -ErrorAction Stop
        Write-Host "  Grupo creado con buzon $Mailbox" -ForegroundColor Green
    }
} catch {
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}

# --- Paso 5: Crear politica de acceso ---
Write-Host ""
Write-Host "[5/5] Creando politica de acceso para la app..." -ForegroundColor Yellow
try {
    New-ApplicationAccessPolicy -AppId $AppId -PolicyScopeGroupId $GroupName -AccessRight RestrictAccess -Description "JobersSMTP SMTP OAuth2 access" -ErrorAction Stop
    Write-Host "  Politica creada" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "  Politica ya existia (OK)" -ForegroundColor Green
    } else {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# --- Verificar ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Verificacion" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service Principals:" -ForegroundColor Yellow
Get-ServicePrincipal | Where-Object { $_.AppId -eq $AppId } | Format-List AppId, ServiceId, ObjectId

Write-Host "Politicas de acceso:" -ForegroundColor Yellow
Get-ApplicationAccessPolicy | Where-Object { $_.AppId -eq $AppId } | Format-List AppId, PolicyScopeGroupId, AccessRight

# --- Desconectar ---
Write-Host ""
Disconnect-ExchangeOnline -Confirm:$false
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup completado!" -ForegroundColor Green
Write-Host "  Puede tardar hasta 30 min en propagarse" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
