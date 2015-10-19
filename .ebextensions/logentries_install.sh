#!/bin/bash

#############################################
#
#	Logentries Agent Installer
#
#	Supported Distro's:
#		Debian 5 and newer
#		Ubuntu 9.10 and newer
#		Fedora 14 and newer
#		CentOS 5/6  (RedHat 6)
#		Amazon AMI
#
#############################################

VERSION="1.0.6"
#############################################
#
#
#	USER CONFIGURATION
#      --------------------

# Get the account key from the logentries. Here is how you get it
# login to logentries.
# Account-->Profile-->Notifications-->Account key-->click on the orange button and paste the key here

export LE_ACCOUNT_KEY="$1"
export LE_TOKEN_KEY="$2"
# provide a list of logs that logentries agent should follow
declare -a LOGS_TO_FOLLOW=(
/var/log/appear/application.log);
#############################################

# Need root to run this script
if [ "$(id -u)" != "0" ]
then
	echo "Please run this install script as root."
	echo "Usage: sudo bash logentries_install.sh"
	exit 1
fi

KEY_CMD_MIT="gpg --homedir /root/.gnupg --keyserver pgp.mit.edu --recv-keys C43C79AD"
KEY_CMD_UBUNTU="gpg --homedir /root/.gnupg --keyserver keyserver.ubuntu.com --recv-keys C43C79AD"
KEY_CMD_EXPORT="gpg --homedir /root/.gnupg -a --export C43C79AD"
KEY_CMD_COMPLETE="apt-key add /tmp/le.key"
KEY_CMD_CLEAN="rm /tmp/le.key"

DEBIAN_REPO_CONF="/etc/apt/sources.list.d/logentries.list"
DEBIAN_UPDATE="apt-get update"
DEBIAN_AGENT_INSTALL="apt-get install logentries -qq -y"
DEBIAN_PROCTITLE_INSTALL="apt-get install python-setproctitle -qq -y"
DEBIAN_DAEMON_INSTALL="apt-get install logentries-daemon -qq -y"
DEBIAN_CURL_INSTALL="apt-get install curl -y"

REDHAT_REPO_CONF="/etc/yum.repos.d/logentries.repo"
REDHAT_AGENT_INSTALL="yum install logentries -q -y"
REDHAT_PROCTITLE_INSTALL="yum install python-setproctitle -q -y"
REDHAT_DAEMON_INSTALL="yum install logentries-daemon -q -y"
REDHAT_CURL_INSTALL="yum install curl curl-devel -y"

DATE=`date +%D`
CONFIG_DELETE_CMD="rm /etc/le/config"
REGISTER_CMD="le register --hostname=$APPNAME --force"
FOLLOW_CMD="le follow"
LOGGER_CMD="logger -t LogentriesTest Test Message Sent By LogentriesAgent"
DAEMON_RESTART_CMD="service logentries restart"
FOUND=0
AGENT_NOT_FOUND="The agent was not found after installation.\n Please contact support@logentries.com\n"
SET_ACCOUNT_KEY="--account-key="

TAG_NAMES=("Kernel - Process Terminated" "Kernel - Process Killed" "Kernel - Process Started" "Kernel - Process Stopped" "User Logged In" "Invalid User Login attempt" "POSSIBLE BREAK-IN ATTEMPT" "Error")
TAG_PATTERNS=("/terminated with status 100/" "/Killed process/" "/\/proc\/kmsg started/" "/Kernel logging (proc) stopped/" "/Accepted publickey for/" "/Invalid user/" "/POSSIBLE BREAK-IN ATTEMPT/" "/Invalid user admin/")
EVENT_COLOR=("66ff00" "6699ff" "009900" "ff6633" "ff0066" "9999ff" "000099" "999966")

CURL="curl"
CONTENT_HEADER="\"Content-Type: application/json\""
HEADER="-H"
DATA="--data"
API="api.logentries.com"

#declare -a LOGS_TO_FOLLOW=(
#/var/log/messages
#/var/log/dmesg
#/var/log/auth.log
#/var/log/boot.log
#/var/log/daemon.log
#/var/log/dkpg.log
#/var/log/kern.log
#/var/log/lastlog
#/var/log/mail.log
#/var/log/user.log
#/var/log/Xorg.x.log
#/var/log/alternatives.log
#/var/log/btmp
#/var/log/cups
#/var/log/anaconda.log
#/var/log/cron
#/var/log/secure
#/var/log/wtmp
#/var/log/faillog);


for j in "${LOGS_TO_FOLLOW[@]}"
		do
			echo $j 
		done
if [ -f /etc/le/config ]; then
#	printf "\n***** WARNING *****\n"
#	printf "It looks like you already have the Logentries agent registered on this machine\n"
#	read -p "Are you sure you want to clear your existing settings and continue with the installation? (y) or (n): "
#	if [[ $REPLY =~ ^[Yy]$ ]]; then
		$CONFIG_DELETE_CMD
                printf "Already existing logentries config has been removed. OK\n"
		echo "[Main]
