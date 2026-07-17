; ##########################################################################
; SCRIPT DE INSTALACIÓN - SALUDSA ACTAS (Actualizado)
; ##########################################################################

[Setup]
AppName=Saludsa Actas
AppVersion=1.0
AppPublisher=Saludsa
AppId={{8FCE32A5-99B4-4D2A-A12B-7FBEA4D0F89E}}

; --- REQUISITO 1: INSTALACIÓN POR USUARIO (SIN ADMINS) ---
PrivilegesRequired=lowest
DefaultDirName={localappdata}\SaludsaActas

; --- SOLUCIÓN AL ÍCONO Y METADATOS EN WINDOWS ---
; Esta línea le dice a Windows que use el ícono de tu propio ejecutable en el menú de desinstalación
UninstallDisplayIcon={app}\SaludsaActas.exe
; Forzar a que Windows registre de forma segura el desinstalador para el usuario actual
CreateUninstallRegKey=yes

; Configuración del instalador de salida
OutputBaseFilename=SaludsaActas_Setup
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
DirExistsWarning=no

[Files]
; --- RUTAS RELATIVAS PARA GITHUB Y TU PC ---
; Copia el ejecutable principal desde la carpeta del servidor
Source: "server-flask\dist\SaludsaActas\SaludsaActas.exe"; DestDir: "{app}"; Flags: ignoreversion
; Copia el resto de archivos necesarios
Source: "server-flask\dist\SaludsaActas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; --- REQUISITO 3: MENÚ INICIO Y ACCESO DIRECTO ---
Name: "{userprograms}\Saludsa Actas\Saludsa Actas"; Filename: "{app}\SaludsaActas.exe"
Name: "{userdesktop}\Saludsa Actas"; Filename: "{app}\SaludsaActas.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Run]
Filename: "{app}\SaludsaActas.exe"; Description: "Lanzar Saludsa Actas ahora"; Flags: nowait postinstall skipifsilent

; --- REQUISITO 2: VALIDACIÓN DE LIBREOFFICE ---
[Code]
function InitializeSetup(): Boolean;
var
  ExisteEnHKLM, ExisteEnHKCU: Boolean;
begin
  Result := True;

  ExisteEnHKLM := RegKeyExists(HKLM32, 'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\soffice.exe') or
                  RegKeyExists(HKLM64, 'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\soffice.exe');
                  
  ExisteEnHKCU := RegKeyExists(HKCU32, 'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\soffice.exe') or
                  RegKeyExists(HKCU64, 'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\soffice.exe');

  if not (ExisteEnHKLM or ExisteEnHKCU) then
  begin
    MsgBox('ERROR CRÍTICO:' + #13#10 + #13#10 +
           'No se ha detectado LibreOffice instalado en esta computadora.' + #13#10 +
           'Saludsa Actas requiere LibreOffice para la conversión automatizada de documentos.' + #13#10 + #13#10 +
           'Por favor, instala LibreOffice primero e intenta nuevamente.', mbCriticalError, MB_OK);
    Result := False; 
  end;
end;
