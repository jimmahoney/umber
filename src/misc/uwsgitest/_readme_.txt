_readme_.txt

From https://www.digitalocean.com/community/tutorials/
     how-to-serve-flask-applications-with-uswgi-and-nginx-on-ubuntu-18-04

 Serving up a test page on port 5000

   (0) If ufw (uncomplicated firewall) is running, poke a hole in it
       $ sudo ufw allow 5000   # for (1) or (2)

       Activate python environment
       $ cd /var/www/umber; . env/activate_development; cd src/misc/uwsgitest

   (1) a straight flask app, using only utest.py
       (venv)$ python utest.py  # run the flask development server
       ... and point a browser at e.g. cs.bennington.college/utest/:5000

   (2) a uwsgi app in a non-production way, using wsgi.py
       (venv)$ uwsgi --socket 0.0.0.0:5000 --protocol=http -w wsgi:app
       ... and point a browser at e.g. cs.bennington.college/utest/:5000

   (3) running from uwsgi socket reverse-proxy through nginx
       ... lots of config ; see the tutorial for the details.
       Files uwsgi :
         ./utest.ini
         /etc/systemd/system/utest.service
       Running uwsgi :
         $ systemctl start utest    # run now
	 $ systemctl enable utest   # run at system boot
         $ systemctl status utest   # is it running?
       Files nginx :
         # -- in /etc/nginx/sites-enabled/cs.bennington --
         location /utest/ {
           # uwsgi test ; see /var/www/umber/src/misc/uwsgitest
	   include uwsgi_params;
	   uwsgi_pass unix:/var/www/umber/src/misc/uwsgitest/utest.sock;
         }
       Running nginx :
         $ nginx -t   # check syntax
	 # systemctl restart nginx
       Don't need an open port 5000; close it.
         $ ufw delete allow 5000;
       And point a browser at https://cs.benington.college/utest/ .

Notes
-----

* The unix socket file (utest.sock) is created by the uwsgi process
  which must be able to write to that folder. Here's I've set it
  to owner:group www-data:www-data, the same as nginx, and set
  that folder to be consistent.

* The URL route needs to be consistent in the flask utest.py and nginx
  location rules. (Also, I had some issues with the trailing slash. I
  used a trailing slash once but then firefox kept filling when I
  tried to go to a url without it.)

* For log information, look at
  $ less /var/log/nginx/error.log
  $ less /var/log/nginx/access.log
  $ journalctl -u nginx            # what systemd knows
  $ journalctl -u utest            # uwsgi's output
  $ 
