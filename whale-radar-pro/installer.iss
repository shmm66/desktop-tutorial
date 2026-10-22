#define AppName "Whale Radar Pro"
#define AppVersion "2.3.4"
#define AppExeName "WhaleRadarPro.exe"

[Setup]
AppId={{9A55D44C-6A70-4B89-89C4-2F28B3A03B12}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\Whale Radar Pro
DefaultGroupName={#AppName}
OutputDir=dist
OutputBaseFilename=WhaleRadarPro-Setup-v2.3.4
SetupIconFile=assets\whaleradar.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Files]
Source: "dist\WhaleRadarPro.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Whale Radar Pro"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\Whale Radar Pro"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch Whale Radar Pro"; Flags: postinstall nowait skipifsilent
