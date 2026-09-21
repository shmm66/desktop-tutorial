#define MyAppName "Trader Planner Pro"
#define MyAppVersion "8.0.0"
#define MyAppExeName "TraderPlannerPro.exe"

[Setup]
AppId={{8D6D0F58-7D16-4C1B-9D0C-20A4F1B8C901}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher="Seyed Hadi Mir Mohammad"
AppCopyright="Copyright (c) 2026 Seyed Hadi Mir Mohammad"
DefaultDirName={localappdata}\Programs\Trader Planner Pro
DefaultGroupName=Trader Planner Pro
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=installer
OutputBaseFilename=TraderPlannerPro_Setup_v8.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes
CloseApplications=yes
CloseApplicationsFilter=TraderPlannerPro.exe
AppMutex=TraderPlannerProV8
UsePreviousAppDir=yes
RestartApplications=no

[Files]
Source: "dist\TraderPlannerPro.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Trader Planner Pro"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Trader Planner Pro"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Trader Planner Pro"; Flags: nowait postinstall skipifsilent
