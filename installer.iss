; Inno Setup Script for Website Blocker & Shield
; Automatically generated for Community Release

[Setup]
AppName=Website Blocker
AppVersion=1.0.0
AppPublisher=Community Shield
DefaultDirName={autopf}\WebsiteBlocker
DefaultGroupName=Website Blocker
UninstallDisplayIcon={app}\WebsiteBlocker.exe
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=..\dist-installer
OutputBaseFilename=WebsiteBlocker-Setup
PrivilegesRequired=admin
DisableWelcomePage=no

[Files]
Source: "dist\WebsiteBlocker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Website Blocker"; Filename: "{app}\WebsiteBlocker.exe"
Name: "{group}\Uninstall Website Blocker"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Website Blocker"; Filename: "{app}\WebsiteBlocker.exe"

[Run]
; 1. Configure the user-chosen Master Password silently
Filename: "{app}\WebsiteBlocker.exe"; Parameters: "--set-init-password ""{code:GetMasterPassword}"""; Flags: runhidden
; 2. Start the background protection daemon immediately
Filename: "{app}\WebsiteBlocker.exe"; Parameters: "--daemon"; Flags: runhidden nowait
; 3. Offer to open the blocker console
Filename: "{app}\WebsiteBlocker.exe"; Description: "Launch Website Blocker Console"; Flags: nowait postinstall skipifsilent

[Code]
var
  WarningPage: TOutputMsgMemoWizardPage;
  PasswordPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  // Page 1: Mandatory Warning Notice
  WarningPage := CreateOutputMsgMemoPage(
    wpWelcome,
    'CRITICAL SECURITY WARNING: READ CAREFULLY',
    'Irreversible Password Protection Notice',
    'PLEASE READ BEFORE CONTINUING:',
    '=====================================================================' + #13#10 +
    '                     WARNING: STRICT SECURITY NOTICE' + #13#10 +
    '=====================================================================' + #13#10#13#10 +
    '1. This application protects your system using strict cryptographic access controls.' + #13#10#13#10 +
    '2. In the next step, you will be required to set a MASTER PASSWORD.' + #13#10#13#10 +
    '3. IMPORTANT WARNING:' + #13#10 +
    '   The blocker console and settings will NEVER OPEN unless you provide this exact password.' + #13#10 +
    '   Protection cannot be paused, stopped, or disabled without this password.' + #13#10#13#10 +
    '4. An Emergency Recovery Key will be generated in your installation folder.' + #13#10 +
    '   Please store both your password and recovery key in a safe place.' + #13#10#13#10 +
    'Click "Next" ONLY if you understand and accept this responsibility.'
  );

  // Page 2: Master Password Prompt
  PasswordPage := CreateInputQueryPage(
    WarningPage.ID,
    'Set Master Password',
    'Create the password required to open or modify the blocker',
    'Please enter the master password. You will need this password every time you open the blocker:'
  );
  PasswordPage.Add('Master Password:', True);
  PasswordPage.Add('Confirm Password:', True);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = PasswordPage.ID then
  begin
    if (PasswordPage.Values[0] = '') then
    begin
      MsgBox('Password cannot be empty. Please enter a valid master password.', mbError, MB_OK);
      Result := False;
    end
    else if (PasswordPage.Values[0] <> PasswordPage.Values[1]) then
    begin
      MsgBox('Passwords do not match. Please re-enter both fields carefully.', mbError, MB_OK);
      Result := False;
    end
    else if Length(PasswordPage.Values[0]) < 4 then
    begin
      MsgBox('Password must be at least 4 characters long.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function GetMasterPassword(Param: String): String;
begin
  Result := PasswordPage.Values[0];
end;
