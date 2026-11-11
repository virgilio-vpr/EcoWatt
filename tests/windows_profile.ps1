param(
    [Parameter(Mandatory=$true)][ValidateSet('create','delete')][string]$Action,
    [Parameter(Mandatory=$true)][ValidatePattern('^EcoWatt\.Synthetic\.[a-f0-9]{32}$')][string]$Name
)
$ErrorActionPreference = 'Stop'
# Ponte de teste fora da identidade MSIX do Python Store. Sem instalação,
# elevação, alteração de firewall ou ACL no runtime original.
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class EcoWattSyntheticProfile {
    [DllImport("userenv.dll", CharSet=CharSet.Unicode)]
    public static extern int CreateAppContainerProfile(string name, string display,
        string description, IntPtr capabilities, uint count, out IntPtr sid);
    [DllImport("userenv.dll", CharSet=CharSet.Unicode)]
    public static extern int DeleteAppContainerProfile(string name);
    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern bool ConvertSidToStringSid(IntPtr sid, out IntPtr text);
    [DllImport("advapi32.dll")] public static extern IntPtr FreeSid(IntPtr sid);
    [DllImport("kernel32.dll")] public static extern IntPtr LocalFree(IntPtr ptr);
}
'@
if ($Action -eq 'create') {
    $sid = [IntPtr]::Zero
    $result = [EcoWattSyntheticProfile]::CreateAppContainerProfile(
        $Name, $Name, 'Synthetic isolation probe', [IntPtr]::Zero, 0, [ref]$sid)
    if ($result -lt 0) { throw "create_profile HRESULT $result" }
    $text = [IntPtr]::Zero
    try {
        if (-not [EcoWattSyntheticProfile]::ConvertSidToStringSid($sid, [ref]$text)) {
            [void][EcoWattSyntheticProfile]::DeleteAppContainerProfile($Name)
            throw 'convert_profile_sid'
        }
        [Runtime.InteropServices.Marshal]::PtrToStringUni($text)
    } finally {
        [void][EcoWattSyntheticProfile]::FreeSid($sid)
        if ($text -ne [IntPtr]::Zero) { [void][EcoWattSyntheticProfile]::LocalFree($text) }
    }
} else {
    $result = [EcoWattSyntheticProfile]::DeleteAppContainerProfile($Name)
    if ($result -lt 0) { throw "delete_profile HRESULT $result" }
}
