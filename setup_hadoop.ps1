# Script to download and setup Hadoop winutils for Windows
$hadoopVersion = "3.3.1"
$hadoopDir = "hadoop-$hadoopVersion"
$winutilsUrl = "https://raw.githubusercontent.com/steveloughran/winutils/master/hadoop-3.0.0/bin/winutils.exe"
$hadoopDllUrl = "https://raw.githubusercontent.com/steveloughran/winutils/master/hadoop-3.0.0/bin/hadoop.dll"

Write-Host "Setting up Hadoop for Windows..."

# Create hadoop directory structure
if (!(Test-Path $hadoopDir)) {
    New-Item -ItemType Directory -Path $hadoopDir | Out-Null
    New-Item -ItemType Directory -Path "$hadoopDir\bin" | Out-Null
}

# Enable TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Download winutils.exe
Write-Host "Downloading winutils.exe..."
try {
    Invoke-WebRequest -Uri $winutilsUrl -OutFile "$hadoopDir\bin\winutils.exe" -UseBasicParsing
    Write-Host "Downloaded winutils.exe successfully"
} catch {
    Write-Host "Error downloading winutils.exe: $_"
    exit 1
}

# Download hadoop.dll
Write-Host "Downloading hadoop.dll..."
try {
    Invoke-WebRequest -Uri $hadoopDllUrl -OutFile "$hadoopDir\bin\hadoop.dll" -UseBasicParsing
    Write-Host "Downloaded hadoop.dll successfully"
} catch {
    Write-Host "Error downloading hadoop.dll: $_"
    exit 1
}

# Set HADOOP_HOME environment variable for current session
$hadoopHome = (Resolve-Path $hadoopDir).Path
Write-Host "`nHadoop setup complete!"
Write-Host "HADOOP_HOME should be set to: $hadoopHome"
Write-Host "`nTo use in your session, run:"
Write-Host "`$env:HADOOP_HOME = '$hadoopHome'"
