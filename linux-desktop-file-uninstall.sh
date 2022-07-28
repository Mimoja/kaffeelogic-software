echo Uninstalling mime types
rm /usr/share/mime/packages/kaffelogic-studio.xml
update-mime-database /usr/share/mime
echo Uninstalling desktop icon
rm /usr/share/applications/kaffelogic-studio.desktop
update-desktop-database /usr/share/applications