user-key = $LE_ACCOUNT_KEY #(env-variable for key)
pull-server-side-config = False
metrics-mem = system
metrics-token = 
metrics-disk = sum
metrics-swap = system
metrics-space = /
metrics-vcpu = 
metrics-net = sum
metrics-interval = 5s
metrics-cpu = system
[$APPNAME]
token = $LE_TOKEN_KEY
path = $LOGS_TO_FOLLOW
destination = /Log Sets/dropbox-test/$APPNAME" >> /etc/le/config
	        $DAEMON_RESTART_CMD >/tmp/logentriesDebug 2>&1
        	/etc/init.d/logentries restart > /tmp/logentriesDebug 2>&1
		exit

#	else
#		echo ""
#		printf "Exiting install script\n"
#		exit 0
#	fi
fi

printf "\n"

# Check if curl is installed, if not, mark it for installation
if hash curl 2>/dev/null;then
	INSTALL_CURL=0
else
	INSTALL_CURL=1
fi

printf "***** Step 1 of 3 - Beginning Logentries Installation *****\n"

if [ -f /etc/issue ] && grep "Amazon Linux AMI" /etc/issue -q; then
	# Amazon Linux AMI
cat << EOL >> $REDHAT_REPO_CONF
[logentries]
name=Logentries repo
enabled=1
metadata_expire=1d
baseurl=http://rep.logentries.com/rh/\$basearch
gpgkey=http://rep.logentries.com/RPM-GPG-KEY-logentries
EOL

	printf "Installing logentries package...\n"
	$REDHAT_AGENT_INSTALL >/tmp/logentriesDebug 2>&1

	# try and install python-setproctitle
	$REDHAT_PROCTITLE_INSTALL >/tmp/logentriesDebug 2>&1

	# Check for agent executable
	if [ ! -f /usr/bin/le ];then
		echo $AGENT_NOT_FOUND
		exit 1
	fi

	# Check if curl is marked for install
	if [ $INSTALL_CURL == "1" ]; then
		$REDHAT_CURL_INSTALL
	fi


	echo ""
	printf "***** Step 2 of 3 - Login *****\n"

	# Prompt the user for their Logentries credentials and register the agent
	if [[ -z "$LE_ACCOUNT_KEY" ]];then
		$REGISTER_CMD
	else
		printf "Account Key found, registering automatically...\n"
		$REGISTER_CMD $SET_ACCOUNT_KEY$LE_ACCOUNT_KEY
	fi


	printf "Installing logentries daemon package...\n"
	$REDHAT_DAEMON_INSTALL >/tmp/logentriesDebug 2>&1

	FOUND=1

elif [ -f /etc/debian_version ]; then

	if hash lsb_release 2>/dev/null; then
		CODENAME=$(lsb_release -c | sed 's/Codename://' | tr -d '[:space:]')
	else
		release=$(cat /etc/debian_version)
		IFS='.' read -a array <<< "$release"

		case "${array[0]}" in
		# Debian
		7) CODENAME="wheezy"
		   ;;
		6) CODENAME="squeeze"
		   ;;
		5) CODENAME="lenny"
		   ;;
		*) CODENAME="UNKNOWN"
		   ;;
		esac
	fi

	if [ "$CODENAME" == "UNKNOWN" ]; then
		printf "Unknown distribution, please contact support@logentries.com\n"
		exit 1
	fi

	# Debian/Ubuntu
	echo "deb http://rep.logentries.com/ ${CODENAME} main" > $DEBIAN_REPO_CONF

	$KEY_CMD_MIT >/tmp/logentriesDebug 2>&1

	if [ "$?" != "0" ]; then
		echo "MIT keyserver not working, fall back to ubuntu keyserver" >>/tmp/logentriesDebug
		# Try different keyserver
		$KEY_CMD_UBUNTU >/tmp/logentriesDebug 2>&1
	fi

	$KEY_CMD_EXPORT >/tmp/le.key
	$KEY_CMD_COMPLETE >/tmp/logentriesDebug 2>&1
	$KEY_CMD_CLEAN

	printf "Updating packages...(This may take a few minutes if you have a lot of updates)\n"
	$DEBIAN_UPDATE >/tmp/logentriesDebug 2>&1

	printf "Installing logentries package...\n"
	$DEBIAN_AGENT_INSTALL >/tmp/logentriesDebug 2>&1
	# Try and install the python-setproctitle package on certain distro's
	$DEBIAN_PROCTITLE_INSTALL >/tmp/logentriesDebug 2>&1

	# Check if agent executable exists before trying to register
	if [ ! -f /usr/bin/le ];then
		echo $AGENT_NOT_FOUND
		exit 1
	fi

	# Check if curl is marked for install
	if [ $INSTALL_CURL == "1" ]; then
		$DEBIAN_CURL_INSTALL
	fi

	printf "\n\n"
	printf "***** Step 2 of 3 - Login *****\n"

	# Prompt the user for their Logentries credentials and register the agent
	if [[ -z "$LE_ACCOUNT_KEY" ]];then
		$REGISTER_CMD
	else
		printf "Account Key found, registering automatically...\n"
		$REGISTER_CMD $SET_ACCOUNT_KEY$LE_ACCOUNT_KEY
	fi

	printf "Installing logentries daemon package...\n"
	$DEBIAN_DAEMON_INSTALL >/tmp/logentriesDebug 2>&1

	FOUND=1

