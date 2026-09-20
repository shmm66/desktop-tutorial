#define MyAppName "Trader Planner Pro"
#define MyAppVersion "7.3.1"
#define MyAppExeName "TraderPlannerPro.exe"
[Setup]
AppId={{8D6D0F58-7D16-4C1B-9D0C-20A4F1B8C901}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher="Seyed Hadi Mir Mohammad"
AppCopyright="Copyright (c) 2026 Seyed Hadi Mir Mohammad"
DefaultDirName={autopf}\Trader Planner Pro
DefaultGroupName=Trader Planner Pro
SetupIconFile=app.ico
OutputDir=installer
OutputBaseFilename=TraderPlannerPro_Setup_v7.3.1
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\Trader Planner Pro"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Trader Planner Pro"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Trader Planner Pro"; Flags: nowait postinstall skipifsilent
