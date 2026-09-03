#define MyAppName "Trader Planner Pro"
#define MyAppVersion "5.0.0-alpha.2"
#define MyAppExeName "TraderPlannerPro.exe"
#define MyWidgetExeName "TraderPlannerProSessionClock.exe"
[Setup]
AppId={{8D6D0F58-7D16-4C1B-9D0C-20A4F1B8C901}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Trader Planner Pro
DefaultGroupName=Trader Planner Pro
OutputDir=installer
OutputBaseFilename=TraderPlannerPro_Setup_V5_Alpha2
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayName={#MyAppName}
[Tasks]
Name: "sessionclock"; Description: "Start Session Clock widget with Windows"; GroupDescription: "Optional desktop tools:"; Flags: unchecked
[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\{#MyWidgetExeName}"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\Trader Planner Pro"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Trader Planner Pro"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\Trader Planner Pro — Session Clock"; Filename: "{app}\{#MyWidgetExeName}"
Name: "{autodesktop}\Trader Planner Pro — Session Clock"; Filename: "{app}\{#MyWidgetExeName}"
Name: "{userstartup}\Trader Planner Pro — Session Clock"; Filename: "{app}\{#MyWidgetExeName}"; Tasks: sessionclock
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Trader Planner Pro"; Flags: nowait postinstall skipifsilent