elif [ -f /etc/redhat-release ]; then
	# CentOS 6  /  RHEL 6 / Fedora / Amazon Linux AMI
DIST=centos5
GPG="gpgcheck=0"

if [ -f /etc/centos-release ] || [ -f /etc/fedora-release ]; then
	# Not CentOS 5, use redhat baseurl and gpgcheck
	DIST=rh
	GPG="gpgkey=http://rep.logentries.com/RPM-GPG-KEY-logentries"
fi

cat << EOL >> $REDHAT_REPO_CONF
[logentries]
name=Logentries repo
enabled=1
metadata_expire=1d
baseurl=http://rep.logentries.com/$DIST/\$basearch
$GPG
EOL

	printf "Installing logentries package...\n"
	$REDHAT_AGENT_INSTALL >/tmp/logentriesDebug 2>&1

	# try and install python-setproctitle
	$REDHAT_PROCTITLE_INSTALL >/tmp/logentriesDebug 2>&1

	# Check that agent executable exists before trying to register
	if [ ! -f /usr/bin/le ];then
		echo $AGENT_NOT_FOUND
	fi

	echo "\n"
	printf "***** Step 2 of 3 - Login *****\n"

	# Prompt the user for their Logentries credentials and register the agent
	if [[ -z "$LE_ACCOUNT_KEY" ]];then
		$REGISTER_CMD
	else
		printf "Account Key found, registering automatically...\n"
		$REGISTER_CMD $SET_ACCOUNT_KEY$LE_ACCOUNT_KEY
	fi

	printf "Installing logentries daemon package...\n"
	$REDHAT_DAEMON_INSTALL >/tmp/logentriesDebug 2>&1

	FOUND=1
fi

if [ $FOUND == "1" ]; then
	printf "Logentries Install Complete\n\n"

	if [ -f /var/log/syslog ]; then
		$FOLLOW_CMD /var/log/syslog >/tmp/logentriesDebug 2>&1
		printf "The Logentries agent is now monitoring /var/log/syslog\n"
	fi

	printf "\n\n"

	printf "***** Step 3 of 3 - Additional Logs *****\n"

	FILES_FOUND=0

	for x in "${LOGS_TO_FOLLOW[@]}"
	do
		if [ -f $x ]; then
			let FILES_FOUND=FILES_FOUND+1
		fi
	done

	printf "$FILES_FOUND additional logs found.\n"
	#read -p "Would you like to monitor all of these too? (n) allows you to choose individual logs...(y) or (n): "
	#printf "\n\n"
	#if [[ $REPLY =~ ^[Yy]$ ]];then
		printf "Monitoring all logs\n"
		for j in "${LOGS_TO_FOLLOW[@]}"
		do
			$FOLLOW_CMD $j >/tmp/LogentriesDebug 2>&1
			printf "."
		done
		printf "\n"
	#else
	#	for j in "${LOGS_TO_FOLLOW[@]}"
	#	do
	#		if [ -f $j ]; then
	#			read -p "Would you like to monitor $j ?..(y) or (n): "
	#			if [[ $REPLY =~ ^[Yy]$ ]]; then
	#				$FOLLOW_CMD $j >/tmp/LogentriesDebug 2>&1
	#			fi
	#		fi
	#	done
	#fi
	rm /etc/le/config
	echo "[Main]
user-key = $LE_ACCOUNT_KEY #(env-variable for key)
pull-server-side-config = False
metrics-mem = system
metrics-token = 
metrics-disk = sum
metrics-swap = system
metrics-space = /
metrics-vcpu = 
metrics-net = sum
metrics-interval = 5s
metrics-cpu = system
[$APPNAME]
token = $LE_TOKEN_KEY
path = $LOGS_TO_FOLLOW
destination = /Log Sets/dropbox-test/$APPNAME" >> /etc/le/config
	$DAEMON_RESTART_CMD >/tmp/logentriesDebug 2>&1
	/etc/init.d/logentries restart > /tmp/logentriesDebug 2>&1
	printf "\n\n"
	printf "***** Install Complete! *****\n"
	printf "Please note that it may take a few moments for the log data to show in your account.\n\n"


else
	printf "Unknown distribution. Please contact support@logentries.com with your system details\n\n"
fi
