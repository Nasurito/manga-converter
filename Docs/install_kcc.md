# Installation de KCC

Pour pouvoir installer KCC, il existe une marche a suivre disponible a cette addresse <https://github.com/ciromattia/kcc/wiki/Installation>, sur cette marche a suivre, celle que j'ai suivis est [la toute derniere](https://github.com/ciromattia/kcc/wiki/Installation#install-from-source) 

## Commandes d'intallation

Commencé par cloné le répot git de kcc :

```bash
    git clone https://github.com/ciromattia/kcc.git
```
Puis installer toutes les dépenadance necessaires :

```bash
    sudo apt-get install python3 python3-dev python3-pip libpng-dev libjpeg-dev p7zip-full python3-pyqt5
```
Installer les requirementes necessaires
```bash
cd kcc
pip3 install -r 'requirements.txt' 
```