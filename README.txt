====================================
Nagios Plugin Python Module (and some plugins)

Author: Ryan C. Catherman
====================================

1. Reasons for writing
2. Getting started
3. Deploying

========================
Reasons for writing
========================
I had deployed nagios at home to send me emails when my work VPN went down or when I
had forgotten to turn on critical VMs. I started looking at the docs on how to write
plugins and figured it would be fun to spend a day or two writing some helpers and tests
to be able to more easily inject data into the system.

There may already be existing python libraries for nagios, but I wanted to learn
by doing so I wrote this.

I hope you find it useful.

======================
Getting started
======================
If you intend to just use any of the plugins provided (have I written any yet?),
jump to the "Deploying" section.

If you intend to dev new ones, or make improvements, these points will be of interest:

 - At the root, you'll find a Makefile with a trivial "make test" rule. This is your friend.
 - If you are writing an actual plugin of value, refer to the "check_random" plugin as a starting point

======================
Deploying
======================
Since the implementation is pretty trivial, for now I find it sufficient to just create
a git clone on my target system and then create symbolic links as needed. If this project
matures, then a more proper installation may be called-for.

# Creating a symlink is as simple as:
$ sudo ln -s ~/nagios.git/plugins/py/src/check_random /usr/lib/nagios/plugins/

# And then create a command and service definition as you would anything else:
define command {
    command_name    check-random
    command_line    /usr/lib/nagios/plugins/check_random --min 0 --max 100 -w 0:90 -c 0:95
}

define service {
    hosts       localhost
    service_description  random
    check_command check-random
    use generic-service
    notification_interval 0
}
