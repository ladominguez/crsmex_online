# Automatic repeating earthquake detector.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This code automatically detects repeating earthquakes reported by the Mexican Seismological Service ([SSN]
(https://www.ssn.unam.mx/)). When a new earthquake is reported through the SSN Twitter Feed, the code looks for nearby
sequences previously reported. In this case, we are using a 22-year catalog from 2001-2022.


# Installation.
1. To be able to read the Twitter fee from SSN, you must have a developer [Twitter acccount](https://datascienceparichay.com/article/get-data-from-twitter-api-in-python-step-by-step-guide/).
2. Once you obtain your credentials (`API_KEY_TWITTER`,`API_KEY_SECRET_TWITTER`), you must save them as enviromental
   variables. For security, <b>NEVER</b> include this values within your code as they may get posted easily. Add you
   credentals to your `.bashrc`.
```
export API_KEY_TWITTER="(Fill)"
export API_KEY_SECRET_TWITTER="(Fill)"
export ROOT_CRSMEX="(Fill)"
```
3. Clone the repository
```
git clone https://github.com/ladominguez/crsmex_online.git
```

4. Go to the directory, create and activate conda enviroment. 
```
cd crsmex_online
conda create -n twitter python=3.8
conda activate twitter
```

5. Create a link to the service
```
ln -s $PATH/crsmex.service /etc/systemd/system/crsmex.service
```

6. Reload the system service files to use the new service, and start the service.
```
sudo systemctl daemon-reload
systemctl --user start crsmex
```


