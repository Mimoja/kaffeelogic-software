echo Installing mime types
cp /opt/kaffelogic-studio/kaffelogic-studio.xml /usr/share/mime/packages
update-mime-database /usr/share/mime
echo Installing desktop icon
desktop-file-install /opt/kaffelogic-studio/kaffelogic-studio.desktop
update-desktop-database /usr/share/applications





