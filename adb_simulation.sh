echo $0
if [ $1 = "devices" ]; then
  echo 1234567890
elif [ $1 = "shell" ]; then
  echo simulate adb shell via ssh into shell
  echo sshpass -p moler_password ssh molerssh@localhost
  sshpass -p moler_password ssh molerssh@localhost
elif [ $1 = "-s" ]; then
  if [ $2 = "1234567890" ] && [ $3 = "shell" ]; then
    echo simulate adb shell via ssh into shell
    echo sshpass -p moler_password ssh molerssh@localhost
    sshpass -p moler_password ssh molerssh@localhost
  fi
fi
