echo $0
whoami
if [ "$1" = "devices" ]; then
  echo 1234567890
elif [ "$1" = "shell" ]; then
  echo simulate adb shell via ssh into shell
  echo sshpass -p adb_password ssh -oStrictHostKeyChecking=no adbshell@localhost
  sshpass -p adb_password ssh -oStrictHostKeyChecking=no adbshell@localhost
  exit_code=$?
  echo "SSH STATUS: $exit_code"
  whoami
elif [ "$1" = "-s" ]; then
  if [ "$2" = "1234567890" ] && [ "$3" = "shell" ]; then
    echo simulate adb shell via ssh into shell
    echo sshpass -p adb_password ssh -oStrictHostKeyChecking=no adbshell@localhost
    sshpass -p adb_password ssh -oStrictHostKeyChecking=no adbshell@localhost
    exit_code=$?
    echo "SSH STATUS: $exit_code"
    whoami
  fi
fi
