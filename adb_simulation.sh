echo $0
if [ $1 = "devices" ]; then
  echo 1234567890
elif [ $1 = "shell" ]; then
  echo simulate adb shell via ssh into shell
  echo sshpass -p adb_password ssh adbshell@localhost
  sshpass -p adb_password ssh adbshell@localhost
elif [ $1 = "-s" ]; then
  if [ $2 = "1234567890" ] && [ $3 = "shell" ]; then
    echo simulate adb shell via ssh into shell
    echo sshpass -p adb_password ssh adbshell@localhost
    sshpass -p adb_password ssh adbshell@localhost
  fi
fi
