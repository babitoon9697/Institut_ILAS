@echo off
echo Adding Windows Firewall Inbound Rule for Port 8080 (Institut ILAS LAN)...
netsh advfirewall firewall delete rule name="Institut ILAS LAN Port 8080" >nul 2>&1
netsh advfirewall firewall add rule name="Institut ILAS LAN Port 8080" dir=in action=allow protocol=TCP localport=8080
echo Firewall Rule Added Successfully!
pause
