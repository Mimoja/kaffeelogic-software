rm -r packages
mkdir packages
mkdir Output
cp "kaffelogic-studio.desktop" packages
cp "one-bean.png" packages
cp "lgpl-3.0.txt" packages
cp "kaffelogic-studio.xml" packages
cp "dist/Kaffelogic Studio" packages
fpm -t deb -s dir -n "kaffelogic-studio" -v 4.4.1 --prefix /opt/kaffelogic-studio -f --chdir ./packages --url "https://kaffelogic.com" -m "devops@kaffelogic.com" --description "coffee roast profile management system" --license LGPL3 --after-install linux-desktop-file-install.sh --after-upgrade linux-desktop-file-install.sh --after-remove linux-desktop-file-uninstall.sh --package ./Output
fpm -t rpm -s dir -n "kaffelogic-studio" -v 4.4.1 --prefix /opt/kaffelogic-studio -f --chdir ./packages --url "https://kaffelogic.com" -m "devops@kaffelogic.com" --description "coffee roast profile management system" --license LGPL3 --after-install linux-desktop-file-install.sh --after-upgrade linux-desktop-file-install.sh --after-remove linux-desktop-file-uninstall.sh --package ./Output
