#define MyAppName "Trader Planner Pro"
#define MyAppVersion "10.0.0"
#define MyAppExeName "TraderPlannerPro.exe"

[Setup]
SetupArchitecture=x64
AppId={{8D6D0F58-7D16-4C1B-9D0C-20A4F1B8C901}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher="Seyed Hadi Mir Mohammad"
AppCopyright="Copyright (c) 2026 Seyed Hadi Mir Mohammad"
DefaultDirName={localappdata}\Programs\Trader Planner Pro
DefaultGroupName=Trader Planner Pro
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=installer
OutputBaseFilename=TraderPlannerPro_Setup_v10.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\trader_planner_logo.ico
WizardImageFile=assets\installer_wizard.bmp
WizardSmallImageFile=assets\installer_small.bmp
WizardImageStretch=no
WizardSmallImageStretch=no
AppComments=Premium glass trading workspace with live market services and integrated Trading Desk
SetupLogging=yes
Uninstallable=yes
CloseApplications=yes
CloseApplicationsFilter=TraderPlannerPro.exe
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
