To be added

project manager-anthony

presentation manager-Francisco

requirements manager-chris

Design manager-ish

Testing manager-theonlyachoudhary

#Setting up the Project for Team 5
#Needed Tools 
- Python 3.8 and onward 
    - Install Python from [python.org](https://www.python.org/downloads/)
- Git CLI
    - Install Git from [git-scm.com](https://git-scm.com/downloads)
- GitHub CLI
    - Install GitHub CLI from [cli.github.com](https://cli.github.com/)
- Docker
    - Install Docker from [docker.com](https://www.docker.com/get-started)
- VsCode(Easier to work with)
    - Install VsCode from [code.visualstudio.com](https://code.visualstudio.com/)
    - Also DownLoad the Docker Extenstion

#Clone the GitHub Repo
helpful commands ls and dir cd ..(move back) cd(location)

Using Cmd, powershell, etc

git clone https://github.com/DePaul-Spring-2025-CSC-394-903/mini-project-team-5.git (In some directory that you can access)

Example:(Dont forget using some kind of bash ie powershell cmd etc)

git clone https://github.com/DePaul-Spring-2025-CSC-394-903/mini-project-team-5.git Desktop/Csc394/mini-project-team-5

To access in terminal cd Desktop/projects/mini-project-team-5

#In Some bash(Also Dont forget to go to that directory)

docker-compose up

To See the website http://localhost:8000/ on any browser 


If postgres database is not updating:

sudo docker-compose exec db psql -U postgres -d template1
SELECT pid, pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'postgres';

DROP DATABASE postgres;
CREATE DATABASE postgres;

\q

sudo docker-compose exec web python manage.py migrate
